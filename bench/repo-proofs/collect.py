"""Collect recently merged pull requests that close a linked issue, with the files each changed.
    python collect.py <owner/name> <default branch> <out.json> [max PRs to scan]"""
import json, subprocess, sys, time
REPO, BRANCH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SCAN = int(sys.argv[4]) if len(sys.argv) > 4 else 600
owner, name = REPO.split("/")
Q = """query($owner:String!,$name:String!,$cursor:String,$base:String!){
 repository(owner:$owner,name:$name){
  pullRequests(states:MERGED, baseRefName:$base, first:25, after:$cursor, orderBy:{field:CREATED_AT,direction:DESC}){
   pageInfo{hasNextPage endCursor}
   nodes{ number title mergedAt mergeCommit{oid}
     closingIssuesReferences(first:3){nodes{number title body}}
     files(first:100){nodes{path}} } } } }"""
prs, cursor, seen = [], None, 0
while seen < SCAN:
    args = ["gh", "api", "graphql", "-f", f"query={Q}", "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"base={BRANCH}"]
    if cursor:
        args += ["-F", f"cursor={cursor}"]
    for attempt in range(5):
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode == 0:
            break
        print("retry", attempt + 1, r.stderr.strip()[:200], flush=True); time.sleep(5 * (attempt + 1))
    else:
        print("giving up at", seen, "PRs scanned"); break
    d = json.loads(r.stdout)["data"]["repository"]["pullRequests"]
    for n in d["nodes"]:
        seen += 1
        issues = n["closingIssuesReferences"]["nodes"]
        if issues and n["mergeCommit"]:
            prs.append({"pr": n["number"], "pr_title": n["title"], "merged": n["mergedAt"], "merge": n["mergeCommit"]["oid"],
                        "issue": issues[0]["number"], "title": issues[0]["title"], "body": issues[0]["body"] or "",
                        "files": [f["path"] for f in n["files"]["nodes"]]})
    if not d["pageInfo"]["hasNextPage"]:
        break
    cursor = d["pageInfo"]["endCursor"]
prs.sort(key=lambda p: p["merged"], reverse=True)
json.dump(prs, open(OUT, "w"), indent=1)
print(REPO, "scanned", seen, "merged PRs; closing an issue:", len(prs), "| newest", prs[0]["merged"][:10] if prs else "-", "oldest", prs[-1]["merged"][:10] if prs else "-")
