"""For candidate windows of the newest N issues, how many keep an answer file that exists at the snapshot (the parent of
the window's oldest merge)? Uses GitHub's tree listing; no clone. python cutoff.py <owner/name> <prs.json>"""
import json, subprocess, sys
from gold import answer_files
REPO, PRS = sys.argv[1], json.load(open(sys.argv[2]))
def gh(*a):
    return json.loads(subprocess.run(["gh", "api", *a], capture_output=True, text=True, check=True).stdout)
for n in (30, 50, 75, 100, 150, 223):
    if n > len(PRS):
        n = len(PRS)
    win = PRS[:n]                               # newest first
    oldest = win[-1]
    parent = gh(f"repos/{REPO}/commits/{oldest['merge']}")["parents"][0]["sha"]
    t = gh(f"repos/{REPO}/git/trees/{parent}?recursive=1")
    paths = {e["path"] for e in t["tree"] if e["type"] == "blob"}
    kept = [p for p in win if any(f in paths for f in answer_files(p["files"]))]
    print(f"{REPO} newest {n:>3}: snapshot {parent[:7]} ({oldest['merged'][:10]}), files {len(paths):,}{' TRUNCATED' if t.get('truncated') else ''}, kept {len(kept)}")
    if n == len(PRS):
        break
