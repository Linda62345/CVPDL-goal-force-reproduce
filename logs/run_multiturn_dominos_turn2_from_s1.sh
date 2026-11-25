# Multi-turn baseline, turn 2 from the turn-1 SEED-1 ending (same actions as the s0 chain: A direct on white ball, B goal on fallen domino2)
# Runs Goal Force, then state extraction + continuity eval for each video. Sequential, one launch.
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=0 VRAM_LIMIT_GB=16 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_HOME=$PWD/imagegen/hf_cache
OUT=outputs/multiturn/dominos_turn2_from_s1
echo "START $(date '+%F %T')"
venv/bin/python -u scripts/inference/inference_goal_force.py --device_id 0 --world_size 1 \
  --control_signal_type goal_force --model_ckpt_path checkpoints/goal_force/step-3000.safetensors \
  --seeds 0 --output_dir $OUT \
  --example_paths datasets/multiturn/dominos/t2A_white_direct_from_s1.csv datasets/multiturn/dominos/t2B_domino_goal_from_s1.csv
echo "GEN_EXIT $? $(date '+%F %T')"
for tag in A_white_direct B_domino_goal; do
  v=$(ls $OUT/step-3000_t2${tag}_from_s1__*seed_0.mp4)
  short=t2${tag%%_*}_from_s1
  imagegen/venv/bin/python -I multiturn/extract_state.py --video "$v" --out outputs/multiturn/dominos/$short \
    --prev_state outputs/multiturn/dominos/t1_s1/state.json --stride 2
done
imagegen/venv/bin/python -I multiturn/eval_continuity.py --states outputs/multiturn/dominos/t1_s1/state.json outputs/multiturn/dominos/t2A_from_s1/state.json \
  --targets red_ball white_ball --out outputs/multiturn/dominos/eval_t2A_from_s1.json
imagegen/venv/bin/python -I multiturn/eval_continuity.py --states outputs/multiturn/dominos/t1_s1/state.json outputs/multiturn/dominos/t2B_from_s1/state.json \
  --targets red_ball domino2 --out outputs/multiturn/dominos/eval_t2B_from_s1.json
echo "ALL_DONE $(date '+%F %T')"
