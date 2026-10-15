"""Graphify cold context (METHOD.md). Run from the graphify checkout: uv run --no-sync python run_gf.py <name>"""
import json, os, re, sys
from networkx.readwrite import json_graph
from graphify import serve as S
W = os.path.expanduser("~/neos/outreach/repo-proofs"); NAME = sys.argv[1]
D = json.load(open(f"{W}/{NAME}_set.json"))
raw = json.load(open(f"{W}/graphs/{NAME}/graphify-out/graph.json"))
raw = dict(raw, links=raw.get("links", raw.get("edges", [])))
raw["links"] = [{**l, "_src": l.get("_src", l.get("source")), "_tgt": l.get("_tgt", l.get("target"))} for l in raw["links"]]
G = json_graph.node_link_graph(raw, edges="links")
out = {}
for it in D["items"]:
    r = {}
    for q in ("q_title", "q_400"):
        text = S._query_graph_text(G, it[q], mode="bfs", depth=2, token_budget=2000); files = []
        for p in re.findall(r"(?m)^NODE .*?\[src=([^ \]]+)", text):
            if p not in files:
                files.append(p)
        r[q] = {"files": files[:10], "chars": len(text)}
    out[f"{it['issue']}#{it['pr']}"] = r
json.dump(out, open(f"{W}/gf_{NAME}.json", "w"))
print(NAME, G.number_of_nodes(), "nodes,", len(out), "issues")
