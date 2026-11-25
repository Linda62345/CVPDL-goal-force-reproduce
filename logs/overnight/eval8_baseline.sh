#!/bin/bash
# #8 baseline evaluation (all available seeds) with the unified evaluator. Resumable (evaluate.py skips existing eval.json).
cd "$(dirname "$0")/../.."
export HF_HOME=$PWD/imagegen/hf_cache
PY=imagegen/venv/bin/python
ev() { # video prev_state target angle out
  [ -f "$1" ] || { echo "missing video $1"; return 0; }
  $PY -I multiturn/evaluate.py --video "$1" --prev_state "$2" --target "$3" --angle "$4" --method baseline --scene dominos --out "$5" || echo "EVAL_FAIL $5"
}
E=outputs/multiturn/exp8/eval/baseline
for start in s0 s1; do
  P=outputs/multiturn/dominos/t1_${start}/state.json
  for seed in 0 1 2; do
    if [ $start = s0 ]; then
      A=$(ls outputs/multiturn/dominos_turn2/step-3000_t2A_*seed_${seed}.mp4 outputs/multiturn/exp8/gf_from_s0/step-3000_t2A_*seed_${seed}.mp4 2>/dev/null | head -1)
      B=$(ls outputs/multiturn/dominos_turn2/step-3000_t2B_*seed_${seed}.mp4 outputs/multiturn/exp8/gf_from_s0/step-3000_t2B_*seed_${seed}.mp4 2>/dev/null | head -1)
    else
      A=$(ls outputs/multiturn/dominos_turn2_from_s1/step-3000_t2A_*seed_${seed}.mp4 outputs/multiturn/exp8/gf_from_s1/step-3000_t2A_*seed_${seed}.mp4 2>/dev/null | head -1)
      B=$(ls outputs/multiturn/dominos_turn2_from_s1/step-3000_t2B_*seed_${seed}.mp4 outputs/multiturn/exp8/gf_from_s1/step-3000_t2B_*seed_${seed}.mp4 2>/dev/null | head -1)
    fi
    [ -n "$A" ] && ev "$A" $P white_ball 0 $E/${start}_A_seed${seed}
    [ -n "$B" ] && ev "$B" $P domino2 0 $E/${start}_B_seed${seed}
  done
done
exit 0
