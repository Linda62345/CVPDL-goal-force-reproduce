#!/bin/bash
# repair_one.sh SCENE RUN_ID VIDEO PREV_STATE TARGET ANGLE CAPTION [EXP]
# baseline eval (track, stride 1) -> appearance + full repair -> eval of both -> 3-row comparison strip. Resumable.
cd "$(dirname "$0")/../.."
export HF_HOME=$PWD/imagegen/hf_cache CUDA_VISIBLE_DEVICES=0
SCENE=$1; RID=$2; V=$3; P=$4; TGT=$5; ANG=$6; CAP=$7; EXP=${8:-exp8}
E=outputs/multiturn/$EXP/eval; R=outputs/multiturn/$EXP/repair/$RID
IPY=imagegen/venv/bin/python; VPY=venv/bin/python
set -e
$IPY -I multiturn/evaluate.py --video "$V" --prev_state "$P" --target $TGT --angle $ANG --method baseline --scene $SCENE --out $E/baseline/$RID ${NOFORCE:+--no_force}
for c in appearance full; do
  $VPY -I multiturn/memory_repair.py --video "$V" --track $E/baseline/$RID/track --prev_state "$P" --target $TGT --cond $c --out $R --prompt "$CAP" --eval $E/baseline/$RID/eval.json
  $IPY -I multiturn/evaluate.py --video $R/$c.mp4 --prev_state "$P" --target $TGT --angle $ANG --method $c --scene $SCENE --out $E/$c/$RID ${NOFORCE:+--no_force}
done
$IPY -I multiturn/compare3.py --videos "$V" $R/appearance.mp4 $R/full.mp4 --labels baseline appearance full --out $R/compare.jpg
