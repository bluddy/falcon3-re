"""Insert Level-1 naming entries into registry/routines.yaml (finding 43).

Two bugs from finding 41 are avoided deliberately here:
  * ea compared as INT (YAML parses `0xNNN` as int; a str never matches);
  * ea/seg/ofs written UNQUOTED so they round-trip as ints (yaml.dump would
    emit decimal or a quoted string, both wrong for this file's style).
Splices before the trailing `counts:` anchor (never at file top) and
refreshes `counts.tracked` / `total_functions` / classification.

Idempotent: skips eas already tracked.

Usage: venv\\Scripts\\python tools\\add_routines_l1.py
"""
import json
import re
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(".")
NAMING = ROOT / "registry" / "naming.yaml"
ROUTINES = ROOT / "registry" / "routines.yaml"
CLS = ROOT / "analysis" / "ida_falconcd" / "classification.json"

naming = yaml.safe_load(NAMING.read_text(encoding="utf-8"))
cls = yaml.safe_load(CLS.read_text(encoding="utf-8"))
text = ROUTINES.read_text(encoding="utf-8")
rout = yaml.safe_load(text) or {}

# CRITICAL (finding 41): normalize to int on BOTH sides before comparing.
existing_eas = set()
for e in rout.get("routines", []):
    ea = e.get("ea")
    if isinstance(ea, str) and ea.lower().startswith("0x"):
        ea = int(ea, 16)
    existing_eas.add(ea)

# Level-1 batch = entries carrying `sig` that were NOT already inserted in
# finding 39/41 (those have been inserted already; this picks up new ones).
targets = []
for e in naming["symbols"]:
    if not e.get("sig") or e["ida"] not in cls:
        continue
    ea = cls[e["ida"]]["ea"]
    if ea not in existing_eas:
        targets.append((ea, e, cls[e["ida"]]))

if not targets:
    print("nothing to insert")
    raise SystemExit(0)

blocks = []
for ea, e, info in sorted(targets):
    # strings via json.dumps: single-line, escaped -> valid YAML double-quoted
    # scalar. (yaml.dump folds at width=80 and emitted unindented continuation
    # lines, which broke the document -- finding 43.)
    blocks.append(
        "  - ea: 0x{ea:X}\n"
        "    seg: 0x{seg:X}\n"
        "    ofs: 0x{ofs:X}\n"
        "    size: {size}\n"
        "    far: {far}\n"
        "    class: {cls}\n"
        "    hypothesis: {hyp}\n"
        "    sig: {sig}\n"
        "    port_status: unported\n"
        "    verified: null\n"
        "    notes: {notes}\n"
        '    updated: "2026-10-16"\n'.format(
            ea=ea, seg=ea >> 4, ofs=ea & 0xF, size=info["size"],
            far="true" if info.get("far", True) else "false",
            cls=info.get("class", "ASM"),
            hyp=json.dumps(e["name"]),
            sig=json.dumps(e["sig"]),
            notes=json.dumps(e.get("notes", "")),
        )
    )

marker = "\ncounts:\n"
if marker not in text:
    raise SystemExit("anchor '\\ncounts:\\n' not found")
head, tail = text.split(marker, 1)
new_text = head + "\n" + "\n".join(blocks) + "\n" + marker + tail

c = Counter(v["class"] for v in cls.values())
n = len(cls)
tracked = len(rout.get("routines", [])) + len(blocks)
new_text = re.sub(r"^(  tracked: )\d+", r"\g<1>%d" % tracked,
                  new_text, count=1, flags=re.M)
new_text = re.sub(r"^(  total_functions: )\d+.*$",
                  r"\g<1>%d           # matches classification.json (findings 39-43)" % n,
                  new_text, count=1, flags=re.M)
for k in ("ASM", "C", "DATA", "LEAF", "NEARTHUNK"):
    new_text = re.sub(r"^(    %s: )\d+" % k, r"\g<1>%d" % c.get(k, 0),
                      new_text, count=1, flags=re.M)

ROUTINES.write_text(new_text, encoding="utf-8")

# ---- assertions (finding 41: assert the round-trip) ----
back = yaml.safe_load(ROUTINES.read_text(encoding="utf-8"))
eas = [e.get("ea") for e in back["routines"]]
types = Counter(type(x).__name__ for x in eas)
assert len(eas) == len(set(eas)), "DUPLICATE eas!"
assert set(types) == {"int"}, "non-int ea remain: %r" % types
fb = json.load(open("analysis/ida_falconcd/function_bytes.json"))
by_ea = {v["ea"]: k for k, v in fb.items()}
hyp_ok = sum(1 for e in back["routines"] if e.get("hypothesis")
             and e["ea"] in by_ea)
print("inserted %d; routines=%d; unique ea=%d; ea types=%s; tracked=%d; hypothesis-resolvable=%d"
      % (len(blocks), len(eas), len(set(eas)), dict(types),
         back["counts"]["tracked"], hyp_ok))
