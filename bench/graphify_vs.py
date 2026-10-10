"""Model D's kit vs Graphify on the "where" decision, no API: the 100 company-repo questions (questions_100.json,
answer files marked), the same corpus (code, config and docs; 234 text files). For each question, each tool's
ranked files are checked against the marked answer files: hit@1, hit@3, hit@5. Also: the size of what each hands the
model, and time per question.
    python bench/graphify_vs.py <graph.json> <model-d-workspace>     (graphify on PATH; see README)"""
import json, os, re, subprocess, sys, time
from statistics import mean

B = os.path.dirname(os.path.abspath(__file__))
GRAPH, WSD = sys.argv[1], sys.argv[2]
Q = json.load(open(f"{B}/questions_100.json"))
CORPUS = f"{B}/data/corpus"   # the folder name is indexed with each path; "corpus" is the name the study used


def kit_files(readout, folder):
    """Model D: the files of its ranked results, in rank order (result headers only, not paths mentioned in the text)."""
    out = []
    for p in re.findall(r"(?m)^\d+\. \[" + re.escape(folder) + r"/([^\]:]+):\d+\]", readout):
        if p not in out:
            out.append(p)
    return out


def graphify_files(text):
    """Graphify: the source files of the nodes it returns, in output order (start nodes first)."""
    out = []
    for p in re.findall(r"(?m)^NODE .*?\[src=([^ \]]+)", text):
        if p not in out:
            out.append(p)
    return out


def graphify(q):
    r = subprocess.run(["graphify", "query", q, "--graph", GRAPH, "--budget", "2000"], capture_output=True, text=True, timeout=120)
    return r.stdout


def main():
    os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from ocm.server import Workspace
    w = Workspace(WSD)
    rows = []
    for q in Q:
        gold = {e["file"] for e in q["evidence"]}
        t0 = time.time(); md = w.handle("ask", {"question": q["question"]}); t_md = time.time() - t0
        t0 = time.time(); gf = graphify(q["question"]); t_gf = time.time() - t0
        r = {"id": q["qid"], "gold": sorted(gold), "kind": "docs" if all(g.endswith((".md", ".txt", ".rst")) for g in gold) else
             ("config" if all(g.endswith((".yml", ".yaml", ".json", ".toml", ".conf")) or "Dockerfile" in g for g in gold) else "code"),
             "md": kit_files(md, os.path.basename(CORPUS))[:10], "gf": graphify_files(gf)[:10],
             "md chars": len(md), "gf chars": len(gf), "md s": round(t_md, 3), "gf s": round(t_gf, 3)}
        rows.append(r)
        print(q["qid"], "MD", any(f in gold for f in r["md"][:5]), "GF", any(f in gold for f in r["gf"][:5]), flush=True)
    json.dump(rows, open(f"{B}/results/code_100.json", "w"), indent=1)
    hit = lambda r, arm, k: any(f in r["gold"] for f in r[arm][:k])
    print("\n| | n | Model D hit@1 | @3 | @5 | Graphify hit@1 | @3 | @5 |\n|---|---|---|---|---|---|---|---|")
    for kind in ("all", "code", "config", "docs"):
        S = [r for r in rows if kind == "all" or r["kind"] == kind]
        if S:
            print(f"| {kind} | {len(S)} | " + " | ".join(f"{sum(hit(r, a, k) for r in S)}" for a in ("md", "gf") for k in (1, 3, 5)) + " |")
    print(f"\nhanded to the model, characters: Model D {mean(r['md chars'] for r in rows):.0f}, Graphify {mean(r['gf chars'] for r in rows):.0f}")
    print(f"time per question, s: Model D {mean(r['md s'] for r in rows):.3f}, Graphify {mean(r['gf s'] for r in rows):.3f}")
    print(f"questions where a tool named no file: Model D {sum(not r['md'] for r in rows)}, Graphify {sum(not r['gf'] for r in rows)}")


if __name__ == "__main__":
    main()
