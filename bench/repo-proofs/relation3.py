"""Served readouts with the candidate relation limit (cue beats the best code text by >= 37 bits = 1 sigma), against
the law as published and cold. Chosen after seeing SigNoz; Plane is the check."""
import json, os, re
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
from ocm.server import Workspace
from ocm.router import lanes as L
W = os.path.dirname(os.path.abspath(__file__)); TAUGHT = "(readout: the code a taught question"
rows = json.load(open(f"{W}/relation_rows.json"))


def served(w, q):
    first = w.handle("ask", {"question": q, "scope": "code"}); text = first
    if first.startswith(TAUGHT):
        nxt = w.handle("next", {"question": q, "scope": "code"})
        if nxt.startswith("(readout:"):
            text = first + "\n\n" + nxt
    files = []
    for p in re.findall(r"(?m)^\d+\. \[([^\]:]+):\d+\]", text):
        p = p.split("/", 1)[1] if "/" in p else p
        if p not in files:
            files.append(p)
    return files[:10], first.startswith(TAUGHT)


for name in ("plane", "signoz"):
    D = json.load(open(f"{W}/{name}_set.json")); item = {f"{it['issue']}#{it['pr']}": it for it in D["items"]}
    gold = {k: set(v["gold"]) for k, v in item.items()}
    wl = Workspace(f"{W}/ws_learn/{name}")
    L.CERT_MIN_OVER_OWN = 37
    for r in rows:
        if r["repo"] != name:
            continue
        q = item[r["id"]]["q_body" if r["kind"] == "paraphrase" else "q_title"]
        files, fired = served(wl, q)
        r["g1"] = bool(files[:1]) and files[0] in gold[r["id"]]; r["g5"] = any(f in gold[r["id"]] for f in files[:5]); r["fired_g"] = fired
    L.CERT_MIN_OVER_OWN = None
json.dump(rows, open(f"{W}/relation_rows.json", "w"), indent=1)
print("top-1 / top-5 (served readout): cold | law as published | with the relation limit (37 bits over code)")
for name in ("signoz", "plane", "both"):
    for kind in ("paraphrase", "new"):
        s = [r for r in rows if r["kind"] == kind and (name == "both" or r["repo"] == name)]
        c = lambda k: sum(r[k] for r in s)
        print(f"  {name:<7} {kind:<10} n={len(s):>3}: {c('cold1'):>3} / {c('cold5'):>3} | {c('off1'):>3} / {c('off5'):>3} | {c('g1'):>3} / {c('g5'):>3}"
              f"   learned first: {sum(r['fired'] for r in s)} -> {sum(r['fired_g'] for r in s)}")
