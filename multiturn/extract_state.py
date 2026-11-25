"""Object-state memory for one turn: track every object through a turn's video and save
  - appearance memory (turn 1 only, then carried forward): frame-0 crop + mask + state of each object
  - this turn's per-object state: first/last frame centroid, bbox, axis angle, coarse pose, trajectory,
    per-frame R-DINO vs the appearance memory
  - last_frame.png (input image of the next turn) and next-turn click points per object

Turn 1 (objects given by clicks on frame 0, TOP-LEFT px):
  HF_HOME=imagegen/hf_cache imagegen/venv/bin/python -I multiturn/extract_state.py --video T1.mp4 \
      --out outputs/multiturn/<scene>/t1_s0 --prompts '{"white_ball":[[242,380]],"red_ball":[[358,372]]}'
Turn k>1 (objects re-prompted from the previous turn's last-frame masks, memory carried):
  ... --video T2.mp4 --out .../t2_s0 --prev_state .../t1_s0/state.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir

import imageio.v3 as iio
import numpy as np
from PIL import Image

from common import Dino, crop, interior_points, mask_state, pose_label, track_objects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompts", help="JSON {name: [[x,y],...]} clicks on frame 0 (turn 1)")
    ap.add_argument("--prev_state", help="state.json of the previous turn (turn > 1)")
    ap.add_argument("--stride", type=int, default=1, help="frame subsampling (testing only)")
    args = ap.parse_args()
    assert bool(args.prompts) != bool(args.prev_state), "give exactly one of --prompts / --prev_state"

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = iio.imread(args.video)[:: args.stride]
    T, H, W, _ = frames.shape

    if args.prompts:
        turn, prompts, prev = 1, json.loads(args.prompts), None
        mem_dir = out / "memory"
    else:
        prev = json.load(open(args.prev_state))
        turn = prev["turn"] + 1
        prompts = {n: o["next_points"] for n, o in prev["objects"].items() if o["next_points"]}
        mem_dir = Path(prev["memory_dir"])
        missing = [n for n, o in prev["objects"].items() if not o["next_points"]]
        if missing:
            print("objects not visible at end of previous turn (not tracked):", missing)

    masks = track_objects(frames, prompts)
    np.savez_compressed(out / "masks.npz", **masks)

    # appearance memory: created once from turn-1 frame 0, then reused unchanged
    if turn == 1:
        mem_dir.mkdir(exist_ok=True)
        memory = {}
        for n, m in masks.items():
            s0 = mask_state(m[0])
            if not s0["visible"]:
                print(f"WARNING {n}: empty mask on frame 0 - check the click")
                continue
            c, _ = crop(frames[0], m[0])
            Image.fromarray(c).save(mem_dir / f"{n}.png")
            np.save(mem_dir / f"{n}_mask.npy", m[0])
            memory[n] = {"crop": f"{n}.png", "state0": s0}
        json.dump(memory, open(mem_dir / "memory.json", "w"), indent=1)
    memory = json.load(open(mem_dir / "memory.json"))

    dino = Dino()
    mem_emb = {n: dino.emb(np.array(Image.open(mem_dir / v["crop"]).convert("RGB"))) for n, v in memory.items()}

    objs = {}
    for n, m in masks.items():
        states = [mask_state(m[t]) for t in range(T)]
        r = []
        for t in range(T):
            if states[t]["visible"] and n in mem_emb:
                c, _ = crop(frames[t], m[t])
                r.append(float(dino.emb(c) @ mem_emb[n]))
            else:
                r.append(None)
        ref0 = memory.get(n, {}).get("state0", states[0])
        last = states[-1]
        objs[n] = {
            "first": states[0], "last": last,
            "pose_first": pose_label(states[0], ref0), "pose_last": pose_label(last, ref0),
            "traj": [s["centroid"] if s["visible"] else None for s in states],
            "visible_frames": int(sum(s["visible"] for s in states)),
            "area_ratio_last": last["area"] / max(ref0["area"], 1),
            "r_dino": r,
            "r_dino_last": r[-1],
            "next_points": interior_points(m[-1]) if last["visible"] else [],
        }

    Image.fromarray(frames[-1]).save(out / "last_frame.png")
    if turn == 1:
        Image.fromarray(frames[0]).save(out / "first_frame.png")
    state = {"turn": turn, "video": args.video, "stride": args.stride, "H": H, "W": W, "T": T,
             "memory_dir": str(mem_dir.resolve()), "prev_state": args.prev_state,
             "last_frame": str((out / "last_frame.png").resolve()), "objects": objs}
    json.dump(state, open(out / "state.json", "w"), indent=1)

    # overlay of first / middle / last frame with each object's mask outline + name
    import cv2
    cols = [(255, 64, 64), (64, 255, 64), (64, 128, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    tiles = []
    for t in [0, T // 2, T - 1]:
        f = frames[t].copy()
        for i, (n, m) in enumerate(masks.items()):
            cs, _ = cv2.findContours(m[t].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(f, cs, -1, cols[i % len(cols)], 2)
            s = mask_state(m[t])
            if s["visible"]:
                cv2.putText(f, n, (int(s["centroid"][0]) - 20, int(s["bbox"][1]) - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, cols[i % len(cols)], 1, cv2.LINE_AA)
        tiles.append(f)
    Image.fromarray(np.concatenate(tiles, 1)).resize((W * 3 // 2, H // 2)).save(out / "state_overlay.png")

    for n, o in objs.items():
        print(f"{n:12} vis {o['visible_frames']:3d}/{T}  last {o['pose_last']:10}  "
              f"area x{o['area_ratio_last']:.2f}  R-DINO last {o['r_dino_last'] if o['r_dino_last'] is None else round(o['r_dino_last'], 2)}")


if __name__ == "__main__":
    main()
