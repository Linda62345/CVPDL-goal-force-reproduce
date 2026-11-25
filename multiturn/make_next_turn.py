"""Write the Goal Force input (image + CSV) for the next turn from a turn's state.json.

The next turn's image is the previous turn's last frame (baseline). The force point is the tracked
centroid of the chosen object in that frame, converted to Goal Force's BOTTOM-LEFT y origin.
A preview PNG with the force arrow is written so the force point can be checked before a 22-min run.

    venv/bin/python -I multiturn/make_next_turn.py --state outputs/multiturn/<scene>/t1_s0/state.json \
        --target red_ball --angle 0 --force 350 --mode goal \
        --caption "The red ball rolls to the right and hits the dominoes." \
        --name t2_red_right --out_dir datasets/multiturn/<scene>
"""
import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image

COLS = ["image", "projectile_force_angle", "projectile_force_magnitude", "projectile_coordx", "projectile_coordy",
        "projectile_mass", "target_indirect_force_angle", "target_indirect_force_magnitude", "target_coordx",
        "target_coordy", "target_mass", "width", "height", "caption"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--target", required=True, help="object name in state.json")
    ap.add_argument("--angle", type=float, required=True, help="deg, 0 = right, 90 = up (image up)")
    ap.add_argument("--force", type=float, default=350)
    ap.add_argument("--mode", choices=["goal", "direct"], default="goal")
    ap.add_argument("--caption", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--point", type=float, nargs=2, help="override force point (TOP-LEFT px)")
    args = ap.parse_args()

    st = json.load(open(args.state))
    o = st["objects"][args.target]
    if args.point:
        x, y_top = args.point
    else:
        assert o["last"]["visible"], f"{args.target} not visible in the last frame"
        x, y_top = o["last"]["centroid"]
    H, W = st["H"], st["W"]
    y_csv = H - y_top  # Goal Force CSV: origin at bottom-left

    out = Path(args.out_dir)
    (out / "images").mkdir(parents=True, exist_ok=True)
    img = Image.open(st["last_frame"]).convert("RGB")
    assert img.size == (W, H) == (832, 480), f"Goal Force expects 832x480, got {img.size}"
    img.save(out / "images" / f"{args.name}.png")

    if args.mode == "goal":
        prj = [-1.0, -1.0, round(x), round(y_csv), -1]
        tgt = [args.angle, args.force, round(x), round(y_csv), -1]
    else:
        prj = [args.angle, args.force, round(x), round(y_csv), -1]
        tgt = [-1.0, -1.0, round(x), round(y_csv), -1]
    row = [f"{args.name}.png", *prj, *tgt, W, H, args.caption]
    pd.DataFrame([row], columns=COLS).to_csv(out / f"{args.name}.csv", index=False)

    # preview: force point + arrow (green = goal force, red = direct force), drawn in image coords
    prev = np.array(img).copy()
    col = (0, 220, 0) if args.mode == "goal" else (230, 0, 0)
    L = 60
    ex, ey = x + L * math.cos(math.radians(args.angle)), y_top - L * math.sin(math.radians(args.angle))
    cv2.circle(prev, (round(x), round(y_top)), 10, col, 2)
    cv2.arrowedLine(prev, (round(x), round(y_top)), (round(ex), round(ey)), col, 2, tipLength=0.3)
    Image.fromarray(prev).save(out / f"{args.name}_preview.png")

    meta = {"from_state": str(Path(args.state).resolve()), "target": args.target, "mode": args.mode,
            "point_topleft": [x, y_top], "point_csv": [round(x), round(y_csv)], "angle": args.angle,
            "force": args.force, "caption": args.caption, "prev_turn": st["turn"]}
    json.dump(meta, open(out / f"{args.name}_meta.json", "w"), indent=1)
    print(f"wrote {out / (args.name + '.csv')}  point(top-left)=({x:.0f},{y_top:.0f}) -> csv y={y_csv:.0f}")


if __name__ == "__main__":
    main()
