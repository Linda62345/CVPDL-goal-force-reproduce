# 原論文照片兩回合實驗計畫（2026-11-26）

## 1. 目的
改用原論文附的照片（`datasets/examples/`），讓結果可以和原論文直接對照。每張照片做**兩回合**施力，回答：

- **RQ：** 讓一張照片可以有多回合的物理互動
  - **sub-RQ1：** 第 1 回合結束後，物體外觀有沒有保持（LoRA 在這裡嘗試）
  - **sub-RQ2：** 第 1 回合和第 2 回合的物理狀態合不合理

## 2. 照片範圍
`datasets/examples/` 共 14 張：
- 12 張是施力例子，全部使用。
- 2 張 `canny-edge-examples/`（山景石窗、斑馬）**不使用**：它們給的是 Canny 邊緣控制模型，輸入是邊緣線影片，沒有施力欄位。

## 3. 第 1 回合：完全照原論文
- 直接使用原論文的 CSV，不修改 prompt、施力點、方向和力道。
- 全部是 Goal Force 模式，力道 350，質量交給模型推測。
- 原 prompt 沒有「The camera is static.」，第 1 回合也不加，保持和原論文一致。
- 角度：0° 往右、90° 往上、180° 往左、270° 往下。

| # | 照片 | 目標物件 | 方向 | 第 1 回合 prompt（原文） |
|---|---|---|---|---|
| 1 | `_pool_tool` 撞球 | 左邊白球 | 180° 左 | A cue stick strikes a pool ball, causing it to roll across the table. |
| 2 | `_tennis` 網球 | 中間靠線的網球 | 175° 左 | A tennis ball rolls across the court, colliding with another ball. |
| 3 | `_golf` 高爾夫 | 白色高爾夫球 | 185° 左 | A golf club hits a golf ball. |
| 4 | `_cantaloupes` 哈密瓜 | 右邊的瓜 | 0° 右 | A cantaloupe rolls across the surface, colliding with another cantaloupe. |
| 5 | `_ballthendominos` 球＋骨牌 | 紅球 | 5° 右 | One pool ball hits the other, which then hits the first domino, triggering a chain reaction |
| 6 | `_pendulum` 鐘擺 | 紅色方塊 | 0° 右 | The pendulum swings, striking and toppling the red block. |
| 7 | `_paw_tool1` 西洋棋 | 狗掌下的棋子 | 335° 右下 | A dog paw nudges a chess piece, causing it to slide across the board. |
| 8 | `_toycar` 玩具車 | 黑色玩具車 | 225° 左下 | A hand reaches out to push the car across a map, and the car travels over various countries and regions. |
| 9 | `_soccer_tool` 足球 | 足球 | 180° 左 | A soccer ball is kicked and rolls across the field. |
| 10 | `_paw_tool2` 狗推藍球 | 藍色小球 | 135° 左上 | A dog nudges a ball with its paw, causing it to roll on the ground. |
| 11 | `_paw_tool3` 貓推紅球 | 紅球 | 180° 左 | A cat's paw nudges a ball, causing it to roll across the grass. |
| 12 | `_bulb_tool` 燈泡 | 左邊燈泡 | 0° 右 | A hand pushes the hanging bulb, causing it to sway. |

## 4. 第 2 回合：我們設計的動作
原則：
- 每回合只推一個物件。
- 盡量推第 1 回合動過的物件，或讓它被撞到，這樣才看得出外觀和位置有沒有被記住。
- 第 2 回合用**直接施力**（指定推誰、往哪推），力道先定 200。我們自己照片的第 2 回合也是這樣設定，可以和之前的結果比較。
- prompt 結尾都加「The camera is static.」。
- **施力點的座標等第 1 回合跑完才定**：用 SAM2 找出物件停下的位置，取它的中心點。

| # | 照片 | 第 1 回合後（預期） | 第 2 回合推誰 | 方向 | 第 2 回合 prompt | 主要看什麼 |
|---|---|---|---|---|---|---|
| 1 | 撞球 | 白球滾到左邊 | 黃球 | 180° 左 | The yellow pool ball rolls to the left and hits the white ball. The camera is static. | 兩顆球顏色會不會互換；白球是不是從新位置被撞 |
| 2 | 網球 | 中間的球被撞往左 | 左上那對球中的一顆 | 0° 右 | A tennis ball rolls to the right across the court. The camera is static. | 一樣的球會不會變多、變少或位置重置 |
| 3 | 高爾夫 | 白球往左 | 黃球 | 180° 左 | The yellow golf ball rolls to the left and hits the white golf ball. The camera is static. | 球的顏色和花紋 |
| 4 | 哈密瓜 | 右邊的瓜往右滾 | 同一顆瓜 | 180° 左 | The cantaloupe rolls back to the left across the surface. The camera is static. | 網紋外觀；會不會直接「瞬移」回原位 |
| 5 | 球＋骨牌 | 骨牌連鎖倒下 | **11/25 已做完，不重跑**：第 1 回合用原論文 CSV（seed 0、1）；第 2 回合 A 白球往右（直接施力 350）、B 第二張骨牌（goal 350），各 3 個 seed＝12 支（exp8）；另有 C 紅球往左（200）、D 後排骨牌往右（150），各 1 支（exp10）。LoRA 修補在 `lora_exp8`、`lora_exp10` | — | （已有） | 骨牌融合 |
| 6 | 鐘擺 | 紅色方塊倒下 | 倒下的方塊 | **180° 左** | The fallen red block slides to the left across the table. The camera is static. | 方塊會不會自己站回去（姿勢倒退）；會不會穿過鐘擺的柱子 |
| 7 | 西洋棋 | 一顆棋子滑往右下 | 左邊的深色主教（dark bishop） | 0° 右 | A dark wooden chess piece slides to the right across the board. The camera is static. | 最難的外觀測試：棋子種類和黑白會不會被畫錯 |
| 8 | 玩具車 | 車往左下開 | 玩具車 | **90° 上** | The toy car drives upward across the map. The camera is static. | 車的外型；地圖背景會不會亂掉 |
| 9 | 足球 | 球往左滾 | 足球 | **90° 上** | The soccer ball is kicked upward and rolls up the field. The camera is static. | 球的黑白花紋；往畫面深處滾，球會變小 |
| 10 | 狗推藍球 | 藍球往左上滾 | 藍球 | 0° 右 | The dog nudges the blue ball back to the right with its paw. The camera is static. | 球很小，可能追蹤失敗 |
| 11 | 貓推紅球 | 紅球往左滾 | 紅球 | 180° 左 | The red ball rolls further to the left across the grass. The camera is static. | 紅球的縫線 |
| 12 | 燈泡 | 燈泡擺盪後回原位 | 右邊燈泡 | 180° 左 | A hand pushes the right bulb, causing it to swing and hit the other bulb. The camera is static. | 只看外觀；燈泡本來就會擺回原位，不用來判斷狀態 |

**說明：**
- 上表的「第 1 回合後」是預期，實際要看生成結果。如果物件出了畫面或沒動，就依實際狀況調整動作，並寫在執行紀錄裡。
- 「往上」在畫面裡通常代表往畫面深處走（玩具車、足球），物件會變小。評估時用位移方向判斷，不能只看大小。

## 5. 執行步驟
1. **第 1 回合生成**：11 張（骨牌沿用 exp8）× 2 個 seed（0、1）= 22 支。輸出到 `outputs/multiturn/paper_t1/`。
2. **第 1 回合檢查**：
   - 用 `turn1_success.py` 檢查目標物件有沒有照方向移動。
   - 每支取最後一格，用 SAM2 標出所有物件。
   - 第 2 回合的施力點由程式自動決定（目標物件在最後一格的中心），預覽圖存在 `datasets/multiturn/paper/<照片>/`。
   - **11/26 決定：兩回合一次跑完，不中途等人工確認。** 預覽圖事後檢查；施力點明顯錯誤的就在報告裡標記。
   - 兩個 seed 都保留，不挑 seed，避免只挑好的結果。
3. **第 2 回合生成**：22 支，用最後一格當輸入，`make_next_turn.py` 產生 CSV。輸出到 `outputs/multiturn/paper_t2/`。
4. **外觀修補**：每支第 2 回合影片做兩種：
   - baseline：不修
   - lora_orig：LoRA＋第 1 回合輸入照片裡的原始裁切當參考圖
   - 時間夠的話，加上舊方法「只有外觀記憶」做對照。
5. **評估**：
   - 自動指標：`evaluate.py`（狀態保留、R-DINO 外觀相似度、第 2 回合是否成功、消失／融合／倒退）。
   - 人工評分：盲評拼圖，見第 7 節。
   - world model 評估：待決定。
6. **彙總**：`aggregate.py` 產生表格和散佈圖，寫成中文報告 `reports/paper_photos_<日期>.md`。

## 6. 時間和資源
- 每支 Goal Force 影片約 22 分鐘（RTX 5090 32GB）。
- 第 1 回合 22 支，約 8 小時。
- 第 2 回合 22 支，約 8 小時。
- 修補和評估：22 支 × 1–2 種，約 2–3 小時。
- **合計約 18–19 小時 GPU**，約兩個晚上。第 1 回合跑完要先等你們確認第 2 回合，所以本來就會分兩段。
- GPU 一次只跑一件；用 `logs/paper/` 的 queue runner，可以中斷後接著跑。

## 7. 人工評分（草案）
- 每支影片做一張拼圖：第 1 回合最後一格、第 2 回合的幾個關鍵格。方法名稱隱藏，順序打亂。
- 評分項目，各 1–5 分：
  1. **外觀一致**：物件看起來還是同一個嗎（顏色、花紋、形狀）
  2. **狀態一致**：第 2 回合開始時，物件是不是在第 1 回合結束的位置和姿勢
  3. **物理合理**：第 2 回合的動作合不合理（方向、碰撞、有沒有穿透或融合）
- 每支影片至少 2 位評分者。評分者和評分表格式待組員確認。

## 8. 需要組員決定
1. 第 2 回合動作還要不要修改（目前已依 11/26 討論改了玩具車、足球、鐘擺）。
2. 人工評分由誰評、評幾分制。
3. world model 評估要用哪一個，或先只做人工評分。

## 9. 實驗 A：五回合累積效應（11/27 加入）
**問題：** 兩回合的結果顯示，直接接最後一格時狀態大致接得上，外觀走樣也不多，多回合的研究意義不明顯。真正的風險可能是「回合越多、外觀越偏離原物」。實驗 A 檢查這件事。

**判斷標準（事先定好）：**
- 每回合結束時，物件對原始照片的 R-DINO（`eval_continuity.py` 的累積外觀）如果**隨回合明顯下降**（第 5 回合比第 1 回合低 0.1 以上，或肉眼看得出越來越不像），多回合＋外觀記憶就有研究價值，繼續這條路。
- 如果 5 回合後外觀和第 1 回合差不多，多回合這個方向基本放棄，改做單回合外觀保持（方向 B）或物理合理性評估（方向 C）。

**設定（11/27 02:05 依組員要求改成「互撞」）：**
- 照片：哈密瓜（兩顆瓜、網紋）、撞球（白球和黃球，可看顏色會不會互換）、西洋棋（多個細節豐富的棋子）。玩具車只有一個物件、無法互撞，所以換成撞球。
- 5 回合，**每回合推一個物件「朝向另一個物件」，讓它們互撞**。方向由程式依上一回合結束時兩個物件的位置自動計算（`toward:<物件>`）。
- 力道小：哈密瓜 150（兩顆瓜距離約 270 px）、撞球 120、西洋棋 100（棋子距離近）。原論文是 350、我們的第 2 回合是 200。往另一個物件推，物件會往畫面中間靠，比較不會出畫面。
- 哈密瓜：右邊的瓜和左邊的瓜輪流撞對方。撞球：黃球和白球輪流撞對方。西洋棋：每回合換一顆棋子去撞另一顆（深色主教→白主教、白兵→深色主教、白兵→深色國王、白主教→白兵、深色國王→白兵）。
- prompt 都寫出「撞到另一個物件」和「The camera is static.」。
- 第 k 回合用第 k−1 回合的最後一格當輸入，施力點是目標物件的追蹤中心。目標不在畫面內就停止，已完成的回合保留。
- 只跑 seed 0，只看 baseline（不修補），先回答「會不會累積」。如果有累積，再加 LoRA 修補比較。
- 順序：**哈密瓜排在佇列最前面**（11/27 約 02:25 開始，約 2 小時），跑完自動產生 `outputs/multiturn/paper_review/chain_cantaloupes.mp4`（左：原始照片，右：第 1–5 回合接起來）。撞球、西洋棋排在佇列最後。
- 設定檔 `multiturn/chain_scenes.json`，腳本 `logs/paper/chain.sh`，佇列工作 `chainA_<照片>`。
- 輸出：影片 `outputs/multiturn/chain/<照片>/gf/`，每回合狀態 `turn<k>/state.json`，累積評估 `chain_eval.json`，每回合評估 `outputs/multiturn/chain_eval/`。

## 10. 執行紀錄
- 11/26 依討論修改第 2 回合：玩具車往上、足球往上、鐘擺方塊往左；西洋棋定為深色主教往右。
- 設定檔：`multiturn/paper_scenes.json`（第 1 回合 CSV、SAM2 點擊座標、第 2 回合設定）。點擊位置預覽：`outputs/multiturn/paper/clicks_preview.jpg`。
- 流程腳本：`logs/paper/scene.sh 照片 seed`（第 1 回合 → SAM2 狀態 → 第 2 回合 CSV → 第 2 回合 → baseline 評估 → lora_orig 修補與評估 → 對照圖）。LoRA 權重用 step-3000（和測試二相同）。
- 佇列：`logs/paper/queue.txt`（11 張 × seed 0、1 = 22 個工作，先跑完全部 seed 0），`logs/paper/runner.sh`；停止：`touch logs/paper/STOP`。
- 輸出：影片 `outputs/multiturn/paper/<照片>/`，評估 `outputs/multiturn/paper_eval/{baseline,lora_orig}/<照片>_s<seed>/`。
- 11/26 15:27 開始執行。每個工作約 55 分鐘，預估全部約 20 小時。
- 11/26 撞球 seed 0：第 1 回合影片在第 12 格左右鏡頭往下移，**兩顆球都從畫面消失**（只剩球桿和手），無法做第 2 回合，記為「第 1 回合失敗」。這是 Goal Force 本身的失敗，保留為分析素材。之後 `scene.sh` 遇到第 2 回合目標不在最後一格時，會印出 `SKIP_TURN2` 並結束。
- 11/26 網球 seed 0：第 1 回合鏡頭持續平移和拉近，左上兩顆球和右邊的球都移出畫面，原定第 2 回合目標（左上第二顆）不在最後一格。
- 因為前兩張都是「目標出畫面」，**加入備用目標**（`paper_scenes.json` 的 `turn2_fallback`）：原定目標不在最後一格時，依序改推仍在畫面內的物件。實際選擇記在 `outputs/multiturn/paper/<照片>/t1_s<seed>/t2_choice.json`（`fallback: true` 代表用了備用目標），分析時分開統計。撞球 seed 0 兩顆球都不見，沒有備用目標可用。網球 seed 0 重新排進佇列（`tennis_s0_fb`）。
- 11/26 高爾夫 seed 0：第 1 回合第 16 格起兩顆球都往左出畫面，鏡頭也跟著平移，最後只剩球桿和草地。兩顆球都不見，備用目標也無法使用。
- **前三張的共同問題**：原論文設定力道 350、prompt 沒有指定鏡頭固定，目標物件又靠近畫面邊緣，所以球直接滾出畫面、鏡頭跟著移動。第 1 回合單看可能是合理的影片，但沒有留下可以做第 2 回合的狀態。
- 11/26 組員決定「兩種都跑」：原論文設定照跑當對照；第 1 回合失敗（`SKIP_TURN2`）的照片／seed，另外跑 **v2**：原 prompt 加上「The camera is static.」，Goal Force 力道 350 → 200，其他不變。佇列尾端的 `v2_<照片>_s<seed>` 工作會自動判斷是否需要（`logs/paper/v2_if_needed.sh`）。v2 輸出：`outputs/multiturn/paper_v2/`、評估 `outputs/multiturn/paper_v2_eval/`、輸入 `datasets/multiturn/paper_v2/`。
- 11/27 01:27 修改 `scene.sh` 時，哈密瓜 seed 1 剛好在執行。為了避免 bash 讀到改到一半的腳本，我用 PID 停掉這個工作，由 runner 自動重試（已生成的影片不會重跑）。
- 11/27 01:30 進度：原設定 seed 0 有 8 張跑完兩回合，seed 1 有網球跑完。撞球、高爾夫兩個 seed 的第 1 回合都失敗（兩顆球都出畫面）。網球兩個 seed 都用了備用目標（下方的球）。
- 11/27 骨牌兩回合（exp8、exp10，共 14 支）也做成同格式的並排影片：`outputs/multiturn/paper_review/paper_ballthendominos_<run>.mp4`，最後的報告會把骨牌一起放進原論文照片的結果表。
- 11/27 02:20 依組員要求調整：
  - **第 2 回合改成「互撞／再推一次」版本（turn2b）**：有兩個以上物件的照片，第 2 回合把目標推向另一個物件（`toward:<物件>` 或 `toward:nearest`，依第 1 回合結束時的位置自動計算方向）；只有一個物件的照片（玩具車、足球、狗推藍球、貓推紅球），改成手、腳或動物的腳掌「再推一次」，方向朝畫面中心，避免出畫面。燈泡因為遮罩包含電線、中心點偏上，固定往左 180°。設定在 `paper_scenes.json` 的 `turn2b`，流程腳本 `logs/paper/scene_t2b.sh`，輸出 `outputs/multiturn/paper/<照片>/t2b_gf/`、`repair_t2b/`，評估 `outputs/multiturn/paper_eval_t2b/`，並排影片 `paper_review/t2b_<照片>_s<seed>.mp4`。
  - seed 1 的工作全部改用 turn2b；seed 0 已有第 1 回合，另外補跑 turn2b 的第 2 回合（每個約 30 分鐘），兩個 seed 用同一種設計比較。原本 seed 0 的第 2 回合（turn2）保留，當作補充資料。網球的備用目標重跑（`tennis_s0_fb`）改由 turn2b 取代。v2 也改用 turn2b。
  - 西洋棋 5 回合互撞（`chainA_paw_tool1`）移到 seed 1 工作之後、seed 0 補跑之前。
- 11/27 02:30 **turn2b 力道調小**：已跑完的 seed 0 第 2 回合（力道 200）裡，玩具車移動 459 px（第 33 格出畫面）、西洋棋 574 px、狗推藍球 565 px、網球 349 px（出畫面）、貓推紅球第 12 格出畫面，燈泡只動 3 px。所以 turn2b 改成：單一物件和距離近的棋子 100，球類 120，距離遠才碰得到的哈密瓜和鐘擺 150，燈泡維持 200。第 1 回合仍照原論文（350），力道降低的版本只在 v2（200）。

- 11/27 04:19 實驗 A 哈密瓜 5 回合完成（力道 150，每回合 ~22 分）。被推的瓜 R-DINO（對原圖，最後一幀）：0.63 → 0.48 → 0.42 → 0.19 → 0.05；另一顆 0.77 → 0.47 → 0.42 → 0.12 → 0.37。肉眼：第 3 回合起瓜變成橢圓、網紋消失、長出蒂頭，第 4–5 回合像木瓜／香瓜；鏡頭也在平移。達成「下降 ≥ 0.1」的判準 → 外觀漂移會累積，多回合值得做。eval_continuity 有 2 個 RESET 旗標（turn 2、4 的 melon_right 位置跳動）。逐回合首／中／尾幀：outputs/multiturn/chain/cantaloupes/frames_first_mid_last.jpg。chain 影片標籤原誤寫 force 100，已改為讀 chain_scenes.json 並重做。
- 11/27 11:55 v2 第 1 回合力道由 200 降為 150（使用者要求力道再小，避免球出框）；修正 v2_if_needed.sh：pool_tool_s0 的失敗訊息是 "not visible in the last frame" 而非 SKIP_TURN2，原本會被誤判為「不需 v2」。v2 尚未開始跑，所以沒有舊的 200 結果。
- 11/27 12:00 使用者要求 seed 0 的第 1 回合也降力道：佇列中 t2b_*_s0、v2_*_s0 改為註解，換成 11 支 v2full_<scene>_s0（scene_t2b.sh <scene> 0 v2：第 1 回合重新生成，原論文 CSV + 鏡頭固定 + 力道 150；第 2 回合 = turn2b 互撞）。輸出 outputs/multiturn/paper_v2/<scene>/，評估 outputs/multiturn/paper_v2_eval/。原佇列備份 logs/paper/queue.before_s0v2.txt。seed 1 的 turn2b 仍是第 1 回合 350（原論文設定）。
- 11/27 12:05 使用者要換電腦：佇列只跑到 seed 0 低力道 11 支 + 並排影片；v2_*_s1（撞球/高爾夫/玩具車 s1 重跑）與 chainA_pool_tool 改為註解，未跑。
- 11/27 12:30 使用者要求骨牌也照現行規則跑兩回合互撞：paper_scenes.json 加入 ballthendominos（turn2b = 紅球往回撞白球，力道 120；fallback 白球撞紅球），佇列加 v2full_ballthendominos_s0（第 1 回合力道 150 + 鏡頭固定），排在 v2full_golf_s0 之後、review_videos 之前。
- 11/27 12:40 使用者希望骨牌第 2 回合「再把其他骨牌推倒」：ballthendominos 的 turn2b 改為直接推後排一塊站著的骨牌（domino_back，點選 (390,258)）往右，力道 100；不設 fallback。
- 11/27 12:30 檢查第 2 回合施力點：paper_bulb_tool_s0（舊 turn2）推錯燈泡——SAM2 把 bulb_left、bulb_right 兩個 mask 都追到左燈泡（中心相同 (158,405)），所以力打在左燈泡。修正 paper_pick_t2.py：最後一幀中心相距 < 12 px 的兩個物件視為追丟，不推（之後的工作生效）。其他已跑的第 2 回合施力點都在正確物體上；狗藍球 s0/s1 的球只剩畫面上緣一小塊。
- 11/27 13:00 使用者讀論文後指出：論文的每個範例都是 goal 模式、文字寫明「誰造成動作」（手、爪子、球桿、另一顆球）。我們的 turn2b 用 direct 模式（看不見的力直接推），一半的文字沒有原因。改為 **turn2c**（paper_scenes.json）：goal 模式，projectile = 造成動作的物體（CSV projectile 點 = 它的追蹤中心），target = 被推動的物體（goal force 在它中心），角度 'away' = projectile→target 方向；手／爪／腳場景 projectile = target（畫面外的施力者，與論文工具範例相同）；文字都寫原因。make_next_turn.py 加 --projectile；paper_pick_t2.py 支援 turn2c（輸出第 5 欄 PROJECTILE）；新腳本 logs/paper/scene_t2c.sh（輸出 t2c_gf/、repair_t2c/、paper_v2_eval_t2c/）。佇列 v2full_* 換成 v2c_<scene>_s0（12 張，第 1 回合仍是 v2：鏡頭固定、力道 150）。在已有的第 1 回合 state 上試跑選擇與 CSV 產生：10 張正常，撞球／高爾夫舊 s0 的球已出框（正確跳過）。並排影片新增 t2c_v2_<scene>_s0.mp4。佇列備份 logs/paper/queue.before_t2c.txt，設定備份 logs/paper/paper_scenes.before_t2c.json。
- 11/27 13:00 實驗 A 西洋棋 5 回合完成（力道 100）。最後一幀對原圖 R-DINO（第 1→5 回合）：dark_king 0.70→0.22、white_pawn_left 0.89→0.40、white_bishop 0.83→0.37、white_pawn_bottom 0.88→0.32。肉眼：棋盤和狗爪穩定，但黑棋第 3 回合起從棋盤上消失或被推出棋盤，第 5 回合又冒出一顆黑棋；白棋有的滑出棋盤，數量和身分在變。和哈密瓜（外觀變形）不同，這裡的漂移主要是物體消失／出現。影片 outputs/multiturn/paper_review/chain_paw_tool1.mp4，逐回合畫面 outputs/multiturn/chain/paw_tool1/frames_first_mid_last.jpg。另：第一支 turn2c（v2c_cantaloupes_s0）13:54 完成，CSV 正確（goal 模式，右瓜→左瓜 176°）。
- 11/27 15:30 使用者要求影片改成有意義的檔名：新增 multiturn/video_names.py（命名規則）與 multiturn/publish_videos.py（複製到 reports/videos/ 改名、重寫 reports/videos.md）；reports/videos/ 的舊檔以 git mv 改名，outputs/ 維持原名。prompt_table.py 改成 A–E 分節、標題用新檔名並附原檔名，新增 turn2c 節。佇列在 review_videos 後加 publish_videos（只產生檔案，不推 GitHub）。注意：西洋棋 turn2c s0 的造成者 white_pawn_target 在畫面右下角落 (826,25)。

- 11/27 22:14 seed-0 turn2c（v2 第 1 回合）排程跑完：9 成功（哈密瓜、鐘擺、西洋棋、玩具車、足球、狗爪藍球、貓爪紅球、網球、骨牌）；燈泡、撞球、高爾夫失敗（第 1 回合後被推物體不在畫面 → SKIP_TURN2，重試一次仍同）。執行器以 `logs/paper/STOP` 停止。看片結論寫在 `multiturn/publish_videos.py` NOTES：因果正確的有足球、骨牌、貓爪（但球消失）；玩具車出畫面、狗爪沒碰到球、網球被指定的球不動且有球消失、西洋棋改由狗爪推。
