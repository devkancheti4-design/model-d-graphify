"""Model D cold context, then learning and generalization (METHOD.md). Writes md_<name>.json.
    PYTHONPATH=<optimal-context-mapping> python run_md.py <name>"""
import json, os, re, shutil, sys
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
from ocm.server import Workspace
W = os.path.dirname(os.path.abspath(__file__)); NAME = sys.argv[1]
D = json.load(open(f"{W}/{NAME}_set.json")); items = D["items"]
TAUGHT = "(readout: the code a taught question"


def parse(text):
    files = []
    for p in re.findall(r"(?m)^\d+\. \[([^\]:]+):\d+\]", text):
        p = p.split("/", 1)[1] if "/" in p else p
        if p not in files:
            files.append(p)
    return files


def ask(w, q, scope):
    """The served readout (ocm.loop.readout): the first, and the next too when the first is learned code (D1)."""
    first = w.handle("ask", {"question": q, "scope": scope}); text = first
    if first.startswith(TAUGHT):
        nxt = w.handle("next", {"question": q, "scope": scope})
        if nxt.startswith("(readout:"):
            text = first + "\n\n" + nxt
    return {"files": parse(text)[:10], "files_first": parse(first)[:10], "chars": len(text), "learned": first.startswith(TAUGHT)}


w = Workspace(f"{W}/ws/{NAME}")
cold = {f"{it['issue']}#{it['pr']}": {f"{q}|{s}": ask(w, it[q], s) for q in ("q_title", "q_400", "q_body") for s in ("code", "all")
                           if it[q]} for it in items}
half = len(items) // 2
teach, test = items[:half], items[half:]                          # oldest first
learn_dir = f"{W}/ws_learn/{NAME}"
shutil.rmtree(learn_dir, ignore_errors=True); shutil.copytree(f"{W}/ws/{NAME}", learn_dir)
wl = Workspace(learn_dir)
pairs = [{"question": it["q_title"], "at": it["teach_at"]} for it in teach if it["teach_at"]]
taught_msg = wl.handle("teach", {"pairs": pairs})
wl = Workspace(learn_dir)                                         # reloaded: what was taught is on disk
after = {f"{it['issue']}#{it['pr']}": {f"{q}|code": ask(wl, it[q], "code") for q in ("q_title", "q_body") if it[q]} for it in items}
taught_files = {it["teach_at"].rsplit(":", 1)[0] for it in teach if it["teach_at"]}
json.dump({"name": NAME, "snapshot": D["snapshot"], "teach_ids": [f"{it['issue']}#{it['pr']}" for it in teach],
           "test_ids": [f"{it['issue']}#{it['pr']}" for it in test], "taught_files": sorted(taught_files), "taught_msg": taught_msg,
           "cold": cold, "after": after}, open(f"{W}/md_{NAME}.json", "w"))
print(NAME, "issues", len(items), "| taught", len(pairs), "|", taught_msg)
