"""RELATION_METHOD.md: relatedness r of each question to the nearest learned question, whether a fired learned match
was right, and L1/L2 with the relation limit r >= 2 (CERT_MIN_LIFT = 74 bits) against without it.
    PYTHONPATH=<optimal-context-mapping> python relation.py plane signoz"""
import json, os, re, sys
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
from ocm.server import Workspace
from ocm.router import lanes as L
W = os.path.dirname(os.path.abspath(__file__)); SIGMA = 37; LIMIT = 2 * SIGMA
TAUGHT = "(readout: the code a taught question"


def parse(text):
    files = []
    for p in re.findall(r"(?m)^\d+\. \[([^\]:]+):\d+\]", text):
        p = p.split("/", 1)[1] if "/" in p else p
        if p not in files:
            files.append(p)
    return files


def served(w, q):
    first = w.handle("ask", {"question": q, "scope": "code"}); text = first
    if first.startswith(TAUGHT):
        nxt = w.handle("next", {"question": q, "scope": "code"})
        if nxt.startswith("(readout:"):
            text = first + "\n\n" + nxt
    return parse(text)[:10], first.startswith(TAUGHT)


rows = []
for name in sys.argv[1:]:
    D = json.load(open(f"{W}/{name}_set.json")); M = json.load(open(f"{W}/md_{name}.json"))
    gold = {f"{it['issue']}#{it['pr']}": set(it["gold"]) for it in D["items"]}
    item = {f"{it['issue']}#{it['pr']}": it for it in D["items"]}
    wl = Workspace(f"{W}/ws_learn/{name}"); m = wl.mem
    jobs = [("paraphrase", i, item[i]["q_body"], "q_body|code") for i in M["teach_ids"] if item[i]["q_body"]] + \
           [("new", i, item[i]["q_title"], "q_title|code") for i in M["test_ids"]]
    for kind, i, q, key in jobs:
        L.CERT_MIN_LIFT = None
        _, obs = wl.lanes.measure(q, allow=wl.code)
        top_file = m.sources[m.src[obs["top"]]]["path"].split("/", 1)[1] if m.src[obs["top"]] >= 0 else None
        off, fired = served(wl, q)
        L.CERT_MIN_LIFT = LIMIT
        on, fired_on = served(wl, q)
        L.CERT_MIN_LIFT = None
        cold = M["cold"][i][key]["files"]
        rows.append({"repo": name, "kind": kind, "id": i, "lead": obs["cert_lead"], "lift": obs["cue_lift"],
                     "r": None if obs["cue_lift"] is None else obs["cue_lift"] / SIGMA, "from_cue": obs["from_cue"],
                     "fired": fired, "fired_gated": fired_on, "learned_right": top_file in gold[i],
                     "cold1": bool(cold[:1]) and cold[0] in gold[i], "cold5": any(f in gold[i] for f in cold[:5]),
                     "off1": bool(off[:1]) and off[0] in gold[i], "off5": any(f in gold[i] for f in off[:5]),
                     "on1": bool(on[:1]) and on[0] in gold[i], "on5": any(f in gold[i] for f in on[:5])})
    print(name, "done", sum(1 for r in rows if r["repo"] == name), "questions", flush=True)
json.dump(rows, open(f"{W}/relation_rows.json", "w"), indent=1)

print("\nrelatedness r of the nearest learned question (median, by kind):")
for kind in ("paraphrase", "new"):
    rs = sorted(r["r"] for r in rows if r["kind"] == kind and r["r"] is not None)
    print(f"  {kind:<10} n={len(rs)}  median r = {rs[len(rs)//2]:.2f}  share r>=2: {sum(x >= 2 for x in rs)/len(rs):.0%}")
print("\nfired learned matches (the law as published): how often the learned code was right, by band of r")
for lo, hi in ((-9, 1), (1, 2), (2, 3), (3, 4), (4, 99)):
    f = [r for r in rows if r["fired"] and r["r"] is not None and lo <= r["r"] < hi]
    if f:
        print(f"  r in [{lo if lo > -9 else '-inf'}, {hi if hi < 99 else 'inf'}): {len(f):>3} fired, right {sum(r['learned_right'] for r in f):>3}  ({sum(r['learned_right'] for r in f)/len(f):.0%})"
              f"  [paraphrase {sum(r['kind']=='paraphrase' for r in f)}, new {sum(r['kind']=='new' for r in f)}]")
print("\ntop-1 / top-5 (served readout): cold | learned, law as published | learned, with r >= 2")
for name in sys.argv[1:] + ["both"]:
    for kind in ("paraphrase", "new"):
        s = [r for r in rows if r["kind"] == kind and (name == "both" or r["repo"] == name)]
        c = lambda k: sum(r[k] for r in s)
        print(f"  {name:<7} {kind:<10} n={len(s):>3}: {c('cold1'):>3} / {c('cold5'):>3} | {c('off1'):>3} / {c('off5'):>3} | {c('on1'):>3} / {c('on5'):>3}"
              f"   fired {sum(r['fired'] for r in s)} -> {sum(r['fired_gated'] for r in s)}")
