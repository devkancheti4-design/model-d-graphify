"""LOCOMO retrieval recall@10, no API: Model D's kit (0.2.1, cold, its /ask readout of 10 units) against BM25 on the
same documents, to compare with Graphify's published table (BENCHMARKS.md: graphify 0.497, hybrid RRF 0.493, dense
RAG 0.439, BM25 0.362, mem0 0.048; their harness is not public).

Documents: every dialogue turn of each conversation, as "Speaker (session date): text [shares a photo: caption]",
one turn per block, so a retrieved unit is one turn (the unit LOCOMO's evidence ids name). Each conversation gets its
own index. recall@10 for a question = share of its evidence turns among the first 10 distinct turns retrieved.
Questions: categories 1-4 (category 5 is adversarial, with no answer in the conversation), all of them, plus a
seeded sample of 300 (seed 20261010).
    python bench/locomo_eval.py"""
import json, math, os, random, re, shutil, sys, textwrap
from collections import Counter
from statistics import mean

os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
from ocm.build import build
from ocm.server import Workspace

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locomo")   # data/locomo10.json: run get_locomo.sh first
D = json.load(open(f"{H}/data/locomo10.json"))


def turns(conv):
    c = conv["conversation"]; out = []
    for k in sorted((k for k in c if re.fullmatch(r"session_\d+", k)), key=lambda k: int(k.split("_")[1])):
        date = c.get(f"{k}_date_time", "")
        for t in c[k]:
            text = t.get("text", "")
            if t.get("blip_caption"):
                text += f" [shares a photo: {t['blip_caption']}]"
            out.append((t["dia_id"], f"{t['speaker']} ({date}): {text}"))
    return out


def evidence(q):
    return {e for x in q.get("evidence", []) for e in re.split(r"[;,\s]+", x) if re.fullmatch(r"D\d+:\d+", e)}


TOK = re.compile(r"\w+")


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = [Counter(TOK.findall(d.lower())) for d in docs]; self.k1, self.b = k1, b
        self.len = [sum(d.values()) for d in self.docs]; self.avg = mean(self.len); n = len(docs)
        df = Counter(w for d in self.docs for w in d)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def top(self, query, k):
        q = TOK.findall(query.lower())
        sc = [sum(self.idf.get(w, 0) * d[w] * (self.k1 + 1) / (d[w] + self.k1 * (1 - self.b + self.b * L / self.avg)) for w in q if w in d)
              for d, L in zip(self.docs, self.len)]
        return sorted(range(len(sc)), key=lambda i: -sc[i])[:k]


def main():
    rows = []
    for ci, conv in enumerate(D):
        ts = turns(conv); folder = f"{H}/docs/conv{ci}"; ws = f"{H}/ws/conv{ci}"
        shutil.rmtree(folder, ignore_errors=True); os.makedirs(folder)
        lines, line_turn = [], {}
        for did, text in ts:
            for part in textwrap.wrap(text, 380) or [text]:
                lines.append(part); line_turn[len(lines)] = did
            lines.append("")
        open(f"{folder}/dialogue.conf", "w").write("\n".join(lines))
        if not os.path.exists(f"{ws}/workspace.json"):
            build([folder], ws, log=lambda *a: None)
        w = Workspace(ws); bm = BM25([t for _, t in ts]); ids = [d for d, _ in ts]
        for qi, q in enumerate(conv["qa"]):
            ev = evidence(q)
            if q.get("category") == 5 or not ev:
                continue
            out = w.handle("ask", {"question": q["question"]})
            got = []
            for ln in re.findall(r"(?m)^\d+\. \[conv\d+/dialogue\.conf:(\d+)\]", out):
                did = line_turn.get(int(ln))
                if did and did not in got:
                    got.append(did)
            bmt = [ids[i] for i in bm.top(q["question"], 10)]
            rows.append({"conv": ci, "q": qi, "category": q["category"], "evidence": sorted(ev),
                         "kit": got[:10], "bm25": bmt,
                         "kit recall": len(ev & set(got[:10])) / len(ev), "bm25 recall": len(ev & set(bmt)) / len(ev)})
        print(f"conv {ci}: {len(ts)} turns, {sum(r['conv'] == ci for r in rows)} questions", flush=True)
    json.dump(rows, open(f"{H}/../results/locomo.json", "w"), indent=1)
    sample = random.Random(20261010).sample(rows, 300)
    print("\n| questions | n | Model D kit recall@10 | BM25 recall@10 (ours) |\n|---|---|---|---|")
    for name, S in (("categories 1-4, all", rows), ("seeded sample of 300", sample)):
        print(f"| {name} | {len(S)} | {mean(r['kit recall'] for r in S):.3f} | {mean(r['bm25 recall'] for r in S):.3f} |")
    for c in (1, 2, 3, 4):
        S = [r for r in rows if r["category"] == c]
        print(f"| category {c} | {len(S)} | {mean(r['kit recall'] for r in S):.3f} | {mean(r['bm25 recall'] for r in S):.3f} |")
    print(f"\nkit returned fewer than 10 distinct turns on {sum(len(r['kit']) < 10 for r in rows)} of {len(rows)} questions; "
          f"mean distinct turns {mean(len(r['kit']) for r in rows):.1f}")


if __name__ == "__main__":
    main()
