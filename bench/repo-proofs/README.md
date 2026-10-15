# Model D on Plane and SigNoz: finding context, learning it, and how far learning reaches

Model D fuses a deterministic kit with the Claude API. The kit maps a repository once and takes the expensive
decision, where in the code to look, at zero model cost. Claude reads what the kit already knows and explores only what
is new, and each exploration teaches the kit. These tests measure the kit's part, offline, on two open-source
repositories.

**The test set:**
- **Issues:** each repository's recent merged pull requests that close a linked issue.
- **The answer:** the source files the fix changed. Nothing here writes a fix; the fix only supplies the answer key.
- **The snapshot:** the code before every fix.

The method was written before the runs (`METHOD.md`, `RELATION_METHOD.md`). Deviations are recorded in those files.

## 1. Finding context cold: fixed file in the top 5

| repository (issues) | query | Model D 0.3.0, code scope | Graphify 0.9.91 | tokens per issue (Model D / Graphify) |
|---|---|---|---|---|
| makeplane/plane (40) | issue title | **10** | 5 | 801 / 1,529 |
| makeplane/plane (40) | title + 400 characters | **12** | 6 | 880 / 1,573 |
| SigNoz/signoz (134) | issue title | **42** | 24 | 734 / 1,695 |
| SigNoz/signoz (134) | title + 400 characters | **44** | 19 | 817 / 1,704 |

## 2. Learning: the same issue in other words
Each older issue was taught by its title, at the first changed line of its fix, then asked by its description alone.

| repository | right file first, before → after teaching | top 5, before → after |
|---|---|---|
| Plane (20 taught) | 2 → **16** | 4 → **16** |
| SigNoz (66 taught) | 4 → **42** | 18 → **46** |

## 3. How far learning reaches
- **Learned code is exactly right or exactly wrong.** When it went first, it was right on 54 of 54 paraphrases and on 0
  of 26 new questions it was never taught.
- **What separates them** is the margin by which the nearest learned question beats the best code text: a median of 74
  bits for paraphrases and 27 for new questions.
- **For the bill, the published law stays the right policy:** 2.15× cheaper than Claude alone on these 172 questions,
  against 1.95× with a relation limit. A wrong learned guess costs one cheap read, while a missed repeat costs a full
  exploration. The rule is: show learned code first when p(right) > E/K = 2.5%.
- **Every law was checked on the real SigNoz workspace:** 11 of 11 checks pass (`laws_check.py`).

Details and limits: `RESULTS.md`, `RELATION_RESULTS.md`.

## Reproduce
1. `collect.py`, `dataset.py`: the test sets from GitHub. Their outputs are `*_set.json`, also included.
2. `prep.sh`: snapshots and indexes.
3. `run_md.py`, `run_gf.py`: every readout (`md_*.json`, `gf_*.json`).
4. `score.py`: the tables.
5. `relation*.py`, `laws_check.py`: the relation analysis and the law checks.

These use Model D 0.3.0 (https://github.com/devkancheti4-design/optimal-context-mapping) and Graphify 0.9.91.
