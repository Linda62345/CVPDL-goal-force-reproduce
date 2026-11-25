"""Collect every eval.json (multiturn/evaluate.py) -> summary tables (markdown), failure taxonomy, trade-off scatter (PNG).

    imagegen/venv/bin/python -I multiturn/aggregate.py --out reports/overnight_assets
Scans outputs/multiturn/*/eval/<method>/<run_id>/eval.json.
"""
import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
METHODS = ["baseline", "appearance", "full", "appearance_global"]
COL = {"baseline": (110, 110, 110), "appearance": (230, 120, 20), "full": (20, 140, 120), "appearance_global": (150, 60, 160)}
NAME = {"baseline": "baseline", "appearance": "appearance memory only", "full": "full (appearance + state)", "appearance_global": "appearance, whole-frame (diag.)"}


def load():
    rows = []
    for p in sorted(glob.glob(str(ROOT / "outputs/multiturn/*/eval/*/*/eval.json"))):
        e = json.load(open(p))
        s = e["summary"]
        rid = Path(p).parent.name
        exp = Path(p).parts[-5]
        scene = (e.get("scene") or "?") + ("_noforce" if exp.endswith("_noforce") else "")
        rows.append({"path": p, "exp": exp, "scene": scene, "method": e["method"], "run": rid,
                     "video": e["video"], **{k: s[k] for k in s}, "target_success": bool(s["target_success"])})
    return rows


def fmt(x, d=2):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def mean(v):
    v = [x for x in v if x is not None]
    return float(np.mean(v)) if v else None


def table(rows, key=lambda r: (r["scene"], r["method"])):
    g = defaultdict(list)
    for r in rows:
        g[key(r)].append(r)
    out = ["| scene | method | n videos | state kept ↑ | start IoU ↑ | R-DINO vs original ↑ | R-DINO vs latest ↑ | turn-2 success | vanished | fused | reverted |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    order = sorted(g, key=lambda k: (k[0], METHODS.index(k[1]) if k[1] in METHODS else 9))
    for k in order:
        rs = g[k]
        out.append(f"| {k[0]} | {k[1]} | {len(rs)} | {fmt(mean([r['state_kept_frac'] for r in rs]))} | "
                   f"{fmt(mean([r['start_iou_mean'] for r in rs]))} | {fmt(mean([r['appearance_mem_end_mean'] for r in rs]))} | "
                   f"{fmt(mean([r['appearance_latest_end_mean'] for r in rs]))} | {sum(r['target_success'] for r in rs)}/{len(rs)} | "
                   f"{sum(r['n_vanished'] for r in rs)} | {sum(r['n_fused'] for r in rs)} | {sum(r['n_reverted'] for r in rs)} |")
    return "\n".join(out)


def taxonomy(rows):
    labs = ["appearance_deformed", "state_lost", "state_reverted", "action_failed"]
    g = defaultdict(list)
    for r in rows:
        g[r["method"]].append(r)
    out = ["| method | n videos | appearance deformed | state lost (vanished/fused) | state reverted | action failed | no failure |",
           "|---|---|---|---|---|---|---|"]
    for m in [m for m in METHODS if m in g] + [m for m in g if m not in METHODS]:
        rs = g[m]
        c = [sum(l in r["failure_labels"] for r in rs) for l in labs]
        ok = sum(not r["failure_labels"] for r in rs)
        out.append(f"| {m} | {len(rs)} | " + " | ".join(str(x) for x in c) + f" | {ok} |")
    return "\n".join(out)


def scatter(rows, xkey, path, title):
    W, H, L, B, T, R = 760, 560, 80, 70, 50, 220
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 13)
    except OSError:
        f = ImageFont.load_default()
    pw, ph = W - L - R, H - T - B
    X = lambda v: L + v * pw
    Y = lambda v: T + (1 - v) * ph
    for i in range(6):
        v = i / 5
        d.line([X(v), T, X(v), T + ph], fill=(235, 235, 235))
        d.line([L, Y(v), L + pw, Y(v)], fill=(235, 235, 235))
        d.text((X(v) - 8, T + ph + 6), f"{v:.1f}", fill=(60, 60, 60), font=f)
        d.text((L - 32, Y(v) - 7), f"{v:.1f}", fill=(60, 60, 60), font=f)
    d.rectangle([L, T, L + pw, T + ph], outline=(80, 80, 80))
    d.text((L, 14), title, fill=(0, 0, 0), font=f)
    d.text((L + pw / 2 - 120, H - 28), f"appearance consistency ({xkey})", fill=(0, 0, 0), font=f)
    d.text((8, T - 22), "state kept (fraction of objects)", fill=(0, 0, 0), font=f)
    rng = np.random.default_rng(0)
    for r in rows:
        x, y = r.get(xkey), r["state_kept_frac"]
        if x is None:
            continue
        jx, jy = rng.normal(0, 3, 2)
        c = COL.get(r["method"], (0, 0, 200))
        cx, cy = X(min(max(x, 0), 1)) + jx, Y(y) + jy
        if r["target_success"]:
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=c)
        else:
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=c, width=2)
    # method means
    for m in METHODS:
        rs = [r for r in rows if r["method"] == m and r.get(xkey) is not None]
        if rs:
            mx, my = np.mean([r[xkey] for r in rs]), np.mean([r["state_kept_frac"] for r in rs])
            d.rectangle([X(mx) - 7, Y(my) - 7, X(mx) + 7, Y(my) + 7], outline=(0, 0, 0), fill=COL[m], width=2)
    ly = T + 10
    for m in METHODS:
        d.ellipse([L + pw + 20, ly, L + pw + 30, ly + 10], fill=COL[m])
        d.text((L + pw + 38, ly - 2), NAME[m], fill=(0, 0, 0), font=f)
        ly += 22
    d.text((L + pw + 20, ly + 6), "filled = turn-2 success", fill=(0, 0, 0), font=f)
    d.text((L + pw + 20, ly + 24), "hollow = action failed", fill=(0, 0, 0), font=f)
    d.text((L + pw + 20, ly + 42), "square = method mean", fill=(0, 0, 0), font=f)
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/overnight_assets")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rows = load()
    md = ["## Per scene x method", table(rows), "", "## All scenes pooled", table(rows, key=lambda r: ("all", r["method"])),
          "", "## Failure taxonomy (labels can overlap)", taxonomy(rows), "", "## Per video",
          "| exp | scene | method | run | state kept | R-DINO orig | R-DINO latest | success | labels |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["scene"], r["run"], METHODS.index(r["method"]) if r["method"] in METHODS else 9)):
        md.append(f"| {r['exp']} | {r['scene']} | {r['method']} | {r['run']} | {fmt(r['state_kept_frac'])} | {fmt(r['appearance_mem_end_mean'])} | "
                  f"{fmt(r['appearance_latest_end_mean'])} | {'✔' if r['target_success'] else '✘'} | {', '.join(r['failure_labels']) or '-'} |")
    (out / "aggregate.md").write_text("\n".join(md) + "\n")
    json.dump(rows, open(out / "aggregate.json", "w"), indent=1)
    scatter(rows, "appearance_mem_end_mean", out / "tradeoff_vs_original.png", "Each point = one turn-2 video (R-DINO vs ORIGINAL crop)")
    scatter(rows, "appearance_latest_end_mean", out / "tradeoff_vs_latest.png", "Each point = one turn-2 video (R-DINO vs LATEST state)")
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()
