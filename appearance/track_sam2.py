"""Track one object through a video with SAM2.1 (transformers) and save per-frame masks.

Run with the imagegen env (caches stay inside goal-force/imagegen/hf_cache):
    HF_HOME=imagegen/hf_cache imagegen/venv/bin/python -I appearance/track_sam2.py \
        --video annotations/videos/daruma_upleft_s1.mp4 --points 444,290 444,335 --out outputs/appearance/daruma_upleft_s1
Writes <out>/masks.npz (bool [T,H,W]) and <out>/track_overlay.png.
"""
import argparse
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import torch
from PIL import Image, ImageDraw
from transformers import Sam2VideoModel, Sam2VideoProcessor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--points", nargs="+", required=True, help="x,y positive clicks on frame 0 (pixels)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="facebook/sam2.1-hiera-large")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = iio.imread(args.video)  # [T,H,W,3] uint8
    T, H, W, _ = frames.shape

    dev = "cuda"
    model = Sam2VideoModel.from_pretrained(args.model).to(dev, dtype=torch.bfloat16)
    proc = Sam2VideoProcessor.from_pretrained(args.model)
    sess = proc.init_video_session(video=list(frames), inference_device=dev, dtype=torch.bfloat16)
    pts = [[float(v) for v in p.split(",")] for p in args.points]
    proc.add_inputs_to_inference_session(
        inference_session=sess, frame_idx=0, obj_ids=1,
        input_points=[[pts]], input_labels=[[[1] * len(pts)]],
    )
    model(inference_session=sess, frame_idx=0)

    masks = np.zeros((T, H, W), dtype=bool)
    for o in model.propagate_in_video_iterator(sess):
        m = proc.post_process_masks([o.pred_masks], original_sizes=[[H, W]], binarize=True)[0]
        masks[o.frame_idx] = m[0, 0].cpu().numpy().astype(bool)
    np.savez_compressed(out / "masks.npz", masks=masks)

    # overlay strip: 8 evenly spaced frames, mask tinted green
    idx = np.linspace(0, T - 1, 8).astype(int)
    tw, th = W // 3, H // 3
    sheet = Image.new("RGB", (tw * len(idx), th))
    d = ImageDraw.Draw(sheet)
    for k, i in enumerate(idx):
        f = frames[i].astype(np.float32)
        f[masks[i]] = 0.5 * f[masks[i]] + 0.5 * np.array([0, 255, 0])
        sheet.paste(Image.fromarray(f.astype(np.uint8)).resize((tw, th)), (k * tw, 0))
        d.text((k * tw + 4, 4), f"{i} area={masks[i].sum()}", fill="yellow")
    sheet.save(out / "track_overlay.png")
    print("frames", T, "area f0", masks[0].sum(), "empty frames", int((masks.sum((1, 2)) == 0).sum()))


if __name__ == "__main__":
    main()
