"""Shared helpers for multi-turn Goal Force: multi-object SAM2 tracking, per-object state, DINO appearance.

Coordinates: everything in this package uses TOP-LEFT pixel coords (x right, y down), like images.
Only make_next_turn.py converts to Goal Force CSV convention (BOTTOM-LEFT origin: y_csv = H - y).
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from appearance.metrics import crop, rgb2lab  # noqa: E402,F401

SAM2_ID = "facebook/sam2.1-hiera-large"
DINO_ID = "facebook/dinov2-base"


# ---------------------------------------------------------------- tracking
def track_objects(frames, prompts, device="cuda"):
    """frames: [T,H,W,3] uint8. prompts: {name: [[x,y], ...]} positive clicks on frame 0 (top-left px).
    Returns {name: bool masks [T,H,W]}."""
    from transformers import Sam2VideoModel, Sam2VideoProcessor

    T, H, W, _ = frames.shape
    model = Sam2VideoModel.from_pretrained(SAM2_ID).to(device, dtype=torch.bfloat16)
    proc = Sam2VideoProcessor.from_pretrained(SAM2_ID)
    sess = proc.init_video_session(video=list(frames), inference_device=device, dtype=torch.bfloat16)
    names = list(prompts)
    # all objects in ONE call (SAM2 video needs them registered together); pad point lists to equal
    # length by repeating the last positive click
    k = max(len(prompts[n]) for n in names)
    pts = [[[float(x), float(y)] for x, y in prompts[n]] for n in names]
    pts = [p + [p[-1]] * (k - len(p)) for p in pts]
    proc.add_inputs_to_inference_session(
        inference_session=sess, frame_idx=0, obj_ids=list(range(1, len(names) + 1)),
        input_points=[pts], input_labels=[[[1] * k for _ in names]],
    )
    model(inference_session=sess, frame_idx=0)
    out = {n: np.zeros((T, H, W), bool) for n in names}
    for o in model.propagate_in_video_iterator(sess):
        m = proc.post_process_masks([o.pred_masks], original_sizes=[[H, W]], binarize=True)[0]
        m = m[:, 0].cpu().numpy().astype(bool)  # [num_obj,H,W], ordered by obj_ids
        for i, n in enumerate(names):
            out[n][o.frame_idx] = m[i]
    del model
    torch.cuda.empty_cache()
    return out


def interior_points(mask, k=3, seed=0):
    """k click points well inside a mask (for re-prompting SAM2 on the next turn)."""
    import cv2

    m = mask.astype(np.uint8)
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    if dist.max() == 0:
        return []
    ys, xs = np.nonzero(dist >= 0.5 * dist.max())
    pts = [(int(xs[i]), int(ys[i])) for i in [int(np.argmax(dist[ys, xs]))]]
    rng = np.random.default_rng(seed)
    if len(xs) > 1:
        for i in rng.choice(len(xs), size=min(k - 1, len(xs) - 1), replace=False):
            pts.append((int(xs[i]), int(ys[i])))
    return [list(p) for p in pts]


# ---------------------------------------------------------------- state
def mask_state(mask, min_area=30):
    a = int(mask.sum())
    if a < min_area:
        return {"visible": False, "area": a}
    ys, xs = np.nonzero(mask)
    cx, cy = float(xs.mean()), float(ys.mean())
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    # principal axis angle (deg, 0 = horizontal, 90 = vertical) and elongation
    cov = np.cov(np.stack([xs - cx, ys - cy]))
    ev, evec = np.linalg.eigh(cov)
    major = evec[:, 1]
    angle = float(np.degrees(np.arctan2(abs(major[1]), abs(major[0]) + 1e-9)))
    elong = float(np.sqrt(ev[1] / max(ev[0], 1e-9)))
    return {"visible": True, "area": a, "centroid": [cx, cy], "bbox": [x0, y0, x1, y1],
            "aspect_hw": (y1 - y0) / max(x1 - x0, 1), "axis_angle": angle, "elongation": elong}


def pose_label(s, ref):
    """Coarse pose vs the object's turn-1 frame-0 state: 'as_initial' / 'changed' (e.g. toppled) / 'missing'.
    Only meaningful for elongated objects (dominoes, blocks, bottles); round objects return 'n/a'."""
    if not s.get("visible"):
        return "missing"
    if ref.get("elongation", 1) < 1.4:
        return "n/a"
    d_angle = abs(s["axis_angle"] - ref["axis_angle"])
    d_aspect = abs(np.log(max(s["aspect_hw"], 1e-3) / max(ref["aspect_hw"], 1e-3)))
    return "changed" if (d_angle > 35 or d_aspect > 0.5) else "as_initial"


# ---------------------------------------------------------------- appearance
class Dino:
    def __init__(self, device="cuda"):
        from transformers import AutoImageProcessor, AutoModel
        self.proc = AutoImageProcessor.from_pretrained(DINO_ID)
        self.model = AutoModel.from_pretrained(DINO_ID).to(device).eval()
        self.device = device

    @torch.no_grad()
    def emb(self, img):
        x = self.proc(images=Image.fromarray(img), return_tensors="pt").to(self.device)
        v = self.model(**x).last_hidden_state[:, 0]
        return torch.nn.functional.normalize(v, dim=-1)[0].cpu().numpy()
