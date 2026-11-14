#!/usr/bin/env python3
"""
Check if the not_head functions need REBASE (start 1 byte earlier).
"""
import os
os.environ["DBFL_KILL"] = "1"

import idc
import idaapi
import idautils
import json

# Not_head targets where call lands 1 byte into current function
candidates = [
    (0x2EFE0, "viewvec_loop_project"),
    (0x356A7, "viewvec_half_add_step"),  
    (0x407BF, "sub_407BF"),
    (0x40BC5, "sub_40BC5"),
    (0x403BD, "sub_403BD"),
    (0x40DDB, "sub_40DDB"),
    (0x40C69, "sub_40C69"),
    (0x40045, "sub_40045"),
    (0x3FD66, "sub_3FD66"),
    (0x404F1, "sub_404F1"),
]

results = []

for func_ea, func_name in candidates:
    result = {
        "current_start": f"0x{func_ea:X}",
        "func_name": func_name,
        "proposed_start": f"0x{func_ea-1:X}",
    }
    
    # Check what's 1 byte before
    prev_ea = func_ea - 1
    result["prev_byte"] = f"0x{idc.get_wide_byte(prev_ea):02X}"
    
    # Try to get disassembly at prev_ea
    # First check if it's in a function
    prev_func = idc.get_func_name(prev_ea)
    result["prev_in_func"] = prev_func if prev_func else "none"
    
    # Get xrefs to current start
    xrefs_to_current = []
    for xref in idautils.XrefsTo(func_ea):
        xrefs_to_current.append({
            "from": f"0x{xref.frm:X}",
            "type": xref.type,
        })
    result["xrefs_to_current"] = len(xrefs_to_current)
    
    # Get xrefs to byte before (the real target)
    xrefs_to_prev = []
    for xref in idautils.XrefsTo(prev_ea):
        xrefs_to_prev.append({
            "from": f"0x{xref.frm:X}",
            "type": xref.type,
        })
    result["xrefs_to_prev"] = len(xrefs_to_prev)
    
    # Check function end
    func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
    result["current_end"] = f"0x{func_end:X}"
    result["size"] = func_end - func_ea
    
    # Get disassembly starting from proposed new start
    lines = []
    try:
        # Temporarily create instruction at prev_ea to see what it would be
        if idc.create_insn(prev_ea):
            for i, ea in enumerate(idautils.Heads(prev_ea, min(prev_ea + 40, func_end))):
                marker = " <-- CURRENT_START" if ea == func_ea else ""
                lines.append(f"{ea:08X}: {idc.generate_disasm_line(ea, 0)}{marker}")
                if i >= 15:
                    break
    except:
        lines.append("Could not decode")
    
    result["disasm_from_proposed"] = lines
    
    results.append(result)

# Write output
with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/rebase_candidates.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Checked {len(results)} REBASE candidates")
for r in results:
    print(f"  {r['current_start']}: xrefs current={r['xrefs_to_current']}, prev={r['xrefs_to_prev']}")

idc.qexit(0)
