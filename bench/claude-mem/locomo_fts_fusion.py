"""LOCOMO retrieval recall@10 with claude-mem's search building blocks. Offline: no API, no claude-mem install.
Needs: torch, transformers, and the LOCOMO file (sh ../get_locomo.sh).

Retrieval methods compared:
  fts_and    FTS5 as claude-mem's SessionSearch.buildFTSMatchQuery queries it: quoted tokens joined by AND, bm25 rank
  fts_rule   AND first; when no row matches and the query has 3+ tokens, the same tokens joined by OR (the proposed fix)
  dense      Chroma's default embedding, all-MiniLM-L6-v2 (mean pooled, normalised, 256 tokens), cosine
  fusion     reciprocal rank fusion, k=60, of dense and fts_rule (50 deep each)

Documents: every dialogue turn, "Speaker (session date): text [photo caption]", one index per conversation. The
questions are categories 1-4 (1,536). recall@10 = the share of a question's evidence turns among the first 10."""
import json, os, re, sqlite3
from statistics import mean

import torch
from transformers import AutoModel, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "..", "locomo", "data", "locomo10.json")))
tok = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2").eval()


def turns(conv):
    c = conv["conversation"]; out = []
    for k in sorted((k for k in c if re.fullmatch(r"session_\d+", k)), key=lambda k: int(k.split("_")[1])):
        for t in c[k]:
            text = t.get("text", "") + (f" [shares a photo: {t['blip_caption']}]" if t.get("blip_caption") else "")
            out.append((t["dia_id"], f"{t['speaker']} ({c.get(f'{k}_date_time', '')}): {text}"))
    return out


def evidence(q):
    return {e for x in q.get("evidence", []) for e in re.split(r"[;,\s]+", x) if re.fullmatch(r"D\d+:\d+", e)}


def embed(texts):
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 64):
            enc = tok(texts[i:i + 64], padding=True, truncation=True, max_length=256, return_tensors="pt")
            h = model(**enc).last_hidden_state; m = enc["attention_mask"].unsqueeze(-1).float()
            out.append(torch.nn.functional.normalize((h * m).sum(1) / m.sum(1).clamp(min=1e-9), dim=1))
    return torch.cat(out)


def tokens(q):
    return [t for t in re.findall(r"\S+", q) if re.search(r"[^\W_]", t)]


def match(q, joiner):
    t = tokens(q)
    return f" {joiner} ".join('"' + x.replace('"', '""') + '"' for x in t) if t else '"' + q.replace('"', '""') + '"'


def rrf(*lists, k=60):
    s = {}
    for lst in lists:
        for r, d in enumerate(lst, 1):
            s[d] = s.get(d, 0.0) + 1.0 / (k + r)
    return sorted(s, key=lambda d: -s[d])


rec = {"fts_and": [], "fts_rule": [], "dense": [], "fusion": []}; empty = 0
for conv in D:
    ts = turns(conv); ids = [d for d, _ in ts]; texts = [t for _, t in ts]
    db = sqlite3.connect(":memory:"); db.execute("CREATE VIRTUAL TABLE f USING fts5(text)")
    db.executemany("INSERT INTO f(rowid, text) VALUES (?, ?)", [(i + 1, t) for i, t in enumerate(texts)])
    E = embed(texts); qs = [q for q in conv["qa"] if q.get("category") != 5 and evidence(q)]; Q = embed([q["question"] for q in qs])
    for q, qv in zip(qs, Q):
        run = lambda j: [ids[r - 1] for (r,) in db.execute("SELECT rowid FROM f WHERE f MATCH ? ORDER BY rank LIMIT 50", (match(q["question"], j),)).fetchall()]
        fts_and = run("AND"); empty += not fts_and
        fts_rule = fts_and or (run("OR") if len(tokens(q["question"])) >= 3 else [])
        dense = [ids[i] for i in torch.topk(E @ qv, min(50, len(ids))).indices.tolist()]
        ev = evidence(q)
        for name, lst in (("fts_and", fts_and), ("fts_rule", fts_rule), ("dense", dense), ("fusion", rrf(dense, fts_rule))):
            rec[name].append(len(ev & set(lst[:10])) / len(ev))
n = len(rec["dense"])
print(f"{n} questions; the AND form matched nothing for {empty} ({empty / n:.1%})")
for name, v in rec.items():
    print(f"{name:9s} recall@10 {mean(v):.3f}")
