#!/usr/bin/env python3
"""Check which REBASE entries are already applied."""
import os
os.environ["DBFL_KILL"] = "1"

import idc
import json

# REBASE entries from apply_orphan_funcs.py
rebase_entries = [
    (0x106EEC, 0x106EE2, "r12_state36_reset_stub"),
    (0x10843D, 0x108430, "r15_op_init_sequence"),
    (0x10CFA6, 0x10CE30, "r27_table_copy_far_entry"),
    (0x4335A, 0x4334E, "unknown"),
    (0x6EF31, 0x6EF30, "r17_ui_event_loop"),
    (0x69723, 0x69720, "r6e_heap_layout_finish"),
    (0x16F4B5, 0x16F4B1, "unknown"),
    (0x6940E, 0x6940B, "r30_record_link"),
    (0x683C5, 0x683C1, "ui_loadout_menu_enter"),
]

results = []
for old_start, new_start, expected_name in rebase_entries:
    result = {
        "old_start": f"0x{old_start:X}",
        "new_start": f"0x{new_start:X}",
        "expected_name": expected_name,
    }
    
    # Check if a function exists at old_start
    func_at_old = idc.get_func_name(old_start)
    result["func_at_old"] = func_at_old if func_at_old else "none"
    
    # Check if a function exists at new_start
    func_at_new = idc.get_func_name(new_start)
    result["func_at_new"] = func_at_new if func_at_new else "none"
    
    # Check function boundaries
    if func_at_new:
        func_start = idc.get_func_attr(new_start, idc.FUNCATTR_START)
        result["actual_start"] = f"0x{func_start:X}"
        result["rebase_applied"] = (func_start == new_start)
    else:
        result["actual_start"] = "n/a"
        result["rebase_applied"] = False
    
    results.append(result)

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/rebase_applied.json", "w") as f:
    json.dump(results, f, indent=2)

for r in results:
    status = "APPLIED" if r["rebase_applied"] else "NOT_APPLIED"
    print(f"{r['new_start']}: {status} - {r['func_at_new']}")

idc.qexit(0)
