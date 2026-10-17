"""Finding 59 step 1a (host, read-only): build the carve seed list for
`sub_2E2F0` exactly as finding 58 defined it:

  * every target of a CALL that originates INSIDE the blob (343),
  * every target CALLED from another function (22),
  * every target reached through a thunk slot (10),
  * plus the blob start itself.

Writes analysis/ida_falconcd/carve_seeds.json -> {"seeds": [ea...]}.

Usage: venv\\Scripts\\python tools\\carve_seeds.py
"""
import json
from bisect import bisect_right
from pathlib import Path

IDA = Path("analysis/ida_falconcd")
LO, HI = 0x2E2F0, 0x3ACAC
THUNK_LO, THUNK_HI = 0x2BD9D, 0x2C973

cls = json.loads((IDA / "classification.json").read_text())
refs = json.loads((IDA / "callgraph_refs.json").read_text())["refs"]
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())
starts = [x[0] for x in ivs]


def owner(ea):
    i = bisect_right(starts, ea) - 1
    return ivs[i][2] if i >= 0 and ivs[i][0] <= ea < ivs[i][1] else None


internal_call, ext_call, thunk = set(), set(), set()
for s, d, c in refs:
    if not (LO <= d < HI):
        continue
    if THUNK_LO <= s < THUNK_HI:
        thunk.add(d)
    elif c and LO <= s < HI:
        internal_call.add(d)
    elif c and owner(s) not in (None, "sub_2E2F0"):
        ext_call.add(d)

seeds = sorted({LO} | internal_call | ext_call | thunk)
(IDA / "carve_seeds.json").write_text(json.dumps({"seeds": seeds}))

print("internal CALL targets : %d" % len(internal_call))
print("external CALL targets : %d" % len(ext_call))
print("thunk targets         : %d" % len(thunk))
print("union (+ blob start)  : %d" % len(seeds))
print("range: 0x%X..0x%X   avg gap %.1f B"
      % (LO, HI, (HI - LO) / max(1, len(seeds) - 1)))
