"""The answer files of a fix: what it changed, minus tests, docs, lockfiles, translations, snapshots and minified files."""
import re
DOCS = (".md", ".mdx", ".rst", ".txt", ".adoc")
LOCKS = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "go.sum", "poetry.lock", "Cargo.lock", "uv.lock", "bun.lockb")
TEST = re.compile(r"(^|/)(tests?|__tests__|e2e|cypress|playwright)(/|$)|\.(test|spec)\.|_test\.go$|(^|/)test_[^/]*\.py$|(^|/)conftest\.py$")
I18N = re.compile(r"(^|/)(locales?|i18n|translations)(/|$)")


def answer_files(files):
    out = []
    for f in files:
        base = f.rsplit("/", 1)[-1]
        if f.lower().endswith(DOCS) or base in LOCKS or base.endswith(".lock") or TEST.search(f) or I18N.search(f) \
                or f.endswith((".snap", ".min.js", ".min.css")) or "/__snapshots__/" in f:
            continue
        out.append(f)
    return out
