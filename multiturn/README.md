# 多回合 Goal Force：物件狀態記憶工具

題目：延伸 Goal Force，以物件狀態記憶改善多回合互動影片的連續性。

**Baseline：** 下一回合的輸入圖是上一回合的最後一格，Goal Force 用新的施力重新生成。

## 流程
```
第 k 回合影片 ──► extract_state.py ──► state.json（逐物件狀態）＋ memory/（第 1 回合的外觀，一路沿用）
                                          │                               last_frame.png
                                          ▼
                           make_next_turn.py ──► datasets/multiturn/<場景>/<名稱>.csv + images/ + _preview.png
                                          │
                                          ▼
                   scripts/inference/inference_goal_force.py ──► 第 k+1 回合影片 ──► extract_state.py --prev_state ...
                                                                                   │
                                              eval_continuity.py（所有 state.json）◄┘
```

| 程式 | 環境 | 功能 |
|---|---|---|
| `extract_state.py` | `imagegen/venv` | 多物件 SAM2 追蹤。第 1 回合用點選位置（`--prompts`）；之後的回合用上一回合最後一格的 mask 重新提示（`--prev_state`）。儲存外觀記憶（第 1 回合的裁切、mask、狀態），以及每個物件第一格和最後一格的狀態（中心、bbox、主軸角度、粗略姿勢）、軌跡、逐格和記憶比較的 R-DINO、`last_frame.png` 和 `state_overlay.png` |
| `make_next_turn.py` | `venv` | 產生下一回合的輸入圖和 CSV。施力點是目標物件的追蹤中心，**已換算成 Goal Force 以左下角為原點的 y 座標**。也會輸出畫好箭頭的 `_preview.png`，在跑 22 分鐘之前先確認施力點 |
| `eval_continuity.py` | `imagegen/venv` | 舊版評估。每回合：姿勢、和記憶比較的 R-DINO、面積比。每次換回合時標記：**JUMP**（狀態沒接上）、**REVERT**（倒下的物件重新立起）、**RESET**（物件漂回第 1 回合的位置）、**VANISH**，以及換回合處的速度（第 k 回合結尾 vs 第 k+1 回合開頭） |
| `evaluate.py` | `imagegen/venv` | 新版統一評估（定義見 `metrics.md`），之後所有實驗都用這個 |
| `memory_repair.py` | `venv` | 記憶修補：`appearance`（只有外觀記憶）和 `full`（完整方法），設計見 `memory_plan.md` |
| `aggregate.py`、`camera_check.py`、`compare3.py` | `imagegen/venv` | 彙總表格與散佈圖、扣除鏡頭運動的成功判定、並排對照圖 |
| `common.py` | — | SAM2 追蹤、逐 mask 狀態、姿勢標籤、DINO |

除了 `make_next_turn.py` 寫出的 CSV，所有座標都以左上角為原點的像素表示。

**姿勢標籤：** 只對骨牌、保齡球瓶、積木這類細長物件有意義。和第 1 回合第 0 格相比，主軸轉動超過 35° 或長寬比變化超過 1.65 倍，就標成 `changed`；圓形物件標成 `n/a`。

## 自我測試（`outputs/multiturn/_selftest`）
第 1 回合用 pilot 的 `bowling_forward_s0`。代替「第 2 回合」的是 `bowling_forward_s2`，它從原圖重新開始，所以工具應該要報告不連續。兩者都用 stride 4。
- 球被標成 **JUMP**（15.7 px）。
- 換回合處球的速度從 2.83 降到 0.06 px/格。
- 被撞倒的瓶子標成 `changed`。
- CSV 的 y 已正確換算（左上角座標 213 → 267）。

## 結果：骨牌（官方 `_ballthendominos_obj1_prompt1`），2026-11-24
第 1 回合用官方 CSV（在紅球上設目標），seed 0 和 1。第 2 回合從第 1 回合 seed 0 的最後一格出發，用 seed 0。輸入檔在 `datasets/multiturn/dominos/`，執行腳本是 `logs/run_multiturn_dominos_turn2.sh`。追蹤用 stride 2，每回合 41 格。輸出在 `outputs/multiturn/dominos/`（不進 git）。

第 1 回合的點選位置（左上角座標）：
```
{"white_ball":[[242,380]],"red_ball":[[358,372]],"domino1":[[424,365],[424,345]],"domino2":[[462,360],[462,340]],
 "domino3":[[500,355],[500,335]],"domino4":[[539,352],[539,332]],"domino_back":[[390,258]]}
```

**第 1 回合：** 兩個 seed 都成功。
- seed 0：白球 → 紅球 → 前排 4 支骨牌倒下（`changed`）。後排骨牌維持 `as_initial`，R-DINO 0.97。兩顆球的 R-DINO 都 ≥ 0.94。
- seed 1：也成功，但結局不同：紅球往畫面深處反彈，倒下的骨牌更多。

**第 2 回合：** 「推白球去撞倒下的骨牌」。
- A：對白球直接施力，0°。
- B：在倒下的骨牌 2 設目標，0°。

| | A（直接施力，白球） | B（目標，骨牌 2） |
|---|---|---|
| 換回合跳動，所有可見物件 | ≤ 0.24 px | ≤ 0.54 px |
| REVERT／RESET | 無 | 無 |
| 後排骨牌（沒被碰到） | `as_initial`，R-DINO 0.95 | `as_initial`，R-DINO 0.87 |
| 第 2 回合結束時兩顆球的 R-DINO | 白 0.86，紅 0.91 | 白 0.93，紅 0.94 |
| 倒下的骨牌 2–4 | **VANISH**（41 格中可見 25/34/28 格） | **VANISH**（可見 20/26/21 格） |

代表的意義：
- **換回合時狀態有接上。** 用最後一格當輸入，跳動幾乎是零，沒有東西重新立起，也沒有東西回到原位。baseline 的問題不在換回合處。
- **問題出在第 2 回合裡面。** 大約第 16–24 格，約 10 支倒下的骨牌**融成一塊長板**，被推出畫面。VANISH 是真的：我逐格看過，物件確實不見了，不是追蹤失誤。B 裡還有一支骨牌飛起來。
- 模型把倒下的骨牌堆當成一個物件，所以**數量和形狀都沒保住**。這正是記憶應該約束的逐物件狀態。
- 在 B 裡，Goal Force 自己選了白球當起因，表示目標模式能往前推出因果鏈。
- 動作不連續：兩支影片的白球都從靜止（0.005 px/格）突然變成約 7 px/格。這是預期的，因為第 2 回合施加了新的力。

## 結果：保齡球（修正施力點後）
用修正 y 座標後的施力點重跑第 1 回合（`logs/run_multiturn_bowling_turn1.sh`，seed 0 和 1），仍然失敗：
- s0：球往鏡頭方向倒退。
- s1：瓶子炸開、數量變多，還變成球。

修正前後的失敗樣子一樣，所以主因是**往畫面深處的運動**，超出 Goal Force 的訓練分布。多回合場景的運動應該保持在畫面平面內，骨牌場景是主要測試場景。

## 下一步（2026-11-24 時的規劃）
- 對融合的骨牌做逐物件參考修補：E2b 式的 VACE，每支骨牌各自的 mask，用記憶裁切當參考（只提供外觀，不提供姿勢）。
- 從 seed 1 的結局再接一次第 2 回合：同樣的動作，不同的世界狀態。
- 第 3 回合／分支：回到第 1 回合，改用不同的第 2 回合推法。

## 結果：從第 1 回合 seed 1 的結局接第 2 回合（#6，2026-11-25）
同樣兩種動作（A 直接推白球 0°、B 在骨牌 2 設目標 0°），Goal Force seed 0，從第 1 回合 **seed 1** 的結局出發。執行：`logs/run_multiturn_dominos_turn2_from_s1.sh` → `outputs/multiturn/dominos_turn2_from_s1/`。
- 兩支影片中，倒下的前排骨牌又**融成一塊長板**被往右推（和 seed 0 那條鏈一樣）→ 到目前為止 **4/4** 支第 2 回合影片都有融合。
- B：一支倒下的骨牌**重新立起**（domino4 被標 REVERT，新版評估也標出了 domino2）。
- A 的長板只看 mask 是看不出來的（SAM2 替每支骨牌都保留了看起來合理的 mask），只有和最新狀態比較的 R-DINO 下降（0.34–0.39）。這促成了統一的評估程式（`evaluate.py`、`metrics.md`），它同時用原始裁切和最新狀態評估外觀，並加上針對融合和分身的目視稽核。
- seed 1、2 的 baseline 和記憶修補比較（#8）：見 `memory_plan.md`、`reports/overnight_2026-11-25.md`。

## 夜間實驗 2026-11-25（#8 記憶修補、照片、分支）
完整紀錄：`reports/overnight_2026-11-25.md`；給組員的摘要：`reports/team_update_2026-11-25.md`。
- 評估：`evaluate.py`（定義見 `metrics.md`）、`aggregate.py`（表格、散佈圖）、`camera_check.py`；目視稽核在 `reports/overnight_assets/visual_audit.md`；盲評拼圖在 `outputs/multiturn/blind/`。
- 方法：`memory_repair.py`（設計見 `memory_plan.md`）。兩種條件：`appearance`（用原始裁切當 VACE 參考圖）和 `full`（剛體跟隨的狀態約束＋只提供顏色的記憶）。
- 照片場景：`photo_scenes.json` → `make_photo_turn1.py`；第 2 回合用 `make_next_turn.py`。
- 主要觀察（初步）：
  - 只有外觀記憶時會錯置身分（白球變紅，14 支中 12 支），兩個面向都變差；
  - `full` 用外觀換來一點狀態；
  - 洋芋片回到原位是施力造成的，記憶從來沒有把位置拉回去。
