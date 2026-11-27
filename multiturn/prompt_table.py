"""List the prompt and force (mode, point, angle, magnitude) of every video in outputs/multiturn/paper_review/,
read from the CSVs actually fed to Goal Force. Writes reports/paper_review_prompts.md.

    venv/bin/python -I multiturn/prompt_table.py
"""
import glob
import json
from pathlib import Path

import pandas as pd

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
    out = ["# paper_review 影片的 prompt 與力（自動產生）", "",
           "由 `multiturn/prompt_table.py` 從實際餵給 Goal Force 的 CSV 讀出。",
           "", "- 角度：0° = 往右、90° = 往上、180° = 往左、270° = 往下。",
           "- 座標：832×480，**y 以左下角為原點**（Goal Force CSV 的規定）。",
           "- goal 模式：指定「目標物體要被往哪推、多大力」，並標出擊球者；direct 模式：直接推施力點上的物體。",
           "- 影片位置：`outputs/multiturn/paper_review/<檔名>`。", ""]

    # 1. paper_<scene>_s<seed>: turn 1 = paper CSV, turn 2 = first design (turn2)
    out += ["## 1. 原論文設定兩回合（`paper_<場景>_s<seed>.mp4`）", "",
            "第 1 回合 = 原論文 CSV（goal，力道 350）；第 2 回合 = 11/26 第一版設計（direct，力道 200）。", ""]
    for v in sorted(REV.glob("paper_*_s[0-9].mp4")):
        scene, seed = v.stem[len("paper_"):].rsplit("_s", 1)
        if scene not in SC:
            continue
        t2 = ROOT / f"datasets/multiturn/paper/{scene}/{scene}_t2_s{seed}.csv"
        out += [f"### {NAMES.get(scene, scene)} — `{v.name}`", "", HDR, row(SC[scene]["csv"], "1"),
                row(t2.relative_to(ROOT), f"2（推 {meta_target(t2.relative_to(ROOT))}）"), ""]

    # 2. dominoes 11/25
    out += ["## 2. 骨牌 11/25 版（`paper_ballthendominos_<第1回合seed>_<版本>_seed<第2回合seed>.mp4`）", "",
            "第 1 回合都是原論文 CSV；A/B 各 3 個第 2 回合 seed（第 1 回合 s0、s1 各一套），C/D 只有 s0 + seed0。", "",
            HDR, row("datasets/examples/multi-object-collision/_ballthendominos_obj1_prompt1.csv", "1（全部）")]
    for tag, f in [("2-A（s0）", "t2A_white_direct_s0"), ("2-A（s1）", "t2A_white_direct_from_s1"),
                   ("2-B（s0）", "t2B_domino_goal_s0"), ("2-B（s1）", "t2B_domino_goal_from_s1"),
                   ("2-C（s0）", "t2C_red_left_s0"), ("2-D（s0）", "t2D_backrow_right_s0")]:
        out.append(row(f"datasets/multiturn/dominos/{f}.csv", tag))
    out += ["", "B 的 CSV 只有目標（一塊倒下的骨牌）沒有擊球者，所以施力點欄顯示 (-1, -1) → 目標。", ""]

    # 3. turn2b (seed 1 done; seed 0 runs tonight as v2)
    out += ["## 3. 兩回合互撞版（`t2b_<場景>_s1.mp4`；今晚的 `t2b_v2_<場景>_s0.mp4`）", "",
            "seed 1：第 1 回合 = 原論文 CSV（力道 350）；第 2 回合 = 互撞／再推一次（direct）。",
            "這些 `t2b_*` 並排影片會在今晚佇列最後的 review_videos 才產生；影片原檔已在 `outputs/multiturn/paper/<場景>/t2b_gf/`。", ""]
    for c in sorted(glob.glob(str(ROOT / "datasets/multiturn/paper/*/*_t2b_s*.csv"))):
        c = Path(c).relative_to(ROOT)
        scene, seed = c.stem.split("_t2b_s")
        out += [f"### {NAMES.get(scene, scene)} — `t2b_{scene}_s{seed}.mp4`", "", HDR, row(SC[scene]["csv"], "1"),
                row(c, f"2（推 {meta_target(c)}）"), ""]
    v2 = sorted(glob.glob(str(ROOT / "datasets/multiturn/paper_v2/*/*.csv")))
    out += ["### 今晚 seed 0（v2：第 1 回合鏡頭固定、力道 150）", ""]
    if v2:
        out += ["已產生的 CSV：", "", HDR] + [row(Path(c).relative_to(ROOT), Path(c).stem) for c in v2] + [""]
    out += ["尚未跑到的場景，第 2 回合依 `multiturn/paper_scenes.json` 的 turn2b 設定；`toward:` 的實際角度要等第 1 回合追蹤完才算得出來：", "",
            "| 場景 | 第 1 回合 | 第 2 回合推誰 | 角度 | 力道 | 第 2 回合文字 prompt |", "|---|---|---|---|---|---|"]
    for s, d in SC.items():
        if s.startswith("_"):
            continue
        t = d["turn2b"]
        out.append(f"| {NAMES.get(s, s)} | 原論文 prompt + The camera is static.，goal 力道 150 | {t['target']} | {t['angle']} | {t['force']} | {t['caption']} |")
    out.append("")

    # 4. chains
    out += ["## 4. 實驗 A：5 回合互撞（`chain_<場景>.mp4`）", ""]
    for d in sorted(glob.glob(str(ROOT / "datasets/multiturn/chain/*"))):
        cs = sorted(glob.glob(f"{d}/*_c[0-9].csv"))
        if not cs:
            continue
        s = Path(d).name
        nv = len(glob.glob(str(ROOT / f"outputs/multiturn/chain/{s}/gf/*seed_0.mp4")))
        if nv == 0:
            continue  # never run (only a dry-run CSV)
        cs = [c for c in cs if int(Path(c).stem.rsplit("_c", 1)[1]) <= nv + 1]
        done = (ROOT / f"outputs/multiturn/chain/{s}/chain_eval.json").exists()
        out += [f"### {NAMES.get(s, s)} — `chain_{s}.mp4`" + ("" if done else f"（進行中：已生成 {nv} 回合）"), "", HDR] + \
               [row(Path(c).relative_to(ROOT), Path(c).stem.rsplit("_c", 1)[1]) for c in cs] + [""]
    p = ROOT / "reports/paper_review_prompts.md"
    p.write_text("\n".join(out))
    print("wrote", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
