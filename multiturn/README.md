# Multi-turn Goal Force: object-state memory tools

Topic: 延伸 Goal Force，以物件狀態記憶改善多回合互動影片的連續性 (extend Goal Force with object-state memory for multi-turn continuity).

**Baseline:** the next turn's input image is the previous turn's last frame. Goal Force runs again with a new force.

## Pipeline
```
turn k video ──► extract_state.py ──► state.json (per-object state)  +  memory/ (turn-1 appearance, carried)
                                          │                               last_frame.png
                                          ▼
                           make_next_turn.py ──► datasets/multiturn/<scene>/<name>.csv + images/ + _preview.png
                                          │
                                          ▼
                   scripts/inference/inference_goal_force.py ──► turn k+1 video ──► extract_state.py --prev_state ...
                                                                                   │
                                              eval_continuity.py (all state.json) ◄┘
```

| Script | Env | Does |
|---|---|---|
| `extract_state.py` | `imagegen/venv` | Multi-object SAM2 tracking. Turn 1 takes clicks (`--prompts`); later turns are re-prompted from the previous turn's last-frame masks (`--prev_state`). Saves the appearance memory (turn-1 crops, masks, states), per-object first and last state (centroid, bbox, principal-axis angle, coarse pose), trajectory, per-frame R-DINO against memory, `last_frame.png` and `state_overlay.png` |
| `make_next_turn.py` | `venv` | Writes the next turn's image and CSV. The force point is the target's tracked centroid, **converted to Goal Force's bottom-left y origin**. Also writes `_preview.png` with the arrow so the point can be checked before a 22-minute run |
| `eval_continuity.py` | `imagegen/venv` | Per turn: pose, R-DINO against memory, area ratio. Per transition, flags **JUMP** (state not carried over), **REVERT** (a fallen object stands up again), **RESET** (an object drifts back to its turn-1 place), **VANISH**, and the speed at the cut (end of turn k against start of turn k+1) |
| `common.py` | — | SAM2 tracking, per-mask state, pose label, DINO |

Coordinates are top-left pixels everywhere, except the CSV written by `make_next_turn.py`.

**Pose label:** only meaningful for elongated objects such as dominoes, pins and blocks. It is `changed` when the principal axis turns more than 35° or the aspect ratio changes by more than 1.65× relative to turn-1 frame 0. Round objects get `n/a`.

## Self-test (`outputs/multiturn/_selftest`)
Turn 1 is pilot `bowling_forward_s0`. The stand-in "turn 2" is `bowling_forward_s2`, which restarts from the original image, so the tools should report a discontinuity. Both run at stride 4.
- The ball is flagged **JUMP** (15.7 px).
- The ball's speed drops 2.83 → 0.06 px/frame at the cut.
- Knocked-down pins are labelled `changed`.
- The CSV y is converted (213 top-left → 267).

## Results: dominoes (official `_ballthendominos_obj1_prompt1`), 2026-11-24
Turn 1 uses the official CSV (goal force on the red ball), seeds 0 and 1. Turn 2 starts from the last frame of turn-1 seed 0 and uses seed 0. The input files are in `datasets/multiturn/dominos/`, and the run is `logs/run_multiturn_dominos_turn2.sh`. Tracking runs at stride 2, so there are 41 frames per turn. Outputs are in `outputs/multiturn/dominos/` (gitignored).

Turn-1 click prompts (top-left px):
```
{"white_ball":[[242,380]],"red_ball":[[358,372]],"domino1":[[424,365],[424,345]],"domino2":[[462,360],[462,340]],
 "domino3":[[500,355],[500,335]],"domino4":[[539,352],[539,332]],"domino_back":[[390,258]]}
```

**Turn 1:** both seeds succeed.
- Seed 0: white → red → the 4 front dominoes fall (`changed`). The back domino stays `as_initial`, with R-DINO 0.97. Both balls have R-DINO ≥ 0.94.
- Seed 1: also succeeds, with a different ending. The red ball bounces back into depth and more dominoes fall.

**Turn 2:** "push the white ball into the fallen dominoes".
- A: direct force on the white ball, angle 0°.
- B: goal force on fallen domino 2, angle 0°.

| | A (direct, white ball) | B (goal, domino 2) |
|---|---|---|
| Boundary jump, all visible objects | ≤ 0.24 px | ≤ 0.54 px |
| REVERT / RESET | none | none |
| Back domino (untouched) | `as_initial`, R-DINO 0.95 | `as_initial`, R-DINO 0.87 |
| Balls R-DINO, end of turn 2 | white 0.86, red 0.91 | white 0.93, red 0.94 |
| Fallen dominoes 2–4 | **VANISH** (visible 25/34/28 of 41) | **VANISH** (visible 20/26/21 of 41) |

What it shows:
- **State carries over at the cut.** Using the last frame as input gives near-zero jumps, nothing stands back up, and nothing resets. The baseline's failure is not at the boundary.
- **The failure is inside turn 2.** Around frames 16–24, the ~10 fallen dominoes **fuse into one plank** that gets pushed off frame. The VANISH flags are real: the objects are gone, which was checked visually and is not a tracking error. In B, one domino also flies up.
- The model treats the fallen pile as a single object, so **count and shape are not preserved**. This is exactly the per-object state that the memory should constrain.
- In B, Goal Force picked the white ball as the cause by itself, so goal mode can plan through the earlier causal chain.
- Motion discontinuity: in both runs the white ball goes from rest (0.005 px/frame) to about 7 px/frame. This is expected because turn 2 applies a new force.

## Results: bowling (corrected force point)
Turn 1 was re-run with the y-corrected force point (`logs/run_multiturn_bowling_turn1.sh`, seeds 0 and 1). It still fails:
- s0: the ball reverses toward the camera.
- s1: the pins explode, multiply and turn into balls.

The failure looks the same as before the fix, so the main cause is **motion into depth**, which is out of distribution for Goal Force. Multi-turn scenes should keep motion in the image plane. The dominoes scene is the main testbed.

## Next
- Per-object reference repair of the fused dominoes: an E2b-style VACE pass with per-domino masks and memory crops as references (appearance only, not pose).
- Run turn 2 from the seed-1 ending: same action, different world state.
- Run turn 3 / branch: go back to turn 1 and apply a different turn 2.
