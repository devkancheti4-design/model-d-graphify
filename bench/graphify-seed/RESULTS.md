# graphify query: order the per-term guaranteed seeds by match strength (2026-10-12, offline, no API)

graphify 0.9.86 (upstream v8 a5ba60d) and the same version with the change (branch seed-order). The graphs are
AST-only (`graphify update <dir> --no-cluster`):
- full-stack-fastapi-template: 1,266 nodes;
- Django at 4a72da7: 16,008 nodes.

The script is eval_seeds.py; it calls graphify's own scoring, seeding and query functions. hit@k = the answer file is
among the first k files `graphify query` prints. "Seed in answer file" = a start node lies in an answer file.

| set | n | seed in answer file (both) | hit@1 v8 / new | hit@3 v8 / new | hit@5 v8 / new |
|---|---|---|---|---|---|
| fastapi, 100 questions | 100 | 35 | 16 / 17 | 29 / 33 | 36 / 37 |
| django SWE-bench Lite issues, title | 114 | 62 | 31 / 31 | 46 / 48 | 54 / 55 |
| django issues, title + 400 chars | 114 | 83 | 39 / 39 | 53 / 58 | 53 / 63 |

**Per question:**
- fastapi: hit@3 +4/-0, hit@5 +1/-0.
- django, title: hit@3 +3/-1, hit@5 +4/-3.
- django, title + 400 chars: hit@3 +5/-0, hit@5 +10/-0.

**Cause:** `_pick_seeds` appends the per-term guaranteed seeds (#1445) in `sorted(best_seed_by_term)`, which is
alphabetical term order, and `_subgraph_to_text` prints seeds first. On long queries the answer file's seed often sat
at positions 6-10.

**Change:** `_score_query` returns `term_order` (per-term winners by their existing key: -singleton score, which
already carries the term's IDF, then -degree, label length, node id; the term breaks ties), and `_pick_seeds`
iterates it.
- The same seeds are picked and BFS reaches the same nodes. Only the order changes.
- The order is deterministic.
- Without `term_order`, the legacy sorted order is kept.

**Tests:**
- tests/test_query_seed_order.py has 5 tests. Four fail on v8 (including an end-to-end case where the common term
  "apple" was printed ahead of the rare exact match "charlie"), and all pass with the change.
- query, serve, MCP and affected: 285 pass.
