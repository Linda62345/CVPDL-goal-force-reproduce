#!/bin/bash
# Goal Force generation wrapper: gf.sh OUT_DIR "SEEDS" CSV...   (resume: inference script skips existing outputs)
cd "$(dirname "$0")/../.."
export CUDA_VISIBLE_DEVICES=0 VRAM_LIMIT_GB=16 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
OUT=$1; SEEDS=$2; shift 2
venv/bin/python -u scripts/inference/inference_goal_force.py --device_id 0 --world_size 1 \
  --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors \
  --seeds $SEEDS --output_dir "$OUT" --example_paths "$@"
