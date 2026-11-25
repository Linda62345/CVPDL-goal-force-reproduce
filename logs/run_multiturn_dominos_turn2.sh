# Multi-turn baseline, turn 2 (input = last frame of turn 1 seed 0): A direct force on white ball, B goal force on fallen domino
source venv/bin/activate
export CUDA_VISIBLE_DEVICES=0 VRAM_LIMIT_GB=16 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "START $(date '+%F %T')"
python -u scripts/inference/inference_goal_force.py --device_id 0 --world_size 1 \
  --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors \
  --seeds 0 --output_dir outputs/multiturn/dominos_turn2 \
  --example_paths datasets/multiturn/dominos/t2A_white_direct_s0.csv datasets/multiturn/dominos/t2B_domino_goal_s0.csv
echo "EXIT $? $(date '+%F %T')"
