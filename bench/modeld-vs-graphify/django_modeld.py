"""Model D's kit on the 114 SWE-bench Lite Django issues: is the file the official fix changed among the first 1, 3, 5
files of the kit's readout? Uses the same issues as ../graphify-seed (django_swebench_lite_114.json).
Build the index first over the `django/` package of a Django checkout at 4a72da71001f154ea60906a2f74898d32b7322a7:
    ocm build <checkout>/django --out ws/django
    python django_modeld.py ws/django"""
import json, os, re, sys
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
from ocm.server import Workspace

HERE = os.path.dirname(os.path.abspath(__file__))
w = Workspace(sys.argv[1])
issues = json.load(open(os.path.join(HERE, "..", "graphify-seed", "django_swebench_lite_114.json")))
for key, label in (("query_title", "issue title"), ("query_400", "title + 400 characters")):
    hits = {1: 0, 3: 0, 5: 0}; chars = 0
    for it in issues:
        out = w.handle("ask", {"question": it[key]}); chars += len(out); files = []
        for p in re.findall(r"(?m)^\d+\. \[([^\]:]+):\d+\]", out):
            p = p.split("/", 1)[1] if "/" in p else p       # drop the indexed folder's name
            if p not in files: files.append(p)
        for k in hits:
            hits[k] += it["gold_file"].removeprefix("django/") in files[:k]
    print(f"{label}: top-1 {hits[1]}, top-3 {hits[3]}, top-5 {hits[5]} of {len(issues)}; ~{chars / len(issues) / 4:,.0f} tokens per issue")
