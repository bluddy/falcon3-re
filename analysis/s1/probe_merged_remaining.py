#!/usr/bin/env python3
"""
Probe the 1 remaining merged function after finding 179.
"""
import os
os.environ["DBFL_KILL"] = "1"

import idc
import idaapi
import idautils
import json

# Target: sub_4113C with split at 0x41167 (after jmp)
target = 0x4113C
split_at = 0x41167

result = {
    "target": f"0x{target:X}",
    "split_at": f"0x{split_at:X}",
    "function_name": idc.get_func_name(target),
    "function_start": f"0x{idc.get_func_attr(target, idc.FUNCATTR_START):X}",
    "function_end": f"0x{idc.get_func_attr(target, idc.FUNCATTR_END):X}",
}

# Check what's at split_at
result["split_mnem"] = idc.print_insn_mnem(split_at)
result["split_disasm"] = idc.generate_disasm_line(split_at, 0)

# Check what's before split_at
prev_ea = idc.prev_head(split_at)
result["prev_ea"] = f"0x{prev_ea:X}"
result["prev_mnem"] = idc.print_insn_mnem(prev_ea)
result["prev_disasm"] = idc.generate_disasm_line(prev_ea, 0)

# Get xrefs to split point
xrefs_to = []
for xref in idautils.XrefsTo(split_at):
    xrefs_to.append({
        "from": f"0x{xref.frm:X}",
        "type": xref.type,
        "from_func": idc.get_func_name(xref.frm)
    })
result["xrefs_to_split"] = xrefs_to

# Get disassembly around the split
lines_before = []
ea = target
for i in range(50):  # Get up to 50 lines
    if ea >= split_at:
        break
    lines_before.append(f"{ea:08X}: {idc.generate_disasm_line(ea, 0)}")
    ea = idc.next_head(ea)

lines_after = []
ea = split_at
for i in range(30):  # Get 30 lines after split
    lines_after.append(f"{ea:08X}: {idc.generate_disasm_line(ea, 0)}")
    next_ea = idc.next_head(ea)
    if next_ea == idc.BADADDR:
        break
    ea = next_ea

result["disasm_before_split"] = lines_before
result["disasm_after_split"] = lines_after

# Check if there are any internal jumps crossing the boundary
result["internal_jumps_crossing"] = []
for ea in idautils.FuncItems(target):
    for xref in idautils.XrefsFrom(ea):
        if xref.to >= target and xref.to < idc.get_func_attr(target, idc.FUNCATTR_END):
            # Internal xref
            crosses_up = ea >= split_at and xref.to < split_at
            crosses_down = ea < split_at and xref.to >= split_at
            if crosses_up or crosses_down:
                result["internal_jumps_crossing"].append({
                    "from": f"0x{ea:X}",
                    "to": f"0x{xref.to:X}",
                    "direction": "up" if crosses_up else "down"
                })

# Write output
with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/merged_remaining.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"Analyzed sub_4113C split at 0x41167")
print(f"Xrefs to split: {len(xrefs_to)}")
print(f"Internal jumps crossing: {len(result['internal_jumps_crossing'])}")

idc.qexit(0)
