"""
Extract full disassembly for ui_campaign_render_coordinator (0x15F5B8)
Size: 745 bytes
Callers: 34 (HIGH TRAFFIC)

This is a deep dive investigation following Rule #6: read actual code first!

IDA Python Script - Batch Mode
"""

import idc
import idaapi
import idautils
import json

# Wait for autoanalysis
idaapi.auto_wait()

def get_func_info(addr):
    """Get comprehensive function information"""
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    info = {
        "address": f"0x{addr:x}",
        "name": idc.get_func_name(addr),
        "start": f"0x{func.start_ea:x}",
        "end": f"0x{func.end_ea:x}",
        "size": func.end_ea - func.start_ea,
        "disasm": [],
        "callees": [],
        "string_refs": []
    }
    
    # Get FULL disassembly
    ea = func.start_ea
    disasm_count = 0
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        info["disasm"].append(f"{ea:08X}  {disasm}")
        disasm_count += 1
        ea = idc.next_head(ea)
    
    info["disasm_line_count"] = disasm_count
    
    # Get callees
    callee_set = set()
    ea = func.start_ea
    while ea < func.end_ea:
        for ref in idautils.CodeRefsFrom(ea, False):
            callee_name = idc.get_func_name(ref)
            if callee_name and ref != addr:  # Exclude self-references
                callee_set.add((ref, callee_name))
        ea = idc.next_head(ea)
    
    info["callees"] = [{"addr": f"0x{addr:x}", "name": name} for addr, name in sorted(callee_set)]
    info["callee_count"] = len(info["callees"])
    
    # Get string references
    ea = func.start_ea
    string_set = set()
    while ea < func.end_ea:
        for ref in idautils.DataRefsFrom(ea):
            str_type = idc.get_str_type(ref)
            if str_type is not None:
                string_val = idc.get_strlit_contents(ref)
                if string_val:
                    try:
                        string_set.add((ref, string_val.decode('utf-8', errors='replace')))
                    except:
                        pass
        ea = idc.next_head(ea)
    
    info["string_refs"] = [{"addr": f"0x{addr:x}", "value": val} for addr, val in sorted(string_set)]
    
    return info

# Target function
addr = 0x15F5B8
print(f"Extracting FULL disassembly for ui_campaign_render_coordinator at 0x{addr:X}")

info = get_func_info(addr)

if info:
    # Save to JSON
    output_file = "func_15f5b8_full.json"
    with open(output_file, "w") as f:
        json.dump(info, f, indent=2)
    
    print(f"\nFunction: {info['name']}")
    print(f"Address: {info['address']}")
    print(f"Size: {info['size']} bytes")
    print(f"Disassembly lines: {info['disasm_line_count']}")
    print(f"Callees: {info['callee_count']}")
    print(f"String references: {len(info['string_refs'])}")
    print(f"\nSaved to {output_file}")
    
    # Print first 30 lines of disassembly
    print("\nFirst 30 lines of disassembly:")
    for line in info["disasm"][:30]:
        print(f"  {line}")
    
    # Print callees
    if info["callees"]:
        print(f"\nCallees ({info['callee_count']}):")
        for callee in info["callees"]:
            print(f"  {callee['addr']}: {callee['name']}")
    
    # Print string references
    if info["string_refs"]:
        print(f"\nString references ({len(info['string_refs'])}):")
        for ref in info["string_refs"]:
            print(f"  {ref['addr']}: \"{ref['value']}\"")
else:
    print(f"ERROR: Function not found at 0x{addr:X}")

# Exit IDA
idc.qexit(0)
