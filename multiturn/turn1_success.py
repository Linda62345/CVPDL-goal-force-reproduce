"""Turn-1 success with the same rule as evaluate.py §3 (target centroid displacement first->last visible frame,
>= max(15px, 0.25*sqrt(area0)) and within 45 deg of the commanded direction). Also reports the motion of the
other tracked objects (to spot camera motion: everything moving together).
    python3 multiturn/turn1_success.py --state outputs/multiturn/photos/<s>/t1_s0/state.json --target X --angle A"""
import argparse, json, math
ap = argparse.ArgumentParser(); ap.add_argument("--state"); ap.add_argument("--target"); ap.add_argument("--angle", type=float)
a = ap.parse_args()
st = json.load(open(a.state)); res = {}
for n, o in st["objects"].items():
    tr = [p for p in o["traj"] if p is not None]
    if not tr:
        res[n] = None; continue
    d = (tr[-1][0] - tr[0][0], tr[-1][1] - tr[0][1]); mag = math.hypot(*d)
    u = (math.cos(math.radians(a.angle)), -math.sin(math.radians(a.angle)))
    ang = math.degrees(math.acos(max(-1, min(1, (d[0] * u[0] + d[1] * u[1]) / (mag + 1e-9))))) if mag > 0 else None
    need = max(15, 0.25 * math.sqrt(o["first"]["area"])) if o["first"]["visible"] else 15
    res[n] = {"dx": round(d[0], 1), "dy": round(d[1], 1), "mag": round(mag, 1), "angle_err": None if ang is None else round(ang, 1),
              "need_px": round(need, 1), "visible": f'{o["visible_frames"]}/{st["T"]}'}
t = res[a.target]
ok = bool(t and t["mag"] >= t["need_px"] and t["angle_err"] is not None and t["angle_err"] <= 45)
print(json.dumps({"target": a.target, "success": ok, "objects": res}, indent=1))
