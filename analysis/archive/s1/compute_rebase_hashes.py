#!/usr/bin/env python3
"""Compute sha256 hashes for new REBASE entries."""
import os
os.environ["DBFL_KILL"] = "1"

import hashlib
import idc
import json

# New REBASE entries for finding 205
rebases = [
    (0x407BF, 0x407BE, 0x40843, 0x407BE, None),  # sub_407BF
    (0x40DDB, 0x40DDA, 0x40E35, 0x40DDA, None),  # sub_40DDB
    (0x40C69, 0x40C68, 0x40C73, 0x40C68, None),  # sub_40C69
    (0x40045, 0x40044, 0x4005C, 0x40044, None),  # sub_40045
    (0x3FD66, 0x3FD65, 0x3FD89, 0x3FD65, None),  # sub_3FD66
    (0x404F1, 0x404F0, 0x404F6, 0x404F0, None),  # sub_404F1
]

results = []
for old_start, new_start, end, clear_lo, ds_para in rebases:
    clear_hi = end  # Default if not specified
    
    # Get function name
    func_name = idc.get_func_name(old_start)
    
    # Get bytes for sha256 of clear region
    clear_bytes = idc.get_bytes(clear_lo, clear_hi - clear_lo)
    sha256 = hashlib.sha256(clear_bytes).hexdigest() if clear_bytes else "none"
    
    entry = {
        "old": f"0x{old_start:X}",
        "new": f"0x{new_start:X}",
        "end": f"0x{end:X}",
        "clear_lo": f"0x{clear_lo:X}",
        "clear_hi": f"0x{clear_hi:X}",
        "name": func_name if func_name else "sub_%X" % old_start,
        "sha256": sha256,
        "size": end - new_start,
    }
    results.append(entry)
    print(f"{entry['old']} -> {entry['new']}: {entry['name']} ({entry['size']}B), sha256={sha256[:16]}...")

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/rebase_manifest.json", "w") as f:
    json.dump(results, f, indent=2)

idc.qexit(0)
