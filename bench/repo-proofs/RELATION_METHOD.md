# How related must a new question be for learned code to help? (written 2026-10-15, before the analysis)

## The quantities (all from the kit, at zero model cost)
For a question q, with the code scope:
- **a_cue:** the bit agreement between q's 1,024-bit vector and the best taught question vector (cue) on the unit
  ranked first.
- **a_2:** the second-best unit's score.
- **a_med:** q's median agreement over all code units, its chance level.
- **σ = 37 bits:** the router law's measured sd of chance agreement (GAP = 74 = 2σ).
- **lead = a_cue − a_2:** the router fires the learned lane when lead ≥ DELTA = 8 bits and the top unit's score comes
  from a cue.
- **relatedness r = (a_cue − a_med) / σ.**

## The question
The law gates the learned lane on the lead alone. A new question only loosely related to a taught one can fire it.

**Hypothesis, fixed now:** the learned lane should also need r ≥ 2 (a_cue at least GAP = 74 bits above the
question's chance level). That is the same 2σ rule the law already uses for FLAT, so it is chosen from the geometry,
not swept on this data.

## Data
The learned workspaces from the Plane and SigNoz runs (`ws_learn/`).
- **Paraphrases (L1):** taught issues asked by their body.
- **New questions (L2):** never-taught issues asked by their title.

A learned match is correct when the top learned unit's file is one of the issue's answer files.

## Reported
- r for paraphrases and for new questions.
- The precision of fired learned matches by band of r.
- L1 and L2 top-1, and top-5 for the served readout, with the hypothesised gate (r ≥ 2) and without it, against cold.
- The gate is judged on both repositories together. An empirical curve is shown for reference, but the limit tested is
  the pre-set r ≥ 2. A limit that would be chosen from this curve is reported as a proposal, to be tested on new data.
