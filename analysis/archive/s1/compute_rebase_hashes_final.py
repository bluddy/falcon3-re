#!/usr/bin/env python3
"""Compute correct sha256 hashes for new REBASE entries."""
import os
os.environ["DBFL_KILL"] = "1"

import hashlib
import idc
import ida_bytes
import json

def sha(ea, end):
    """Match the sha function from apply_orphan_funcs.py"""
    return hashlib.sha256(ida_bytes.get_bytes(ea, end - ea)).hexdigest()

# New REBASE entries for finding 205
# Format: (old_start, new_start, end, clear_lo, ds_para)
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
    # Get function name at old location
    func_name = idc.get_func_name(old_start)
    if not func_name:
        func_name = "sub_%X" % old_start
    
    # Check if function is far
    f = idc.get_func_attr(old_start, idc.FUNCATTR_FLAGS)
    is_far = bool(f & 0x0001) if f != idc.BADADDR else True  # Assume far if unknown
    
    # Compute the THREE required sha256 values (matching line 1562-1563)
    main_sha = sha(new_start, end)         # sha256 of [new_start, end)
    old_sha = sha(old_start, end)          # old_sha256 of [old_start, end)
    prefix_sha = sha(new_start, old_start) if old_start > new_start else ""  # prefix
    
    entry = {
        "ea": new_start,
        "old_ea": old_start,
        "end": end,
        "clear_lo": clear_lo,
        "ds": ds_para,
        "name": func_name,
        "far": is_far,
        "sha256": main_sha,
        "old_sha256": old_sha,
        "prefix_sha256": prefix_sha,
        "lost_heads": None
    }
    results.append(entry)
    print(f"{func_name}: 0x{old_start:X} -> 0x{new_start:X}")
    print(f"  sha256={main_sha[:16]}...")
    print(f"  old_sha256={old_sha[:16]}...")
    print(f"  prefix_sha256={prefix_sha[:16] if prefix_sha else '(empty)'}...")

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/rebase_manifest_final.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nWrote {len(results)} entries to rebase_manifest_final.json")

idc.qexit(0)
