#!/bin/bash
# #10 branch from dominoes turn-1 seed 0 with a different push (C: red ball left; D: back-row domino right). Goal Force seed 0 + repair + eval.
cd "$(dirname "$0")/../.."
D=datasets/multiturn/dominos; OUT=outputs/multiturn/exp10/gf
logs/overnight/gf.sh $OUT 0 $D/t2C_red_left_s0.csv $D/t2D_backrow_right_s0.csv || exit 1
P=outputs/multiturn/dominos/t1_s0/state.json
VC=$(ls $OUT/step-3000_t2C_*seed_0.mp4); VD=$(ls $OUT/step-3000_t2D_*seed_0.mp4)
logs/overnight/repair_one.sh dominos_branch s0_C_seed0 "$VC" $P red_ball 180 "The red pool ball rolls back to the left and hits the white ball." exp10
logs/overnight/repair_one.sh dominos_branch s0_D_seed0 "$VD" $P domino_back 0 "A standing domino in the back row is pushed to the right and the dominoes next to it fall over one after another." exp10
