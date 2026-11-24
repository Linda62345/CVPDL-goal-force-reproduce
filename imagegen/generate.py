"""Generate placeholder product-on-rail scenes with Qwen-Image (Apache 2.0, ungated).

Run from goal-force/ with the isolated env (all caches stay inside imagegen/):
    HF_HOME=imagegen/hf_cache imagegen/venv/bin/python imagegen/generate.py --seeds 0 1 2
Outputs: imagegen/outputs/<scene>_s<seed>.png  (+ prompts.jsonl log)
"""
import argparse
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(HERE / "hf_cache"))

import torch  # noqa: E402
from diffusers import DiffusionPipeline  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default=str(HERE / "scenes.json"))
    ap.add_argument("--only", nargs="*", help="scene ids to run (default: all)")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--width", type=int, default=1664)
    ap.add_argument("--height", type=int, default=928)
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--out", default=str(HERE / "outputs"))
    args = ap.parse_args()

    cfg = json.loads(Path(args.scenes).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    pipe = DiffusionPipeline.from_pretrained("Qwen/Qwen-Image", torch_dtype=torch.bfloat16)
    # transformer (~41GB) does not fit in 32GB VRAM: stream weights from CPU RAM
    pipe.enable_group_offload(onload_device=torch.device("cuda"), offload_device=torch.device("cpu"),
                              offload_type="leaf_level", use_stream=True)

    log = open(out / "prompts.jsonl", "a")
    for sc in cfg["scenes"]:
        if args.only and sc["id"] not in args.only:
            continue
        prompt = f'{sc["prompt"]} {cfg["common_suffix"]}'
        for seed in args.seeds:
            path = out / f'{sc["id"]}_s{seed}.png'
            if path.exists():
                print("skip", path.name)
                continue
            img = pipe(
                prompt,
                width=args.width,
                height=args.height,
                num_inference_steps=args.steps,
                negative_prompt=" ",
                true_cfg_scale=4.0,
                generator=torch.Generator("cpu").manual_seed(seed),
            ).images[0]
            img.save(path)
            log.write(json.dumps({"file": path.name, "scene": sc["id"], "split": sc["split"],
                                  "seed": seed, "prompt": prompt}) + "\n")
            log.flush()
            print("saved", path.name)


if __name__ == "__main__":
    main()
