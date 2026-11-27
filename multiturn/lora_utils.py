"""LoRA helpers for Wan2.1-VACE-1.3B (shared by training, evaluation and memory_repair.py)."""
import torch
from peft import LoraConfig, inject_adapter_in_model
from safetensors.torch import load_file, save_file

TARGETS = ["q", "k", "v", "o", "ffn.0", "ffn.2"]
LORA_MODULES = ("dit", "vace")
M = "./models/Wan-AI"


def load_vace_pipe(device="cuda"):
    from diffsynth.pipelines.wan_video_new import ModelConfig, WanVideoPipeline
    return WanVideoPipeline.from_pretrained(
        torch_dtype=torch.bfloat16, device=device,
        model_configs=[ModelConfig(path=f"{M}/Wan2.1-VACE-1.3B/diffusion_pytorch_model.safetensors"),
                       ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/models_t5_umt5-xxl-enc-bf16.pth"),
                       ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/Wan2.1_VAE.pth")],
        tokenizer_config=ModelConfig(path=f"{M}/Wan2.1-T2V-1.3B/google/umt5-xxl"))


def inject_lora(pipe, rank=32, alpha=None):
    cfg = LoraConfig(r=rank, lora_alpha=alpha or rank, target_modules=TARGETS)
    for name in LORA_MODULES:
        m = inject_adapter_in_model(cfg, getattr(pipe, name))
        for n, p in m.named_parameters():
            if "lora_" in n:
                p.data = p.data.to(dtype=pipe.torch_dtype, device=pipe.device)
        setattr(pipe, name, m)


def lora_parameters(pipe):
    for name in LORA_MODULES:
        for n, p in getattr(pipe, name).named_parameters():
            if "lora_" in n:
                yield p


def save_lora(pipe, path):
    sd = {}
    for name in LORA_MODULES:
        for k, v in getattr(pipe, name).state_dict().items():
            if "lora_" in k:
                sd[f"{name}.{k}"] = v.detach().to("cpu", torch.bfloat16).contiguous()
    save_file(sd, path)
    return len(sd)


def load_lora(pipe, path, rank=32):
    """inject adapters and load weights from save_lora() output"""
    inject_lora(pipe, rank=rank)
    sd = load_file(path)
    n_loaded = 0
    for name in LORA_MODULES:
        sub = {k[len(name) + 1:]: v for k, v in sd.items() if k.startswith(name + ".")}
        missing, unexpected = getattr(pipe, name).load_state_dict(sub, strict=False)
        assert not unexpected, unexpected[:5]
        n_loaded += len(sub)
    assert n_loaded == len(sd)
    return n_loaded
