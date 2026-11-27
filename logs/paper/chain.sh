#!/bin/bash
# chain.sh SCENE : experiment A, a 5-turn chain (multiturn/chain_scenes.json), seed 0, small direct force; each turn pushes
# one object toward another (angle 'toward:<obj>'). Resumable.
# Each turn: inputs (turn 1 from the original photo, turn k from turn k-1's state) -> Goal Force -> SAM2 state -> eval.
# Stops early (exit 3) if the turn's target is not visible; the turns done so far are kept.
cd "$(dirname "$0")/../.."
export HF_HOME=$PWD/imagegen/hf_cache CUDA_VISIBLE_DEVICES=0
S=$1; SD=0
IPY=imagegen/venv/bin/python; VPY=venv/bin/python
B=outputs/multiturn/chain/$S; D=datasets/multiturn/chain/$S
get() { $VPY -c "import json;c=json.load(open('multiturn/chain_scenes.json'));s=c['$S'];print($1)"; }
F=$(get "s['force']"); NT=$(get "len(s['turns'])")
set -e
mkdir -p $D/images $B
for k in $(seq 1 $NT); do
  TGT=$(get "s['turns'][$k-1][0]"); ANG=$(get "s['turns'][$k-1][1]"); CAP=$(get "s['turns'][$k-1][2]")
  if [[ $ANG == toward:* ]]; then
    OTHER=${ANG#toward:}
    ANG=$($VPY -c "
import json, math
s = json.load(open('multiturn/chain_scenes.json'))['$S']
if $k == 1:
    p = {n: v[0] for n, v in s['prompts'].items()}
else:
    o = json.load(open('$B/turn$((k-1))/state.json'))['objects']
    p = {n: o[n]['last']['centroid'] for n in ('$TGT', '$OTHER') if o.get(n, {}).get('last', {}).get('visible')}
    if '$OTHER' not in p:  # other object gone: fall back to its click on the original photo
        p['$OTHER'] = s['prompts']['$OTHER'][0]
a = math.degrees(math.atan2(-(p['$OTHER'][1] - p['$TGT'][1]), p['$OTHER'][0] - p['$TGT'][0])) % 360
print(round(a))")
    echo "turn $k: $TGT -> $OTHER angle $ANG"
  fi
  N=${S}_c$k
  if [ $k -eq 1 ]; then
    [ -f $D/$N.csv ] || $VPY -I - <<PY
import json, pandas as pd
from PIL import Image
c = json.load(open('multiturn/chain_scenes.json')); s = c['$S']
Image.open(s['image']).convert('RGB').save('$D/images/$N.png')
x, y = s['prompts']['$TGT'][0]; yc = 480 - y
cols = ["image","projectile_force_angle","projectile_force_magnitude","projectile_coordx","projectile_coordy","projectile_mass",
        "target_indirect_force_angle","target_indirect_force_magnitude","target_coordx","target_coordy","target_mass","width","height","caption"]
pd.DataFrame([["$N.png", $ANG, $F, x, yc, -1, -1.0, -1.0, x, yc, -1, 832, 480, """$CAP"""]], columns=cols).to_csv('$D/$N.csv', index=False)
PY
  else
    P=$B/turn$((k-1))/state.json
    V=$($VPY -c "import json;print(json.load(open('$P'))['objects'].get('$TGT',{}).get('last',{}).get('visible',False))")
    if [ "$V" != "True" ]; then echo "CHAIN_STOP: $TGT not visible after turn $((k-1)) ($S)"; exit 3; fi
    [ -f $D/$N.csv ] || $VPY -I multiturn/make_next_turn.py --state $P --target $TGT --mode direct --angle $ANG --force $F \
        --caption "$CAP" --name $N --out_dir $D
  fi
  logs/overnight/gf.sh $B/gf $SD $D/$N.csv
  VID=$(ls $B/gf/step-3000_${N}__*seed_${SD}.mp4 | head -1)
  if [ ! -f $B/turn$k/state.json ]; then
    if [ $k -eq 1 ]; then
      $IPY -I multiturn/extract_state.py --video "$VID" --out $B/turn$k --prompts "$(get "json.dumps(s['prompts'])")" --stride 1
    else
      $IPY -I multiturn/extract_state.py --video "$VID" --out $B/turn$k --prev_state $B/turn$((k-1))/state.json --stride 1
    fi
  fi
  if [ $k -gt 1 ]; then
    $IPY -I multiturn/evaluate.py --video "$VID" --prev_state $B/turn$((k-1))/state.json --target $TGT --angle $ANG \
        --method baseline --scene chain_$S --out outputs/multiturn/chain_eval/$S/turn$k
  fi
done
STATES=$(for k in $(seq 1 $NT); do echo -n "$B/turn$k/state.json "; done)
TGTS=$($VPY -c "import json;print(' '.join(t[0] for t in json.load(open('multiturn/chain_scenes.json'))['$S']['turns']))")
$IPY -I multiturn/eval_continuity.py --states $STATES --targets $TGTS --out $B/chain_eval.json
exit 0
