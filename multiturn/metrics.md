# 第 2 回合評估指標（所有實驗共用）

程式：`multiturn/evaluate.py`，每支影片呼叫一次。所有方法、seed、場景都用同一份程式和同一組門檻評分。

```
HF_HOME=imagegen/hf_cache imagegen/venv/bin/python -I multiturn/evaluate.py --video T2.mp4 \
  --prev_state <第1回合>/state.json --target <物件> --angle <角度> --method <baseline|appearance|full> \
  --scene <場景名> --out <輸出資料夾>
```

**追蹤方式。** 第 1 回合結束時看得到的每個物件，都會用 SAM2.1-large 在第 2 回合影片中追蹤。追蹤的提示點取自各物件在第 1 回合最後一格的 mask 內部（`extract_state.py`，stride 1，81 格）。修補後的影片也會從頭重新追蹤，所以不同方法之間不會共用 mask。

## 1. 狀態保留（先逐物件判定，再彙總成整支影片）

| 項目 | 定義 |
|---|---|
| `start_iou` | 物件在**第 1 回合最後一格**和**第 2 回合第 0 格**的 mask IoU，用來看換回合時狀態有沒有接上。用上一回合最後一格當輸入時，會接近 1。 |
| `vanished`（消失） | 第 2 回合結束時看不到（面積 < 30 px），**而且**消失前的 mask 沒有碰到畫面邊緣。 |
| `exited`（離開畫面） | 結束時看不到，但最後一次看到時 mask 碰到邊緣（4 px 以內）。這是合理的離開，**不算**遺失。 |
| `fused`（融合） | 符合下列任一條：在 ≥ 3 格中，和其他物件的 mask 重疊超過較小那個 mask 的 50%；結束時面積小於第 2 回合開始時的 0.3 倍（**塌縮**，被別的 mask 吃掉）；結束時面積大於開始時的 3 倍（**膨脹**，吃掉了別的物件）。 |
| `pose_revert`（姿勢倒退） | 第 1 回合結束時姿勢是 `changed`（例如倒下），第 2 回合結束時又變回 `as_initial`。姿勢標籤來自 `common.pose_label`：和第 1 回合第 0 格相比，主軸轉動超過 35° 或長寬比變化超過 1.65 倍，就算 `changed`。只對細長物件計算。 |
| `pos_reset`（位置被拉回） | 第 1 回合結束時，物件已經離初始位置超過 15 px；第 2 回合結束時，距離縮到不到原本的一半。如果這個物件就是**被推的目標**，而且指定方向是朝初始位置（cos > 0.7），就標成 `returned_by_force`（施力造成的回歸），不算被拉回。 |
| `lost`（遺失） | `vanished` 或 `fused` |
| `reverted`（倒退） | `pose_revert` 或 `pos_reset` |
| `kept`（保留） | 既不是 `lost` 也不是 `reverted` |

整支影片的數值：
- `state_kept_frac`：被追蹤物件中 `kept` 的比例，也就是散佈圖上「狀態保留」那一軸。
- 計數：`n_vanished`、`n_fused`、`n_reverted`、`n_exited`。
- `start_iou_mean`

## 2. 外觀一致性

R-DINO 是物件裁切圖（背景塗白）的 DINOv2-base CLS 特徵的餘弦相似度，和 HECTOR 的做法相同。

- `r_dino_mem_*`：和第 1 回合外觀記憶中的**原始物件裁切**（第 1 回合第 0 格）比較。這是你要求的指標。
- `r_dino_latest_*`：和物件在**第 1 回合最後一格**的裁切比較，也就是它的最新狀態。

兩者都會算第 2 回合中所有看得到的格的平均（`_mean`）和最後一格的值（`_end`）。整支影片的數值，是結束時看得到的物件的平均：`appearance_mem_end_mean` 和 `appearance_latest_end_mean`。

**為什麼要兩個。** 和原始裁切比較的 R-DINO，也會獎勵「**維持原本的姿勢**」。一支正確倒下的骨牌，就算外觀完全沒問題，和它直立時的記憶裁切比，也只有約 0.2–0.5。所以只看 `r_dino_mem` 無法分辨「外觀保住了」和「被拉回原本姿勢」，我們要研究的 trade-off 會被藏在指標裡。`r_dino_latest` 是和同一個物件的最新狀態比，第 1 回合動作造成的姿勢改變就不會被扣分。

## 3. 第 2 回合成功（目標有沒有動）

- 方向用 Goal Force 的慣例：0° 是右，90° 是上。換成畫面座標是 u = (cos θ, −sin θ)。
- d 是目標中心從第 2 回合第 0 格到**最後一次看得到的那格**的位移。所以如果目標是朝正確方向離開畫面，仍然算成功。
- **成功**：|d| ≥ max(15 px, 0.25·√初始面積)，**而且** d 和 u 的夾角 ≤ 45°。
- **目標模式**（goal force 設在最終要移動的物件上）：對那個物件套用同樣的規則。
- **不施力對照組**（`--no_force`）：目標移動小於 15 px 才算成功。
- 如果第 2 回合一開始就看不到目標，算失敗。
- **補充（夜間新增，`camera_check.py`）**：扣除鏡頭運動的版本，用目標位移減掉其他被追蹤物件位移的中位數，需要至少 2 個其他物件。只有在其他物件是靜止時才有效。

## 4. 失敗標籤（以影片為單位，可以重疊）

| 標籤 | 規則 |
|---|---|
| `appearance_deformed`（外觀變形） | 結束時看得到的某個物件，`r_dino_latest_end` < 0.5 |
| `state_lost`（狀態遺失） | `n_vanished` + `n_fused` > 0 |
| `state_reverted`（狀態倒退） | `n_reverted` > 0 |
| `action_failed`（動作失敗） | 不符合目標位移規則 |

這些門檻是經驗值，在跑任何方法之前就定好了，所有方法都一樣。用來檢驗它們的是盲評（§5）。

## 5. 盲評用的關鍵幀拼圖

- 每支影片取 6 張平均分布的影格（第 0、16、32、48、64、80 格），縮成 416×240，排成 2×3，上面**不標方法、檔名或箭頭**。
- 拼圖存在 `outputs/multiturn/blind/<blind_id>.jpg`，`blind_id` 是影片路徑 SHA-1 的前 8 碼。
- 對照表在 `outputs/multiturn/blind/_key_DO_NOT_SHOW_RATERS.jsonl`，不要給評分的人看。
- 每份 `eval.json` 旁邊另存一張 `keyframes.jpg`，給我們自己看。

## 6. 和舊版 `eval_continuity.py` 的差異

| | `eval_continuity.py`（舊） | `evaluate.py`（新） |
|---|---|---|
| 消失 | `VANISH` = 結束時看不到，包括合理離開畫面的物件 | 分開 `vanished` 和 `exited`（mask 碰到邊緣） |
| 融合 | 偵測不到。在 seed 1 那條鏈上，SAM2 在融合的長板上保留了很小的 mask（domino3 面積 ×0.08），所以就算骨牌明顯融合也沒被標出來。 | `fused` = 重疊、塌縮（< 0.3 倍）或膨脹（> 3 倍） |
| 換回合處 | 中心點跳動的 px 數 | mask IoU（`start_iou`），也能抓到形狀和姿勢的變化 |
| 被拉回 | `RESET` 只看非目標物件 | 也看目標物件；往指定方向回到原位的標成 `returned_by_force`（洋芋片診斷需要） |
| 外觀 | 只和記憶比，只看最後一格 | 同時和記憶及最新狀態比，有平均值也有最後一格的值 |
| 成功 | 不量 | 目標位移規則（§3） |
| stride | 2（41 格） | 1（81 格） |

舊的數字（`outputs/multiturn/dominos/eval_t2*.json`）保留不動。夜間報告裡的所有比較都只用 `evaluate.py`。
