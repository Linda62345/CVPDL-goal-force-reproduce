cd "$(dirname "$0")/.."
# wait for the rack pilot batch to finish first (single GPU)
until grep -qE "^EXIT" logs/run_rack_pilot.log; do sleep 30; done
source venv/bin/activate
export CUDA_VISIBLE_DEVICES=0
export VRAM_LIMIT_GB=16
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
COMMON="--device_id 0 --world_size 1 --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors --seeds 0 1 2"
echo "START rack-resume $(date '+%F %T')"   # re-run pilot: skips finished, completes any missing
python -u scripts/inference/inference_goal_force.py $COMMON --output_dir outputs/rack_pilot \
  --example_paths datasets/rack/mug_left.csv datasets/rack/mug_right.csv
echo "START daruma+bowling $(date '+%F %T')"
python -u scripts/inference/inference_goal_force.py $COMMON --output_dir outputs/daruma_bowling \
  --example_paths datasets/daruma/daruma_up.csv datasets/daruma/daruma_upleft.csv datasets/daruma/daruma_upright.csv datasets/bowling/bowling_forward.csv
echo "EXIT $? $(date '+%F %T')"
