# Model D on Plane and SigNoz: finding context, learning it, generalizing it

Written 2026-10-15, before any result. This is exploratory: there are no predictions, and results are reported
whichever way they come out. Model D's job is context: where in the code to look. Nothing here writes a fix. A fixed
issue only supplies the answer key, which is the files its fix changed.

## Data
- **Issues:** recent pull requests merged into the default branch (makeplane/plane `preview`, SigNoz/signoz `main`)
  that close a linked issue (GitHub's closing references).
- **Answer files:** the files the pull request changed, minus:
  - tests (`test`/`tests`/`__tests__` folders, `.test.`, `.spec.`, `_test.go`, `test_*.py`);
  - documentation (`.md`, `.mdx`, `.rst`, `.txt`, `.adoc`);
  - lockfiles and `go.sum`;
  - translation files (`locales`, `i18n`, `translations`);
  - snapshots and minified files.
- **Snapshot:** the first parent of the oldest kept pull request's merge commit. Every fix comes after it, so none of
  the answers are in the indexed code. An issue is kept when at least one answer file exists in the snapshot.
- **Queries:**
  - the issue title;
  - the title plus the start of the body, cut to 400 characters;
  - for the learning test, the body alone: the first 400 characters after template headings and comments are removed.

## Tools
- **Model D 0.3.0** (optimal-context-mapping main), indexing the whole snapshot. `ask` runs with `"scope": "code"`
  and with the full scope. Files count in rank order, top 10 kept.
- **Graphify**, its latest release. `graphify update --no-cluster` builds the graph, with output outside the
  repository. Queries use defaults: BFS, depth 2, 2,000-token budget. Files count in printed order.

## Measures
1. **Cold context:** for each issue and query, whether an answer file is in the top 1, 3 and 5, and the tokens handed
   over (characters divided by 4).
2. **Learning and generalization** (Model D, code scope). Issues are sorted by merge date and split into an older half
   and a newer half.
   - **Teaching:** each older issue is taught to a copy of the workspace. The question is the issue title. The
     location is the first answer file, at the first changed line of its diff (the hunk's old-side start line).
   - **L1, the same issue in other words:** each taught issue is asked by its body alone, cold and after teaching.
     Measured: top-1 and top-5 hits, and the share of readouts led by learned code.
   - **L2, new questions:** each newer issue, never taught, is asked by its title, cold and after teaching. Measured:
     top-1, 3 and 5 hits, for all newer issues and for those whose answer files were among the taught files (the
     same area of the code).

## Windows (chosen from file listings, before any query was run)
- **Plane:** the newest 50 issue-closing pull requests. The snapshot is `3618ffc`, from 2025-07-10, and 40 issues
  keep an answer file. A window of 70 kept only 20, because Plane reorganised its code.
- **SigNoz:** the newest 150. The snapshot is `8a0c5bc`, from 2025-10-19, and 134 issues keep an answer file.

## Deviations (recorded after the first Plane run)
- **D1, the served readout.** When the first readout is learned code, Model D's hybrid and hooks also send the next
  readout (`ocm.loop.readout`). The first run kept only the first readout, a single unit, so a wrong learned match
  pushed every other file out of the top 5. All Model D results now count the served readout: the first readout, plus
  the next one when the first is learned. The first-readout-only numbers are reported too. Cold results don't change,
  because nothing is learned yet.
- **D2, keys.** Results are keyed by issue and pull request together, because one SigNoz issue is closed by two pull
  requests.
