"""Appearance-consistency metrics of a tracked object vs. its frame-0 appearance.

Per frame t (object mask from track_sam2.py):
  r_dino   cosine sim of DINOv2 CLS features: object crop (bg -> white) at t vs at 0   (HECTOR's R-DINO idea)
  shape_iou IoU of bbox-normalised silhouettes (64x64) at t vs 0                     (shape kept?)
  dE       CIELAB distance between mean object colour at t and at 0                  (colour kept?)
  area     mask area / area at frame 0                                               (vanish / split / scale)
Summary = mean over frames where the object is visible, plus #frames where it is missing.

    HF_HOME=imagegen/hf_cache imagegen/venv/bin/python -I appearance/metrics.py \
        --video X.mp4 --masks outputs/appearance/X/masks.npz --out outputs/appearance/X/metrics.json
"""
import argparse
import json
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel


def rgb2lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def crop(frame, mask, pad=4):
    ys, xs = np.nonzero(mask)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, mask.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, mask.shape[1])
    img = frame[y0:y1, x0:x1].copy()
    m = mask[y0:y1, x0:x1]
    img[~m] = 255
    return img, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--masks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min_area", type=int, default=50)
    ap.add_argument("--ref_video", default=None, help="take the frame-0 reference object from this video instead")
    ap.add_argument("--ref_masks", default=None)
    args = ap.parse_args()

    frames = iio.imread(args.video)
    masks = np.load(args.masks)["masks"]
    T = min(len(frames), len(masks))
    proc = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
    dino = AutoModel.from_pretrained("facebook/dinov2-base").cuda().eval()

    @torch.no_grad()
    def emb(img):
        x = proc(images=Image.fromarray(img), return_tensors="pt").to("cuda")
        v = dino(**x).last_hidden_state[:, 0]
        return torch.nn.functional.normalize(v, dim=-1)[0]

    rf = iio.imread(args.ref_video)[0] if args.ref_video else frames[0]
    rm = np.load(args.ref_masks)["masks"][0] if args.ref_masks else masks[0]
    c0, m0 = crop(rf, rm)
    e0 = emb(c0)
    s0 = np.array(Image.fromarray(m0.astype(np.uint8) * 255).resize((64, 64))) > 127
    lab0 = rgb2lab(rf[rm].astype(np.float64)).mean(0)
    a0 = rm.sum()

    per = []
    for t in range(T):
        a = int(masks[t].sum())
        if a < args.min_area:
            per.append({"t": t, "visible": False, "area": a / a0})
            continue
        c, m = crop(frames[t], masks[t])
        s = np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((64, 64))) > 127
        lab = rgb2lab(frames[t][masks[t]].astype(np.float64)).mean(0)
        per.append({
            "t": t, "visible": True, "area": a / a0,
            "r_dino": float(emb(c) @ e0),
            "shape_iou": float((s & s0).sum() / max((s | s0).sum(), 1)),
            "dE": float(np.linalg.norm(lab - lab0)),
        })
    vis = [p for p in per if p["visible"]]
    summ = {
        "video": args.video,
        "frames": T,
        "missing_frames": T - len(vis),
        "r_dino_mean": float(np.mean([p["r_dino"] for p in vis])),
        "r_dino_min": float(np.min([p["r_dino"] for p in vis])),
        "shape_iou_mean": float(np.mean([p["shape_iou"] for p in vis])),
        "dE_mean": float(np.mean([p["dE"] for p in vis])),
        "area_cv": float(np.std([p["area"] for p in vis]) / np.mean([p["area"] for p in vis])),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump({"summary": summ, "per_frame": per}, open(args.out, "w"), indent=1)
    print(json.dumps(summ))


if __name__ == "__main__":
    main()
