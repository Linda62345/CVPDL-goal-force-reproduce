# CLAUDE.md

研究題目：延伸 Goal Force，以物件狀態記憶改善多回合互動影片的連續性。

**開始工作前先讀 `reports/handoff_2026-11-27.md`**（研究背景、至今結果、檔案位置、未完成工作、注意事項）。

## 使用者規矩
- 一律用繁體中文回答；報告以中文為主（程式碼、路徑、術語可英文）。
- 用虛擬環境（`venv/`、`imagegen/venv/`），只在這個 repo 資料夾底下操作；cache 放 repo 內（`HF_HOME=imagegen/hf_cache`）。
- 不要刪檔、不要 pip install／升級套件、不要 git push（除非使用者明說）、不要改 `photos/` 和既有的 outputs；新結果放新資料夾。
- 長時間工作用 nohup、可續跑，log 放 `logs/`；單支失敗重試一次，再失敗就跳過並記錄。
- GPU 一次只跑一件。
- Goal Force CSV 的 y 座標是左下角原點。
