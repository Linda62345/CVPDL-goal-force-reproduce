#!/bin/bash
# E0 -> track -> E2b (VACE, first 4 frames kept) -> metrics, for several videos of the same scene.
# usage: bash appearance/run_e2b_batch.sh "<prompt>" "<x,y> <x,y>" vid1 vid2 ...   (vid = annotations/videos/<vid>.mp4)
set -e
cd "$(dirname "$0")/.."
export HF_HOME=$PWD/imagegen/hf_cache HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
PROMPT="$1"; POINTS="$2"; shift 2
PY=imagegen/venv/bin/python
for V in "$@"; do
  SRC=annotations/videos/$V.mp4; D=outputs/appearance/$V
  echo "=== $V $(date +%T)"
  $PY -I appearance/track_sam2.py --video $SRC --points $POINTS --out $D 2>&1 | tail -1
  $PY -I appearance/metrics.py --video $SRC --masks $D/masks.npz --out $D/E0_metrics.json 2>&1 | tail -1
  venv/bin/python -I appearance/prepare_inputs.py --video $SRC --dir $D --keep_first 4 --suffix _k4
  venv/bin/python -I appearance/vace_refine.py --dir $D --src vace_src_gray_k4.mp4 --mask vace_mask_k4.mp4 \
      --tag E2b --prompt "$PROMPT" > $D/E2b.log 2>&1
  tail -1 $D/E2b.log
  $PY -I appearance/track_sam2.py --video $D/E2b.mp4 --points $POINTS --out $D/E2btrk 2>&1 | tail -1
  $PY -I appearance/metrics.py --video $D/E2b.mp4 --masks $D/E2btrk/masks.npz --ref_video $SRC \
      --ref_masks $D/masks.npz --out $D/E2b_metrics.json 2>&1 | tail -1
  venv/bin/python -I appearance/compare_strip.py --out $D/compare_E0_E2b.png --scale 0.3 \
      --frames 0 6 12 24 36 48 60 72 80 --videos E0=$SRC E2b=$D/E2b.mp4
done
echo "=== done $(date +%T)"
