#!/bin/bash
# v2_if_needed.sh SCENE SEED : run the v2 turn-1 variant (camera static, goal force 150) only if the paper-setting turn 1
# for SCENE/SEED left no visible turn-2 target (SKIP_TURN2). Turn 2 = turn2b (collision version, 11/27). Else exit 0.
cd "$(dirname "$0")/../.."
S=$1; SD=$2
if [ -f logs/paper/done/t2b_${S}_s${SD}.ok ]; then echo "turn2b run succeeded for $S seed $SD; v2 not needed"; exit 0; fi
if grep -qsE "SKIP_TURN2|not visible in the last frame" logs/paper/${S}_s${SD}.log logs/paper/t2b_${S}_s${SD}.log; then
  exec logs/paper/scene_t2b.sh $S $SD v2
fi
echo "paper-setting turn 1 usable for $S seed $SD; v2 not needed"
