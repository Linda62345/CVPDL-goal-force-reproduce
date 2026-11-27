# paper_review 影片的 prompt 與力（自動產生）

由 `multiturn/prompt_table.py` 從實際餵給 Goal Force 的 CSV 讀出。

- 角度：0° = 往右、90° = 往上、180° = 往左、270° = 往下。
- 座標：832×480，**y 以左下角為原點**（Goal Force CSV 的規定）。
- goal 模式：指定「目標物體要被往哪推、多大力」，並標出擊球者；direct 模式：直接推施力點上的物體。
- 影片位置：`outputs/multiturn/paper_review/<檔名>`。

## 1. 原論文設定兩回合（`paper_<場景>_s<seed>.mp4`）

第 1 回合 = 原論文 CSV（goal，力道 350）；第 2 回合 = 11/26 第一版設計（direct，力道 200）。

### 燈泡 — `paper_bulb_tool_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (185, 87) → 目標 (185, 87) | 0° | 350 | A hand pushes the hanging bulb, causing it to sway. |
| 2（推 bulb_right） | direct | (158, 75) | 180° | 200 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. |

### 哈密瓜 — `paper_cantaloupes_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 350 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 2（推 melon_right） | direct | (809, 126) | 180° | 200 | The cantaloupe rolls back to the left across the surface. The camera is static. |

### 哈密瓜 — `paper_cantaloupes_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 350 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 2（推 melon_right） | direct | (757, 183) | 180° | 200 | The cantaloupe rolls back to the left across the surface. The camera is static. |

### 西洋棋（狗） — `paper_paw_tool1_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (513, 201) → 目標 (513, 201) | 335° | 350 | A dog paw nudges a chess piece, causing it to slide across the board. |
| 2（推 dark_bishop） | direct | (256, 235) | 0° | 200 | A dark wooden chess piece slides to the right across the board. The camera is static. |

### 藍球（狗） — `paper_paw_tool2_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (536, 102) → 目標 (536, 102) | 135° | 350 | A dog nudges a ball with its paw, causing it to roll on the ground. |
| 2（推 ball） | direct | (117, 439) | 0° | 200 | The dog nudges the blue ball back to the right with its paw. The camera is static. |

### 紅球（貓） — `paper_paw_tool3_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (480, 214) → 目標 (482, 214) | 180° | 350 | A cat's paw nudges a ball, causing it to roll across the grass. |
| 2（推 ball） | direct | (170, 220) | 180° | 200 | The red ball rolls further to the left across the grass. The camera is static. |

### 鐘擺 — `paper_pendulum_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (368, 108) → 目標 (545, 114) | 0° | 350 | The pendulum swings, striking and toppling the red block. |
| 2（推 red_block） | direct | (750, 51) | 180° | 200 | The fallen red block slides to the left across the table. The camera is static. |

### 足球 — `paper_soccer_tool_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (477, 234) → 目標 (477, 236) | 180° | 350 | A soccer ball is kicked and rolls across the field. |
| 2（推 ball） | direct | (84, 274) | 90° | 200 | The soccer ball is kicked upward and rolls up the field. The camera is static. |

### 網球 — `paper_tennis_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (781, 336) → 目標 (469, 307) | 175° | 350 | A tennis ball rolls across the court, colliding with another ball. |
| 2（推 ball_bottom） | direct | (476, 101) | 0° | 200 | A tennis ball rolls to the right across the court. The camera is static. |

### 玩具車 — `paper_toycar_s0.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (660, 286) → 目標 (660, 286) | 225° | 350 | A hand reaches out to push the car across a map, and the car travels over various countries and regions. |
| 2（推 car） | direct | (129, 39) | 90° | 200 | The toy car drives upward across the map. The camera is static. |

## 2. 骨牌 11/25 版（`paper_ballthendominos_<第1回合seed>_<版本>_seed<第2回合seed>.mp4`）

第 1 回合都是原論文 CSV；A/B 各 3 個第 2 回合 seed（第 1 回合 s0、s1 各一套），C/D 只有 s0 + seed0。

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1（全部） | goal | 擊球者 (241, 104) → 目標 (356, 112) | 5° | 350 | One pool ball hits the other, which then hits the first domino, triggering a chain reaction |
| 2-A（s0） | direct | (328, 100) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-A（s1） | direct | (325, 127) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-B（s0） | goal | 擊球者 (509, 107) → 目標 (509, 107) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-B（s1） | goal | 擊球者 (503, 104) → 目標 (503, 104) | 0° | 350 | The white pool ball rolls to the right, hits the red ball, and pushes into the fallen dominoes. |
| 2-C（s0） | direct | (421, 112) | 180° | 200 | The red pool ball rolls back to the left and hits the white ball. |
| 2-D（s0） | direct | (391, 222) | 0° | 150 | A standing domino in the back row is pushed to the right and the dominoes next to it fall over one after another. |

B 的 CSV 只有目標（一塊倒下的骨牌）沒有擊球者，所以施力點欄顯示 (-1, -1) → 目標。

## 3. 兩回合互撞版（`t2b_<場景>_s1.mp4`；今晚的 `t2b_v2_<場景>_s0.mp4`）

seed 1：第 1 回合 = 原論文 CSV（力道 350）；第 2 回合 = 互撞／再推一次（direct）。
這些 `t2b_*` 並排影片會在今晚佇列最後的 review_videos 才產生；影片原檔已在 `outputs/multiturn/paper/<場景>/t2b_gf/`。

### 燈泡 — `t2b_bulb_tool_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (185, 87) → 目標 (185, 87) | 0° | 350 | A hand pushes the hanging bulb, causing it to sway. |
| 2（推 bulb_right） | direct | (264, 85) | 180° | 200 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. |

### 哈密瓜 — `t2b_cantaloupes_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 350 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 2（推 melon_right） | direct | (757, 183) | 181° | 150 | The cantaloupe rolls across the surface and bumps into the other cantaloupe. The camera is static. |

### 西洋棋（狗） — `t2b_paw_tool1_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (513, 201) → 目標 (513, 201) | 335° | 350 | A dog paw nudges a chess piece, causing it to slide across the board. |
| 2（推 dark_bishop） | direct | (256, 235) | 163° | 100 | A dark chess piece slides across the board and knocks into another chess piece. The camera is static. |

### 藍球（狗） — `t2b_paw_tool2_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (536, 102) → 目標 (536, 102) | 135° | 350 | A dog nudges a ball with its paw, causing it to roll on the ground. |
| 2（推 ball） | direct | (121, 458) | 324° | 100 | The dog nudges the blue ball again with its paw. The camera is static. |

### 紅球（貓） — `t2b_paw_tool3_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (480, 214) → 目標 (482, 214) | 180° | 350 | A cat's paw nudges a ball, causing it to roll across the grass. |
| 2（推 ball） | direct | (34, 207) | 5° | 100 | The cat's paw reaches out and nudges the red ball again. The camera is static. |

### 鐘擺 — `t2b_pendulum_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (368, 108) → 目標 (545, 114) | 0° | 350 | The pendulum swings, striking and toppling the red block. |
| 2（推 bob） | direct | (319, 114) | 350° | 150 | The pendulum swings again and hits the fallen red block. The camera is static. |

### 足球 — `t2b_soccer_tool_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (477, 234) → 目標 (477, 236) | 180° | 350 | A soccer ball is kicked and rolls across the field. |
| 2（推 ball） | direct | (25, 272) | 355° | 100 | The player's foot kicks the soccer ball again and it rolls across the field. The camera is static. |

### 網球 — `t2b_tennis_s1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | goal | 擊球者 (781, 336) → 目標 (469, 307) | 175° | 350 | A tennis ball rolls across the court, colliding with another ball. |
| 2（推 ball_bottom） | direct | (476, 101) | 33° | 120 | A tennis ball rolls across the court and hits another tennis ball. The camera is static. |

### 今晚 seed 0（v2：第 1 回合鏡頭固定、力道 150）

已產生的 CSV：

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| _cantaloupes_v2 | goal | 擊球者 (326, 175) → 目標 (594, 163) | 0° | 150 | A cantaloupe rolls across the surface, colliding with another cantaloupe. The camera is static. |
| cantaloupes_t2c_s0 | goal | 擊球者 (799, 125) → 目標 (519, 146) | 176° | 150 | A cantaloupe rolls back across the surface, colliding with the other cantaloupe and pushing it away. The camera is static. |
| _pendulum_v2 | goal | 擊球者 (368, 108) → 目標 (545, 114) | 0° | 150 | The pendulum swings, striking and toppling the red block. The camera is static. |
| pendulum_t2c_s0 | goal | 擊球者 (390, 109) → 目標 (743, 52) | 351° | 150 | The pendulum swings again, striking the fallen red block and pushing it across the table. The camera is static. |

尚未跑到的場景，第 2 回合依 `multiturn/paper_scenes.json` 的 turn2b 設定；`toward:` 的實際角度要等第 1 回合追蹤完才算得出來：

| 場景 | 第 1 回合 | 第 2 回合推誰 | 角度 | 力道 | 第 2 回合文字 prompt |
|---|---|---|---|---|---|
| 撞球 | 原論文 prompt + The camera is static.，goal 力道 150 | yellow_ball | toward:white_ball | 120 | The yellow pool ball rolls and hits the white ball. The camera is static. |
| 網球 | 原論文 prompt + The camera is static.，goal 力道 150 | ball_bottom | toward:nearest | 120 | A tennis ball rolls across the court and hits another tennis ball. The camera is static. |
| 高爾夫 | 原論文 prompt + The camera is static.，goal 力道 150 | yellow_ball | toward:white_ball | 120 | The yellow golf ball rolls and hits the white golf ball. The camera is static. |
| 哈密瓜 | 原論文 prompt + The camera is static.，goal 力道 150 | melon_right | toward:melon_left | 150 | The cantaloupe rolls across the surface and bumps into the other cantaloupe. The camera is static. |
| 鐘擺 | 原論文 prompt + The camera is static.，goal 力道 150 | bob | toward:red_block | 150 | The pendulum swings again and hits the fallen red block. The camera is static. |
| 西洋棋（狗） | 原論文 prompt + The camera is static.，goal 力道 150 | white_pawn_target | toward:nearest | 100 | The dog's paw nudges the chess piece again, and it slides into another chess piece. The camera is static. |
| 玩具車 | 原論文 prompt + The camera is static.，goal 力道 150 | car | toward:center | 100 | A hand reaches out and pushes the toy car again across the map. The camera is static. |
| 足球 | 原論文 prompt + The camera is static.，goal 力道 150 | ball | toward:center | 100 | The player's foot kicks the soccer ball again and it rolls across the field. The camera is static. |
| 藍球（狗） | 原論文 prompt + The camera is static.，goal 力道 150 | ball | toward:center | 100 | The dog nudges the blue ball again with its paw. The camera is static. |
| 紅球（貓） | 原論文 prompt + The camera is static.，goal 力道 150 | ball | toward:center | 100 | The cat's paw reaches out and nudges the red ball again. The camera is static. |
| 燈泡 | 原論文 prompt + The camera is static.，goal 力道 150 | bulb_right | 180 | 200 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. |
| 骨牌 | 原論文 prompt + The camera is static.，goal 力道 150 | domino_back | 0 | 100 | A standing domino in the back row is pushed to the right, and the dominoes next to it fall over one after another. The camera is static. |

## 4. 實驗 A：5 回合互撞（`chain_<場景>.mp4`）

### 哈密瓜 — `chain_cantaloupes.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | direct | (596, 160) | 177° | 150 | The cantaloupe on the right rolls to the left and bumps into the other cantaloupe. The camera is static. |
| 2 | direct | (19, 163) | 347° | 150 | The cantaloupe on the left rolls to the right and bumps into the other cantaloupe. The camera is static. |
| 3 | direct | (449, 73) | 174° | 150 | The cantaloupe on the right rolls to the left and bumps into the other cantaloupe. The camera is static. |
| 4 | direct | (94, 110) | 1° | 150 | The cantaloupe on the left rolls to the right and bumps into the other cantaloupe. The camera is static. |
| 5 | direct | (653, 79) | 181° | 150 | The cantaloupe on the right rolls to the left and bumps into the other cantaloupe. The camera is static. |

### 西洋棋（狗） — `chain_paw_tool1.mp4`

| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |
|---|---|---|---|---|---|
| 1 | direct | (258, 230) | 338° | 100 | A dark wooden chess piece slides across the board and knocks into a light wooden chess piece. The camera is static. |
| 2 | direct | (306, 81) | 169° | 100 | A light wooden pawn slides across the board and knocks into a dark chess piece. The camera is static. |
| 3 | direct | (207, 251) | 45° | 100 | A light wooden pawn slides across the board and knocks into a dark chess piece. The camera is static. |
| 4 | direct | (501, 120) | 68° | 100 | A light wooden chess piece slides across the board and knocks into another light piece. The camera is static. |
| 5 | direct | (408, 352) | 247° | 100 | A dark wooden chess piece slides across the board and knocks into a light wooden pawn. The camera is static. |
