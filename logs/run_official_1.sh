source venv/bin/activate
export CUDA_VISIBLE_DEVICES=0
export VRAM_LIMIT_GB=16
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "START $(date +%T)"
python -u scripts/inference/inference_goal_force.py --device_id 0 --world_size 1 --seed 5 \
  --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors \
  --example_paths datasets/examples/human-object-interaction/_bulb_tool_obj1_prompt1.csv 2>&1 \
  | while IFS= read -r line; do echo "$(date +%T) $line"; done
echo "EXIT ${PIPESTATUS[0]} $(date +%T)"
