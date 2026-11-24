# Goal Force 小規模試驗報告（Pilot）

- 日期：2026-11-23 ~ 11-24
- 模型：Goal Force `step-3000`（Wan2.2-I2V-A14B + 10 層 ControlNet），zero-shot、未微調
- 硬體：1 × RTX 5090（32GB）
- 標註來源：**Claude 依每支影片 6 格抽樣的初判**（`annotations/claude_initial_guess.csv`），尚未經人工確認

---

## 1. 研究問題

> 以「移動方向、目標達成、生成瑕疵」驗收每支影片，採「演對就停、每個操作最多試 4 次」的策略，能否在維持可用率的情況下，少跑幾次 Goal Force？

本次 pilot 的目的是量測兩件事：
1. **時間**：模型載入與單支生成各要多久
2. **可行性**：每個分支是否至少有一支演對

---

## 2. 環境與修改

| 項目 | 內容 |
|---|---|
| Python 環境 | `goal-force/venv`（Python 3.12） |
| PyTorch | 2.11.0 + cu128（README 指定的 torch 2.5 / cu121 不支援 RTX 5090 Blackwell） |
| 權重 | 約 134GB（Wan2.2 兩個 expert 114GB、T5/VAE 12GB、Goal Force ckpt 7.6GB） |

對 `scripts/inference/inference_goal_force.py` 的修改（不加參數時維持原行為）：
- `VRAM_LIMIT_GB` 環境變數：限制常駐 GPU 的權重量。原設定在 32GB 卡上會 OOM，本次設為 16
- `--seeds`：模型只載入一次，連續跑多個 seed
- `--output_dir`：自訂輸出資料夾
- 每支耗時寫入 `timings.jsonl`
- 已存在的輸出會跳過，可從斷點續跑

---

## 3. 實驗設定

所有條件的力的大小都是 **350**（與官方範例一致），質量填 -1（由模型推斷），每個條件跑 seed 0、1、2，同一場景的 caption 都相同。

| 場景 | 圖片 | 模式 | 分支（角度） | caption |
|---|---|---|---|---|
| 杯子 mug | 自拍，手在杯子左側 | Goal Force | 左推 180°、右推 0° | A hand pushes the white mug, and the mug slides across the black shelf. The camera is static. |
| 達摩 daruma | 自拍，畫面中無施力者 | Goal Force | 正上 90°、左上 135°、右上 45° | A small red daruma doll on a grey fabric surface is knocked up and flies into the air. The camera is static. |
| 保齡球 bowling | 網路圖（Wikimedia） | Direct Force（力直接施加在球上） | 往前 90° | A blue bowling ball rolls forward down the lane and crashes into the pins, knocking all of them down. The camera is static. |

另外跑了 1 支官方範例（`_bulb_tool`，seed 5）驗證環境，結果正常。

---

## 4. 結果一：耗時

| 項目 | 實測 |
|---|---|
| 模型首次載入（冷啟動，要讀硬碟） | 約 3 分鐘 |
| 模型載入（檔案已在系統快取） | 24–30 秒 |
| **載入後每支（50 步去噪 + VAE 編解碼 + 存檔）** | **1311 秒 ≈ 21.9 分鐘**（18 支差異 < 0.2%） |
| 去噪每一步 | 約 25.7 秒 |

→ 正式批次可以用「載入一次 + N × 22 分鐘」來估。耗時幾乎固定，跟場景無關。

---

## 5. 結果二：各分支結果（Claude 初判）

usable = 方向正確、達成目標，且沒有嚴重瑕疵。

| 分支 | seed 0 | seed 1 | seed 2 | 方向正確 | **usable** |
|---|---|---|---|---|---|
| mug 左推 | 翻倒 | 掉下架 | 飛出畫面 | 3/3 | **0/3** |
| mug 右推 | ✅ | 掉下架 | ✅ | 3/3 | **2/3** |
| daruma 正上 | 偏右 | ✅ | 偏右 | 1/3 | **1/3** |
| daruma 左上 | ✅ | ✅ | 力道不足 | 3/3 | **2/3** |
| daruma 右上 | 物體分裂 | 物體消失 | ✅ | 2/3 | **1/3** |
| bowling 往前全倒 | 部分倒 | 方向錯＋崩壞 | 接近全倒 | 2/3 | **0/3** |

逐格對照圖：
- `outputs/rack_pilot/contact_mug_left.png`、`contact_mug_right.png`
- `outputs/daruma_bowling/contact_daruma_up.png`、`contact_daruma_upleft.png`、`contact_daruma_upright.png`、`contact_bowling.png`

### 觀察
1. **方向條件大致有效**：14/18 支方向正確，杯子左右兩個分支都是 3/3。
2. **力的大小偏強**：杯子左推 3 支都失控（翻倒、掉落、飛出）。手在左側，模型只能用「拉」的方式往左，更容易失控。
3. **沒有施力者也能動**：達摩畫面裡沒有手，模型就讓它自己彈起來，三個方向都有至少一支正確。
4. **「全倒」很難做到**：即使 caption 寫明全倒，3 支都沒全倒。這種結果類的目標，模型不容易控制。
5. **常見瑕疵**：物體消失或分裂、白瓶變成白球、背景螢幕出現亂碼文字。

---

## 6. 對研究問題的初步分析

假設驗收完全正確，用「最多試 4 次、演對就停」的期望值來算，p 是 pilot 估出的單支成功率：

| 分支 | p̂ | 實際照 seed 順序，到第一支成功要幾支（上限 3） | 期望要跑幾支（上限 4） | 可用率（上限 4） |
|---|---|---|---|---|
| mug 左推 | 0 | 3（失敗） | 4.00 | 0% |
| mug 右推 | 0.67 | 1 | 1.48 | 98.8% |
| daruma 正上 | 0.33 | 2 | 2.41 | 80.2% |
| daruma 左上 | 0.67 | 1 | 1.48 | 98.8% |
| daruma 右上 | 0.33 | 3 | 2.41 | 80.2% |
| bowling | 0 | 3（失敗） | 4.00 | 0% |
| **合計** | | **13 支**（固定跑 3 支要 18 支，**省 28%**） | **15.8 支**（固定跑 4 支要 24 支，**省 34%**） | |

換算成時間：固定跑 4 支約 8.8 小時，提早停止約 5.8 小時。

### 解讀
- 容易的分支（p 約 0.67）平均 1.5 支就能停，省下的次數主要來自這裡。
- **p = 0 的分支（杯子左推、保齡球全倒）試 4 次也是白跑**，反而吃掉最多預算。照原計劃，這種分支應該先改條件（降低力的大小、調整手的位置、換配件或換拍攝角度），而不是靠多試幾次。
- 這裡的節省是假設「驗收完全正確」。實際能不能維持可用率，取決於驗收器會不會誤判，需要人工標註來檢驗。

---

## 7. 限制

1. **標註未經人工確認**：目前用的是 Claude 從 6 格抽樣做的初判，可能漏掉中間的瑕疵或誤判方向。
2. **樣本極少**：每個分支只有 3 支，p 的估計誤差很大。例如 p = 0.33 時，3 支全錯的機率還有 30%。
3. **場景與原始研究目標不同**：杯子、達摩、保齡球都**沒有「滑軌裝配」**，三項驗收中的「滑軌對齊、裝配結果」沒有測到。
4. **杯子左右不對稱**：手只在左側，左推和右推的難度本來就不同。
5. **caption 可能帶結果**：保齡球的 caption 寫了「全倒」，達摩的 caption 寫了「飛起來」。結果有一部分可能來自文字，不全是力的條件造成的。

---

## 8. 建議下一步

1. **人工標註**：填 `annotations/pilot_labels.csv`，再跟 Claude 初判比對，算出驗收器的一致率。
2. **修正 p = 0 的分支**：杯子左推把力的大小降到 150–200，或重拍手在右側的版本；保齡球加一組 caption 不提「全倒」的對照。
3. **增加樣本**：成功率在 0.2–0.8 之間的分支，每個加到 6–8 支，再離線模擬不同的停止上限（2、3、4 次）。
4. **回到原始任務**：拍攝有滑軌和終點的配件照片，背景單純、手的位置左右對稱。

---

## 9. 與原論文評估方法的比較

來源：Gillman et al., *Goal Force*, arXiv 2601.05848（HTML v2）。論文**沒有**一套逐支影片打分的標註表，而是依評估目的用了三種方法。

### 9.1 論文的評估方法

**(1) 人工兩兩比較（2AFC 使用者研究），§4.1 / Table 1**
- 75 個場景，分四類：兩物體碰撞、多物體碰撞、人和物體互動、工具和物體互動。圖片來自 Pexels、Pixabay、Unsplash 和 AI 生成。
- 在 Prolific 上找 40 位受試者，每題看兩支影片（Goal Force 對比只用文字描述的 baseline），從中選一支。
- 評三個面向：**Goal Force Adherence**（"Does the video accomplish the specified goal?"）、**Realistic Motion**、**Visual Quality**。
- 結果用「選 Goal Force 的百分比」呈現，例如兩物體碰撞的 adherence 是 73.4%。這是**相對比較**，不判斷單支影片的對錯。

**(2) 逐支判斷成功或失敗（visual planning），§5.1 / Table 2、Table 5**
- 22 個有干擾物的場景，每個場景生成 **50 支**。
- 成功的定義："the goal force is initiated by the correct, unconstrained object, rather than by a distractor or through spontaneous, non-causal motion"。工具場景是「正確使用工具達成指定的 goal force」。
- **先排除生成崩壞的影片**（例如 object hallucination），再算正確率 = 成功數 ÷ 有效數。
- 各場景正確率介於 54.5% 到 100% 之間。依 Table 5 加總約 898 / 1006 ≈ 89%（加總是我們自己算的，論文沒有寫總數）。
- 論文沒有說明判斷者是誰、「有效」怎麼判定，也沒有說明有沒有多人交叉確認。

**(3) 自動量測，§5.2–5.3**
- 多樣性：骨牌場景跑 26 個 seed，統計被打到的是哪一張骨牌，用 1 − JSD 計算分布與均勻分布的接近程度（Table 3，模型得分 0.658）。
- 質量：用 Faster R-CNN 偵測球的位置、算出速度，檢查重的物體是否需要更大的撞擊。每種組合 15 支（Figure 6）。

論文**沒有用到**：FVD、VLM 或 GPT 評審、自動判斷方向的指標，也沒有 best-of-N 或「演對就停」這類多次嘗試的設計。

### 9.2 與本研究標註欄位的對應

| 本研究欄位 | 論文中的對應 |
|---|---|
| `usable` | 最接近 §5.1 的「成功」，也接近 2AFC 的 Goal Force Adherence |
| `artifact` | 對應 §5.1 的「先排除崩壞影片」 |
| `goal_ok` | 對應各場景自己的成功定義 |
| `direction_ok` | 論文沒有單獨列這一項 |

### 9.3 建議
1. 本研究需要「**逐支判斷收或不收**」，應該採用 **§5.1 的做法**，而不是 2AFC。
2. 照 §5.1 的做法，把 `artifact` 嚴重的影片視為**無效**：成功率的分母只算有效的影片，同時另外報告崩壞的比例，數字就能直接跟論文的 Table 5 比較。不過對研究問題本身來說，崩壞的影片也算「沒收下」，所以可用率還是要用全部影片當分母，兩個數字都報告。
3. 論文每個場景 50 支，本研究每個分支 3 支。引用論文的成功率當參考時，要註明樣本數差異。
4. 論文正文寫 2AFC 有 40 位受試者，附錄 §7.1 的 direct-force 研究寫 10 位。引用時要分清楚是哪一項研究。

---

## 附：檔案位置（相對於 `goal-force/`）

| 內容 | 路徑 |
|---|---|
| 杯子影片 | `outputs/rack_pilot/` |
| 達摩、保齡球影片 | `outputs/daruma_bowling/` |
| 每支耗時 | `outputs/*/timings.jsonl` |
| 輸入圖與 CSV | `datasets/rack/`、`datasets/daruma/`、`datasets/bowling/` |
| 標註表與初判 | `annotations/` |
| **標註用影片（短檔名）** | `annotations/videos/` |
| 執行腳本與 log | `logs/` |

---

## 附：影片檔名說明

### 短檔名（標註用，`annotations/videos/`）
格式：`<場景>_<分支>_s<seed>.mp4`，檔名就是 `pilot_labels.csv` 的 `video_id`。

```
mug_left_s0.mp4          ← 杯子、往左推、seed 0
mug_left_s0_arrow.mp4    ← 同一支，畫上力的箭頭
daruma_upleft_s2.mp4     ← 達摩、往左上、seed 2
bowling_forward_s1.mp4   ← 保齡球、往前、seed 1
```

`_arrow` 版本（原始檔名結尾是 `-with-prompt.mp4`）的開頭幾格會畫出力的箭頭：**綠色是 Goal Force，紅色是直接施力**。

### 原始檔名（`outputs/` 底下）
範例：
```
step-3000_mug__prj_coords_0.54_0.45__tgt_coords_0.54_0.45__prj_mass_-1.0__tgt_mass_-1.0
__prj_force_-1.0__prj_angle_-1.0__tgt_indirect_force_350.0__tgt_indirect_angle_180.0__seed_0.mp4
```

| 片段 | 意思 |
|---|---|
| `step-3000` | 用的 checkpoint |
| `mug` | 輸入圖片名稱 |
| `prj_*` | **projectile（直接施力）**的設定。`-1` 代表沒用到 |
| `tgt_*` | **target（Goal Force 目標）**的設定 |
| `coords_0.54_0.45` | 施力點位置，用比例表示：x 是從左往右 54%，y 是從上往下 45% |
| `mass_-1.0` | 質量，-1 代表由模型自己推斷 |
| `tgt_indirect_angle_180.0` | **Goal Force 的方向** |
| `tgt_indirect_force_350.0` | Goal Force 的力的大小 |
| `prj_angle_*`、`prj_force_*` | 直接施力的方向與大小（只有保齡球用到） |
| `seed_0` | 隨機種子 |

### 角度對照
**0° 往右，90° 往上，180° 往左，45° 右上，135° 左上**，跟數學上的角度定義一樣。

| 場景 | 看哪一段 | 對應 |
|---|---|---|
| 杯子 | `tgt_indirect_angle` | `180.0` 往左、`0.0` 往右 |
| 達摩 | `tgt_indirect_angle` | `90.0` 正上、`135.0` 左上、`45.0` 右上 |
| 保齡球 | `prj_angle` | `90.0` 往前（畫面往上），`tgt_*` 都是 -1 |
