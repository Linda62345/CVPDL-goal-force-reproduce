# 標註說明（pilot_labels.csv）

每一列 = 一支影片。看 `video_with_arrow`（有綠/紅色力箭頭）或 `video`，填右邊 6 欄。
**先自己標完，再打開 `claude_initial_guess.csv` 比較**（避免被影響）。

## 欄位
| 欄位 | 填法 | 意思 |
|---|---|---|
| direction_ok | 1 / 0 | 物體主要的移動方向是否符合指定角度 |
| goal_ok | 1 / 0 | 是否達成該場景的任務目標（見下表） |
| artifact | 1 / 0 | 是否有明顯生成瑕疵：物體消失/分裂/變形、多出物體、亂碼文字等 |
| usable | 1 / 0 | **整體能不能收下**（研究裡的「演對」）。建議：direction_ok=1 且 goal_ok=1 且無嚴重瑕疵 |
| failure_type | 文字 | usable=0 時填主要原因，盡量用下方代碼 |
| notes | 文字 | 任何補充 |

## 各場景的 goal_ok 標準
| 場景 | goal_ok = 1 的條件 |
|---|---|
| mug（左推/右推） | 杯子朝指定方向移動後，**仍直立且留在架子上** |
| daruma（上/左上/右上） | 達摩**明顯離地**，且飛行軌跡大致沿指定方向 |
| bowling（往前） | 球往球道前方滾並撞擊，**瓶子全倒** |

## failure_type 代碼
`wrong_dir`（方向錯）· `too_weak`（幾乎沒動/力道不足）· `fell_off`（掉下平台）· `left_frame`（飛出畫面）· `tipped`（翻倒）· `partial_strike`（沒全倒）· `object_vanished`（物體消失）· `duplicate_obj`（物體分裂/多出）· `deformed`（變形）· `other`

## 注意
- 標準可以改，但改了要**所有影片用同一套**，並更新這份文件。
- 不確定的填你的最佳判斷，在 notes 寫「不確定」。
