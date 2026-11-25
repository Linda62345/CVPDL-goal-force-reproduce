"""Cross-turn continuity of a chain of turns (state.json from extract_state.py, in turn order).

Per object and per turn:
  pose      coarse pose at end of turn vs turn-1 start (as_initial / changed / missing / n/a)
  R-DINO    appearance at end of turn vs the turn-1 appearance memory (accumulated drift)
  area      area at end of turn / turn-1 area (vanish / split / shrink)
Per transition k -> k+1 (flags):
  JUMP      centroid at start of k+1 differs from end of k by > --jump_px      (state not carried over)
  REVERT    pose 'changed' at end of k but 'as_initial' at end of k+1, object not the target (e.g. fallen domino stands up)
  RESET     non-target object moves back toward its turn-1 position by > 50% and > --jump_px
  VANISH    visible at end of k, missing at end of k+1
  speed     mean speed over the last 5 frames of k vs first 5 frames of k+1 (px/frame; baseline restarts from rest)

    imagegen/venv/bin/python -I multiturn/eval_continuity.py --states t1/state.json t2/state.json \
        --targets white_ball red_ball --out chain_eval.json
"""
import argparse
import json

import numpy as np


def speed(traj, stride, at_start, n=5):
    pts = traj[:n] if at_start else traj[-n:]
    pts = [p for p in pts if p is not None]
    if len(pts) < 2:
        return None
    d = np.linalg.norm(np.diff(np.array(pts), axis=0), axis=1)
    return float(d.mean() / stride)


def dist(a, b):
    return float(np.linalg.norm(np.array(a) - np.array(b)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="+", required=True)
    ap.add_argument("--targets", nargs="+", required=True, help="the object pushed in each turn")
    ap.add_argument("--jump_px", type=float, default=15)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    S = [json.load(open(p)) for p in args.states]
    assert len(args.targets) == len(S)
    mem = json.load(open(S[0]["memory_dir"] + "/memory.json"))
    names = list(mem)

    rows, flags, transitions = [], [], []
    for k, st in enumerate(S):
        for n in names:
            o = st["objects"].get(n)
            if o is None:
                rows.append({"turn": k + 1, "object": n, "pose": "untracked"})
                continue
            rows.append({"turn": k + 1, "object": n, "target": n == args.targets[k], "pose": o["pose_last"],
                         "r_dino_last": o["r_dino_last"], "area_ratio": o["area_ratio_last"],
                         "visible_frames": f"{o['visible_frames']}/{st['T']}"})
    for k in range(len(S) - 1):
        a, b = S[k], S[k + 1]
        tgt = args.targets[k + 1]
        for n in names:
            oa, ob = a["objects"].get(n), b["objects"].get(n)
            if oa is None or not oa["last"]["visible"]:
                continue
            t = {"transition": f"{k + 1}->{k + 2}", "object": n}
            if ob is None or not ob["last"]["visible"]:
                flags.append(("VANISH", k + 2, n))
                t["vanish"] = True
                transitions.append(t)
                continue
            if ob["first"]["visible"]:
                j = dist(oa["last"]["centroid"], ob["first"]["centroid"])
                t["boundary_jump_px"] = j
                if j > args.jump_px:
                    flags.append(("JUMP", k + 2, n, round(j, 1)))
            if n != tgt and oa["pose_last"] == "changed" and ob["pose_last"] == "as_initial":
                flags.append(("REVERT", k + 2, n))
            orig = mem[n]["state0"]["centroid"]
            d_before, d_after = dist(oa["last"]["centroid"], orig), dist(ob["last"]["centroid"], orig)
            if n != tgt and d_before > args.jump_px and d_after < 0.5 * d_before:
                flags.append(("RESET", k + 2, n, round(d_before), round(d_after)))
            t["speed_end_prev"] = speed(oa["traj"], a["stride"], at_start=False)
            t["speed_start_next"] = speed(ob["traj"], b["stride"], at_start=True)
            transitions.append(t)

    json.dump({"states": args.states, "targets": args.targets, "per_turn": rows,
               "transitions": transitions, "flags": flags}, open(args.out, "w"), indent=1)

    print("| turn | object | pushed | pose at end | R-DINO vs memory | area ratio | visible |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        rd = "-" if r.get("r_dino_last") is None else f"{r['r_dino_last']:.2f}"
        ar = "-" if r.get("area_ratio") is None else f"{r['area_ratio']:.2f}"
        print(f"| {r['turn']} | {r['object']} | {'✔' if r.get('target') else ''} | {r['pose']} | {rd} | {ar} | {r.get('visible_frames', '-')} |")
    print("\ntransitions:")
    for t in transitions:
        print(" ", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in t.items()})
    print("flags:", flags if flags else "none")


if __name__ == "__main__":
    main()
