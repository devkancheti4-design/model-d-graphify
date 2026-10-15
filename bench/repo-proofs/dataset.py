"""Build each repo's test set: kept issues with their answer files at the snapshot, queries, and the teach location
(first answer file with a diff hunk, at the hunk's old-side start line). python dataset.py <owner/name> <prs.json> <N> <out>"""
import json, re, subprocess, sys
from gold import answer_files
REPO, PRS, N, OUT = sys.argv[1], json.load(open(sys.argv[2])), int(sys.argv[3]), sys.argv[4]
def gh(*a):
    return json.loads(subprocess.run(["gh", "api", *a], capture_output=True, text=True, check=True).stdout)
win = PRS[:N]
snap = gh(f"repos/{REPO}/commits/{win[-1]['merge']}")["parents"][0]["sha"]
paths = {e["path"] for e in gh(f"repos/{REPO}/git/trees/{snap}?recursive=1")["tree"] if e["type"] == "blob"}
def clean_body(b):
    lines = [l for l in re.sub(r"<!--.*?-->", "", b, flags=re.S).splitlines() if l.strip() and not l.lstrip().startswith("#")]
    return " ".join(" ".join(lines).split())
items = []
for p in reversed(win):                                   # oldest first
    gold = [f for f in answer_files(p["files"]) if f in paths]
    if not gold:
        continue
    files = gh(f"repos/{REPO}/pulls/{p['pr']}/files?per_page=100")
    at = None
    for f in files:
        if f["filename"] in gold and f.get("patch"):
            m = re.search(r"^@@ -(\d+)", f["patch"], re.M)
            if m:
                at = f"{f['filename']}:{max(1, int(m.group(1)))}"; break
    body = clean_body(p["body"])
    items.append({"issue": p["issue"], "pr": p["pr"], "merged": p["merged"], "title": p["title"],
                  "q_title": p["title"], "q_400": (p["title"] + "\n" + body)[:400], "q_body": body[:400],
                  "gold": gold, "teach_at": at})
json.dump({"repo": REPO, "snapshot": snap, "items": items}, open(OUT, "w"), indent=1)
print(REPO, "snapshot", snap[:7], "issues", len(items), "with a teach line", sum(1 for i in items if i["teach_at"]),
      "with a body", sum(1 for i in items if len(i["q_body"]) >= 40))
