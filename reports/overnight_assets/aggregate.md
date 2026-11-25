## Per scene x method
| scene | method | n videos | state kept ↑ | start IoU ↑ | R-DINO vs original ↑ | R-DINO vs latest ↑ | turn-2 success | vanished | fused | reverted |
|---|---|---|---|---|---|---|---|---|---|---|
| books_pull | baseline | 1 | 0.67 | 0.95 | 0.55 | 0.77 | 1/1 | 1 | 0 | 0 |
| books_pull | appearance | 1 | 0.67 | 0.95 | 0.38 | 0.52 | 1/1 | 1 | 0 | 0 |
| books_pull | full | 1 | 0.67 | 0.95 | 0.48 | 0.65 | 1/1 | 1 | 0 | 0 |
| books_push | baseline | 1 | 0.60 | 0.86 | 0.50 | 0.60 | 1/1 | 0 | 2 | 0 |
| books_push | appearance | 1 | 0.20 | 0.87 | - | - | 1/1 | 1 | 4 | 0 |
| books_push | full | 1 | 0.60 | 0.87 | 0.30 | 0.48 | 1/1 | 0 | 2 | 0 |
| bottle | baseline | 1 | 0.00 | 0.93 | 0.34 | 0.42 | 1/1 | 0 | 1 | 0 |
| bottle | appearance | 1 | 0.00 | 0.92 | 0.32 | 0.43 | 1/1 | 0 | 1 | 0 |
| bottle | full | 1 | 0.00 | 0.99 | 0.45 | 0.59 | 1/1 | 0 | 1 | 0 |
| chips | baseline | 3 | 1.00 | 0.97 | 0.86 | 0.86 | 3/3 | 0 | 0 | 0 |
| chips | appearance | 3 | 1.00 | 0.99 | 0.76 | 0.73 | 3/3 | 0 | 0 | 0 |
| chips | full | 3 | 1.00 | 0.99 | 0.86 | 0.86 | 3/3 | 0 | 0 | 0 |
| chips_noforce | baseline | 3 | 1.00 | 0.99 | 0.86 | 0.98 | 3/3 | 0 | 0 | 0 |
| chips_noforce | appearance | 3 | 1.00 | 0.99 | 0.87 | 0.98 | 3/3 | 0 | 0 | 0 |
| chips_noforce | full | 3 | 1.00 | 0.99 | 0.84 | 0.96 | 3/3 | 0 | 0 | 0 |
| chips_noforce | appearance_global | 3 | 1.00 | 0.99 | 0.85 | 0.97 | 3/3 | 0 | 0 | 0 |
| coffee | baseline | 1 | 1.00 | 0.94 | 0.62 | 0.71 | 1/1 | 0 | 0 | 0 |
| coffee | appearance | 1 | 0.50 | 0.94 | 0.69 | 0.69 | 1/1 | 0 | 1 | 0 |
| coffee | full | 1 | 1.00 | 0.94 | 0.35 | 0.35 | 1/1 | 0 | 0 | 0 |
| dominos | baseline | 12 | 0.73 | 0.90 | 0.59 | 0.71 | 10/12 | 2 | 22 | 3 |
| dominos | appearance | 12 | 0.58 | 0.89 | 0.47 | 0.57 | 10/12 | 10 | 27 | 1 |
| dominos | full | 12 | 0.77 | 0.90 | 0.46 | 0.57 | 10/12 | 2 | 17 | 3 |
| dominos_branch | baseline | 2 | 1.00 | 0.94 | 0.53 | 0.86 | 2/2 | 0 | 0 | 0 |
| dominos_branch | appearance | 2 | 1.00 | 0.94 | 0.46 | 0.76 | 2/2 | 0 | 0 | 0 |
| dominos_branch | full | 2 | 0.86 | 0.94 | 0.45 | 0.66 | 2/2 | 0 | 0 | 2 |

## All scenes pooled
| scene | method | n videos | state kept ↑ | start IoU ↑ | R-DINO vs original ↑ | R-DINO vs latest ↑ | turn-2 success | vanished | fused | reverted |
|---|---|---|---|---|---|---|---|---|---|---|
| all | baseline | 24 | 0.79 | 0.93 | 0.64 | 0.76 | 22/24 | 3 | 25 | 3 |
| all | appearance | 24 | 0.68 | 0.93 | 0.56 | 0.66 | 22/24 | 12 | 33 | 1 |
| all | full | 24 | 0.80 | 0.93 | 0.54 | 0.66 | 22/24 | 3 | 20 | 5 |
| all | appearance_global | 3 | 1.00 | 0.99 | 0.85 | 0.97 | 3/3 | 0 | 0 | 0 |

## Failure taxonomy (labels can overlap)
| method | n videos | appearance deformed | state lost (vanished/fused) | state reverted | action failed | no failure |
|---|---|---|---|---|---|---|
| baseline | 24 | 15 | 10 | 2 | 2 | 8 |
| appearance | 24 | 15 | 15 | 1 | 2 | 7 |
| full | 24 | 15 | 8 | 5 | 2 | 6 |
| appearance_global | 3 | 0 | 0 | 0 | 0 | 3 |

## Per video
| exp | scene | method | run | state kept | R-DINO orig | R-DINO latest | success | labels |
|---|---|---|---|---|---|---|---|---|
| ph_books_pull | books_pull | baseline | books_pull_t2_seed0 | 0.67 | 0.55 | 0.77 | ✔ | state_lost |
| ph_books_pull | books_pull | appearance | books_pull_t2_seed0 | 0.67 | 0.38 | 0.52 | ✔ | appearance_deformed, state_lost |
| ph_books_pull | books_pull | full | books_pull_t2_seed0 | 0.67 | 0.48 | 0.65 | ✔ | state_lost |
| ph_books_push | books_push | baseline | books_push_t2_seed0 | 0.60 | 0.50 | 0.60 | ✔ | appearance_deformed, state_lost |
| ph_books_push | books_push | appearance | books_push_t2_seed0 | 0.20 | - | - | ✔ | state_lost |
| ph_books_push | books_push | full | books_push_t2_seed0 | 0.60 | 0.30 | 0.48 | ✔ | appearance_deformed, state_lost |
| ph_bottle | bottle | baseline | bottle_t2_seed0 | 0.00 | 0.34 | 0.42 | ✔ | appearance_deformed, state_lost |
| ph_bottle | bottle | appearance | bottle_t2_seed0 | 0.00 | 0.32 | 0.43 | ✔ | appearance_deformed, state_lost |
| ph_bottle | bottle | full | bottle_t2_seed0 | 0.00 | 0.45 | 0.59 | ✔ | state_lost |
| ph_chips | chips | baseline | chips_t2_seed0 | 1.00 | 0.87 | 0.88 | ✔ | - |
| ph_chips | chips | appearance | chips_t2_seed0 | 1.00 | 0.91 | 0.85 | ✔ | - |
| ph_chips | chips | full | chips_t2_seed0 | 1.00 | 0.87 | 0.89 | ✔ | - |
| ph_chips | chips | baseline | chips_t2_seed1 | 1.00 | 0.87 | 0.86 | ✔ | - |
| ph_chips | chips | appearance | chips_t2_seed1 | 1.00 | 0.68 | 0.66 | ✔ | - |
| ph_chips | chips | full | chips_t2_seed1 | 1.00 | 0.86 | 0.86 | ✔ | - |
| ph_chips | chips | baseline | chips_t2_seed2 | 1.00 | 0.84 | 0.84 | ✔ | - |
| ph_chips | chips | appearance | chips_t2_seed2 | 1.00 | 0.68 | 0.66 | ✔ | - |
| ph_chips | chips | full | chips_t2_seed2 | 1.00 | 0.84 | 0.85 | ✔ | - |
| ph_chips_noforce | chips_noforce | baseline | chips_t2_seed0 | 1.00 | 0.87 | 0.98 | ✔ | - |
| ph_chips_noforce | chips_noforce | appearance | chips_t2_seed0 | 1.00 | 0.87 | 0.97 | ✔ | - |
| ph_chips_noforce | chips_noforce | full | chips_t2_seed0 | 1.00 | 0.83 | 0.96 | ✔ | - |
| ph_chips_noforce | chips_noforce | appearance_global | chips_t2_seed0 | 1.00 | 0.86 | 0.97 | ✔ | - |
| ph_chips_noforce | chips_noforce | baseline | chips_t2_seed1 | 1.00 | 0.85 | 0.97 | ✔ | - |
| ph_chips_noforce | chips_noforce | appearance | chips_t2_seed1 | 1.00 | 0.88 | 0.98 | ✔ | - |
| ph_chips_noforce | chips_noforce | full | chips_t2_seed1 | 1.00 | 0.85 | 0.96 | ✔ | - |
| ph_chips_noforce | chips_noforce | appearance_global | chips_t2_seed1 | 1.00 | 0.86 | 0.97 | ✔ | - |
| ph_chips_noforce | chips_noforce | baseline | chips_t2_seed2 | 1.00 | 0.86 | 0.99 | ✔ | - |
| ph_chips_noforce | chips_noforce | appearance | chips_t2_seed2 | 1.00 | 0.87 | 0.98 | ✔ | - |
| ph_chips_noforce | chips_noforce | full | chips_t2_seed2 | 1.00 | 0.84 | 0.97 | ✔ | - |
| ph_chips_noforce | chips_noforce | appearance_global | chips_t2_seed2 | 1.00 | 0.84 | 0.97 | ✔ | - |
| ph_coffee | coffee | baseline | coffee_t2_seed0 | 1.00 | 0.62 | 0.71 | ✔ | - |
| ph_coffee | coffee | appearance | coffee_t2_seed0 | 0.50 | 0.69 | 0.69 | ✔ | state_lost |
| ph_coffee | coffee | full | coffee_t2_seed0 | 1.00 | 0.35 | 0.35 | ✔ | appearance_deformed |
| exp8 | dominos | baseline | s0_A_seed0 | 0.43 | 0.75 | 0.79 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | appearance | s0_A_seed0 | 0.57 | 0.54 | 0.57 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s0_A_seed0 | 0.43 | 0.43 | 0.48 | ✔ | appearance_deformed, state_lost, state_reverted |
| exp8 | dominos | baseline | s0_A_seed1 | 0.43 | 0.64 | 0.70 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | appearance | s0_A_seed1 | 0.43 | 0.61 | 0.65 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s0_A_seed1 | 0.43 | 0.53 | 0.56 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | baseline | s0_A_seed2 | 1.00 | 0.56 | 0.71 | ✔ | appearance_deformed |
| exp8 | dominos | appearance | s0_A_seed2 | 0.71 | 0.44 | 0.62 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s0_A_seed2 | 0.86 | 0.47 | 0.61 | ✔ | appearance_deformed, state_reverted |
| exp8 | dominos | baseline | s0_B_seed0 | 0.57 | 0.79 | 0.81 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | appearance | s0_B_seed0 | 0.43 | 0.47 | 0.52 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s0_B_seed0 | 0.43 | 0.45 | 0.50 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | baseline | s0_B_seed1 | 0.57 | 0.54 | 0.59 | ✘ | appearance_deformed, state_lost, state_reverted, action_failed |
| exp8 | dominos | appearance | s0_B_seed1 | 0.14 | 0.38 | 0.43 | ✔ | appearance_deformed, state_lost, state_reverted |
| exp8 | dominos | full | s0_B_seed1 | 0.86 | 0.44 | 0.52 | ✘ | appearance_deformed, state_reverted, action_failed |
| exp8 | dominos | baseline | s0_B_seed2 | 0.43 | 0.50 | 0.58 | ✘ | appearance_deformed, state_lost, action_failed |
| exp8 | dominos | appearance | s0_B_seed2 | 0.14 | 0.49 | 0.60 | ✘ | appearance_deformed, state_lost, action_failed |
| exp8 | dominos | full | s0_B_seed2 | 0.57 | 0.43 | 0.55 | ✘ | appearance_deformed, state_lost, action_failed |
| exp8 | dominos | baseline | s1_A_seed0 | 1.00 | 0.55 | 0.69 | ✔ | appearance_deformed |
| exp8 | dominos | appearance | s1_A_seed0 | 0.71 | 0.61 | 0.62 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s1_A_seed0 | 1.00 | 0.45 | 0.57 | ✔ | appearance_deformed |
| exp8 | dominos | baseline | s1_A_seed1 | 1.00 | 0.53 | 0.76 | ✔ | appearance_deformed |
| exp8 | dominos | appearance | s1_A_seed1 | 0.86 | 0.41 | 0.62 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s1_A_seed1 | 1.00 | 0.44 | 0.61 | ✔ | appearance_deformed |
| exp8 | dominos | baseline | s1_A_seed2 | 1.00 | 0.56 | 0.72 | ✔ | appearance_deformed |
| exp8 | dominos | appearance | s1_A_seed2 | 0.86 | 0.41 | 0.57 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s1_A_seed2 | 1.00 | 0.47 | 0.65 | ✔ | appearance_deformed |
| exp8 | dominos | baseline | s1_B_seed0 | 0.57 | 0.50 | 0.66 | ✔ | appearance_deformed, state_lost, state_reverted |
| exp8 | dominos | appearance | s1_B_seed0 | 0.57 | 0.44 | 0.48 | ✘ | appearance_deformed, state_lost, action_failed |
| exp8 | dominos | full | s1_B_seed0 | 1.00 | 0.46 | 0.58 | ✔ | appearance_deformed |
| exp8 | dominos | baseline | s1_B_seed1 | 0.71 | 0.61 | 0.79 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | appearance | s1_B_seed1 | 0.57 | 0.39 | 0.55 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | full | s1_B_seed1 | 0.71 | 0.43 | 0.58 | ✔ | appearance_deformed, state_lost |
| exp8 | dominos | baseline | s1_B_seed2 | 1.00 | 0.59 | 0.75 | ✔ | appearance_deformed |
| exp8 | dominos | appearance | s1_B_seed2 | 1.00 | 0.46 | 0.62 | ✔ | appearance_deformed |
| exp8 | dominos | full | s1_B_seed2 | 1.00 | 0.47 | 0.66 | ✔ | appearance_deformed |
| exp10 | dominos_branch | baseline | s0_C_seed0 | 1.00 | 0.56 | 0.89 | ✔ | - |
| exp10 | dominos_branch | appearance | s0_C_seed0 | 1.00 | 0.45 | 0.75 | ✔ | - |
| exp10 | dominos_branch | full | s0_C_seed0 | 0.86 | 0.46 | 0.70 | ✔ | state_reverted |
| exp10 | dominos_branch | baseline | s0_D_seed0 | 1.00 | 0.50 | 0.84 | ✔ | appearance_deformed |
| exp10 | dominos_branch | appearance | s0_D_seed0 | 1.00 | 0.47 | 0.76 | ✔ | appearance_deformed |
| exp10 | dominos_branch | full | s0_D_seed0 | 0.86 | 0.43 | 0.63 | ✔ | appearance_deformed, state_reverted |
