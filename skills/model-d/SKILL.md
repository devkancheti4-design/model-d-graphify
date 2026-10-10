---
name: model-d
description: Use when answering a question about this codebase, or finding where something is implemented, configured or documented. Ask the Model D workspace first (workspace_ask), answer from what it returns when that is enough, and teach it each answer's path:line once at the end of the work.
---

# Model D: ask the workspace first

Model D maps this repository on your machine. For a question, it ranks the code blocks and doc sentences most likely to
hold the answer. It learns from every answered question, so a teammate's similar question goes straight to the right
line next time.

## How to work with it

1. **Before searching the code**, call `workspace_ask` with the question in plain words.
   - If the code it returns answers the question, answer from it. No search is needed.
   - If not, call `workspace_next` once, then search as usual.
2. **For every question you answered**, keep the one line its answer is on, as `path:line`.
3. **At the end of your work**, call `workspace_teach` once with every question and its `path:line`. One call for
   everything keeps the cost down.

What it returns is ranked, not verified. Use it only when it actually answers the question.

## If the tools are missing or fail

The tools need the Model D package and a running workspace server. Set them up once, in a terminal:

```bash
python3 -m venv ~/modeld && ~/modeld/bin/pip install "numpy>=2.0" "torch>=2.1" "transformers>=4.40"
~/modeld/bin/pip install --no-index --find-links "${CLAUDE_PLUGIN_ROOT}/wheels" optimal-context-mapping
~/modeld/bin/ocm build /path/to/your/repo --out ~/modeld-ws      # once per repository
~/modeld/bin/ocm serve ~/modeld-ws                               # leave running
```

Then set this plugin's **Python with Model D installed** option to the venv's Python, for example
`/Users/you/modeld/bin/python`, and restart Claude Code.

The package runs on macOS (Apple silicon) and on Linux x86-64, including Windows WSL2, with Python 3.10-3.14. It
needs a local process, so it works in Claude Code and the desktop app, not in claude.ai on the web.
