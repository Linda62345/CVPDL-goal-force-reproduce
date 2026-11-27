"""Test 1 of lora_plan.md: held-out DAVIS val videos with fixed synthetic degradations.

Stage gen   (venv):        venv/bin/python -I multiturn/lora_eval.py gen --variant base
                           venv/bin/python -I multiturn/lora_eval.py gen --variant step-1000 --lora outputs/lora/vace_appearance/step-1000.safetensors
Stage score (imagegen):    HF_HOME=imagegen/hf_cache imagegen/venv/bin/python -I multiturn/lora_eval.py score

Metrics per sample (edited frames only, inside the edit mask / object mask of the CLEAN target):
  psnr      PSNR of the edit region vs the clean target                       (closer to the truth = better)
  r_dino    DINOv2 similarity of the object crop (target mask) vs target crop (appearance right = better)
  ref_copy  sim(output crop, reference) - sim(target crop, reference)         (> 0: output drifted toward the
            reference, e.g. copied its pose; ~0 or < 0 is good)
"""
import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402

OUT = HERE.parent / "outputs/lora/eval_davis"


def build_samples(T=33):
    from lora_data import davis_split, load_video, make_sample
    d = OUT / "samples"
    d.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(davis_split("val")):
        f = d / f"{name}.npz"
        if f.exists():
            continue
        fr, lb = load_video(name)
        rng = random.Random(1000 + i)
        s = None
        for _ in range(50):
            s = make_sample(name, fr, lb, rng, T)
            if s is not None:
                break
        if s is None:
            print("skip", name)
            continue
        np.savez_compressed(f, target=s["target"], source=s["source"], mask=s["mask"], reference=s["reference"],
                            prompt=s["prompt"], meta=json.dumps(s["meta"]))
        print("sample", name)


def gen(variant, lora):
    import imageio.v3 as iio
    from PIL import Image
    from lora_utils import load_lora, load_vace_pipe
    build_samples()
    pipe = load_vace_pipe("cuda")
    if lora:
        print("LoRA tensors:", load_lora(pipe, lora))
    vd = OUT / variant
    vd.mkdir(parents=True, exist_ok=True)
    for f in sorted((OUT / "samples").glob("*.npz")):
        o = vd / (f.stem + ".mp4")
        if o.exists():
            continue
        s = np.load(f)
        T = len(s["target"])
        video = pipe(prompt=str(s["prompt"]), negative_prompt="",
                     vace_video=[Image.fromarray(x) for x in s["source"]],
                     vace_video_mask=[Image.fromarray((m * 255).astype(np.uint8)).convert("RGB") for m in s["mask"]],
                     vace_reference_image=Image.fromarray(s["reference"]), height=480, width=832, num_frames=T,
                     seed=0, num_inference_steps=50, tiled=True)
        iio.imwrite(o, np.stack([np.array(v) for v in video]), fps=15, codec="libx264", quality=9)
        print("gen", variant, f.stem, flush=True)


def score():
    import imageio.v3 as iio
    from common import Dino, crop
    dino = Dino()
    samples = sorted((OUT / "samples").glob("*.npz"))
    variants = sorted(p.name for p in OUT.iterdir() if p.is_dir() and p.name != "samples")
    res = {}
    for v in variants:
        rows = []
        for f in samples:
            o = OUT / v / (f.stem + ".mp4")
            if not o.exists():
                continue
            s = np.load(f)
            out = iio.imread(o)
            tgt, mask = s["target"], s["mask"]
            T = min(len(out), len(tgt))
            ys = [t for t in range(T) if mask[t].sum() > 0]
            err = np.concatenate([(out[t].astype(np.float32) - tgt[t].astype(np.float32))[mask[t]] for t in ys])
            psnr = float(10 * np.log10(255 ** 2 / max(np.mean(err ** 2), 1e-6)))
            refm = (s["reference"] < 250).any(-1)
            e_ref = dino.emb(crop(s["reference"], refm)[0])
            rd, cp = [], []
            for t in ys[:: max(1, len(ys) // 8)]:
                obj = mask[t]
                e_o, e_t = dino.emb(crop(out[t], obj)[0]), dino.emb(crop(tgt[t], obj)[0])
                rd.append(float(e_o @ e_t))
                cp.append(float(e_o @ e_ref - e_t @ e_ref))
            rows.append({"video": f.stem, "psnr": psnr, "r_dino": float(np.mean(rd)), "ref_copy": float(np.mean(cp))})
        res[v] = {"n": len(rows), "psnr": float(np.mean([r["psnr"] for r in rows])),
                  "r_dino": float(np.mean([r["r_dino"] for r in rows])),
                  "ref_copy": float(np.mean([r["ref_copy"] for r in rows])), "per_video": rows}
        print(f"{v:12} n={len(rows)} PSNR {res[v]['psnr']:.2f}  R-DINO {res[v]['r_dino']:.3f}  ref_copy {res[v]['ref_copy']:+.3f}")
    json.dump(res, open(OUT / "scores.json", "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["gen", "score", "samples"])
    ap.add_argument("--variant", default="base")
    ap.add_argument("--lora", default=None)
    a = ap.parse_args()
    if a.stage == "samples":
        build_samples()
    elif a.stage == "gen":
        gen(a.variant, a.lora)
    else:
        score()
