"""Training-free memory repair of a turn-k+1 Goal Force video (design: multiturn/memory_plan.md).

Two conditions share the same Goal Force video, the same object tracks and the same edit mask; they differ only in
what the memory contributes:

  appearance : "appearance memory only" (the naive way, = E2b of appearance/)
               source = object regions grayed out; VACE reference = ORIGINAL turn-1 crops at their ORIGINAL places.
               No state information -> expected to pull objects back to the initial pose (the #2 effect).
  full       : appearance memory + state constraint
               state:      per object and frame, the tracked mask is trusted only if it is plausible (visible, area within
                           [0.3, 3] x its turn-start area, no >50% overlap with another object, R-DINO vs latest state
                           >= 0.5). Untrusted -> the object keeps the SHAPE and PIXELS of its last trusted frame and follows
                           the tracked centroid rigidly (if the track is lost it stays where last seen; released once it
                           has mostly left the frame). The implausible pixels (fused slab, ghost, duplicate) are replaced
                           by the clean background plate.  (v1 held untrusted objects in place; see memory_plan.md)
               appearance: pixels always come from the LATEST state (current frame if trusted, else the last trusted
                           frame); the original memory crop only contributes colour statistics (Lab mean/std transfer,
                           strength 0.5). VACE reference = latest-state crops at their latest places.
               -> original image gives appearance only; position and pose always follow the last frame / track.

    venv/bin/python -I multiturn/memory_repair.py --video T2.mp4 --track <evaluate out>/track \
        --prev_state t1/state.json --target white_ball --cond full --out <dir> --prompt "..."
Output: <out>/<cond>.mp4 (+ inputs, meta). Skips if the output exists.
"""
import argparse
import sys
import json
import time
from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np
from PIL import Image

KEEP_FIRST = 4
APPEAR_MIN = 0.5   # same threshold as evaluate.py APPEAR_BAD: R-DINO vs latest state below this -> untrusted
DIL = 11


def rgb2lab(x):
    return cv2.cvtColor(x, cv2.COLOR_RGB2LAB).astype(np.float32)


def lab2rgb(x):
    return cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)


def color_match(pix, ref_pix, strength=0.5):
    """pix [N,3] uint8 -> shifted towards the Lab mean/std of ref_pix [M,3]."""
    if len(pix) < 10 or len(ref_pix) < 10:
        return pix
    a = rgb2lab(pix[None])[0]
    b = rgb2lab(ref_pix[None])[0]
    out = (a - a.mean(0)) / (a.std(0) + 1e-3) * b.std(0) + b.mean(0)
    out = (1 - strength) * a + strength * out
    return lab2rgb(out[None])[0]


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def touches_border(m, H, W, b=4):
    x0, y0, x1, y1 = bbox(m)
    return x0 <= b or y0 <= b or x1 >= W - b or y1 >= H - b


def build(frames, masks, prev_last, prev_masks_last, memory, mem_dir, target, rlat=None):
    T, H, W, _ = frames.shape
    names = list(masks)
    k = np.ones((DIL, DIL), np.uint8)
    dil = {n: np.stack([cv2.dilate(m.astype(np.uint8), k) > 0 for m in masks[n]]) for n in names}
    cover = np.zeros((T, H, W), bool)
    for n in names:
        cover |= dil[n]
    stack = np.where(cover[..., None], np.nan, frames.astype(np.float32))
    plate = np.nanmedian(stack, axis=0)
    plate = np.where(np.isnan(plate), prev_last, plate).astype(np.uint8)

    mem_pix = {}
    for n in names:
        mc = np.array(Image.open(mem_dir / memory[n]["crop"]).convert("RGB"))
        mm = np.load(mem_dir / f"{n}_mask.npy")
        x0, y0, x1, y1 = bbox(mm)
        # crop() pads by 4 px; recover pixels with a white-background test instead of exact alignment
        mem_pix[n] = mc[(mc < 250).any(-1)]

    # ---- state constraint: trusted / held masks per object and frame
    # untrusted frame -> the object keeps the SHAPE + PIXELS of its last trusted frame (latest plausible state) and
    # follows the tracked centroid rigidly (motion stays Goal Force's); if the track is lost it stays where it was last seen.
    held_mask = {n: np.zeros((T, H, W), bool) for n in names}
    held_src = {n: [None] * T for n in names}    # frame index whose pixels are used (-1 = previous-turn last frame)
    held_off = {n: [(0, 0)] * T for n in names}  # integer (dy, dx) shift applied to the source mask
    trust_log = {}

    def cen(mk):
        ys, xs = np.nonzero(mk)
        return np.array([ys.mean(), xs.mean()])

    def shifted(mk, dy, dx):
        out = np.zeros_like(mk)
        ys, xs = np.nonzero(mk)
        ys, xs = ys + dy, xs + dx
        k = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        out[ys[k], xs[k]] = True
        return out

    for n in names:
        m = masks[n]
        a_ref = max(int(m[0].sum()), 1)
        last_t, off = None, (0, 0)
        tl = []
        for t in range(T):
            a = int(m[t].sum())
            ok = a >= 30 and 0.3 <= a / a_ref <= 3.0
            if ok and rlat is not None and rlat.get(n) is not None and rlat[n][t] is not None and rlat[n][t] < APPEAR_MIN:
                ok = False   # mask looks plausible but the content is no longer this object (fused slab, duplicate, ghost)
            if ok:
                for n2 in names:
                    if n2 != n and masks[n2][t].sum() >= 30:
                        ov = np.logical_and(m[t], masks[n2][t]).sum() / min(a, masks[n2][t].sum())
                        if ov > 0.5:
                            ok = False
                            break
            src_m = m[last_t] if last_t is not None else prev_masks_last[n]
            if ok:
                last_t, off = t, (0, 0)
                held_mask[n][t] = m[t]
                held_src[n][t] = t
            elif src_m.sum() >= 30:
                if a >= 30:  # follow the (implausible) track's centroid
                    d = cen(m[t]) - cen(src_m)
                    off = (int(round(d[0])), int(round(d[1])))
                hm = shifted(src_m, *off)
                if hm.sum() >= 0.5 * src_m.sum():   # released once it has mostly left the frame
                    held_mask[n][t] = hm
                    held_src[n][t] = last_t if last_t is not None else -1
                    held_off[n][t] = off
            tl.append(bool(ok))
        trust_log[n] = {"trusted_frames": int(sum(tl)),
                        "held_frames": int(sum(1 for t in range(T) if held_src[n][t] is not None and held_src[n][t] != t))}

    # shared edit mask (identical for both conditions)
    edit = cover.copy()
    for n in names:
        edit |= np.stack([cv2.dilate(h.astype(np.uint8), k) > 0 for h in held_mask[n]])
    edit[:KEEP_FIRST] = False

    # ---- full: composite source
    comp = frames.copy()
    for t in range(KEEP_FIRST, T):
        f = comp[t]
        # remove every tracked object region that is not trusted at t (fused slab, ghosts)
        for n in names:
            if held_src[n][t] != t and masks[n][t].sum() > 0:
                f[dil[n][t]] = plate[dil[n][t]]
        for n in names:
            s = held_src[n][t]
            if s is None:
                continue
            src_img = prev_last if s == -1 else frames[s]
            src_m = prev_masks_last[n] if s == -1 else masks[n][s]
            dy, dx = held_off[n][t]
            ys, xs = np.nonzero(src_m)
            pix = color_match(src_img[ys, xs], mem_pix[n])
            ys2, xs2 = ys + dy, xs + dx
            k = (ys2 >= 0) & (ys2 < H) & (xs2 >= 0) & (xs2 < W)
            f[ys2[k], xs2[k]] = pix[k]
    # ---- appearance-only: gray source
    gray = frames.copy()
    gray[edit] = 127

    # references
    ref_app = np.full((H, W, 3), 255, np.uint8)
    for n in names:
        mm = np.load(mem_dir / f"{n}_mask.npy")
        f0 = None
        mc = np.array(Image.open(mem_dir / memory[n]["crop"]).convert("RGB"))
        x0, y0, x1, y1 = bbox(mm)
        # crop() padded by 4 px around the mask bbox, clipped to the image
        px0, py0 = max(x0 - 4, 0), max(y0 - 4, 0)
        h, w = mc.shape[:2]
        reg = ref_app[py0:py0 + h, px0:px0 + w]
        sub = mc[:reg.shape[0], :reg.shape[1]]
        sel = (sub < 250).any(-1)
        reg[sel] = sub[sel]
    ref_full = np.full((H, W, 3), 255, np.uint8)
    for n in names:
        pm = prev_masks_last[n]
        if pm.sum() < 30:
            continue
        ref_full[pm] = color_match(prev_last[pm], mem_pix[n])
    return comp, gray, edit, ref_app, ref_full, trust_log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--track", required=True, help="dir with masks.npz/state.json of this video (stride 1)")
    ap.add_argument("--prev_state", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--cond", choices=["appearance", "full", "appearance_global", "lora", "nolora", "lora_orig"], required=True)
    ap.add_argument("--lora", default=None, help="LoRA weights (train_vace_lora.py) for --cond lora")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--prep_only", action="store_true")
    ap.add_argument("--eval", default=None, help="baseline eval.json of this video (per-frame R-DINO vs latest state, stride 1)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    final = out / f"{args.cond}.mp4"
    if final.exists():
        print("[skip] exists", final)
        return

    st = json.load(open(Path(args.track) / "state.json"))
    assert st["stride"] == 1, "repair needs a stride-1 track"
    prev = json.load(open(args.prev_state))
    mem_dir = Path(st["memory_dir"])
    memory = json.load(open(mem_dir / "memory.json"))
    frames = iio.imread(args.video)
    masks = dict(np.load(Path(args.track) / "masks.npz"))
    pml = {n: v[-1] for n, v in np.load(Path(args.prev_state).parent / "masks.npz").items()}
    prev_last = np.array(Image.open(prev["last_frame"]).convert("RGB"))

    rlat = None
    if args.eval:
        ev = json.load(open(args.eval))
        assert ev["series"]["stride"] == 1
        rlat = ev["series"]["r_dino_latest"]
    comp, gray, edit, ref_app, ref_full, trust = build(frames, masks, prev_last, pml, memory, mem_dir, args.target, rlat)
    src = comp if args.cond == "full" else gray
    ref = ref_full if args.cond == "full" else ref_app
    if args.cond in ("lora", "nolora", "lora_orig"):
        # lora_plan.md: NO state rule (motion/pose = Goal Force). Source = current pixels colour-matched to memory,
        # edit mask = dilated tracked masks only, reference = latest-state crops at their latest places.
        k = np.ones((DIL, DIL), np.uint8)
        edit = np.zeros(frames.shape[:3], bool)
        src = frames.copy()
        for n, m in masks.items():
            mc = np.array(Image.open(mem_dir / memory[n]["crop"]).convert("RGB"))
            mem_pix = mc[(mc < 250).any(-1)]
            for t in range(KEEP_FIRST, len(frames)):
                if m[t].sum() >= 30:
                    src[t][m[t]] = color_match(frames[t][m[t]], mem_pix)
                    edit[t] |= cv2.dilate(m[t].astype(np.uint8), k) > 0
        # lora/nolora: reference = latest-state crops. lora_orig: reference = ORIGINAL turn-1 crops (appearance memory);
        # the LoRA was trained to take appearance from a reference in a different pose without copying the pose.
        ref = ref_app if args.cond == "lora_orig" else ref_full
    if args.cond == "appearance_global":
        # diagnostic only (chips no-force control): the WHOLE frame may be re-rendered (after KEEP_FIRST), the source
        # video is kept as context (not grayed), and the reference is the original crop at its ORIGINAL place.
        # If appearance memory pulls objects back to their initial position, it can only show up here.
        edit = np.ones_like(edit)
        edit[:KEEP_FIRST] = False
        src = frames.copy()
    tag = args.cond
    iio.imwrite(out / f"{args.cond}_src.mp4", src, fps=15, codec="libx264", quality=9)
    iio.imwrite(out / ("edit_mask.mp4" if args.cond != "appearance_global" else "edit_mask_global.mp4"), (edit[..., None].repeat(3, -1) * 255).astype(np.uint8), fps=15, codec="libx264", quality=9)
    Image.fromarray(ref).save(out / f"{args.cond}_reference.png")
    json.dump(trust, open(out / f"{args.cond}_trust.json", "w"), indent=1)
    print("trust:", trust, " edit px/frame:", int(edit.sum((1, 2)).mean()))
    if args.prep_only:
        return

    import torch
    from diffsynth.data import save_video
    from diffsynth.pipelines.wan_video_new import ModelConfig, WanVideoPipeline
    M = "./models/Wan-AI"
    NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，"
           "丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，"
           "静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")
    pipe = WanVideoPipeline.from_pretrained(
        torch_dtype=torch.bfloat16, device="cuda",
        model_configs=[ModelConfig(path=f"{M}/Wan2.1-VACE-1.3B/diffusion_pytorch_model.safetensors"),
                       ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/models_t5_umt5-xxl-enc-bf16.pth"),
                       ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/Wan2.1_VAE.pth")],
        tokenizer_config=ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/google/umt5-xxl"))
    if args.cond in ("lora", "lora_orig"):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from lora_utils import load_lora
        print("LoRA tensors loaded:", load_lora(pipe, args.lora))
    if args.cond not in ("lora", "nolora", "lora_orig"):  # peft LoRA layers are not handled by DiffSynth's VRAM wrappers; both
        pipe.enable_vram_management()        # lora/nolora run fully on GPU so the pair stays comparable
    T, H, W, _ = frames.shape
    T = (T - 1) // 4 * 4 + 1
    t0 = time.time()
    video = pipe(prompt=args.prompt, negative_prompt=NEG,
                 vace_video=[Image.fromarray(x) for x in src[:T]],
                 vace_video_mask=[Image.fromarray((e * 255).astype(np.uint8)).convert("RGB") for e in edit[:T]],
                 vace_reference_image=Image.fromarray(ref), height=H, width=W, num_frames=T,
                 seed=args.seed, num_inference_steps=50, tiled=True)
    save_video(video, str(final), fps=15, quality=9)
    json.dump({"cond": args.cond, "video": args.video, "seconds": time.time() - t0, "prompt": args.prompt,
               "seed": args.seed, "trust": trust}, open(out / f"{args.cond}_meta.json", "w"), indent=1)
    print(args.cond, "done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
