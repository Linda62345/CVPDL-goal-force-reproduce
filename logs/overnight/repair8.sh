#!/bin/bash
# repair8.sh START(s0|s1) PUSH(A|B) SEED : resolves the dominoes turn-2 Goal Force video and runs repair_one.sh
cd "$(dirname "$0")/../.."
ST=$1; PU=$2; SD=$3
if [ $ST = s0 ]; then D1=outputs/multiturn/dominos_turn2; D2=outputs/multiturn/exp8/gf_from_s0; else D1=outputs/multiturn/dominos_turn2_from_s1; D2=outputs/multiturn/exp8/gf_from_s1; fi
V=$(ls $D1/step-3000_t2${PU}_*seed_${SD}.mp4 $D2/step-3000_t2${PU}_*seed_${SD}.mp4 2>/dev/null | head -1)
[ -n "$V" ] || { echo "no video for $ST $PU $SD"; exit 1; }
if [ $PU = A ]; then TGT=white_ball; else TGT=domino2; fi
exec logs/overnight/repair_one.sh dominos ${ST}_${PU}_seed${SD} "$V" outputs/multiturn/dominos/t1_${ST}/state.json $TGT 0 \
  "The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes."
