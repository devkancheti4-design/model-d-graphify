# Model D vs Graphify: finding the right file

The test, offline with no API: for each question, which tool lists the file that holds the answer among its first
1, 3 and 5 files? Both tools index the same code snapshot. Versions:
- **Graphify 0.9.86**: its default code graph (`graphify update <dir> --no-cluster`, tree-sitter, no LLM), queried
  with `graphify query` defaults (BFS, 2,000-token answer). Files are counted in the order it prints them.
- **Model D 0.2.1**: its local index (`ocm build <dir>`), queried for its ranked readout. Files are counted in rank
  order.

| set | questions | Model D top-1 / 3 / 5 | Graphify top-1 / 3 / 5 | tokens per question (Model D / Graphify) |
|---|---|---|---|---|
| Django, SWE-bench Lite issues, title | 114 | **54 / 74 / 84** | 31 / 46 / 54 | ~667 / ~1,457 |
| Django, SWE-bench Lite issues, title + 400 characters | 114 | **63 / 84 / 93** | 39 / 53 / 53 | ~719 / ~1,640 |
| full-stack-fastapi-template, 100 questions | 100 | **32 / 61 / 75** | 16 / 29 / 36 | ~441 / ~1,644 |

**Snapshots:**
- Django: the `django/` package at `4a72da7`, SWE-bench Lite's Django snapshot. The answer is the file the official
  fix changed.
- FastAPI: `../data/corpus`, with answer files marked in `../questions_100.json`.

**Reproduce:**
- Django, Model D: `python django_modeld.py <index>` (this folder).
- Django, Graphify: `../graphify-seed/eval_seeds.py`.
- FastAPI, both tools: `../graphify_vs.py`.

**Not tested:**
- Graphify's LLM extraction of docs, papers and images.
- End-to-end answer quality with an agent.

On LOCOMO memory retrieval the two tie (see the top-level README). Model D indexes each file's path with its text, so
the indexed folder's name shifts its numbers slightly. The table uses the folders named above.
