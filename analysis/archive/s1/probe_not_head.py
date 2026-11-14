#!/usr/bin/env python3
"""
Probe not_head misdecodes - calls landing mid-instruction.
"""
import os
os.environ["DBFL_KILL"] = "1"

import idc
import idaapi
import idautils
import json

# Targets from survey_mid.json
targets = [
    (0x2EFE1, 0x2EFE0, "viewvec_loop_project"),
    (0x3592C, 0x356A7, "viewvec_half_add_step"),
    (0x407C0, 0x407BF, "sub_407BF"),
    (0x40BC6, 0x40BC5, "sub_40BC5"),
    (0x403BE, 0x403BD, "sub_403BD"),
    (0x40DDC, 0x40DDB, "sub_40DDB"),
    (0x40C6A, 0x40C69, "sub_40C69"),
    (0x40046, 0x40045, "sub_40045"),
    (0x3FD67, 0x3FD66, "sub_3FD66"),
    (0x404F2, 0x404F1, "sub_404F1"),
]

results = []

for target_ea, func_start, func_name in targets[:5]:  # Check first 5
    result = {
        "target": f"0x{target_ea:X}",
        "func_start": f"0x{func_start:X}",
        "func_name": func_name,
    }
    
    # Get xrefs to target
    xrefs = []
    for xref in idautils.XrefsTo(target_ea):
        xrefs.append({
            "from": f"0x{xref.frm:X}",
            "type": xref.type,
            "from_func": idc.get_func_name(xref.frm) or "?"
        })
    result["xrefs_count"] = len(xrefs)
    result["xrefs"] = xrefs[:10]  # First 10
    
    # Check if target is mid-instruction
    insn_start = idc.get_item_head(target_ea)
    result["insn_start"] = f"0x{insn_start:X}"
    result["is_mid_insn"] = (insn_start != target_ea)
    
    if result["is_mid_insn"]:
        result["insn_at_head"] = idc.generate_disasm_line(insn_start, 0)
    
    # Get disassembly around target (both alignments if mid-insn)
    lines_around = []
    ea = func_start
    for i in range(20):
        if ea > target_ea + 20:
            break
        marker = " <-- TARGET" if ea == target_ea else ""
        marker += " <-- INSN_HEAD" if ea == insn_start else ""
        lines_around.append(f"{ea:08X}: {idc.generate_disasm_line(ea, 0)}{marker}")
        ea = idc.next_head(ea)
    result["disasm_around"] = lines_around
    
    results.append(result)

# Write output
with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/not_head_probe.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Probed {len(results)} not_head targets")
for r in results:
    print(f"  {r['target']}: {r['xrefs_count']} xrefs, mid_insn={r['is_mid_insn']}")

idc.qexit(0)
