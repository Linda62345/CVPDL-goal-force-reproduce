"""Camera-motion check for the target-motion rule (metrics.md §3 addendum).
Relative displacement = target displacement - median displacement of the OTHER tracked objects that are visible on the
first and last frame (needs >= 2 such objects; otherwise 'n/a'). Same thresholds as evaluate.py.
    python3 multiturn/camera_check.py <state.json> <target> <angle>        (one turn)
    python3 multiturn/camera_check.py --all                                (every turn-2 eval under outputs/multiturn/*/eval)
"""
import glob, json, math, statistics, sys

def check(state_path, target, angle):
    st = json.load(open(state_path))
    def disp(o):
        tr = [p for p in o["traj"] if p is not None]
        if not tr or o["traj"][0] is None:
            return None
        return (tr[-1][0] - tr[0][0], tr[-1][1] - tr[0][1])
    t = st["objects"].get(target)
    if t is None or disp(t) is None:
        return {"rel_success": None, "reason": "target not tracked"}
    others = [disp(o) for n, o in st["objects"].items() if n != target and o["traj"][0] is not None and o["traj"][-1] is not None]
    others = [d for d in others if d is not None]
    if len(others) < 2:
        return {"rel_success": None, "reason": f"only {len(others)} reference objects", "abs_disp": disp(t)}
    cam = (statistics.median(d[0] for d in others), statistics.median(d[1] for d in others))
    d = disp(t); r = (d[0] - cam[0], d[1] - cam[1]); mag = math.hypot(*r)
    u = (math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
    ang = math.degrees(math.acos(max(-1, min(1, (r[0] * u[0] + r[1] * u[1]) / (mag + 1e-9))))) if mag > 0 else 180
    need = max(15, 0.25 * math.sqrt(t["first"]["area"]))
    return {"rel_success": bool(mag >= need and ang <= 45), "camera": [round(c, 1) for c in cam], "rel_disp": [round(x, 1) for x in r],
            "angle_err": round(ang, 1), "need_px": round(need, 1)}

if __name__ == "__main__":
    if sys.argv[1] == "--all":
        out = []
        for p in sorted(glob.glob("outputs/multiturn/*/eval/*/*/eval.json")):
            e = json.load(open(p))
            c = check(p.replace("eval.json", "track/state.json"), e["target"]["name"], e["target"]["angle"])
            if e["target"].get("no_force"):
                c = {"rel_success": None, "reason": "no-force control"}
            out.append({"eval": p, "method": e["method"], "scene": e["scene"], "abs_success": e["target"]["success"], **c})
        json.dump(out, open("reports/overnight_assets/camera_check.json", "w"), indent=1)
        for o in out:
            print(o["scene"], o["method"], o["eval"].split("/")[-2], "abs", o["abs_success"], "rel", o["rel_success"], o.get("camera", o.get("reason")))
    else:
        print(json.dumps(check(sys.argv[1], sys.argv[2], float(sys.argv[3])), indent=1))
