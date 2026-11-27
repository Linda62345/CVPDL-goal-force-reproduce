"""Copy the review videos to reports/videos/ under readable names (multiturn/video_names.py) and rewrite reports/videos.md.
Old script-named copies already in reports/videos/ are renamed with `git mv` (so links change, history is kept).
outputs/ is never modified.

    venv/bin/python -I multiturn/publish_videos.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from video_names import SCENE_EN, pub_name  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/multiturn/paper_review"
DST = ROOT / "reports/videos"
URL = "https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/"
ZH = {"cantaloupes": "哈密瓜", "pendulum": "鐘擺", "chess_dogpaw": "西洋棋（狗爪）", "toycar_hand": "玩具車（手）",
      "soccer_kick": "足球（腳）", "ball_dogpaw": "藍球（狗爪）", "ball_catpaw": "紅球（貓爪）", "bulbs_hand": "燈泡（手）",
      "tennis": "網球", "pool_cue": "撞球（球桿）", "golf_club": "高爾夫（球桿）", "dominoes": "骨牌"}
NOTES = {  # what to look at (filled in after watching)
    "A_5turns_cantaloupes.mp4": "**外觀漂移**：物理大致合理，但第 3 回合起瓜變橢圓、網紋消失、長蒂頭；被推的瓜外觀分數 0.63→0.05",
    "A_5turns_chess_dogpaw.mp4": "**物體消失／出現**：黑棋第 3 回合起消失或被推出棋盤，第 5 回合又冒出；棋盤和狗爪穩定",
    "B_2turns_causal_lowforce_cantaloupes_seed0.mp4": "右瓜撞回左瓜、左瓜被撞往左：**因果正確**；但瓜已開始變黃、變橢圓",
    "B_2turns_causal_lowforce_pendulum_seed0.mp4": "第 1 回合撞倒方塊；第 2 回合方塊在最右邊，**鐘擺搆不到**，方塊沒動",
    "D_2turns_firstdesign_bulbs_hand_seed0_INVALID.mp4": "**作廢**：追蹤把兩個燈泡當成同一個，力推在錯的燈泡上",
}


def publish():
    DST.mkdir(parents=True, exist_ok=True)
    srcs = sorted(SRC.glob("*.mp4")) + sorted((ROOT / "outputs/multiturn/chain").glob("*/frames_first_mid_last.jpg"))
    for s in srcs:
        name = f"chain_{s.parent.name}_frames.jpg" if s.suffix == ".jpg" else s.name
        new = pub_name(name)
        if new is None:
            continue
        old = DST / name
        if old.exists() and not (DST / new).exists():
            subprocess.run(["git", "mv", str(old.relative_to(ROOT)), f"reports/videos/{new}"], cwd=ROOT, check=True)
        elif not (DST / new).exists():
            shutil.copy2(s, DST / new)


def link(f):
    return f"[{f}]({URL}{f}?raw=true)"


def scene_of(f, head):
    rest = f[len(head):].rsplit("_seed", 1)
    return rest[0].lstrip("_"), rest[1].split(".")[0].replace("_INVALID", "") if len(rest) > 1 else ""


def index():
    V = sorted(p.name for p in DST.glob("*.mp4"))
    o = ["# 影片總覽（給組員看）", "",
         "點連結會用瀏覽器直接播放。全部是 Goal Force（Wan2.2-I2V-A14B + ControlNet）在**原論文範例照片**上生成。",
         "每支影片的 prompt、施力點、角度、力道見 [`paper_review_prompts.md`](paper_review_prompts.md)；研究背景與進度見 [`handoff_2026-11-27.md`](handoff_2026-11-27.md)。",
         "", "檔名開頭字母 = 建議觀看順序：**A** 5 回合 → **B** 新版兩回合（照論文的因果寫法）→ **C** 互撞版兩回合 → **D** 第一版兩回合 → **E** 骨牌 11/25 版。"
         "`lowforce` = 第 1 回合鏡頭固定、力道 150（原論文 350）；`seed` = 隨機種子。", ""]

    def table(title, desc, head, cols=("場景", "seed")):
        rows = [f for f in V if f.startswith(head)]
        if not rows:
            return
        o.extend([f"## {title}", "", desc, "", "| 場景 | seed | 影片 | 看什麼 |", "|---|---|---|---|"])
        for f in rows:
            sc, sd = scene_of(f, head)
            sc = sc.replace("lowforce_", "")
            o.append(f"| {ZH.get(sc, sc)} | {sd} | {link(f)} | {NOTES.get(f, '')} |")
        o.append("")

    o += ["## A. 實驗 A：同一張照片連續 5 回合互撞", "", "左 = 原照片，右 = 第 1→5 回合連續播放。", "",
          "| 場景 | 影片 | 看什麼 |", "|---|---|---|"]
    for f in V:
        if f.startswith("A_5turns_"):
            sc = f[len("A_5turns_"):-4]
            o.append(f"| {ZH.get(sc, sc)} | {link(f)} | {NOTES.get(f, '')} |")
    o.append("")
    for j in sorted(DST.glob("A_5turns_*_frames.jpg")):
        sc = j.name[len("A_5turns_"):-len("_frames.jpg")]
        o += [f"{ZH.get(sc, sc)}：每回合開頭／中間／結尾（一列一回合）", "", f"![{sc}](videos/{j.name})", ""]
    lay = "左 = 原照片，中 = baseline（直接拿上一回合最後一幀生成），右 = LoRA 外觀修補；先播第 1 回合（中、右相同）再播第 2 回合。"
    table("B. 新版兩回合：照論文的因果寫法（11/27）",
          "第 2 回合用 goal 模式，文字寫明誰造成動作（手、爪子、球桿、另一顆球）。" + lay, "B_2turns_causal")
    table("C. 互撞版兩回合（direct 模式，力道 100–150）", "第 2 回合用看不見的力直接推物體去撞另一個（或再推一次）。" + lay,
          "C_2turns_directpush")
    table("D. 第一版兩回合（11/26，direct 模式，力道 200）", "第 2 回合固定方向推一次。" + lay, "D_2turns_firstdesign")
    o += ["## E. 骨牌 11/25 版（第 2 回合四種設計）", "",
          "`t1seed` = 第 1 回合 seed，`t2seed` = 第 2 回合 seed。A = 白球再撞一次；B = goal 指定倒下的骨牌；C = 紅球撞回白球；D = 推後排站著的骨牌。" + lay, "",
          "| 影片 |", "|---|"] + [f"| {link(f)} |" for f in V if f.startswith("E_dominoes")] + [""]
    (ROOT / "reports/videos.md").write_text("\n".join(o))


if __name__ == "__main__":
    publish()
    index()
    print("published", len(list(DST.glob("*.mp4"))), "videos; wrote reports/videos.md")
