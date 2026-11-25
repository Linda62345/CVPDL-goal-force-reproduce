"""Test 2 of lora_plan.md: re-repair the overnight turn-2 videos with `nolora` and `lora` (no state rule) and score them
with the same evaluate.py. Uses the overnight baseline tracks and captions. Resumable (skips finished outputs).

    python3 multiturn/lora_test2.py --lora outputs/lora/vace_appearance/step-3000.safetensors
Outputs: outputs/multiturn/lora_<exp>/repair/<run>/{nolora,lora}.mp4 + compare4.jpg, evals in outputs/multiturn/lora_<exp>/eval/
"""
import argparse
import glob
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPS = ["exp8", "exp10", "ph_chips", "ph_coffee", "ph_bottle", "ph_books_pull", "ph_books_push"]


def run(cmd, env=None):
    print("+", " ".join(cmd)[:200], flush=True)
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lora", required=True)
    a = ap.parse_args()
    env = dict(os.environ, HF_HOME=str(ROOT / "imagegen/hf_cache"))
    fails = []
    for exp in EXPS:
        for ev in sorted(glob.glob(str(ROOT / f"outputs/multiturn/{exp}/eval/baseline/*/eval.json"))):
            e = json.load(open(ev))
            rid = Path(ev).parent.name
            meta = ROOT / f"outputs/multiturn/{exp}/repair/{rid}/full_meta.json"
            cap = json.load(open(meta))["prompt"]
            out = ROOT / f"outputs/multiturn/lora_{exp}/repair/{rid}"
            for cond in ["nolora", "lora"]:
                cmd = ["venv/bin/python", "-I", "multiturn/memory_repair.py", "--video", e["video"],
                       "--track", str(Path(ev).parent / "track"), "--prev_state", e["prev_state"],
                       "--target", e["target"]["name"], "--cond", cond, "--out", str(out), "--prompt", cap]
                if cond == "lora":
                    cmd += ["--lora", a.lora]
                if run(cmd, env) != 0:
                    fails.append((exp, rid, cond, "repair"))
                    continue
                if run(["imagegen/venv/bin/python", "-I", "multiturn/evaluate.py", "--video", str(out / f"{cond}.mp4"),
                        "--prev_state", e["prev_state"], "--target", e["target"]["name"], "--angle", str(e["target"]["angle"]),
                        "--method", cond, "--scene", e["scene"],
                        "--out", str(ROOT / f"outputs/multiturn/lora_{exp}/eval/{cond}/{rid}")], env) != 0:
                    fails.append((exp, rid, cond, "eval"))
            full = ROOT / f"outputs/multiturn/{exp}/repair/{rid}/full.mp4"
            vids = [e["video"], str(full), str(out / "nolora.mp4"), str(out / "lora.mp4")]
            if all(Path(v).exists() for v in vids):
                run(["imagegen/venv/bin/python", "-I", "multiturn/compare3.py", "--videos", *vids,
                     "--labels", "baseline", "full", "nolora", "lora", "--out", str(out / "compare4.jpg")], env)
    print("FAILS", fails)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
