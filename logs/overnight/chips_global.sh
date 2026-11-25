#!/bin/bash
# Diagnostic: appearance memory with a whole-frame edit mask on the chips NO-FORCE control (does memory pull the bag back?)
cd "$(dirname "$0")/../.."
export HF_HOME=$PWD/imagegen/hf_cache CUDA_VISIBLE_DEVICES=0
P=outputs/multiturn/photos/chips/t1_s0/state.json; E=outputs/multiturn/ph_chips_noforce/eval
CAP="A large bag of potato chips rests on a supermarket shelf."
rc=0
for sd in 0 1 2; do
  V=$(ls outputs/multiturn/photos/chips/t2_noforce_gf/step-3000_chips_t2_noforce__*seed_${sd}.mp4)
  R=outputs/multiturn/ph_chips_noforce/repair/chips_t2_seed$sd
  venv/bin/python -I multiturn/memory_repair.py --video "$V" --track $E/baseline/chips_t2_seed$sd/track --prev_state $P --target front_bag \
    --cond appearance_global --out $R --prompt "$CAP" --eval $E/baseline/chips_t2_seed$sd/eval.json || { rc=1; continue; }
  imagegen/venv/bin/python -I multiturn/evaluate.py --video $R/appearance_global.mp4 --prev_state $P --target front_bag --angle 0 --no_force \
    --method appearance_global --scene chips --out $E/appearance_global/chips_t2_seed$sd || rc=1
  imagegen/venv/bin/python -I multiturn/compare3.py --videos "$V" $R/appearance.mp4 $R/appearance_global.mp4 $R/full.mp4 \
    --labels baseline appearance appearance_global full --out $R/compare4.jpg
done
exit $rc
