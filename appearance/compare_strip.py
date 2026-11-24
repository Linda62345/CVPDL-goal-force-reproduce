"""Stack variants (rows) x sampled frames (cols) into one PNG for visual comparison.
    venv/bin/python -I appearance/compare_strip.py --out X.png --frames 0 10 20 30 40 50 60 70 80 \
        --videos E0=a.mp4 E1=b.mp4 ...
"""
import argparse

import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("--videos", nargs="+", required=True)
ap.add_argument("--frames", nargs="+", type=int, default=[0, 10, 20, 30, 40, 50, 60, 70, 80])
ap.add_argument("--out", required=True)
ap.add_argument("--scale", type=float, default=0.33)
ap.add_argument("--crop", type=int, nargs=4, default=None, help="x0 y0 x1 y1 crop before scaling")
a = ap.parse_args()

rows = []
for spec in a.videos:
    name, path = spec.split("=", 1)
    fr = iio.imread(path)
    rows.append((name, [Image.fromarray(fr[min(i, len(fr) - 1)]) for i in a.frames]))
im0 = rows[0][1][0].crop(a.crop) if a.crop else rows[0][1][0]
tw, th = int(im0.width * a.scale), int(im0.height * a.scale)
sheet = Image.new("RGB", (tw * len(a.frames), th * len(rows)), "white")
d = ImageDraw.Draw(sheet)
font = ImageFont.load_default(size=16)
for r, (name, ims) in enumerate(rows):
    for c, im in enumerate(ims):
        if a.crop:
            im = im.crop(a.crop)
        sheet.paste(im.resize((tw, th)), (c * tw, r * th))
        d.text((c * tw + 3, r * th + 2), f"{name} f{a.frames[c]}", fill="yellow", font=font,
               stroke_width=2, stroke_fill="black")
sheet.save(a.out)
print(a.out, sheet.size)
