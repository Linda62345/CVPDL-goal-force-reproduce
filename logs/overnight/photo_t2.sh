#!/bin/bash
# photo_t2.sh SCENE TARGET MODE ANGLE FORCE "SEEDS" "CAPTION" [noforce]
# turn-2 inputs from the turn-1 state -> Goal Force (seeds) -> repair_one (baseline/appearance/full + eval) per seed. Resumable.
cd "$(dirname "$0")/../.."
S=$1; TGT=$2; MODE=$3; ANG=$4; F=$5; SEEDS=$6; CAP=$7; NF=$8
P=outputs/multiturn/photos/$S/t1_s0/state.json
[ -f $P ] || { echo "no turn-1 state for $S"; exit 1; }
NAME=${S}_t2; OUT=outputs/multiturn/photos/$S/t2_gf; EXP=ph_$S
if [ "$NF" = noforce ]; then NAME=${S}_t2_noforce; OUT=outputs/multiturn/photos/$S/t2_noforce_gf; EXP=ph_${S}_noforce; export GF_ZERO_CONTROL=1 NOFORCE=1; fi
[ -f datasets/multiturn/$S/$NAME.csv ] || venv/bin/python -I multiturn/make_next_turn.py --state $P --target $TGT --mode $MODE \
   --angle $ANG --force $F --caption "$CAP" --name $NAME --out_dir datasets/multiturn/$S || exit 1
logs/overnight/gf.sh $OUT "$SEEDS" datasets/multiturn/$S/$NAME.csv || exit 1
rc=0
for sd in $SEEDS; do
  V=$(ls $OUT/step-3000_${NAME}__*seed_${sd}.mp4 | head -1)
  logs/overnight/repair_one.sh $S ${S}_t2_seed$sd "$V" $P $TGT $ANG "$CAP" $EXP || { echo "REPAIR_FAIL seed $sd"; rc=1; }
done
exit $rc
