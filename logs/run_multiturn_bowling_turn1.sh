# Multi-turn baseline, turn 1 for bowling with the corrected (bottom-left) force point, 2 seeds
source venv/bin/activate
export CUDA_VISIBLE_DEVICES=0 VRAM_LIMIT_GB=16 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "START $(date '+%F %T')"
python -u scripts/inference/inference_goal_force.py --device_id 0 --world_size 1 \
  --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors \
  --seeds 0 1 --output_dir outputs/multiturn/bowling_turn1 \
  --example_paths datasets/bowling/bowling_forward.csv
echo "EXIT $? $(date '+%F %T')"
