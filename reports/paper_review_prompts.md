# 每支影片的 prompt 與力（自動產生）

由 `multiturn/prompt_table.py` 從實際餵給 Goal Force 的 CSV 讀出。影片總覽見 [`videos.md`](videos.md)；標題是 `reports/videos/` 裡的檔名（可點），後面小字是 `outputs/multiturn/paper_review/` 裡的原檔名。

- 角度：0° = 往右、90° = 往上、180° = 往左、270° = 往下。
- 座標：832×480，**y 以左下角為原點**（Goal Force CSV 的規定）。
- goal 模式：指定「目標物體要被往哪推、多大力」，並標出造成動作的物體（擊球者）；擊球者 = 目標時代表施力者在畫面外（手、爪子），和論文一樣。direct 模式：直接推施力點上的物體。

## A. 實驗 A：5 回合互撞

### 哈密瓜 — [`A_5turns_cantaloupes.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/A_5turns_cantaloupes.mp4?raw=true)　<sub>原檔 `chain_cantaloupes.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | direct | (596, 160) | 177° | 150 | The cantaloupe on the right rolls to the left and bumps into the other cantaloupe. The camera is static. |
| 2 | direct | (19, 163) | 347° | 150 | The cantaloupe on the left rolls to the right and bumps into the other cantaloupe. The camera is static. |
| 3 | direct | (449, 73) | 174° | 150 | The cantaloupe on the right rolls to the left and bumps into the other cantaloupe. The camera is static. |
| 4 | direct | (94, 110) | 1° | 150 | The cantaloupe on the left rolls to the right and bumps into the other cantaloupe. The camera is static. |
| 5 | direct | (653, 79) | 181° | 150 | The cantaloupe on the right rolls to the left and bumps into the other cantaloupe. The camera is static. |

### 西洋棋（狗） — [`A_5turns_chess_dogpaw.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/A_5turns_chess_dogpaw.mp4?raw=true)　<sub>原檔 `chain_paw_tool1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | direct | (258, 230) | 338° | 100 | A dark wooden chess piece slides across the board and knocks into a light wooden chess piece. The camera is static. |
| 2 | direct | (306, 81) | 169° | 100 | A light wooden pawn slides across the board and knocks into a dark chess piece. The camera is static. |
| 3 | direct | (207, 251) | 45° | 100 | A light wooden pawn slides across the board and knocks into a dark chess piece. The camera is static. |
| 4 | direct | (501, 120) | 68° | 100 | A light wooden chess piece slides across the board and knocks into another light piece. The camera is static. |
| 5 | direct | (408, 352) | 247° | 100 | A dark wooden chess piece slides across the board and knocks into a light wooden pawn. The camera is static. |

## B. 新版兩回合：照論文的因果寫法（turn2c）

第 1 回合 = 原論文 CSV + 「The camera is static.」，goal 力道 150；第 2 回合 = goal 模式，文字寫明原因。

### 哈密瓜 — [`B_2turns_causal_lowforce_cantaloupes_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/B_2turns_causal_lowforce_cantaloupes_seed0.mp4?raw=true)　<sub>原檔 `t2c_v2_cantaloupes_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 150 | A cantaloupe rolls across the surface, colliding with another cantaloupe. The camera is static. |
| 2（melon_right → melon_left） | goal | 擊球者 (799, 125) → 目標 (519, 146) | 176° | 150 | A cantaloupe rolls back across the surface, colliding with the other cantaloupe and pushing it away. The camera is static. |

### 西洋棋（狗） — `B_2turns_causal_lowforce_chess_dogpaw_seed0.mp4`（尚未產生）　<sub>原檔 `t2c_v2_paw_tool1_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (513, 201) → 目標 (513, 201) | 335° | 150 | A dog paw nudges a chess piece, causing it to slide across the board. The camera is static. |
| 2（white_pawn_target → white_bishop） | goal | 擊球者 (826, 25) → 目標 (479, 143) | 161° | 100 | The dog's paw nudges the chess piece again, and it slides into another chess piece, knocking it over. The camera is static. |

### 鐘擺 — [`B_2turns_causal_lowforce_pendulum_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/B_2turns_causal_lowforce_pendulum_seed0.mp4?raw=true)　<sub>原檔 `t2c_v2_pendulum_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (368, 108) → 目標 (545, 114) | 0° | 150 | The pendulum swings, striking and toppling the red block. The camera is static. |
| 2（bob → red_block） | goal | 擊球者 (390, 109) → 目標 (743, 52) | 351° | 150 | The pendulum swings again, striking the fallen red block and pushing it across the table. The camera is static. |

還沒跑到的場景（設定見 `multiturn/paper_scenes.json` 的 turn2c；`away` = 從造成者指向被推物體的方向，實際角度要等第 1 回合追蹤完才算得出來）：

| 場景 | 誰造成 → 誰被推 | 角度 | 力道 | 第 2 回合文字 prompt |
|---|---|---|---|---|
| 撞球 | yellow_ball → white_ball | away | 120 | A cue stick strikes the yellow pool ball, which rolls and hits the white ball. The camera is static. |
| 網球 | ball_bottom → nearest | away | 120 | A tennis ball rolls across the court, colliding with another ball. The camera is static. |
| 高爾夫 | yellow_ball → white_ball | away | 120 | A golf club hits the yellow golf ball, which rolls into the white golf ball. The camera is static. |
| 玩具車 | car → car | toward:center | 100 | A hand reaches out and pushes the toy car again, and the car travels across the map. The camera is static. |
| 足球 | ball → ball | toward:center | 100 | The player's foot kicks the soccer ball again, and it rolls across the field. The camera is static. |
| 藍球（狗） | ball → ball | toward:center | 100 | A dog nudges the blue ball again with its paw, causing it to roll on the ground. The camera is static. |
| 紅球（貓） | ball → ball | toward:center | 100 | A cat's paw reaches out and nudges the red ball again, causing it to roll across the grass. The camera is static. |
| 燈泡 | bulb_right → bulb_left | away | 200 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. |
| 骨牌 | domino_back → domino_back | 0 | 100 | A hand pushes a standing domino in the back row, and the dominoes next to it fall over one after another. The camera is static. |

## C. 互撞版兩回合（turn2b，direct 模式）

第 1 回合 = 原論文 CSV（力道 350）；第 2 回合 = 直接推物體去撞另一個（或再推一次）。

### 燈泡 — [`C_2turns_directpush_bulbs_hand_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_bulbs_hand_seed1.mp4?raw=true)　<sub>原檔 `t2b_bulb_tool_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (185, 87) → 目標 (185, 87) | 0° | 350 | A hand pushes the hanging bulb, causing it to sway. |
| 2（推 bulb_right） | direct | (264, 85) | 180° | 200 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. |

### 哈密瓜 — [`C_2turns_directpush_cantaloupes_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_cantaloupes_seed1.mp4?raw=true)　<sub>原檔 `t2b_cantaloupes_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 350 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 2（推 melon_right） | direct | (757, 183) | 181° | 150 | The cantaloupe rolls across the surface and bumps into the other cantaloupe. The camera is static. |

### 西洋棋（狗） — [`C_2turns_directpush_chess_dogpaw_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_chess_dogpaw_seed1.mp4?raw=true)　<sub>原檔 `t2b_paw_tool1_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (513, 201) → 目標 (513, 201) | 335° | 350 | A dog paw nudges a chess piece, causing it to slide across the board. |
| 2（推 dark_bishop） | direct | (256, 235) | 163° | 100 | A dark chess piece slides across the board and knocks into another chess piece. The camera is static. |

### 藍球（狗） — [`C_2turns_directpush_ball_dogpaw_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_ball_dogpaw_seed1.mp4?raw=true)　<sub>原檔 `t2b_paw_tool2_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (536, 102) → 目標 (536, 102) | 135° | 350 | A dog nudges a ball with its paw, causing it to roll on the ground. |
| 2（推 ball） | direct | (121, 458) | 324° | 100 | The dog nudges the blue ball again with its paw. The camera is static. |

### 紅球（貓） — [`C_2turns_directpush_ball_catpaw_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_ball_catpaw_seed1.mp4?raw=true)　<sub>原檔 `t2b_paw_tool3_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (480, 214) → 目標 (482, 214) | 180° | 350 | A cat's paw nudges a ball, causing it to roll across the grass. |
| 2（推 ball） | direct | (34, 207) | 5° | 100 | The cat's paw reaches out and nudges the red ball again. The camera is static. |

### 鐘擺 — [`C_2turns_directpush_pendulum_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_pendulum_seed1.mp4?raw=true)　<sub>原檔 `t2b_pendulum_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (368, 108) → 目標 (545, 114) | 0° | 350 | The pendulum swings, striking and toppling the red block. |
| 2（推 bob） | direct | (319, 114) | 350° | 150 | The pendulum swings again and hits the fallen red block. The camera is static. |

### 足球 — [`C_2turns_directpush_soccer_kick_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_soccer_kick_seed1.mp4?raw=true)　<sub>原檔 `t2b_soccer_tool_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (477, 234) → 目標 (477, 236) | 180° | 350 | A soccer ball is kicked and rolls across the field. |
| 2（推 ball） | direct | (25, 272) | 355° | 100 | The player's foot kicks the soccer ball again and it rolls across the field. The camera is static. |

### 網球 — [`C_2turns_directpush_tennis_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/C_2turns_directpush_tennis_seed1.mp4?raw=true)　<sub>原檔 `t2b_tennis_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (781, 336) → 目標 (469, 307) | 175° | 350 | A tennis ball rolls across the court, colliding with another ball. |
| 2（推 ball_bottom） | direct | (476, 101) | 33° | 120 | A tennis ball rolls across the court and hits another tennis ball. The camera is static. |

## D. 第一版兩回合（turn2，11/26）

第 1 回合 = 原論文 CSV（goal，力道 350）；第 2 回合 = direct，力道 200。

### 燈泡 — [`D_2turns_firstdesign_bulbs_hand_seed0_INVALID.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_bulbs_hand_seed0_INVALID.mp4?raw=true)　<sub>原檔 `paper_bulb_tool_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (185, 87) → 目標 (185, 87) | 0° | 350 | A hand pushes the hanging bulb, causing it to sway. |
| 2（推 bulb_right） | direct | (158, 75) | 180° | 200 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. |

### 哈密瓜 — [`D_2turns_firstdesign_cantaloupes_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_cantaloupes_seed0.mp4?raw=true)　<sub>原檔 `paper_cantaloupes_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 350 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 2（推 melon_right） | direct | (809, 126) | 180° | 200 | The cantaloupe rolls back to the left across the surface. The camera is static. |

### 哈密瓜 — [`D_2turns_firstdesign_cantaloupes_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_cantaloupes_seed1.mp4?raw=true)　<sub>原檔 `paper_cantaloupes_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 350 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 2（推 melon_right） | direct | (757, 183) | 180° | 200 | The cantaloupe rolls back to the left across the surface. The camera is static. |

### 西洋棋（狗） — [`D_2turns_firstdesign_chess_dogpaw_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_chess_dogpaw_seed0.mp4?raw=true)　<sub>原檔 `paper_paw_tool1_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (513, 201) → 目標 (513, 201) | 335° | 350 | A dog paw nudges a chess piece, causing it to slide across the board. |
| 2（推 dark_bishop） | direct | (256, 235) | 0° | 200 | A dark wooden chess piece slides to the right across the board. The camera is static. |

### 藍球（狗） — [`D_2turns_firstdesign_ball_dogpaw_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_ball_dogpaw_seed0.mp4?raw=true)　<sub>原檔 `paper_paw_tool2_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (536, 102) → 目標 (536, 102) | 135° | 350 | A dog nudges a ball with its paw, causing it to roll on the ground. |
| 2（推 ball） | direct | (117, 439) | 0° | 200 | The dog nudges the blue ball back to the right with its paw. The camera is static. |

### 紅球（貓） — [`D_2turns_firstdesign_ball_catpaw_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_ball_catpaw_seed0.mp4?raw=true)　<sub>原檔 `paper_paw_tool3_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (480, 214) → 目標 (482, 214) | 180° | 350 | A cat's paw nudges a ball, causing it to roll across the grass. |
| 2（推 ball） | direct | (170, 220) | 180° | 200 | The red ball rolls further to the left across the grass. The camera is static. |

### 鐘擺 — [`D_2turns_firstdesign_pendulum_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_pendulum_seed0.mp4?raw=true)　<sub>原檔 `paper_pendulum_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (368, 108) → 目標 (545, 114) | 0° | 350 | The pendulum swings, striking and toppling the red block. |
| 2（推 red_block） | direct | (750, 51) | 180° | 200 | The fallen red block slides to the left across the table. The camera is static. |

### 足球 — [`D_2turns_firstdesign_soccer_kick_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_soccer_kick_seed0.mp4?raw=true)　<sub>原檔 `paper_soccer_tool_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (477, 234) → 目標 (477, 236) | 180° | 350 | A soccer ball is kicked and rolls across the field. |
| 2（推 ball） | direct | (84, 274) | 90° | 200 | The soccer ball is kicked upward and rolls up the field. The camera is static. |

### 網球 — [`D_2turns_firstdesign_tennis_seed1.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_tennis_seed1.mp4?raw=true)　<sub>原檔 `paper_tennis_s1.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (781, 336) → 目標 (469, 307) | 175° | 350 | A tennis ball rolls across the court, colliding with another ball. |
| 2（推 ball_bottom） | direct | (476, 101) | 0° | 200 | A tennis ball rolls to the right across the court. The camera is static. |

### 玩具車 — [`D_2turns_firstdesign_toycar_hand_seed0.mp4`](https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/D_2turns_firstdesign_toycar_hand_seed0.mp4?raw=true)　<sub>原檔 `paper_toycar_s0.mp4`</sub>

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (660, 286) → 目標 (660, 286) | 225° | 350 | A hand reaches out to push the car across a map, and the car travels over various countries and regions. |
| 2（推 car） | direct | (129, 39) | 90° | 200 | The toy car drives upward across the map. The camera is static. |

## E. 骨牌 11/25 版（`E_dominoes_1125_t1seed<a>_<版本>_t2seed<b>.mp4`）

第 1 回合都是原論文 CSV；A/B 各 3 個第 2 回合 seed（第 1 回合 seed 0、1 各一套），C/D 只有第 1 回合 seed 0 + 第 2 回合 seed 0。

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1（全部） | goal | 擊球者 (241, 104) → 目標 (356, 112) | 5° | 350 | One pool ball hits the other, which then hits the first domino, triggering a chain reaction |
| 2-A（t1seed0） | direct | (328, 100) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-A（t1seed1） | direct | (325, 127) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-B（t1seed0） | goal | 擊球者 (509, 107) → 目標 (509, 107) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-B（t1seed1） | goal | 擊球者 (503, 104) → 目標 (503, 104) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-C（t1seed0） | direct | (421, 112) | 180° | 200 | The red pool ball rolls back to the left and hits the white ball. |
| 2-D（t1seed0） | direct | (391, 222) | 0° | 150 | A standing domino in the back row is pushed to the right and the dominoes next to it fall over one after another. |

B 的 CSV 只有目標（一塊倒下的骨牌）沒有擊球者，所以施力點欄顯示 (-1, -1) → 目標。
