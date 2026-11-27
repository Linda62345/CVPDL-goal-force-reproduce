#!/bin/bash
# scene.sh SCENE SEED [v2] : two-turn run on one paper example photo (multiturn/paper_scenes.json). Resumable.
# turn 1 (paper CSV, unchanged) -> SAM2 state -> turn-2 CSV (direct force on tracked centroid) -> turn 2
# -> baseline eval -> lora_orig repair + eval -> comparison strip.
cd "$(dirname "$0")/../.."
export HF_HOME=$PWD/imagegen/hf_cache CUDA_VISIBLE_DEVICES=0
S=$1; SD=$2; VAR=${3:-}
IPY=imagegen/venv/bin/python; VPY=venv/bin/python
LORA=outputs/lora/vace_appearance/step-3000.safetensors
B=outputs/multiturn/paper/$S; E=outputs/multiturn/paper_eval; DT=datasets/multiturn/paper/$S
get() { $VPY -c "import json;s=json.load(open('multiturn/paper_scenes.json'))['$S'];print($1)"; }
CSV=$(get "s['csv']"); IMG=$(basename $(get "s['csv']") | sed 's/_obj1_prompt1.csv//')
if [ "$VAR" = v2 ]; then
  # turn-1 variant: paper CSV + "The camera is static." + goal force 200 (paper: 350, no camera sentence)
  B=outputs/multiturn/paper_v2/$S; E=outputs/multiturn/paper_v2_eval; DT=datasets/multiturn/paper_v2/$S
  mkdir -p $DT/images; cp -n $(dirname $CSV)/images/$IMG.png $DT/images/
  [ -f $DT/${IMG}_v2.csv ] || $VPY -c "
import pandas as pd; d=pd.read_csv('$CSV'); d['target_indirect_force_magnitude']=200.0
d['caption']=d['caption'].str.rstrip('. ')+'. The camera is static.'; d.to_csv('$DT/${IMG}_v2.csv',index=False)"
  CSV=$DT/${IMG}_v2.csv
fi
PROMPTS=$(get "json.dumps(s['prompts'])")
TGT=$(get "s['turn2']['target']"); ANG=$(get "s['turn2']['angle']"); F=$(get "s['turn2']['force']"); CAP=$(get "s['turn2']['caption']")
set -e
# turn 1
logs/overnight/gf.sh $B/t1_gf $SD $CSV
V1=$(ls $B/t1_gf/step-3000_${IMG}__*seed_${SD}.mp4 | head -1)
[ -f $B/t1_s$SD/state.json ] || $IPY -I multiturn/extract_state.py --video "$V1" --out $B/t1_s$SD --prompts "$PROMPTS" --stride 1
# turn 2 inputs
D=$DT; N=${S}_t2_s$SD
CH=$($VPY -I multiturn/paper_pick_t2.py $S $B/t1_s$SD/state.json) || { echo "SKIP_TURN2: no visible turn-2 target ($S seed $SD)"; exit 3; }
IFS=$'\t' read -r TGT ANG F CAP <<< "$CH"; echo "turn-2 choice: $TGT angle $ANG ($B/t1_s$SD/t2_choice.json)"
[ -f $D/$N.csv ] || $VPY -I multiturn/make_next_turn.py --state $B/t1_s$SD/state.json --target $TGT --mode direct \
   --angle $ANG --force $F --caption "$CAP" --name $N --out_dir $D
logs/overnight/gf.sh $B/t2_gf $SD $D/$N.csv
V2=$(ls $B/t2_gf/step-3000_${N}__*seed_${SD}.mp4 | head -1)
P=$B/t1_s$SD/state.json; RID=${S}_s$SD; R=$B/repair/$RID
$IPY -I multiturn/evaluate.py --video "$V2" --prev_state $P --target $TGT --angle $ANG --method baseline --scene $S --out $E/baseline/$RID
[ -f $R/lora_orig.mp4 ] || $VPY -I multiturn/memory_repair.py --video "$V2" --track $E/baseline/$RID/track --prev_state $P \
   --target $TGT --cond lora_orig --lora $LORA --out $R --prompt "$CAP" --eval $E/baseline/$RID/eval.json
$IPY -I multiturn/evaluate.py --video $R/lora_orig.mp4 --prev_state $P --target $TGT --angle $ANG --method lora_orig --scene $S --out $E/lora_orig/$RID
[ -f $R/compare.jpg ] || $IPY -I multiturn/compare3.py --videos "$V2" $R/lora_orig.mp4 --labels baseline lora_orig --out $R/compare.jpg
exit 0
