# Finding the file a fix changed: SWE-bench Lite in full repositories

The test: for each of the 300 SWE-bench Lite issues, does a tool list the file the official fix changed among its first
1, 3 and 5 files? It runs offline with no API, and each tool indexes the whole repository at SWE-bench Lite's snapshot
(the newest base commit per repository).

**Set-up:**
- **Issues:** 285 are scored; an issue counts when one of its fixed files exists in the snapshot.
- **Queries:** each issue is asked twice, by its title and by its title plus the first 400 characters.
- **Graphify 0.9.87:** `graphify update <repo> --no-cluster` builds the code graph (tree-sitter, no LLM), written
  outside the repository with `GRAPHIFY_OUT`. Queries use `graphify query` defaults: BFS, depth 2, 2,000-token budget.
- **Model D 0.2.2:** `ocm build <repo>` builds the index; `ask` runs with `"scope": "code"` and with the full scope.

| query | Model D, code scope | Model D, full scope | Graphify 0.9.87 |
|---|---|---|---|
| issue title, top-1 / 3 / 5 | **80 / 154 / 176** | 32 / 80 / 117 | 78 / 115 / 131 |
| title + 400 characters, top-1 / 3 / 5 | **96 / 161 / 183** | 64 / 129 / 157 | 67 / 99 / 122 |
| tokens per issue (characters / 4) | 634 / 700 | 524 / 620 | 1,520 / 1,652 |

**Paired top-5, code scope vs Graphify:**
- On titles, the code scope finds 72 issues Graphify misses, and Graphify finds 27 the code scope misses (exact
  McNemar p = 6.9e-6).
- On title + 400 characters it is 82 against 21 (p = 1.1e-9).

**Why there are two Model D columns:**
- The full scope ranks documentation too. In a full repository, release notes and reference pages filled about half
  its top five, and it lost to Graphify on titles (117 vs 131).
- The code scope (`ocm.units.DOCS` left out) was added for that.
- It was tested against a plan fixed in advance: `PROTOCOL_CODEONLY.md`. The plan, runner and scorer were hashed
  before the run, and 5 of 5 predictions held. The result is in `RESULTS_CODEONLY.md`.

**Where Graphify is ahead or level:**
- Top-1 on titles is about even: 80 vs 78.
- Graphify is ahead on seaborn (4 issues), on flask (3 issues, titles) and on xarray (5 issues, title + 400
  characters).

**Files:**
- `run_modeld_scope.py`, `run_graphify.py`, `score_codeonly.py`, `score.py`, `prep.sh`;
- the rows: `codeonly.json`, `regress_all2.json`, `graphify_ranked_087.json`, `modeld_ranked.json`;
- the issues: `swebench_lite_by_repo.json`, `kept_issues.json`.

The same files, with a check that recomputes the table, are in the Model D repository's `evidence/swe-bench-lite/`
(`python evidence/verify.py`).
