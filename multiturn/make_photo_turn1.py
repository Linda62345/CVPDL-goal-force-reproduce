"""Turn-1 inputs from real photos: landscape crop -> 832x480 image, Goal Force CSV (BOTTOM-LEFT y), arrow preview, meta.
Spec: multiturn/photo_scenes.json (crop box in ORIGINAL photo pixels after EXIF rotation; points in 832x480 TOP-LEFT px).

    imagegen/venv/bin/python -I multiturn/make_photo_turn1.py [--only chips]
"""
import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
W, H = 832, 480
COLS = "image,projectile_force_angle,projectile_force_magnitude,projectile_coordx,projectile_coordy,projectile_mass," \
       "target_indirect_force_angle,target_indirect_force_magnitude,target_coordx,target_coordy,target_mass,width,height,caption"


def csv_row(img, mode, x, y, angle, force, caption):
    yc = H - int(round(y))
    x = int(round(x))
    cap = '"' + caption.replace('"', "'") + '"'
    if mode == "direct":
        return f"{img},{angle},{force},{x},{yc},-1,-1.0,-1.0,{x},{yc},-1,{W},{H},{cap}"
    return f"{img},-1.0,-1.0,{x},{yc},-1,{angle},{force},{x},{yc},-1,{W},{H},{cap}"


def preview(im, x, y, angle, force, mode, prompts, path, note=""):
    p = im.copy()
    d = ImageDraw.Draw(p)
    col = (255, 0, 0) if mode == "direct" else (0, 255, 0)
    L = W / 8 + (W / 2 - W / 8) * (force - 30) / (400 - 30)   # Goal Force blob travel for this force
    x1, y1 = x + L * math.cos(math.radians(angle)), y - L * math.sin(math.radians(angle))
    d.ellipse([x - 20, y - 20, x + 20, y + 20], outline=col, width=3)
    d.line([x, y, x1, y1], fill=col, width=4)
    a = math.atan2(y1 - y, x1 - x)
    for s in (2.6, -2.6):
        d.line([x1, y1, x1 + 14 * math.cos(a + s), y1 + 14 * math.sin(a + s)], fill=col, width=4)
    for n, pts in (prompts or {}).items():
        for px, py in pts:
            d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(255, 255, 0))
        d.text((pts[0][0] + 6, pts[0][1] - 6), n, fill=(255, 255, 0))
    d.text((6, 6), f"{mode} force {force} angle {angle}  {note}", fill=(255, 255, 255))
    p.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    spec = json.load(open(ROOT / "multiturn/photo_scenes.json"))
    for name, s in spec.items():
        if args.only and name != args.only:
            continue
        out = ROOT / "datasets/multiturn" / name
        (out / "images").mkdir(parents=True, exist_ok=True)
        im = ImageOps.exif_transpose(Image.open(ROOT / s["photo"])).convert("RGB")
        x0, y0, x1, y1 = s["crop"]
        assert abs((x1 - x0) / (y1 - y0) - W / H) < 0.01, f"{name}: crop aspect {(x1 - x0) / (y1 - y0):.3f}"
        im = im.crop((x0, y0, x1, y1)).resize((W, H), Image.LANCZOS)
        t = s["turn1"]
        fn = f"{name}_t1.png"
        im.save(out / "images" / fn)
        (out / f"{name}_t1.csv").write_text(COLS + "\n" + csv_row(fn, t["mode"], *t["point"], t["angle"], t["force"], t["caption"]) + "\n")
        preview(im, *t["point"], t["angle"], t["force"], t["mode"], s["prompts"], out / f"{name}_t1_preview.png")
        json.dump({"photo": s["photo"], "crop": s["crop"], **t, "prompts": s["prompts"], "notes": s.get("notes", "")},
                  open(out / f"{name}_t1_meta.json", "w"), indent=1, ensure_ascii=False)
        print("wrote", out)


if __name__ == "__main__":
    main()
