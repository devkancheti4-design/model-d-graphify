# How related must a new question be to a learned one? (2026-10-15, Plane + SigNoz, offline)

Method: RELATION_METHOD.md, fixed before the analysis. The follow-ups below are labelled exploratory.

## The quantities, from the kit at zero model cost
- **Agreement:** a(q, u) = 1,024 − Hamming(bits(q), bits(u)). Chance has sd σ = 37 bits.
- **A unit's score:** max(own(u), cue(u)). own(u) is the question's agreement with the unit's code text. cue(u) is its
  best agreement with a taught question vector placed on that unit.
- **Router law, learned lane:** fires when cue(u₁) ≥ own(u₁) and a₁ − a₂ ≥ δ = 8 bits.
- **Relation margin:** m(q) = max_t a(q, t) − max_u own(u). It measures how much better the nearest learned question
  explains q than any code text does.

## What the data shows (172 questions)

**The pre-set hypothesis, r ≥ 2 against chance: failed.**
- Every question cleared it: median r was 6.3 for paraphrases and 5.0 for new questions.
- A question about a project is "related" to the project, so chance-relative closeness can't tell the same question
  from a neighbouring one.

**Learned code is exactly right or exactly wrong.**
- When learned code went first, it was right on 54 of 54 paraphrases and on 0 of 26 new questions.
- The margin separates the two:

  | kind | median margin m |
  |---|---|
  | paraphrases | 74 bits (≈ 2σ) |
  | new questions | 27 bits (< σ) |

**Exploratory limit, m ≥ σ = 37 bits.** Chosen after seeing SigNoz and checked on Plane. It keeps 85–86% of the
learned-first answers right:

| policy | paraphrases (85): right file first / top 5 | new questions (87): right file first / top 5 | bill vs Claude alone |
|---|---|---|---|
| cold, nothing learned | 6 / 22 | 16 / 27 | — |
| law as published | **58 / 62** | 10 / 25 | **2.15×** |
| limit on learned-first only | 57 / 62 | 10 / 25 | 1.95× |
| limit on all learned influence | 45 / 51 | 14 / 26 | 1.95× |

## The formula for the bill (Model D: kit + Claude)
A learned read costs E. If the learned code is wrong, Claude says so and explores, at a cost of E + K. With no
learned match, it costs K. So:

> **show learned code first when p(right | m) > E / K**

With the measured E = $0.0005 and K = $0.02, that bar is 2.5%. A wrong guess costs one cheap read, while a missed
repeat costs a full exploration, 40× more.

- **For the bill, the law as published is the right policy:** 2.15× cheaper than Claude alone on these 172 questions.
- **For the kit alone, without Claude** (ranking quality, such as a code search box), the relation limit on all
  learned influence protects new questions (14 vs 10 right first, cold 16), at the cost of 13 repeats.

Both limits ship as options in `ocm/router/lanes.py`, off by default: `RELATION_LIMIT` and `CERT_MIN_OVER_OWN`.

## Expected bill with learning
- **C = n_rep·[f·E + (1 − f)·K] + n_new·[g·(E + K) + (1 − g)·K]**
  - f: the share of repeats where learned code goes first and is right;
  - g: the share of new questions where learned code goes first and is wrong.
- **Saving = A·n / C.**

## Every law checked on the real SigNoz workspace (laws_check.py): 11 of 11
- **Vector law:** a text agrees with itself on all 1,024 bits, and 54 of 60 code units rank first for their own text.
- **Router law:**
  - every observation is one byte;
  - all 27 readout sequences end with "no more readouts", after 2–3 readouts;
  - advancing strictly reduces the live set.
- **Learned law:** all 6,561 searchable laws are monotone on all 256 words. The gate is honest: with 58 examples it
  stays off, because it hasn't beaten the vector order. It is working as specified, but adds nothing here yet.
- **Life:** byte-exact after reload. 58 of 58 taught entries hold the exact line of their file, and the 58 question
  vectors match the 58 entries. The carry tests pass (2 of 2).
- **Scope law:** 0 of 27 code-scope readouts contained a documentation file.
