# Reproduction & Pilot Study (branch `reproduce-pilot`)

This branch is a fork of [brown-palm/goal-force](https://github.com/brown-palm/goal-force) (MIT License) used to reproduce Goal Force inference on a single **RTX 5090 (32GB)** and run a small pilot study.

- 📄 Pilot report (in Chinese): [`reports/pilot_report_2026-11-24.md`](reports/pilot_report_2026-11-24.md)
- 🎞️ Generated videos (short names, for annotation): [`annotations/videos/`](annotations/videos/)
- 📝 Annotation sheet + guide: [`annotations/`](annotations/)

## Environment
```bash
python3 -m venv venv && source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128   # Blackwell needs cu128
pip install -e .
```
Weights (~134GB) were downloaded with `logs/download_weights.sh` (note: the original version mis-used `--include`; the committed one is the fixed version for the remaining files — see the report).

## Changes to `scripts/inference/inference_goal_force.py`
All are opt-in; without the new args/env vars the original behaviour is unchanged.
- `VRAM_LIMIT_GB` env var — caps resident weights on GPU (default setting OOMs on 32GB; we use 16)
- `--seeds 0 1 2` — load the model once, run every CSV for every seed
- `--output_dir` — custom output folder
- per-video timing written to `<output_dir>/timings.jsonl`
- skips videos that already exist (resume after interruption)

Example: see `logs/run_rack_pilot.sh` and `logs/run_queue2.sh`.

## Image credits
- `datasets/bowling/images/bowling.png` — cropped/resized from [File:Bowling_-_albury.jpg](https://commons.wikimedia.org/wiki/File:Bowling_-_albury.jpg) by **Fir0002/Flagstaffotos**, licensed **CC BY-NC 3.0** (non-commercial) / GFDL 1.2.
- `datasets/rack/images/mug.png`, `datasets/daruma/images/daruma.png` — own photos.
