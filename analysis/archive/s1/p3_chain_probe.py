"""
p3_chain_probe.py  —  check current owners of the remaining far_mode_event_dispatch entries.
Run: idat -A -S"analysis/s1/p3_chain_probe.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import ida_funcs, idc, json
from pathlib import Path

# The 5 remaining P3 entries for far_mode_event_dispatch chain
# (original owner 0x33443, but after batch 1 split at 0x3352A, 0x33443 ends at 0x3352A)
TARGETS = [0x33468, 0x334C2, 0x339B2, 0x33C1B, 0x33D83]

LOG = Path("analysis/s1/p3_chain_probe.log")
OUT = Path("analysis/s1/p3_chain_probe.json")

results = []
log = []

for at in TARGETS:
    f = ida_funcs.get_func(at)
    if f is None:
        entry = {"at": hex(at), "owner": None, "note": "no_function"}
    else:
        # check if at is a function head
        is_head = (f.start_ea == at)
        entry = {
            "at": hex(at),
            "owner": hex(f.start_ea),
            "owner_end": hex(f.end_ea),
            "is_head": is_head,
            "note": "already_a_head" if is_head else "mid_body"
        }
    results.append(entry)
    log.append(str(entry))

OUT.write_text(json.dumps(results, indent=1))
LOG.write_text("\n".join(log))

import idaapi; idaapi.qexit(0)
