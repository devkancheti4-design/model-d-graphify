"""How well does `graphify query` find the file that answers a question? Offline: AST-only graphs, no LLM.

Sets:
  fastapi  the 100 questions in ../questions_100.json, answer files marked; graph built over ../data/corpus
  django   114 SWE-bench Lite Django issues (django_swebench_lite_114.json); the answer is the file the official fix
           changed. Queried by the issue title (first line) and by the title plus the first 400 characters. Graph built
           over the `django/` package of a Django checkout at 4a72da71001f154ea60906a2f74898d32b7322a7.

Build the graphs (AST only, no LLM):
    graphify update <fastapi dir> --no-cluster ; graphify update <django checkout>/django --no-cluster

For each question: the start nodes graphify picks (seed hit = a start node lies in an answer file), and the files in
the order `graphify query` prints them (hit@k). Runs graphify's own functions from the checkout on sys.path.
    python eval_seeds.py <fastapi graph.json> <django graph.json> [label]   (with graphify importable)"""
import json, os, re, sys

import networkx as nx
from networkx.readwrite import json_graph

from graphify import serve as S

HERE = os.path.dirname(os.path.abspath(__file__))
FAST_GRAPH, DJ_GRAPH = sys.argv[1], sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else "run"


def load(path):
    raw = json.load(open(path))
    if "links" not in raw and "edges" in raw:
        raw = dict(raw, links=raw["edges"])
    raw = dict(raw, links=[{**l, "_src": l.get("_src", l.get("source")), "_tgt": l.get("_tgt", l.get("target"))} for l in raw["links"]])
    try:
        return json_graph.node_link_graph(raw, edges="links")
    except TypeError:
        return json_graph.node_link_graph(raw)


def seeds(G, q):
    terms = S._query_terms(q)
    qs = S._score_query(G, terms, collect_per_term_seeds=True)
    best = qs.best_seed_by_term
    intent = {t for t in best if t in S._RELATIONAL_INTENT_TERMS}
    if intent and any(t not in S._RELATIONAL_INTENT_TERMS for t in terms):
        best = {t: n for t, n in best.items() if t not in intent}
    extra = {"term_order": qs.term_order} if hasattr(qs, "term_order") else {}   # present only with the change
    return S._pick_seeds(qs.ranked, G=G, best_seed_by_term=best, **extra)


def output_files(text):
    out = []
    for p in re.findall(r"(?m)^NODE .*?\[src=([^ \]]+)", text):
        if p not in out:
            out.append(p)
    return out


def run(G, items):
    rows = []
    for it in items:
        st = seeds(G, it["q"])
        sfiles = []
        for n in st:
            f = (G.nodes[n].get("source_file") or "")
            if f and f not in sfiles:
                sfiles.append(f)
        text = S._query_graph_text(G, it["q"], mode="bfs", depth=2, token_budget=2000)
        files = output_files(text)
        gold = it["gold"]
        rows.append({"id": it["id"], "seed_hit": any(f in gold for f in sfiles), "n_seeds": len(st),
                     "hit1": any(f in gold for f in files[:1]), "hit3": any(f in gold for f in files[:3]),
                     "hit5": any(f in gold for f in files[:5]), "seed_files": sfiles[:5], "files": files[:5],
                     "seed_labels": [G.nodes[n].get("label", n) for n in st][:5]})
    return rows


def summary(name, rows):
    n = len(rows); s = lambda k: sum(r[k] for r in rows)
    return f"| {name} | {n} | {s('seed_hit')} | {s('hit1')} | {s('hit3')} | {s('hit5')} |"


def main():
    qs100 = json.load(open(os.path.join(HERE, "..", "questions_100.json")))
    fast = [{"id": q["qid"], "q": q["question"], "gold": {e["file"] for e in q["evidence"]}} for q in qs100]
    iss = json.load(open(os.path.join(HERE, "django_swebench_lite_114.json")))
    dj_title = [{"id": i["instance_id"], "q": i["query_title"], "gold": {i["gold_file"].removeprefix("django/")}} for i in iss]
    dj_long = [{"id": i["instance_id"], "q": i["query_400"], "gold": {i["gold_file"].removeprefix("django/")}} for i in iss]
    Gf = load(FAST_GRAPH)
    Gd = load(DJ_GRAPH)
    results = {"fastapi": run(Gf, fast), "django_title": run(Gd, dj_title), "django_400": run(Gd, dj_long)}
    code_ids = {q["qid"] for q in qs100 if any(e["file"].endswith((".py", ".ts", ".tsx", ".js")) for e in q["evidence"])}
    print(f"\n### {LABEL}\n\n| set | n | seed in answer file | hit@1 | hit@3 | hit@5 |\n|---|---|---|---|---|---|")
    print(summary("fastapi, all", results["fastapi"]))
    print(summary("fastapi, code answers", [r for r in results["fastapi"] if r["id"] in code_ids]))
    print(summary("django, issue title", results["django_title"]))
    print(summary("django, title + 400 chars", results["django_400"]))
    json.dump(results, open(os.path.join(HERE, f"results_{LABEL}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
