# Model D on Plane and SigNoz (2026-10-15, offline, no API)

Method: METHOD.md, fixed before the runs, with deviations D1 and D2 recorded. An issue's answer is the set of source
files its fix changed. Each snapshot predates every fix. Tools: Model D 0.3.0 (the kit alone, at zero model cost) and
Graphify 0.9.91 (defaults).

## 1. Finding context cold: fixed file in the top 1 / 3 / 5

| repository (issues) | query | Model D, code scope | Graphify 0.9.91 | tokens per issue (Model D / Graphify) |
|---|---|---|---|---|
| Plane (40) | issue title | **7 / 9 / 10** | 2 / 5 / 5 | 801 / 1,529 |
| Plane (40) | title + 400 characters | **5 / 10 / 12** | 4 / 5 / 6 | 880 / 1,573 |
| SigNoz (134) | issue title | **18 / 30 / 42** | 7 / 16 / 24 | 734 / 1,695 |
| SigNoz (134) | title + 400 characters | **17 / 32 / 44** | 8 / 15 / 19 | 817 / 1,704 |

**Reading it:**
- On SigNoz the full scope (docs included) scored 35 and 33 top-5, so the code scope helps there. Plane has few docs,
  so both scopes are the same.
- Absolute rates are modest, 25–33% top-5. The snapshots are 12–15 months older than the newest fixes, and many
  issues describe UI behaviour, not code.

## 2. Learning: the same issue in other words (code scope)
Each older issue was taught by its title, at the first changed line of its fix. It was then asked by its description
alone.

| repository | issues taught (placed) | right file first, before → after teaching | top 5, before → after | readouts led by learned code |
|---|---|---|---|---|
| Plane | 20 (16) | 2 → **16** | 4 → **16** | 14 |
| SigNoz | 66 (58) | 4 → **42** | 18 → **46** | 40 |

## 3. Generalizing to new questions (never taught), asked by title

| repository | new issues | top 1 / 3 / 5, before → after teaching | same area as a taught file: before → after |
|---|---|---|---|
| Plane | 20 | 5 / 5 / 6 → 4 / 5 / 6 | 5 issues: 2 / 2 / 3 → 2 / 2 / 3 |
| SigNoz | 67 | 11 / 17 / 21 → **6 / 11 / 19** | 17 issues: 4 / 5 / 7 → 4 / 5 / 6 |

**Not shown, and worse at the top:** for brand-new questions, a nearby learned match took the first place. On SigNoz,
top-1 fell from 11 to 6. In the hybrid, Claude reads that learned code once, and if it doesn't answer, it says so and
explores, which costs one cheap read. The value program found the reader never answered from 57 deliberately
misleading lessons. For the kit alone, though, learning helps repeated questions and does not yet help new ones.

**Files:**
- `plane_set.json`, `signoz_set.json` (issues, answer files, teach lines);
- `md_*.json`, `gf_*.json` (every readout);
- `score.py`, which prints these tables.
