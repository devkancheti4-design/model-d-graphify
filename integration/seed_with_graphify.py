"""Model D chooses where a graphify query starts.

Model D ranks the files most likely to hold the answer, then graphify expands from them with
`graphify query --seed` (graphify PR #4289). This shows the plug point only; it makes no claim about accuracy.

    python integration/seed_with_graphify.py <model-d-workspace> <graph.json> "<question>" [k]"""
import os, re, subprocess, sys

from ocm.server import Workspace


def top_files(ws_dir, question, k):
    out, root = Workspace(ws_dir).handle("ask", {"question": question}), None
    files = []
    for path in re.findall(r"(?m)^\d+\. \[([^\]:]+):\d+\]", out):
        rel = path.split("/", 1)[1] if "/" in path else path      # drop the workspace's folder name
        if rel not in files:
            files.append(rel)
    return files[:k]


if __name__ == "__main__":
    ws, graph, question = sys.argv[1], sys.argv[2], sys.argv[3]
    k = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    seeds = top_files(ws, question, k)
    print("Model D start files:", seeds, file=sys.stderr)
    cmd = ["graphify", "query", question, "--graph", graph]
    for s in seeds:
        cmd += ["--seed", s]
    sys.exit(subprocess.run(cmd).returncode)
