# Model D and Graphify: a retrieval study

**Model D** is a local retrieval kit. For a question, it ranks the code, config and docs an AI assistant should read
first. It also learns from every answered question, so a team's repeated questions get cheaper. This artifact compares
its retrieval with [Graphify](https://github.com/Graphify-Labs/graphify) on two tests, and ships everything needed to
rerun them.

The kit is a compiled evaluation build (`wheels/`). Its method and its learning layer are not described or included.

## Results

### 1. LOCOMO retrieval recall@10 (long conversations; the benchmark Graphify publishes on)

Every row below runs in the same harness, on the same documents and the same per-conversation indexes. The questions
are LOCOMO's categories 1-4 (1,536 of them).

| BM25 | dense | hybrid RRF (dense + BM25) | **Model D** |
|---|---|---|---|
| 0.540 | 0.583 | 0.655 | **0.657** |

Graphify's published table (`BENCHMARKS.md`) reads: graphify 0.497, hybrid RRF 0.493, dense 0.439, BM25 0.362. Its
harness is not public, and our BM25 scores higher than theirs, so the raw numbers cannot be compared directly. The
comparable point is that **each system ties hybrid RRF in its own harness.** On this benchmark the two retrieve at the
same level. Model D uses a smaller embedder (bge-base, 110M parameters) than the BGE-m3 used in Graphify's runs.
Learning plays no part here, because LOCOMO asks each question once.

### 2. Finding the right file in a full-stack repo (100 questions with marked answer files)

The corpus is [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (MIT),
snapshotted in `bench/data/corpus` (202 text files: code, config and docs). The 100 questions and their answer files
are in `bench/questions_100.json`. Each cell counts the questions where a tool's first *k* files include an answer
file.

| | n | Model D top 1 | top 3 | **top 5** | Graphify top 1 | top 3 | **top 5** |
|---|---|---|---|---|---|---|---|
| all | 100 | 32 | 61 | **75** | 12 | 22 | **28** |
| code | 71 | 21 | 40 | **50** | 12 | 22 | **28** |
| config | 24 | 8 | 16 | 20 | 0 | 0 | 0 |
| docs | 5 | 3 | 5 | 5 | 0 | 0 | 0 |

Each tool hands the model this much per question:

| | Model D | Graphify |
|---|---|---|
| characters handed to the model | 1,764 | 6,792 |
| time per question | 0.07 s | 0.16 s |

How to read this table:
- **Code is the fair comparison.** Graphify builds code nodes locally with tree-sitter, so it was at full strength.
- **Config and docs are not a fair comparison.** Graphify sends those files to an LLM. Our build used a local
  `qwen3.5:4b` through Ollama, which failed Graphify's output format, so those files produced no nodes. A stronger
  backend would change those two rows.
- **How each tool's files were counted.** Graphify's `query` is a traversal for an agent to explore, not a ranking.
  Its files are counted in output order (start nodes first). Model D's files are counted in its rank order.
- **The folder name matters slightly.** The kit indexes each file's path, so it uses the study's folder name,
  `corpus`. Named `fastapi-template`, the same build scores 69/100 overall and 46/71 on code.

### 3. A plug point: `graphify query --seed`

[Graphify-Labs/graphify#4289](https://github.com/Graphify-Labs/graphify/pull/4289) (issue
[#4293](https://github.com/Graphify-Labs/graphify/issues/4293)) lets any external ranker choose where `graphify query`
starts. `integration/seed_with_graphify.py` shows Model D choosing the start files. It is shown as an integration
point, with no claim about accuracy.

## What the learning layer adds (results only, measured separately with Claude)

These were pre-registered runs with Claude Sonnet and Haiku, graded blind. They are summarised here, and their
harness is not part of this artifact.

**SWE-QA** (7 public repositories, 336 questions, graded with SWE-QA's own rubric):
- Model D answered at **2.2x lower cost**, scoring 61.0 against 65.3 out of 100 for Sonnet alone.
- With prompt caching and the same answer instruction for both, it answered at **1.9x lower cost**, scoring 73.3
  against 75.9 (96.5% of Sonnet alone).

**Repeated questions** on a company-style repository: **5-10x cheaper**, because answered questions go straight to the
right code.

**Writing bug fixes** (SWE-ContextBench, Django tasks): **no saving.** Those issues already name the code, so there is
little "where" to decide.

## Use it in Claude Code (plugin)

This repository is also a Claude Code plugin. It gives Claude Model D's tools (`workspace_ask`, `workspace_next`,
`workspace_recall`, `workspace_teach`) and a skill that tells Claude to ask Model D before searching.

1. **Install the package and map your repository, once:**
   ```bash
   python3 -m venv ~/modeld && ~/modeld/bin/pip install "numpy>=2.0" "torch>=2.1" "transformers>=4.40"
   ~/modeld/bin/pip install --no-index --find-links wheels optimal-context-mapping   # from this repository's folder
   ~/modeld/bin/ocm build /path/to/your/repo --out ~/modeld-ws
   ~/modeld/bin/ocm serve ~/modeld-ws        # leave running
   ```
2. **Add the plugin in Claude Code:**
   ```
   /plugin marketplace add devkancheti4-design/model-d-graphify
   /plugin install model-d@model-d
   ```
   Or run `claude --plugin-dir /path/to/model-d-graphify` from a local clone.
3. **Point the plugin at your Python.** When asked, set **Python with Model D installed** to
   `/Users/you/modeld/bin/python` (an absolute path), then restart Claude Code.

Model D runs as a local process, so the plugin works in Claude Code and the desktop app. Uploading this repository's ZIP
to claude.ai's plugin page passes its check, but the tools cannot start in claude.ai on the web.

## Reproduce

```bash
# Model D (Python 3.10-3.14; macOS on Apple silicon, or Linux x86-64)
pip install "numpy>=2.0" "torch>=2.1" "transformers>=4.40"
pip install --no-index --find-links wheels optimal-context-mapping

# 1. LOCOMO (fetched from its authors; not redistributed here)
sh bench/get_locomo.sh
python bench/locomo_eval.py && python bench/locomo_calibrate.py

# 2. The full-stack repo
ocm build bench/data/corpus --out ws/corpus
pip install graphifyy==0.9.84      # build a graph, or use bench/results/graphify_graph_fastapi.json (ours)
python bench/graphify_vs.py bench/results/graphify_graph_fastapi.json ws/corpus
```

Both runs above reproduce the tables exactly. Per-question results are in `bench/results/`: `code_100.json`,
`locomo.json`, and Graphify's graph as built.

## Licences

- `wheels/`: the compiled package is under the evaluation licence in `LICENSE`. Third-party notices are in
  `THIRD_PARTY_NOTICES`.
- `bench/` scripts and results: may be used to reproduce and discuss this study.
- `bench/data/corpus`: MIT, see its own `LICENSE`.
- LOCOMO is not included.

Contact: [@devkancheti4-design](https://github.com/devkancheti4-design) on GitHub.
