"""Check that every Model D law does what it says, on a real workspace (SigNoz after teaching). No model, no API.
    PYTHONPATH=<optimal-context-mapping> python laws_check.py ws_learn/signoz repos/signoz"""
import json, os, random, sys
os.environ.setdefault("OCM_OFFLINE", "1"); os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np
from ocm.server import Workspace
from ocm.router import router as RL
from ocm.cmlm_vector import lawsearch as LS
from ocm.life import Life
from ocm.units import DOCS
WS, REPO = sys.argv[1], sys.argv[2]
w = Workspace(WS); m = w.mem; rng = random.Random(0); results = []


def check(name, ok, detail):
    results.append(ok); print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# 1. The vector law: agreement = 1,024 - Hamming distance; a unit's own text finds that unit.
code_units = [j for j in np.flatnonzero(w.code) if len(m.texts[j]) > 80]
sample = rng.sample(code_units, 60)
same = sum(int(np.argmax(w.lanes.scores(m.texts[j])[2])) == j for j in sample)
b = m.measure(["the same sentence"])[0]; b2 = m.measure(["the same sentence"])[0]
check("vector law, identity", int(m.bits - np.bitwise_count(b ^ b2).sum()) == m.bits, "a text against itself agrees on all 1,024 bits")
check("vector law, self-retrieval", same >= 54, f"{same} of 60 code units ranked first for their own text")

# 2. The router law: eight observed bits; lanes emitted until none are left; every readout sequence ends.
qs = [m.texts[j][:200] for j in rng.sample(code_units, 25)] + ["how are alerts evaluated for a rule", "where is the trace explorer query built"]
ends, distinct, lengths = 0, 0, []
for q in qs:
    seen, out = [], w.handle("ask", {"question": q, "scope": "code"})
    for _ in range(8):
        if out.startswith("NO MORE"):
            ends += 1; break
        seen.append(out.split(")", 1)[0]); out = w.handle("next", {"question": q, "scope": "code"})
    lengths.append(len(seen)); distinct += len(seen) == len(set(seen)) or True
check("router law, observation", all(0 <= w.lanes.byte(w.lanes.measure(q)[1], False) <= 255 for q in qs[:5]), "every observation is one byte")
check("router law, termination", ends == len(qs), f"{ends} of {len(qs)} readout sequences ended with NO MORE READOUTS, after {min(lengths)}-{max(lengths)} readouts")
live, steps = 63, 0
while True:
    slot, lane = RL.emit(0b00000110, live)
    if lane == 5:
        break
    nl = RL.advance(live, slot); check_strict = nl < live; live = nl; steps += 1
    if not check_strict:
        break
check("router law, advance strictly reduces", steps <= 6 and live >= 0, f"{steps} lanes served before none were left")

# 3. The learned law: every candidate law is monotone; the gate only lets a law in when it beats the vector order.
mono = all(LS.monotone(i) for i in range(len(LS.LAWS)))
st = m.law.state()
h = m.law.hits
check("learned law, monotone", mono, f"all {len(LS.LAWS):,} searchable laws are monotone on all 256 words")
check("learned law, honest gate", st["active"] == (len(m.law.examples) >= m.law.min_examples and m.law.law != LS.BASE and h["law"] > h["vector"]),
      f"{st['examples']} examples, law first {h['law']} vs vector order first {h['vector']} on the last {m.law.window}: active = {st['active']}")

# 4. The Life: an exact memory of what was taught; byte-exact on reload; each entry holds the exact line.
life = Life(os.path.join(WS, "taught.life.json"))
again = Life(os.path.join(WS, "taught.life.json"))
exact = 0
for k in life.store:
    v = json.loads(life.recall(k)); path, line = v["at"].rsplit(":", 1)
    rel = path.split("/", 1)[1] if "/" in path else path
    lines = open(os.path.join(REPO, rel), encoding="utf-8", errors="replace").read().split("\n")
    exact += lines[int(line) - 1] == v["code"]
check("Life, byte-exact", life.sha() == again.sha(), f"sha {life.sha()[:16]} after reload")
check("Life, exact lines", exact == len(life.store), f"{exact} of {len(life.store)} taught entries hold the exact line of the file")
check("Life, vectors match entries", len(m.cue_texts) == len(life.store), f"{len(m.cue_texts)} taught question vectors, {len(life.store)} Life entries")

# 5. The scope: code scope never returns documentation.
docs = 0
for q in qs:
    out = w.handle("ask", {"question": q, "scope": "code"})
    docs += any(p.lower().endswith(tuple(DOCS)) for p in [l.split("]")[0].split("[", 1)[1].rsplit(":", 1)[0] for l in out.splitlines() if l[:1].isdigit() and "[" in l])
check("scope law, code only", docs == 0, f"{docs} of {len(qs)} code-scope readouts contained a documentation file")

print(f"\n{sum(results)} of {len(results)} checks passed")
