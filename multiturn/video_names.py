"""Readable names for the videos published in reports/videos/ (11/27, for the team).

outputs/multiturn/paper_review/ keeps the original (script) names; reports/videos/ holds copies under readable names.
The letter prefix sorts the files in the order we recommend watching them:
  A_ 5-turn chains (experiment A)          chain_<scene>.mp4
  B_ two turns, causal goal-mode turn 2    t2c[_v2]_<scene>_s<k>.mp4
  C_ two turns, direct-push turn 2         t2b[_v2]_<scene>_s<k>.mp4
  D_ two turns, first turn-2 design        paper_<scene>_s<k>.mp4 / v2_<scene>_s<k>.mp4
  E_ dominoes, 11/25 designs A-D           paper_ballthendominos_s<a>_<X>_seed<b>.mp4
"""
import re

SCENE_EN = {"cantaloupes": "cantaloupes", "pendulum": "pendulum", "paw_tool1": "chess_dogpaw", "toycar": "toycar_hand",
            "soccer_tool": "soccer_kick", "paw_tool2": "ball_dogpaw", "paw_tool3": "ball_catpaw", "bulb_tool": "bulbs_hand",
            "tennis": "tennis", "pool_tool": "pool_cue", "golf": "golf_club", "ballthendominos": "dominoes"}
DOMINO_DESIGN = {"A": "white_ball_again", "B": "goal_on_fallen_domino", "C": "red_ball_back", "D": "push_backrow_domino"}
INVALID = {"paper_bulb_tool_s0"}  # SAM2 merged both bulbs -> turn-2 force on the wrong bulb


def pub_name(src):
    """Script name (e.g. 't2c_v2_cantaloupes_s0.mp4') -> readable name; None if not a known pattern."""
    stem, ext = src.rsplit(".", 1)
    bad = "_INVALID" if stem in INVALID else ""
    m = re.fullmatch(r"chain_(.+?)(_frames)?", stem)
    if m:
        return f"A_5turns_{SCENE_EN.get(m[1], m[1])}{m[2] or ''}.{ext}"
    m = re.fullmatch(r"paper_ballthendominos_s(\d)_([A-D])_seed(\d)", stem)
    if m:
        return f"E_dominoes_1125_t1seed{m[1]}_{m[2]}_{DOMINO_DESIGN[m[2]]}_t2seed{m[3]}.{ext}"
    m = re.fullmatch(r"(t2c|t2b|paper|v2)(_v2)?_(.+)_s(\d)", stem)
    if m:
        kind, v2, scene, seed = m[1], m[2] or m[1] == "v2", m[3], m[4]
        head = {"t2c": "B_2turns_causal", "t2b": "C_2turns_directpush", "paper": "D_2turns_firstdesign",
                "v2": "D_2turns_firstdesign"}[kind]
        return f"{head}{'_lowforce' if v2 else ''}_{SCENE_EN.get(scene, scene)}_seed{seed}{bad}.{ext}"
    return None
