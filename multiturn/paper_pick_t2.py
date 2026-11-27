"""Pick the turn-2 action for one paper scene: the planned target if visible in the turn-1 last frame, else the first
visible fallback. Writes <t1_state_dir>/<key>_choice.json and prints TARGET<TAB>ANGLE<TAB>FORCE<TAB>CAPTION (exit 3 if none).
Angle may be a number or 'toward:<obj>' / 'toward:nearest' / 'toward:center' (direction from the target's centroid at the
end of turn 1 to that object's centroid / the nearest other visible object / the image centre).
    venv/bin/python -I multiturn/paper_pick_t2.py SCENE STATE_JSON [turn2|turn2b|turn2c]
turn2c (goal mode) prints a 5th field PROJECTILE.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
scene, state = sys.argv[1], sys.argv[2]
key = sys.argv[3] if len(sys.argv) > 3 else "turn2"
s = json.load(open(ROOT / "multiturn/paper_scenes.json"))[scene]
st = json.load(open(state))
objs = st["objects"]
plan = s[key]
cands = [dict(plan, fallback=False)] + [dict(f, force=plan["force"], fallback=True) for f in s.get(key + "_fallback", [])]
vis = {n: bool(o["last"]["visible"]) for n, o in objs.items()}
# 11/27: SAM2 can collapse two objects onto the same mask (bulb_tool seed 0: bulb_left and bulb_right both ended on the
# left bulb, so turn 2 pushed the wrong bulb). Two visible objects whose last centroids are < 12 px apart are treated
# as lost (not visible), so the wrong object is never pushed.
merged = set()
for a in objs:
    for b in objs:
        if a < b and vis[a] and vis[b] and math.dist(objs[a]["last"]["centroid"], objs[b]["last"]["centroid"]) < 12:
            merged |= {a, b}
for n in merged:
    vis[n] = False
cen = {n: o["last"]["centroid"] for n, o in objs.items() if vis[n]}


def resolve(c):
    a = c["angle"]
    if not (isinstance(a, str) and a.startswith("toward:")):
        return c
    to = a.split(":", 1)[1]
    x, y = cen[c["target"]]
    if to == "center":
        tx, ty = st["W"] / 2, st["H"] / 2
    elif to == "nearest":
        others = [n for n in cen if n != c["target"]]
        if not others:
            return None
        o = min(others, key=lambda n: math.dist(cen[n], (x, y)))
        tx, ty = cen[o]; c = dict(c, toward=o)
    else:
        if to not in cen:
            return None
        tx, ty = cen[to]
    return dict(c, angle=round(math.degrees(math.atan2(-(ty - y), tx - x)) % 360), angle_rule=a)


def resolve_c(c):
    """turn2c (goal mode): projectile causes the motion, target is pushed. Returns c with concrete target/angle or None."""
    prj = c["projectile"]
    if not vis.get(prj):
        return None
    tg = c["target"]
    if tg == "nearest":
        others = [n for n in cen if n != prj]
        if not others:
            return None
        tg = min(others, key=lambda n: math.dist(cen[n], cen[prj]))
    if not vis.get(tg):
        return None
    a = c["angle"]
    if a == "away" and tg != prj:
        (x, y), (tx, ty) = cen[prj], cen[tg]
    elif a == "toward:center":
        (x, y), (tx, ty) = cen[tg], (st["W"] / 2, st["H"] / 2)
    elif isinstance(a, (int, float)):
        return dict(c, target=tg)
    else:
        return None
    return dict(c, target=tg, angle=round(math.degrees(math.atan2(-(ty - y), tx - x)) % 360), angle_rule=a)


pick = None
if key == "turn2c":
    for c in cands:
        pick = resolve_c(c)
        if pick:
            break
for c in ([] if key == "turn2c" else cands):
    if vis.get(c["target"]):
        pick = resolve(c)
        if pick:
            break
json.dump({"key": key, "planned": plan["target"], "visible_last": vis, "chosen": pick},
          open(Path(state).parent / ("t2_choice.json" if key == "turn2" else f"{key}_choice.json"), "w"), indent=1)
if pick is None:
    print(f"no visible {key} target; visible_last={vis}", file=sys.stderr)
    sys.exit(3)
if key == "turn2c":
    print(f"{pick['target']}\t{pick['angle']}\t{pick['force']}\t{pick['caption']}\t{pick['projectile']}")
else:
    print(f"{pick['target']}\t{pick['angle']}\t{pick['force']}\t{pick['caption']}")
