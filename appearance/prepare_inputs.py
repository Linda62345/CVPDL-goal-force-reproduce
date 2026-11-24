"""From a Goal Force video + SAM2 masks, build:
  E1  composite.mp4      : frame-0 object pasted rigidly at each frame's tracked centroid
                           (original object removed with a clean background plate)
  VACE inputs            : edit-region mask (generous box around object, >= frame-0 object size),
                           gray-filled source (E2), composite-filled source (E3), reference image.

    venv/bin/python -I appearance/prepare_inputs.py --video V.mp4 --dir outputs/appearance/<id>
"""
import argparse
from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np
from PIL import Image


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--min_area", type=int, default=50)
    ap.add_argument("--box_margin", type=float, default=0.3)
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--keep_first", type=int, default=0, help="leave the first N frames unedited (original pixels as context)")
    ap.add_argument("--suffix", default="", help="suffix for vace_* output files")
    args = ap.parse_args()
    d = Path(args.dir)
    frames = iio.imread(args.video)
    masks = np.load(d / "masks.npz")["masks"]
    T, H, W, _ = frames.shape
    vis = masks.sum((1, 2)) >= args.min_area

    k = np.ones((15, 15), np.uint8)
    dil = np.stack([cv2.dilate(m.astype(np.uint8), k) > 0 for m in masks])

    # clean background plate: per-pixel median over frames where that pixel is not covered
    stack = np.where(dil[..., None], np.nan, frames.astype(np.float32))
    plate = np.nanmedian(stack, axis=0)
    plate = np.where(np.isnan(plate), frames[0], plate).astype(np.uint8)

    # frame-0 object sprite
    x0, y0, x1, y1 = bbox(masks[0])
    sprite = frames[0][y0:y1, x0:x1]
    alpha = cv2.GaussianBlur(masks[0][y0:y1, x0:x1].astype(np.float32), (5, 5), 0)[..., None]
    sh, sw = sprite.shape[:2]
    ys0, xs0 = np.nonzero(masks[0])
    off = (ys0.mean() - y0, xs0.mean() - x0)  # centroid offset inside sprite

    comp, edit_mask = [], []
    for t in range(T):
        f = frames[t].copy()
        f[dil[t]] = plate[dil[t]]  # erase (possibly deformed) object, keep its shadow
        em = np.zeros((H, W), bool)
        if vis[t]:
            ys, xs = np.nonzero(masks[t])
            cy, cx = ys.mean(), xs.mean()
            ty, tx = int(round(cy - off[0])), int(round(cx - off[1]))
            # paste with clipping
            sy0, sx0 = max(0, -ty), max(0, -tx)
            sy1, sx1 = min(sh, H - ty), min(sw, W - tx)
            if sy1 > sy0 and sx1 > sx0:
                reg = f[ty + sy0:ty + sy1, tx + sx0:tx + sx1].astype(np.float32)
                a = alpha[sy0:sy1, sx0:sx1]
                f[ty + sy0:ty + sy1, tx + sx0:tx + sx1] = (a * sprite[sy0:sy1, sx0:sx1] + (1 - a) * reg).astype(np.uint8)
            # edit region: union of tracked bbox and frame-0-sized box at centroid, with margin
            bx0, by0, bx1, by1 = bbox(masks[t])
            hw = max(bx1 - bx0, sw) * (0.5 + args.box_margin)
            hh = max(by1 - by0, sh) * (0.5 + args.box_margin)
            em[int(max(0, cy - hh)):int(min(H, cy + hh)), int(max(0, cx - hw)):int(min(W, cx + hw))] = True
        comp.append(f)
        edit_mask.append(em | dil[t])
    comp = np.stack(comp)
    edit_mask = np.stack(edit_mask)
    if args.keep_first:
        edit_mask[:args.keep_first] = False
        comp[:args.keep_first] = frames[:args.keep_first]
    sfx = args.suffix

    iio.imwrite(d / "E1_composite.mp4", comp, fps=args.fps, codec="libx264", quality=9)
    gray = frames.copy()
    gray[edit_mask] = 127
    iio.imwrite(d / f"vace_src_gray{sfx}.mp4", gray, fps=args.fps, codec="libx264", quality=9)
    iio.imwrite(d / f"vace_src_comp{sfx}.mp4", comp, fps=args.fps, codec="libx264", quality=9)
    iio.imwrite(d / f"vace_mask{sfx}.mp4", (edit_mask[..., None].repeat(3, -1) * 255).astype(np.uint8),
                fps=args.fps, codec="libx264", quality=9)
    np.savez_compressed(d / f"edit_mask{sfx}.npz", masks=edit_mask)

    # reference: object on white canvas, full frame size
    ref = np.full((H, W, 3), 255, np.uint8)
    cy, cx = H // 2 - sh // 2, W // 2 - sw // 2
    ref[cy:cy + sh, cx:cx + sw] = (alpha * sprite + (1 - alpha) * 255).astype(np.uint8)
    Image.fromarray(ref).save(d / "reference.png")
    print("visible", int(vis.sum()), "/", T, "edit-area mean px", int(edit_mask.sum((1, 2)).mean()))


if __name__ == "__main__":
    main()
