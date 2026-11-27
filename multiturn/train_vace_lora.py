"""Train the VACE appearance LoRA (plan: multiturn/lora_plan.md).

    venv/bin/python -I multiturn/train_vace_lora.py --out outputs/lora/vace_appearance --steps 3000
    (smoke test: --steps 20 --save_every 20)
Resumable: picks up the latest step-<N>.safetensors in --out (optimizer state restarts; noted in the log).
"""
import argparse
import glob
import json
import os
import random
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

from lora_data import DavisLoRADataset  # noqa: E402
from lora_utils import inject_lora, load_lora, load_vace_pipe, lora_parameters, save_lora  # noqa: E402


def to_pil(arr):
    return [Image.fromarray(a) for a in arr]


os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--save_every", type=int, default=500)
    ap.add_argument("--frames", type=int, default=33)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(a.seed)
    random.seed(a.seed)

    ds = DavisLoRADataset("train", T=a.frames, seed=a.seed)
    pipe = load_vace_pipe("cuda")

    # text contexts: one prompt per DAVIS train video, computed once, then T5 leaves the GPU
    ctx = {}
    with torch.no_grad():
        for name in ds.names:
            p = "a video of " + name.replace("-", " ")
            ctx[p] = pipe.prompter.encode_prompt(p, positive=True, device="cuda").detach()
    pipe.text_encoder.to("cpu")
    torch.cuda.empty_cache()

    pipe.scheduler.set_timesteps(1000, training=True)
    pipe.freeze_except([])
    start = 0
    ckpts = sorted(glob.glob(str(out / "step-*.safetensors")), key=lambda p: int(re.findall(r"step-(\d+)", p)[0]))
    if ckpts:
        load_lora(pipe, ckpts[-1], rank=a.rank)
        start = int(re.findall(r"step-(\d+)", ckpts[-1])[0])
        print("resumed from", ckpts[-1])
    else:
        inject_lora(pipe, rank=a.rank)
    # model_fn_wan_video calls vace(...) without the checkpointing flag -> turn it on here (no library edit)
    _vace_forward = pipe.vace.forward
    pipe.vace.forward = lambda *args, **kw: _vace_forward(*args, use_gradient_checkpointing=True, **kw)
    params = list(lora_parameters(pipe))
    for p in params:
        p.requires_grad_(True)
    print("trainable LoRA params:", sum(p.numel() for p in params) / 1e6, "M")
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.01)

    from diffsynth.pipelines.wan_video_new import WanVideoUnit_PromptEmbedder
    units = [u for u in pipe.units if not isinstance(u, WanVideoUnit_PromptEmbedder)]
    log = open(out / "train_log.jsonl", "a")
    if start:
        log.write(json.dumps({"event": "resume", "step": start, "note": "optimizer state restarted"}) + "\n")
    t0 = time.time()
    run = []
    for step in range(start + 1, a.steps + 1):
        s = ds.sample()
        inputs_shared = {
            "input_video": to_pil(s["target"]), "height": 480, "width": 832, "num_frames": a.frames,
            "cfg_scale": 1, "tiled": False, "rand_device": "cuda", "seed": random.randint(0, 2**31 - 1),
            "use_gradient_checkpointing": True, "use_gradient_checkpointing_offload": False, "cfg_merge": False,
            "vace_scale": 1, "max_timestep_boundary": 1.0, "min_timestep_boundary": 0.0,
            "vace_video": to_pil(s["source"]),
            "vace_video_mask": to_pil((s["mask"][..., None].repeat(3, -1) * 255).astype(np.uint8)),
            "vace_reference_image": Image.fromarray(s["reference"]),
        }
        inputs_posi = {"context": ctx[s["prompt"]]}
        inputs_nega = {}
        with torch.no_grad():
            for unit in units:
                inputs_shared, inputs_posi, inputs_nega = pipe.unit_runner(unit, pipe, inputs_shared, inputs_posi, inputs_nega)
        inputs = {**inputs_shared, **inputs_posi}
        loss = pipe.training_loss(dit=pipe.dit, motion_controller=pipe.motion_controller, vace=pipe.vace, **inputs)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        run.append(float(loss))
        if step % 10 == 0 or step == start + 1:
            rec = {"step": step, "loss": float(np.mean(run)), "sec_per_step": (time.time() - t0) / (step - start),
                   "mem_gb": torch.cuda.max_memory_allocated() / 1e9, "video": s["meta"]["video"]}
            log.write(json.dumps(rec) + "\n")
            log.flush()
            print(rec, flush=True)
            run = []
        if step % a.save_every == 0 or step == a.steps:
            n = save_lora(pipe, out / f"step-{step}.safetensors")
            print(f"saved step-{step} ({n} tensors)", flush=True)
    log.write(json.dumps({"event": "done", "step": a.steps, "hours": (time.time() - t0) / 3600}) + "\n")


if __name__ == "__main__":
    main()
