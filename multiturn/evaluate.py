"""Unified turn-2 evaluation (one video). Definitions: multiturn/metrics.md. Used for every method and scene.

    HF_HOME=imagegen/hf_cache imagegen/venv/bin/python -I multiturn/evaluate.py \
        --video T2.mp4 --prev_state outputs/.../t1_s0/state.json --target white_ball --angle 0 \
        --method baseline --out outputs/multiturn/exp8/eval/<run_id> [--blind_dir outputs/multiturn/blind]

Steps: (1) track every object of the previous turn through this video (extract_state.py, re-prompted from the
previous turn's last-frame masks, stride 1) -> <out>/track/ ; (2) per-object state / appearance metrics ;
(3) target-motion success ; (4) video-level labels ; (5) unlabeled key-frame montage for blind rating.
Skips everything if <out>/eval.json exists (resume).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

# ---- thresholds (documented in metrics.md) ----
JUMP_PX = 15          # min displacement that counts as "moved"
SUCCESS_MIN_PX = 15   # target must move at least max(15 px, 0.25*sqrt(area))
SUCCESS_MAX_DEG = 45  # ... within 45 deg of the commanded direction
COLLAPSE = 0.30       # area at end / area at turn-2 start below this -> collapsed (absorbed into another mask)
BALLOON = 3.0         # area ratio above this -> absorbed other objects
OVERLAP = 0.5         # overlap / smaller mask above this, on >= FUSE_FRAMES frames -> fused
FUSE_FRAMES = 3
BORDER = 4            # px; a mask touching the border before disappearing = left the frame (not vanished)
APPEAR_BAD = 0.5      # R-DINO vs latest state below this at the end -> appearance deformed


def iou(a, b):
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 0.0


def touches_border(m, H, W):
    ys, xs = np.nonzero(m)
    return len(xs) > 0 and (xs.min() <= BORDER or ys.min() <= BORDER or xs.max() >= W - 1 - BORDER or ys.max() >= H - 1 - BORDER)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--prev_state", required=True)
    ap.add_argument("--target", required=True, help="object the new force is applied to (goal mode: object that must move)")
    ap.add_argument("--angle", type=float, required=True, help="commanded direction, Goal Force convention (0=right, 90=up)")
    ap.add_argument("--no_force", action="store_true", help="control run without force: success = target stays (< JUMP_PX)")
    ap.add_argument("--method", required=True)
    ap.add_argument("--scene", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--blind_dir", default="outputs/multiturn/blind")
    ap.add_argument("--stride", type=int, default=1)
    args = ap.parse_args()
    out = Path(args.out)
    if (out / "eval.json").exists() and "series" in json.load(open(out / "eval.json")):
        print("[skip] exists", out / "eval.json")
        return
    out.mkdir(parents=True, exist_ok=True)

    # (1) tracking
    tr = out / "track"
    if not (tr / "state.json").exists():
        env = dict(os.environ, HF_HOME=os.environ.get("HF_HOME", "imagegen/hf_cache"))
        subprocess.run([sys.executable, "-I", str(HERE / "extract_state.py"), "--video", args.video, "--out", str(tr),
                        "--prev_state", args.prev_state, "--stride", str(args.stride)], check=True, env=env)
    st = json.load(open(tr / "state.json"))
    prev = json.load(open(args.prev_state))
    masks = dict(np.load(tr / "masks.npz"))
    prev_masks = dict(np.load(Path(args.prev_state).parent / "masks.npz"))
    mem_dir = Path(st["memory_dir"])
    memory = json.load(open(mem_dir / "memory.json"))
    H, W, T = st["H"], st["W"], st["T"]

    import imageio.v3 as iio
    from common import Dino, crop
    frames = iio.imread(args.video)[:: args.stride]
    prev_last = np.array(Image.open(prev["last_frame"]).convert("RGB"))
    dino = Dino()
    names = list(masks)

    # (2) per object
    objs, series = {}, {}
    for n in names:
        m = masks[n]
        o = st["objects"][n]
        po = prev["objects"][n]
        area = m.reshape(T, -1).sum(1)
        vis = area >= 30
        pm_last = prev_masks[n][-1]
        a_start = max(int(m[0].sum()), 1)
        r = {"target": n == args.target}
        r["start_iou"] = iou(pm_last, m[0])
        r["visible_frac"] = float(vis.mean())
        r["end_visible"] = bool(vis[-1])
        last_vis = int(np.nonzero(vis)[0].max()) if vis.any() else -1
        r["exited"] = bool(not vis[-1] and last_vis >= 0 and touches_border(m[last_vis], H, W))
        r["vanished"] = bool(not vis[-1] and not r["exited"])
        r["area_end_ratio"] = float(area[-1] / a_start)
        r["collapsed"] = bool(vis[-1] and r["area_end_ratio"] < COLLAPSE)
        r["ballooned"] = bool(vis[-1] and r["area_end_ratio"] > BALLOON)
        fuse_frames = 0
        for t in range(T):
            if not vis[t]:
                continue
            for n2 in names:
                if n2 == n or masks[n2][t].sum() < 30:
                    continue
                ov = np.logical_and(m[t], masks[n2][t]).sum() / min(m[t].sum(), masks[n2][t].sum())
                if ov > OVERLAP:
                    fuse_frames += 1
                    break
        r["overlap_frames"] = fuse_frames
        r["fused"] = bool(fuse_frames >= FUSE_FRAMES or r["collapsed"] or r["ballooned"])
        # reverted towards the turn-1 initial state
        orig = memory[n]["state0"]["centroid"]
        c1 = po["last"]["centroid"] if po["last"]["visible"] else None
        c2 = o["last"]["centroid"] if o["last"]["visible"] else None
        r["pose_t1_end"], r["pose_t2_end"] = po["pose_last"], o["pose_last"]
        r["pose_revert"] = bool(po["pose_last"] == "changed" and o["pose_last"] == "as_initial")
        r["pos_reset"] = False
        r["returned_by_force"] = False
        if c1 and c2:
            d1 = float(np.hypot(c1[0] - orig[0], c1[1] - orig[1]))
            d2 = float(np.hypot(c2[0] - orig[0], c2[1] - orig[1]))
            r["dist_to_initial_t1_end"], r["dist_to_initial_t2_end"] = d1, d2
            if d1 > JUMP_PX and d2 < 0.5 * d1:
                u = np.array([np.cos(np.radians(args.angle)), -np.sin(np.radians(args.angle))])
                back = np.array(orig) - np.array(c1)
                toward = float(back @ u / (np.linalg.norm(back) + 1e-9))
                if r["target"] and not args.no_force and toward > 0.7:
                    r["returned_by_force"] = True
                else:
                    r["pos_reset"] = True
        r["reverted"] = bool(r["pose_revert"] or r["pos_reset"])
        # appearance: vs original memory crop, and vs latest state (turn-1 last frame crop)
        e_mem = dino.emb(np.array(Image.open(mem_dir / memory[n]["crop"]).convert("RGB")))
        e_lat = dino.emb(crop(prev_last, pm_last)[0]) if pm_last.sum() >= 30 else None
        rm, rl, ser_l = [], [], []
        for t in range(T):
            if vis[t]:
                e = dino.emb(crop(frames[t], m[t])[0])
                rm.append(float(e @ e_mem))
                rl.append(float(e @ e_lat) if e_lat is not None else None)
                ser_l.append(rl[-1])
            else:
                ser_l.append(None)
        series[n] = ser_l
        r["r_dino_mem_mean"] = float(np.mean(rm)) if rm else None
        r["r_dino_mem_end"] = rm[-1] if rm and vis[-1] else None
        rl2 = [x for x in rl if x is not None]
        r["r_dino_latest_mean"] = float(np.mean(rl2)) if rl2 else None
        r["r_dino_latest_end"] = rl[-1] if rl and vis[-1] and rl[-1] is not None else None
        r["lost"] = bool(r["vanished"] or r["fused"])
        r["kept"] = bool(not r["lost"] and not r["reverted"])
        objs[n] = r

    # (3) target motion
    tgt = {"name": args.target, "angle": args.angle, "no_force": args.no_force}
    if args.target in masks:
        m = masks[args.target]
        vis = m.reshape(T, -1).sum(1) >= 30
        if vis[0] and vis.any():
            ys, xs = np.nonzero(m[0]); c0 = np.array([xs.mean(), ys.mean()]); a0 = len(xs)
            tl = int(np.nonzero(vis)[0].max())
            ys, xs = np.nonzero(m[tl]); cl = np.array([xs.mean(), ys.mean()])
            d = cl - c0
            u = np.array([np.cos(np.radians(args.angle)), -np.sin(np.radians(args.angle))])
            mag = float(np.linalg.norm(d))
            ang = float(np.degrees(np.arccos(np.clip(d @ u / (mag + 1e-9), -1, 1)))) if mag > 0 else None
            need = max(SUCCESS_MIN_PX, 0.25 * np.sqrt(a0))
            tgt.update(displacement=[float(d[0]), float(d[1])], magnitude=mag, angle_err=ang, need_px=float(need),
                       last_visible_frame=tl * args.stride)
            if args.no_force:
                tgt["success"] = bool(mag < JUMP_PX)
            else:
                tgt["success"] = bool(mag >= need and ang is not None and ang <= SUCCESS_MAX_DEG)
        else:
            tgt.update(success=False, reason="target not visible at turn-2 start")
    else:
        tgt.update(success=False, reason="target not tracked (not visible at end of previous turn)")

    # (4) video-level
    vals = list(objs.values())
    app_end = [o["r_dino_mem_end"] for o in vals if o["r_dino_mem_end"] is not None]
    lat_end = [o["r_dino_latest_end"] for o in vals if o["r_dino_latest_end"] is not None]
    summary = {
        "n_objects": len(vals),
        "state_kept_frac": float(np.mean([o["kept"] for o in vals])),
        "start_iou_mean": float(np.mean([o["start_iou"] for o in vals])),
        "n_vanished": int(sum(o["vanished"] for o in vals)),
        "n_fused": int(sum(o["fused"] for o in vals)),
        "n_reverted": int(sum(o["reverted"] for o in vals)),
        "n_exited": int(sum(o["exited"] for o in vals)),
        "appearance_mem_end_mean": float(np.mean(app_end)) if app_end else None,
        "appearance_latest_end_mean": float(np.mean(lat_end)) if lat_end else None,
        "target_success": tgt["success"],
    }
    labels = []
    if any(x < APPEAR_BAD for x in lat_end):
        labels.append("appearance_deformed")
    if summary["n_vanished"] or summary["n_fused"]:
        labels.append("state_lost")
    if summary["n_reverted"]:
        labels.append("state_reverted")
    if not tgt["success"]:
        labels.append("action_failed")
    summary["failure_labels"] = labels

    # (5) blind montage: 6 key frames, no method / file name on the image
    bid = hashlib.sha1(os.path.abspath(args.video).encode()).hexdigest()[:8]
    bdir = Path(args.blind_dir)
    bdir.mkdir(parents=True, exist_ok=True)
    full = iio.imread(args.video)
    idx = np.linspace(0, len(full) - 1, 6).round().astype(int)
    tiles = [np.array(Image.fromarray(full[i]).resize((416, 240))) for i in idx]
    mont = np.concatenate([np.concatenate(tiles[:3], 1), np.concatenate(tiles[3:], 1)], 0)
    Image.fromarray(mont).save(bdir / f"{bid}.jpg", quality=90)
    with open(bdir / "_key_DO_NOT_SHOW_RATERS.jsonl", "a") as f:
        f.write(json.dumps({"blind_id": bid, "video": args.video, "method": args.method, "scene": args.scene}) + "\n")
    # labeled montage for our own reports
    Image.fromarray(mont).save(out / "keyframes.jpg", quality=90)

    res = {"video": args.video, "prev_state": args.prev_state, "method": args.method, "scene": args.scene,
           "blind_id": bid, "objects": objs, "series": {"r_dino_latest": series, "stride": args.stride}, "target": tgt, "summary": summary}
    json.dump(res, open(out / "eval.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))
    for n, o in objs.items():
        print(f"{n:14} kept={o['kept']!s:5} lost={o['lost']!s:5} rev={o['reverted']!s:5} startIoU={o['start_iou']:.2f} "
              f"area_end={o['area_end_ratio']:.2f} Rmem={o['r_dino_mem_end']} Rlat={o['r_dino_latest_end']}")


if __name__ == "__main__":
    main()
