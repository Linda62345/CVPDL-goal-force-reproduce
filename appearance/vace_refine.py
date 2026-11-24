"""Stage-2 appearance restoration with Wan2.1-VACE-1.3B (diffsynth).
Keeps everything outside the edit mask, regenerates the object region guided by the reference image.

    venv/bin/python -I appearance/vace_refine.py --dir outputs/appearance/<id> --src vace_src_gray.mp4 \
        --tag E2 --prompt "..."
"""
import argparse
import json
import time
from pathlib import Path

import imageio.v3 as iio
import torch
from PIL import Image

from diffsynth.data import save_video
from diffsynth.pipelines.wan_video_new import ModelConfig, WanVideoPipeline

M = "./models/Wan-AI"
NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，"
       "丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，"
       "静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")


def load_frames(p):
    return [Image.fromarray(f) for f in iio.imread(p)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--src", default="vace_src_gray.mp4")
    ap.add_argument("--tag", default="E2")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--vace_scale", type=float, default=1.0)
    ap.add_argument("--no_ref", action="store_true")
    ap.add_argument("--mask", default="vace_mask.mp4")
    args = ap.parse_args()
    d = Path(args.dir)

    pipe = WanVideoPipeline.from_pretrained(
        torch_dtype=torch.bfloat16, device="cuda",
        model_configs=[
            ModelConfig(path=f"{M}/Wan2.1-VACE-1.3B/diffusion_pytorch_model.safetensors"),
            ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/models_t5_umt5-xxl-enc-bf16.pth"),
            ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/Wan2.1_VAE.pth"),
        ],
        tokenizer_config=ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/google/umt5-xxl"),
    )
    pipe.enable_vram_management()

    src = load_frames(d / args.src)
    mask = load_frames(d / args.mask)
    T = len(src)
    H, W = src[0].height, src[0].width
    t0 = time.time()
    video = pipe(
        prompt=args.prompt, negative_prompt=NEG,
        vace_video=src, vace_video_mask=mask,
        vace_reference_image=None if args.no_ref else Image.open(d / "reference.png").convert("RGB"),
        vace_scale=args.vace_scale,
        height=H, width=W, num_frames=T, seed=args.seed, num_inference_steps=args.steps, tiled=True,
    )
    dt = time.time() - t0
    save_video(video, str(d / f"{args.tag}.mp4"), fps=15, quality=9)
    json.dump({"tag": args.tag, "src": args.src, "seconds": dt, "prompt": args.prompt, "seed": args.seed,
               "vace_scale": args.vace_scale, "mask": args.mask, "ref": not args.no_ref},
              open(d / f"{args.tag}_meta.json", "w"), indent=1)
    print(args.tag, "done in", round(dt), "s")


if __name__ == "__main__":
    main()
