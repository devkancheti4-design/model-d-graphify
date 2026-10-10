"""LOCOMO calibration, no API: in the same harness as locomo_eval.py (same documents, same per-conversation indexes,
same embedder), add the two baselines Graphify's table puts it next to: dense retrieval (the kit's /recall, nearest in
meaning, k=10) and hybrid RRF (dense + BM25 fused by reciprocal rank, k=60). Graphify's published table: graphify 0.497,
hybrid RRF 0.493, dense RAG 0.439, BM25 0.362."""
import json, os, re, random, sys
from statistics import mean
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locomo_eval as L
from ocm.server import Workspace

rows = json.load(open(f"{L.H}/../results/locomo.json"))
by = {(r["conv"], r["q"]): r for r in rows}
for ci, conv in enumerate(L.D):
    ts = L.turns(conv); w = Workspace(f"{L.H}/ws/conv{ci}")
    text = open(f"{L.H}/docs/conv{ci}/dialogue.conf").read().split("\n")
    line_turn, k = {}, 0
    for did, t in ts:
        for part in L.textwrap.wrap(t, 380) or [t]:
            k += 1; line_turn[k] = did
        k += 1
    bm = L.BM25([t for _, t in ts]); ids = [d for d, _ in ts]
    for qi, q in enumerate(conv["qa"]):
        r = by.get((ci, qi))
        if not r:
            continue
        out = w.handle("recall", {"query": q["question"], "k": 10})
        dense = []
        for ln in re.findall(r"\[conv\d+/dialogue\.conf:(\d+)\]", out):
            d = line_turn.get(int(ln))
            if d and d not in dense:
                dense.append(d)
        bml = [ids[i] for i in bm.top(q["question"], 10)]
        sc = {}
        for lst in (dense, bml):
            for rank, d in enumerate(lst, 1):
                sc[d] = sc.get(d, 0) + 1 / (60 + rank)
        rrf = sorted(sc, key=lambda d: -sc[d])[:10]
        ev = set(r["evidence"])
        r["dense recall"] = len(ev & set(dense[:10])) / len(ev); r["rrf recall"] = len(ev & set(rrf)) / len(ev)
    print("conv", ci, flush=True)
json.dump(rows, open(f"{L.H}/../results/locomo.json", "w"), indent=1)
sample = random.Random(20261010).sample(rows, 300)
print("\n| questions | n | BM25 | dense | hybrid RRF | Model D kit |\n|---|---|---|---|---|---|")
for name, S in (("categories 1-4, all", rows), ("seeded sample of 300", sample)):
    print(f"| {name} | {len(S)} | " + " | ".join(f"{mean(r[k] for r in S):.3f}" for k in ("bm25 recall", "dense recall", "rrf recall", "kit recall")) + " |")
