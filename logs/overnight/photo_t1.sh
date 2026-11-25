#!/bin/bash
# photo_t1.sh SCENE : Goal Force turn 1 (seed 0) + turn-1 state extraction (stride 1). Resumable.
cd "$(dirname "$0")/../.."
S=$1
OUT=outputs/multiturn/photos/$S/t1_gf
logs/overnight/gf.sh $OUT 0 datasets/multiturn/$S/${S}_t1.csv || exit 1
V=$(ls $OUT/step-3000_${S}_t1__*seed_0.mp4 | grep -v -- -with-prompt | grep -v control | head -1)
PROMPTS=$(venv/bin/python -c "import json;print(json.dumps(json.load(open('multiturn/photo_scenes.json'))['$S']['prompts']))")
[ -f outputs/multiturn/photos/$S/t1_s0/state.json ] || \
  HF_HOME=$PWD/imagegen/hf_cache imagegen/venv/bin/python -I multiturn/extract_state.py --video "$V" --out outputs/multiturn/photos/$S/t1_s0 --prompts "$PROMPTS" --stride 1
