# Appearance preservation for Goal Force videos (two-stage: Goal Force → track → restore)

Goal: when the object moves, its shape and color stay like the product in frame 0. The two-stage idea is borrowed from HECTOR (ICML 2026, arXiv 2603.08850): motion comes from Goal Force, and appearance is restored using a reference image of the product.

| Script | Env | Purpose |
|---|---|---|
| `track_sam2.py` | `imagegen/venv` | SAM2.1 tracks the object from a click on frame 0 → `masks.npz` |
| `metrics.py` | `imagegen/venv` | R-DINO (DINOv2 object-region similarity, as in HECTOR), silhouette IoU, Lab ΔE, area variation |
| `prepare_inputs.py` | `venv` | E1 rigid paste-back, plus VACE inputs (edit mask, source video, reference image) |
| `vace_refine.py` | `venv` | Wan2.1-VACE-1.3B repaints the edit region (diffsynth) |
| `compare_strip.py` | `venv` | Side-by-side comparison strip of several variants |

Both envs and every model cache live inside `goal-force/` (`HF_HOME=imagegen/hf_cache`, VACE weights in `models/Wan-AI/Wan2.1-VACE-1.3B`).

## Variants
- **E0**: original Goal Force output
- **E1**: frame-0 object cut out and pasted rigidly at each tracked centroid (original object erased with a clean background plate)
- **E2**: VACE repaints a box around the object (gray fill) with the reference image
- **E2b**: same as E2, but the first 4 frames are left unedited as context (`--keep_first 4`)
- **E3**: VACE harmonizes the E1 composite

## Result on `daruma_upleft_s1` (1 video, seed 0)
| | R-DINO ↑ | frames <0.5 | shape IoU ↑ | ΔE ↓ | notes |
|---|---|---|---|---|---|
| E0 | 0.38 | 65/81 | 0.83 | 15.6 | doll turns into a faceless red ball mid-flight |
| E1 | 0.99 | 0 | 0.99 | 0.5 | shape exact but no rotation (stays upright in flight) |
| E2 | 0.60 | 21 | 0.89 | 16.9 | frame 0 broken (red cone) because it was masked |
| **E2b** | **0.69** | **17** | **0.92** | **8.4** | face and gold pattern kept, natural tumble; low frames are mid-spin and blurred |
| E3 | 0.83 | 1 | 0.98 | 7.4 | no rotation; VACE turns the gold pattern green |

Caveat: R-DINO compares against the frame-0 front view, so legitimate rotation (back side, blur) is penalized. That is why E1 and E3 score high while looking unnatural.
VACE pass: about 285 s per 81-frame video on the RTX 5090 (a Goal Force rerun takes about 1311 s).

## Result on 4 daruma videos (E0 → E2b, same pipeline, `run_e2b_batch.sh`)
| video | R-DINO | shape IoU | ΔE |
|---|---|---|---|
| daruma_upleft_s1 | 0.38 → 0.69 | 0.83 → 0.92 | 15.6 → 8.4 |
| daruma_up_s2 | 0.49 → 0.78 | 0.84 → 0.93 | 7.5 → 7.4 |
| daruma_upleft_s2 | 0.48 → 0.70 | 0.85 → 0.90 | 6.0 → 6.4 |
| daruma_upright_s2 | 0.42 → 0.74 | 0.84 → 0.91 | 11.8 → 6.3 |
| **mean** | **0.44 → 0.73** | **0.84 → 0.92** | **10.2 → 7.1** |

Visual check (`outputs/appearance/compare_3videos.png`):
- Identity is kept in all 4 videos: the face and pattern stay visible, and the object no longer becomes a ball.
- **Pose collapse:** VACE pulls the object toward the reference pose (upright, facing front). Tumbling and rolling are reduced. In `upleft_s2` the original video rolls along the ground, but the E2b version sits upright, so the motion itself changed. That video also has a semi-transparent ghost at f24.
- This matters for multi-turn: a reference of an upright object would push a fallen object back upright. The reference must give appearance only, not pose or state.

Note: the daruma inputs were generated with a wrong force point (y-axis bug, see the pilot report). This test still holds as a check of appearance restoration.
