"""List the prompt and force (mode, point, angle, magnitude) of every published video (reports/videos/, readable names
from multiturn/video_names.py; script names in outputs/multiturn/paper_review/),
read from the CSVs actually fed to Goal Force. Writes reports/paper_review_prompts.md.

    venv/bin/python -I multiturn/prompt_table.py
"""
import glob
import json
from pathlib import Path

import pandas as pd
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from video_names import pub_name  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "outputs/multiturn/paper_review"
SC = json.load(open(ROOT / "multiturn/paper_scenes.json"))
NAMES = {"cantaloupes": "哈密瓜", "pendulum": "鐘擺", "paw_tool1": "西洋棋（狗）", "toycar": "玩具車", "soccer_tool": "足球",
         "paw_tool2": "藍球（狗）", "paw_tool3": "紅球（貓）", "bulb_tool": "燈泡", "tennis": "網球", "pool_tool": "撞球",
         "golf": "高爾夫", "ballthendominos": "骨牌"}


def row(csv, who=""):
    r = pd.read_csv(ROOT / csv).iloc[0]
    if r["target_indirect_force_magnitude"] > 0:      # goal mode
        mode = "goal"
        pt = f"擊球者 ({int(r.projectile_coordx)}, {int(r.projectile_coordy)}) → 目標 ({int(r.target_coordx)}, {int(r.target_coordy)})"
        ang, f = r.target_indirect_force_angle, r.target_indirect_force_magnitude
    else:
        mode = "direct"
        pt = f"({int(r.projectile_coordx)}, {int(r.projectile_coordy)})"
        ang, f = r.projectile_force_angle, r.projectile_force_magnitude
    return f"| {who} | {mode} | {pt} | {ang:g}° | {f:g} | {r.caption} |"


HDR = "| 回合 | 模式 | 施力點（CSV 座標，左下角原點） | 角度 | 力道 | 文字 prompt |\n|---|---|---|---|---|---|"


def meta_target(csv):
    m = Path(str(ROOT / csv).replace(".csv", "_meta.json"))
    return json.load(open(m))["target"] if m.exists() else ""


def main():
    URL = "https://github.com/Linda62345/CVPDL-goal-force-reproduce/blob/appearance-multiturn/reports/videos/"
    PUB = ROOT / "reports/videos"

    def title(zh, src):
        """Heading with the published (readable) name linked; script name in small print."""
        n = pub_name(src)
        if n and (PUB / n).exists():
            return f"### {zh} — [`{n}`]({URL}{n}?raw=true)　<sub>原檔 `{src}`</sub>"
        return f"### {zh} — `{n or src}`（尚未產生）　<sub>原檔 `{src}`</sub>"

    out = ["# 每支影片的 prompt 與力（自動產生）", "",
           "由 `multiturn/prompt_table.py` 從實際餵給 Goal Force 的 CSV 讀出。影片總覽見 [`videos.md`](videos.md)；"
           "標題是 `reports/videos/` 裡的檔名（可點），後面小字是 `outputs/multiturn/paper_review/` 裡的原檔名。",
           "", "- 角度：0° = 往右、90° = 往上、180° = 往左、270° = 往下。",
           "- 座標：832×480，**y 以左下角為原點**（Goal Force CSV 的規定）。",
           "- goal 模式：指定「目標物體要被往哪推、多大力」，並標出造成動作的物體（擊球者）；擊球者 = 目標時代表施力者在畫面外（手、爪子），和論文一樣。direct 模式：直接推施力點上的物體。", ""]

    # A. chains
    out += ["## A. 實驗 A：5 回合互撞", ""]
    for d in sorted(glob.glob(str(ROOT / "datasets/multiturn/chain/*"))):
        cs = sorted(glob.glob(f"{d}/*_c[0-9].csv"))
        s = Path(d).name
        nv = len(glob.glob(str(ROOT / f"outputs/multiturn/chain/{s}/gf/*seed_0.mp4")))
        if not cs or nv == 0:
            continue  # never run (only a dry-run CSV)
        cs = [c for c in cs if int(Path(c).stem.rsplit("_c", 1)[1]) <= nv + 1]
        done = (ROOT / f"outputs/multiturn/chain/{s}/chain_eval.json").exists()
        out += [title(NAMES.get(s, s), f"chain_{s}.mp4") + ("" if done else f"（進行中：已生成 {nv} 回合）"), "", HDR] + \
               [row(Path(c).relative_to(ROOT), Path(c).stem.rsplit("_c", 1)[1]) for c in cs] + [""]

    # B. turn2c (goal mode, causal), turn 1 = v2 (camera static, force 150)
    out += ["## B. 新版兩回合：照論文的因果寫法（turn2c）", "",
            "第 1 回合 = 原論文 CSV + 「The camera is static.」，goal 力道 150；第 2 回合 = goal 模式，文字寫明原因。", ""]
    done_c = set()
    for c in sorted(glob.glob(str(ROOT / "datasets/multiturn/paper_v2/*/*_t2c_s*.csv"))):
        c = Path(c).relative_to(ROOT)
        scene, seed = c.stem.split("_t2c_s")
        t1 = sorted(glob.glob(str(ROOT / f"datasets/multiturn/paper_v2/{scene}/*_v2.csv")))
        done_c.add(scene)
        out += [title(NAMES.get(scene, scene), f"t2c_v2_{scene}_s{seed}.mp4"), "", HDR,
                row(Path(t1[0]).relative_to(ROOT), "1") if t1 else "| 1 | | | | | |",
                row(c, f"2（{json.load(open(ROOT / str(c).replace('.csv', '_meta.json'))).get('projectile', '')} → {meta_target(c)}）"), ""]
    rest = [s for s in SC if not s.startswith("_") and "turn2c" in SC[s] and s not in done_c]
    if rest:
        out += ["還沒跑到的場景（設定見 `multiturn/paper_scenes.json` 的 turn2c；`away` = 從造成者指向被推物體的方向，實際角度要等第 1 回合追蹤完才算得出來）：", "",
                "| 場景 | 誰造成 → 誰被推 | 角度 | 力道 | 第 2 回合文字 prompt |", "|---|---|---|---|---|"]
        for s in rest:
            t = SC[s]["turn2c"]
            out.append(f"| {NAMES.get(s, s)} | {t['projectile']} → {t['target']} | {t['angle']} | {t['force']} | {t['caption']} |")
        out.append("")

    # C. turn2b (direct push), seed 1
    out += ["## C. 互撞版兩回合（turn2b，direct 模式）", "",
            "第 1 回合 = 原論文 CSV（力道 350）；第 2 回合 = 直接推物體去撞另一個（或再推一次）。", ""]
    for c in sorted(glob.glob(str(ROOT / "datasets/multiturn/paper/*/*_t2b_s*.csv"))):
        c = Path(c).relative_to(ROOT)
        scene, seed = c.stem.split("_t2b_s")
        out += [title(NAMES.get(scene, scene), f"t2b_{scene}_s{seed}.mp4"), "", HDR, row(SC[scene]["csv"], "1"),
                row(c, f"2（推 {meta_target(c)}）"), ""]

    # D. first design
    out += ["## D. 第一版兩回合（turn2，11/26）", "",
            "第 1 回合 = 原論文 CSV（goal，力道 350）；第 2 回合 = direct，力道 200。", ""]
    for v in sorted(REV.glob("paper_*_s[0-9].mp4")):
        scene, seed = v.stem[len("paper_"):].rsplit("_s", 1)
        if scene not in SC:
            continue
        t2 = ROOT / f"datasets/multiturn/paper/{scene}/{scene}_t2_s{seed}.csv"
        out += [title(NAMES.get(scene, scene), v.name), "", HDR, row(SC[scene]["csv"], "1"),
                row(t2.relative_to(ROOT), f"2（推 {meta_target(t2.relative_to(ROOT))}）"), ""]

    # E. dominoes 11/25
    out += ["## E. 骨牌 11/25 版（`E_dominoes_1125_t1seed<a>_<版本>_t2seed<b>.mp4`）", "",
            "第 1 回合都是原論文 CSV；A/B 各 3 個第 2 回合 seed（第 1 回合 seed 0、1 各一套），C/D 只有第 1 回合 seed 0 + 第 2 回合 seed 0。", "",
            HDR, row("datasets/examples/multi-object-collision/_ballthendominos_obj1_prompt1.csv", "1（全部）")]
    for tag, f in [("2-A（t1seed0）", "t2A_white_direct_s0"), ("2-A（t1seed1）", "t2A_white_direct_from_s1"),
                   ("2-B（t1seed0）", "t2B_domino_goal_s0"), ("2-B（t1seed1）", "t2B_domino_goal_from_s1"),
                   ("2-C（t1seed0）", "t2C_red_left_s0"), ("2-D（t1seed0）", "t2D_backrow_right_s0")]:
        out.append(row(f"datasets/multiturn/dominos/{f}.csv", tag))
    out += ["", "B 的 CSV 只有目標（一塊倒下的骨牌）沒有擊球者，所以施力點欄顯示 (-1, -1) → 目標。", ""]
    p = ROOT / "reports/paper_review_prompts.md"
    p.write_text("\n".join(out))
    print("wrote", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
