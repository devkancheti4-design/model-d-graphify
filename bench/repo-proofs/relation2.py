"""Exploratory follow-up to RELATION_METHOD.md (chance-relative r did not separate). For each question: the cue's
absolute agreement a_cue, its margin over the best code text (a_cue - own_max) and the lead; precision of fired
learned matches by threshold, chosen on SigNoz, checked on Plane."""
import json, os, sys
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np
from ocm.server import Workspace
W = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(f"{W}/relation_rows.json"))
by = {}
for name in ("plane", "signoz"):
    D = json.load(open(f"{W}/{name}_set.json")); item = {f"{it['issue']}#{it['pr']}": it for it in D["items"]}
    wl = Workspace(f"{W}/ws_learn/{name}"); pool = np.flatnonzero(wl.code)
    for r in rows:
        if r["repo"] != name:
            continue
        q = item[r["id"]]["q_body" if r["kind"] == "paraphrase" else "q_title"]
        strong, weak, own, cue = wl.lanes.scores(q)
        sp, op, cp = strong[pool], own[pool], cue[pool]
        r["a_cue"] = int(cp.max()); r["own_max"] = int(op.max()); r["cue_over_own"] = int(cp.max()) - int(op.max())
json.dump(rows, open(f"{W}/relation_rows.json", "w"), indent=1)
fired = [r for r in rows if r["fired"]]
for kind in ("paraphrase", "new"):
    f = [r for r in fired if r["kind"] == kind]
    print(f"fired on {kind}: {len(f)}, learned code right {sum(r['learned_right'] for r in f)}"
          f"; median a_cue {np.median([r['a_cue'] for r in f]):.0f}, median cue-over-own {np.median([r['cue_over_own'] for r in f]):.0f}")
print("\nthreshold on cue-over-own (bits), chosen on SigNoz -> checked on Plane: fired kept, right among kept")
for t in (0, 10, 20, 30, 40, 50, 60, 80):
    out = []
    for name in ("signoz", "plane"):
        f = [r for r in fired if r["repo"] == name]; k = [r for r in f if r["cue_over_own"] >= t]
        out.append(f"{name}: kept {len(k):>2}/{len(f):<2} right {sum(r['learned_right'] for r in k):>2} ({(sum(r['learned_right'] for r in k)/len(k) if k else 0):.0%}),"
                   f" wrong dropped {sum(not r['learned_right'] for r in f if r['cue_over_own'] < t):>2}, right dropped {sum(r['learned_right'] for r in f if r['cue_over_own'] < t):>2}")
    print(f"  >= {t:>3}: " + " | ".join(out))
print("\nthreshold on a_cue (absolute bits of 1,024)")
for t in (600, 650, 700, 750, 800):
    out = []
    for name in ("signoz", "plane"):
        f = [r for r in fired if r["repo"] == name]; k = [r for r in f if r["a_cue"] >= t]
        out.append(f"{name}: kept {len(k):>2}/{len(f):<2} right {sum(r['learned_right'] for r in k):>2}, right dropped {sum(r['learned_right'] for r in f if r['a_cue'] < t):>2}")
    print(f"  >= {t}: " + " | ".join(out))
