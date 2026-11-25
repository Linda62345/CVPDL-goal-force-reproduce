"""Side-by-side strip: one row per video (method), 6 key frames each.  imagegen/venv/bin/python -I multiturn/compare3.py --videos a.mp4 b.mp4 --labels a b --out x.jpg"""
import argparse
import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
ap.add_argument("--videos", nargs="+", required=True)
ap.add_argument("--labels", nargs="+", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--frames", type=int, nargs="+", default=[0, 16, 32, 48, 64, 80])
a = ap.parse_args()
rows = []
for v, lab in zip(a.videos, a.labels):
    fr = iio.imread(v)
    tiles = []
    for t in a.frames:
        im = Image.fromarray(fr[min(t, len(fr) - 1)]).resize((312, 180))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 150, 14], fill=(0, 0, 0))
        d.text((3, 2), f"{lab} f{t}", fill=(255, 255, 0))
        tiles.append(np.array(im))
    rows.append(np.concatenate(tiles, 1))
Image.fromarray(np.concatenate(rows, 0)).save(a.out, quality=88)
print("wrote", a.out)
