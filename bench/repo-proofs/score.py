"""Score the Plane and SigNoz runs (METHOD.md). python score.py plane signoz"""
import json, sys
from statistics import mean


def hits(rows, gold, k):
    return sum(any(f in gold[i] for f in r["files"][:k]) for i, r in rows)


rep = {}
for name in sys.argv[1:]:
    D = json.load(open(f"{name}_set.json")); M = json.load(open(f"md_{name}.json")); G = json.load(open(f"gf_{name}.json"))
    gold = {f"{it['issue']}#{it['pr']}": set(it["gold"]) for it in D["items"]}; ids = list(gold)
    print(f"\n## {D['repo']} at {D['snapshot'][:7]}: {len(ids)} issues")
    print("\n| query | Model D, code scope | Model D, full scope | Graphify | tokens (code / full / Graphify) |\n|---|---|---|---|---|")
    r = {"issues": len(ids)}
    for q, label in (("q_title", "issue title"), ("q_400", "title + 400 characters")):
        cells, toks = [], []
        for src in ("code", "all", "gf"):
            rows = [(i, G[i][q] if src == "gf" else M["cold"][i][f"{q}|{src}"]) for i in ids]
            cells.append(" / ".join(str(hits(rows, gold, k)) for k in (1, 3, 5)))
            toks.append(f"{mean(x['chars'] for _, x in rows) / 4:,.0f}")
        r[label] = dict(zip(("code", "all", "graphify"), cells)); r[label]["tokens"] = toks
        print(f"| {label}, top-1 / 3 / 5 | {cells[0]} | {cells[1]} | {cells[2]} | {' / '.join(toks)} |")
    teach = [i for i in M["teach_ids"] if "q_body|code" in M["cold"][i]]
    c = [(i, M["cold"][i]["q_body|code"]) for i in teach]; a = [(i, M["after"][i]["q_body|code"]) for i in teach]
    l1 = {"issues": len(teach), "cold top-1/5": (hits(c, gold, 1), hits(c, gold, 5)), "after top-1/5": (hits(a, gold, 1), hits(a, gold, 5)),
          "led by learned code": sum(x["learned"] for _, x in a)}
    print(f"\nL1, the same issue in other words (taught by title, asked by its body): {len(teach)} issues")
    print(f"  cold: top-1 {l1['cold top-1/5'][0]}, top-5 {l1['cold top-1/5'][1]}  ->  after teaching: top-1 {l1['after top-1/5'][0]}, top-5 {l1['after top-1/5'][1]}; readouts led by learned code {l1['led by learned code']}")
    test = M["test_ids"]; taught = set(M["taught_files"])
    same = [i for i in test if gold[i] & taught]
    def l2(sub):
        c = [(i, M["cold"][i]["q_title|code"]) for i in sub]; a = [(i, M["after"][i]["q_title|code"]) for i in sub]
        return [hits(c, gold, k) for k in (1, 3, 5)], [hits(a, gold, k) for k in (1, 3, 5)]
    allc, alla = l2(test); samec, samea = l2(same)
    first = [(i, {"files": M["after"][i]["q_title|code"]["files_first"]}) for i in test]
    first_hits = [hits(first, gold, k) for k in (1, 3, 5)]
    print(f"L2, new questions (never taught), asked by title: {len(test)} issues; {len(same)} in a taught file's area")
    print(f"  all new: top-1/3/5 cold {allc} -> after {alla}")
    print(f"  same area: top-1/3/5 cold {samec} -> after {samea}")
    print(f"  all new, first readout only (before D1): after {first_hits}")
    r["L1"] = l1; r["L2"] = {"all": [len(test), allc, alla], "same area": [len(same), samec, samea]}; r["taught"] = M["taught_msg"]
    rep[name] = r
json.dump(rep, open("report.json", "w"), indent=1)
