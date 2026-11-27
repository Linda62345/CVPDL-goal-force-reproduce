"""Side-by-side review videos for the paper-photo two-turn runs (multiturn/paper_photos_plan.md).

For each finished run writes outputs/multiturn/paper_review/<variant>_<scene>_s<seed>.mp4:
  [original photo (appearance reference)] | [baseline: turn 1 then turn 2 as generated] | [lora_orig: turn 1 then repaired turn 2]
Turn 1 is the same video in both right-hand panels; the label switches to "TURN 2" when turn 2 starts.
Skips runs whose review video already exists.

    imagegen/venv/bin/python -I multiturn/paper_review.py
"""
import glob
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PW, PH = 624, 360  # panel size
OUT = ROOT / "outputs/multiturn/paper_review"


def font(sz):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if Path(f).exists():
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


F = font(22)


def panel(img, label, color=(255, 255, 0)):
    im = Image.fromarray(img).convert("RGB").resize((PW, PH))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, 32], fill=(0, 0, 0))
    d.text((8, 4), label, fill=color, font=F)
    return np.array(im)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # (output prefix, base dir, repair dir, turn-2 dir): turn2 = first design, turn2b = collision / push-again design (11/27)
    for variant, base, rep, t2d in [("paper", "outputs/multiturn/paper", "repair", "t2_gf"),
                                    ("v2", "outputs/multiturn/paper_v2", "repair", "t2_gf"),
                                    ("t2b", "outputs/multiturn/paper", "repair_t2b", "t2b_gf"),
                                    ("t2b_v2", "outputs/multiturn/paper_v2", "repair_t2b", "t2b_gf"),
                                    ("t2c_v2", "outputs/multiturn/paper_v2", "repair_t2c", "t2c_gf")]:  # 11/27 goal-mode causal turn 2
        for lo in sorted(glob.glob(str(ROOT / base / f"*/{rep}/*/lora_orig.mp4"))):
            lo = Path(lo)
            rid = lo.parent.name                      # <scene>_s<seed>
            scene, seed = rid.rsplit("_s", 1)
            sd = ROOT / base / scene
            out = OUT / f"{variant}_{rid}.mp4"
            if out.exists():
                continue
            t1 = [v for v in glob.glob(str(sd / f"t1_gf/*seed_{seed}.mp4"))]
            t2 = [v for v in glob.glob(str(sd / f"{t2d}/*seed_{seed}.mp4"))]
            if not t1 or not t2:
                continue
            v1, v2, vl = iio.imread(t1[0]), iio.imread(t2[0]), iio.imread(lo)
            ref = v1[0]
            frames = []
            for t in range(len(v1)):
                p1 = panel(v1[t], "TURN 1  (same video)", (180, 220, 255))
                frames.append(np.concatenate([panel(ref, "original photo (reference)"), p1, p1], 1))
            for t in range(len(v2)):
                l = vl[min(t, len(vl) - 1)]
                frames.append(np.concatenate([panel(ref, "original photo (reference)"),
                                              panel(v2[t], "TURN 2  baseline (no repair)"),
                                              panel(l, "TURN 2  LoRA repaired (lora_orig)", (120, 255, 120))], 1))
            iio.imwrite(out, np.stack(frames), fps=16, codec="libx264", quality=7)
            print("wrote", out.relative_to(ROOT))
    dominoes()
    chains()
    # joined()  # 11/27: user removed joined/ ; keep only the 3-panel videos


def chains():
    """Experiment A: all turns of a chain back to back, [original photo | chain video], label = turn number.
    outputs/multiturn/paper_review/chain_<scene>.mp4 (rebuilt when more turns are available)."""
    for gfd in sorted(glob.glob(str(ROOT / "outputs/multiturn/chain/*/gf"))):
        scene = Path(gfd).parent.name
        vids = []
        k = 1
        while True:
            v = glob.glob(f"{gfd}/step-3000_{scene}_c{k}__*seed_0.mp4")
            if not v:
                break
            vids.append(v[0]); k += 1
        if not vids:
            continue
        out = OUT / f"chain_{scene}.mp4"
        stamp = OUT / f".chain_{scene}.n"
        if out.exists() and stamp.exists() and stamp.read_text() == str(len(vids)):
            continue
        import json
        force = json.load(open(ROOT / "multiturn/chain_scenes.json")).get(scene, {}).get("force", "?")
        frames = []
        ref = None
        for k, v in enumerate(vids, 1):
            vv = iio.imread(v)
            ref = vv[0] if ref is None else ref
            for t in range(len(vv)):
                frames.append(np.concatenate([panel(ref, "original photo"), panel(vv[t], f"TURN {k} / {len(vids)}  (force {force})")], 1))
        iio.imwrite(out, np.stack(frames), fps=16, codec="libx264", quality=7)
        stamp.write_text(str(len(vids)))
        print("wrote", out.relative_to(ROOT), len(vids), "turns")


def joined():
    """Plain full-size videos with turn 1 and turn 2 joined back to back (no side panels, no labels):
    outputs/multiturn/paper_review/joined/<name>_{baseline,lora}.mp4, built from the side-by-side review videos' sources."""
    import json
    J = OUT / "joined"
    J.mkdir(exist_ok=True)
    runs = []
    for variant, base in [("paper", "outputs/multiturn/paper"), ("v2", "outputs/multiturn/paper_v2")]:
        for lo in sorted(glob.glob(str(ROOT / base / "*/repair/*/lora_orig.mp4"))):
            lo = Path(lo); scene, seed = lo.parent.name.rsplit("_s", 1); sd = ROOT / base / scene
            t1 = glob.glob(str(sd / f"t1_gf/*seed_{seed}.mp4")); t2 = glob.glob(str(sd / f"t2_gf/*seed_{seed}.mp4"))
            if t1 and t2:
                runs.append((f"{variant}_{lo.parent.name}", t1[0], t2[0], lo))
    for exp in ["exp8", "exp10"]:
        for ev in sorted(glob.glob(str(ROOT / f"outputs/multiturn/{exp}/eval/baseline/*/eval.json"))):
            rid = Path(ev).parent.name; lo = ROOT / f"outputs/multiturn/lora_{exp}/repair/{rid}/lora_orig.mp4"
            if lo.exists():
                e = json.load(open(ev))
                runs.append((f"paper_ballthendominos_{rid}", ROOT / json.load(open(ROOT / e["prev_state"]))["video"], ROOT / e["video"], lo))
    for name, t1, t2, lo in runs:
        for tag, second in [("baseline", t2), ("lora", lo)]:
            out = J / f"{name}_{tag}.mp4"
            if out.exists():
                continue
            v = np.concatenate([iio.imread(t1), iio.imread(second)], 0)
            iio.imwrite(out, v, fps=16, codec="libx264", quality=8)
            print("wrote", out.relative_to(ROOT))


def dominoes():
    """Paper photo _ballthendominos: two turns were run on 11/25 (exp8: A/B x 3 seeds from turn-1 seeds 0 and 1;
    exp10: C/D from turn-1 seed 0). Same layout as the other photos, one file per run:
    outputs/multiturn/paper_review/paper_ballthendominos_<run>.mp4"""
    import json
    for exp in ["exp8", "exp10"]:
        for ev in sorted(glob.glob(str(ROOT / f"outputs/multiturn/{exp}/eval/baseline/*/eval.json"))):
            rid = Path(ev).parent.name
            out = OUT / f"paper_ballthendominos_{rid}.mp4"
            lo = ROOT / f"outputs/multiturn/lora_{exp}/repair/{rid}/lora_orig.mp4"
            if out.exists() or not lo.exists():
                continue
            e = json.load(open(ev))
            v1 = iio.imread(ROOT / json.load(open(ROOT / e["prev_state"]))["video"])
            v2, vl = iio.imread(ROOT / e["video"]), iio.imread(lo)
            ref = v1[0]
            frames = []
            for t in range(len(v1)):
                p1 = panel(v1[t], "TURN 1  (same video)", (180, 220, 255))
                frames.append(np.concatenate([panel(ref, "original photo (reference)"), p1, p1], 1))
            for t in range(len(v2)):
                frames.append(np.concatenate([panel(ref, "original photo (reference)"),
                                              panel(v2[t], "TURN 2  baseline (no repair)"),
                                              panel(vl[min(t, len(vl) - 1)], "TURN 2  LoRA repaired (lora_orig)", (120, 255, 120))], 1))
            iio.imwrite(out, np.stack(frames), fps=16, codec="libx264", quality=7)
            print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
