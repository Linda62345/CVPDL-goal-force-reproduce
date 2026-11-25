"""Training pairs for the VACE appearance LoRA (design: multiturn/lora_plan.md §3).

One sample = (clean clip = target, degraded clip = vace_video, mask = vace_video_mask, reference = vace_reference_image,
prompt). The object keeps its pose/position in the degraded clip; the reference shows the SAME object at a DIFFERENT
time (different pose), on a white 832x480 canvas, often at a random place -> the model must take appearance from the
reference and pose/position from the clip.

    venv/bin/python -I multiturn/lora_data.py --preview outputs/lora/vace_appearance/data_preview   (writes 4 previews)
"""
import argparse
import glob
import os
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DAVIS = ROOT / "datasets/davis/DAVIS"
W, H = 832, 480
KEEP_FIRST = 4
EVAL_VAL_VIDEOS = 15  # first 15 (sorted) DAVIS val videos are the held-out test set


def davis_split(split):
    names = (DAVIS / f"ImageSets/2017/{split}.txt").read_text().split()
    if split == "val":
        names = sorted(names)[:EVAL_VAL_VIDEOS]
    return names


def load_video(name):
    fr = sorted(glob.glob(str(DAVIS / f"JPEGImages/480p/{name}/*.jpg")))
    an = sorted(glob.glob(str(DAVIS / f"Annotations/480p/{name}/*.png")))
    frames = np.stack([np.array(Image.open(f).convert("RGB")) for f in fr])
    labels = np.stack([np.array(Image.open(a)) for a in an])  # palette index per object
    return frames, labels


def fit(img, x0, nearest=False):
    """480 x ~854 -> 480 x 832 crop starting at column x0 (resizes first if height differs)."""
    h, w = img.shape[:2]
    if h != H:
        s = H / h
        img = cv2.resize(img, (int(round(w * s)), H), interpolation=cv2.INTER_NEAREST if nearest else cv2.INTER_AREA)
        w = img.shape[1]
    if w < W:
        pad = W - w
        img = cv2.copyMakeBorder(img, 0, 0, 0, pad, cv2.BORDER_REFLECT)
    return img[:, x0:x0 + W]


# ------------------------------------------------------------------ degradations (inside the mask only)
def degrade(clip, mask, rng):
    """clip [T,H,W,3] uint8, mask [T,H,W] bool -> degraded copy. 1-3 random ops, same ops for the whole clip
    (slowly varying), applied only inside the mask, never on the first KEEP_FIRST frames."""
    out = clip.astype(np.float32).copy()
    ops = rng.sample(["blur", "lowres", "color", "erase", "smooth", "fuse"], k=rng.randint(1, 3))
    T = len(clip)
    sigma = rng.uniform(2, 6)
    factor = rng.choice([4, 6, 8])
    dL, da, db = rng.uniform(-20, 20), rng.uniform(-18, 18), rng.uniform(-18, 18)
    sat = rng.uniform(0.4, 1.4)
    shift = (rng.randint(-60, 60), rng.randint(-40, 40))
    for t in range(KEEP_FIRST, T):
        f = out[t]
        m = mask[t]
        if not m.any():
            continue
        g = f.copy()
        if "blur" in ops:
            g = cv2.GaussianBlur(g, (0, 0), sigma)
        if "lowres" in ops:
            small = cv2.resize(g, (W // factor, H // factor), interpolation=cv2.INTER_AREA)
            g = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
        if "smooth" in ops:
            g = cv2.medianBlur(np.clip(g, 0, 255).astype(np.uint8), 9).astype(np.float32)
        if "color" in ops:
            lab = cv2.cvtColor(np.clip(g, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
            lab[..., 0] += dL
            lab[..., 1] = 128 + (lab[..., 1] - 128) * sat + da
            lab[..., 2] = 128 + (lab[..., 2] - 128) * sat + db
            g = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
        if "fuse" in ops:  # blend in pixels from a shifted copy of the frame (neighbour bleeding into the object)
            sh = np.roll(np.roll(clip[t].astype(np.float32), shift[0], axis=1), shift[1], axis=0)
            g = 0.55 * g + 0.45 * sh
        if "erase" in ops:  # gray blobs over part of the object
            ys, xs = np.nonzero(m)
            blob = np.zeros((H, W), np.uint8)
            r = random.Random(t * 7 + 1)
            for _ in range(3):
                i = r.randrange(len(xs))
                cv2.circle(blob, (int(xs[i]), int(ys[i])), r.randint(8, 30), 1, -1)
            g[blob.astype(bool)] = 127
        f[m] = g[m]
        out[t] = f
    return np.clip(out, 0, 255).astype(np.uint8)


def reference_canvas(frame, m, rng):
    """object crop (white background) on a white 832x480 canvas; 50% at its own place, else random place; scale 0.8-1.2"""
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    crop = frame[y0:y1, x0:x1].copy()
    cm = m[y0:y1, x0:x1]
    crop[~cm] = 255
    s = rng.uniform(0.8, 1.2)
    ch, cw = crop.shape[:2]
    nh, nw = max(4, min(H, int(ch * s))), max(4, min(W, int(cw * s)))
    crop = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    cm = cv2.resize(cm.astype(np.uint8), (nw, nh), interpolation=cv2.INTER_NEAREST).astype(bool)
    canvas = np.full((H, W, 3), 255, np.uint8)
    if rng.random() < 0.5:
        px, py = min(max(0, x0), W - nw), min(max(0, y0), H - nh)
    else:
        px, py = rng.randint(0, W - nw), rng.randint(0, H - nh)
    reg = canvas[py:py + nh, px:px + nw]
    reg[cm] = crop[cm]
    return canvas


def make_sample(name, frames, labels, rng, T=33):
    """returns dict(target, source, mask, reference, prompt, meta) or None if this video/object does not fit"""
    n = len(frames)
    if n < T:
        return None
    ids = [i for i in np.unique(labels) if i != 0]
    if not ids:
        return None
    obj = rng.choice(ids)
    stride = 2 if n >= 2 * T and rng.random() < 0.5 else 1
    start = rng.randint(0, n - stride * (T - 1) - 1)
    idx = list(range(start, start + stride * T, stride))
    x0 = rng.randint(0, max(0, frames.shape[2] - W)) if frames.shape[1] == H else 0
    clip = np.stack([fit(frames[i], x0) for i in idx])
    obj_m = np.stack([fit((labels[i] == obj).astype(np.uint8), x0, nearest=True) for i in idx]).astype(bool)
    if obj_m[KEEP_FIRST:].reshape(T - KEEP_FIRST, -1).sum(1).min() < 400:  # object must be visible in every edited frame
        return None
    # reference from a frame far from the clip (different pose)
    far = [i for i in range(n) if min(abs(i - idx[0]), abs(i - idx[-1])) >= 15 or not (idx[0] <= i <= idx[-1])]
    far = [i for i in far if (labels[i] == obj).sum() >= 400] or [i for i in range(n) if (labels[i] == obj).sum() >= 400]
    r = rng.choice(far)
    rf, rm = fit(frames[r], x0), fit((labels[r] == obj).astype(np.uint8), x0, nearest=True).astype(bool)
    if rm.sum() < 200:
        return None
    reference = reference_canvas(rf, rm, rng)
    k = rng.choice([7, 11, 15])
    ker = np.ones((k, k), np.uint8)
    mask = np.stack([cv2.dilate(m.astype(np.uint8), ker) > 0 for m in obj_m])
    mask[:KEEP_FIRST] = False
    source = degrade(clip, mask & obj_m | (mask & (rng.random() < 0.3)), rng)
    prompt = "a video of " + name.replace("-", " ")
    return {"target": clip, "source": source, "mask": mask, "reference": reference, "prompt": prompt,
            "meta": {"video": name, "object": int(obj), "frames": idx, "ref_frame": int(r)}}


class DavisLoRADataset:
    """infinite random samples from DAVIS train (or a fixed list for eval). Caches decoded videos in RAM."""

    def __init__(self, split="train", T=33, seed=0):
        self.names = davis_split(split)
        self.T = T
        self.rng = random.Random(seed)
        self.cache = {}

    def video(self, name):
        if name not in self.cache:
            self.cache[name] = load_video(name)
        return self.cache[name]

    def sample(self):
        for _ in range(50):
            name = self.rng.choice(self.names)
            fr, lb = self.video(name)
            s = make_sample(name, fr, lb, self.rng, self.T)
            if s is not None:
                return s
        raise RuntimeError("could not build a sample")


def preview(s, path):
    T = len(s["target"])
    idx = [0, KEEP_FIRST, T // 2, T - 1]
    rows = []
    for key in ["target", "source"]:
        rows.append(np.concatenate([s[key][i] for i in idx], 1))
    rows.append(np.concatenate([np.repeat(s["mask"][i][..., None] * 255, 3, 2).astype(np.uint8) for i in idx], 1))
    rows.append(np.concatenate([s["reference"]] + [np.full((H, W, 3), 255, np.uint8)] * 3, 1))
    img = Image.fromarray(np.concatenate(rows, 0)).resize((W * 2, H * 2))
    img.save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", required=True)
    ap.add_argument("--n", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.preview, exist_ok=True)
    ds = DavisLoRADataset("train", seed=123)
    for i in range(a.n):
        s = ds.sample()
        preview(s, f"{a.preview}/sample{i}.jpg")
        print(i, s["meta"], s["prompt"])
