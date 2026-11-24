source venv/bin/activate
export CUDA_VISIBLE_DEVICES=0
export VRAM_LIMIT_GB=16
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "START $(date '+%F %T')"
python -u scripts/inference/inference_goal_force.py --device_id 0 --world_size 1 \
  --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors \
  --seeds 0 1 2 --output_dir outputs/rack_pilot \
  --example_paths datasets/rack/mug_left.csv datasets/rack/mug_right.csv
echo "EXIT $? $(date '+%F %T')"
