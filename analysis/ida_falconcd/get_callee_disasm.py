"""
Extract disassembly for key callees of squadron_mission_file_loader
Focuses on unique callees (0 other callers) and high-traffic functions
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
    
    # Get disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        info["disasm"].append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea)
    
    # Get callees
    for ref in idautils.CodeRefsFrom(func.start_ea, True):
        callee_name = idc.get_func_name(ref)
        if callee_name:
            info["callees"].append({
                "addr": f"0x{ref:x}",
                "name": callee_name
            })
    
    # Get string references
    ea = func.start_ea
    while ea < func.end_ea:
        for ref in idautils.DataRefsFrom(ea):
            str_type = idc.get_str_type(ref)
            if str_type is not None:
                string_val = idc.get_strlit_contents(ref)
                if string_val:
                    info["string_refs"].append({
                        "addr": f"0x{ref:x}",
                        "value": string_val.decode('utf-8', errors='replace')
                    })
        ea = idc.next_head(ea)
    
    return info

# Functions to analyze
targets = [
    (0x138E6A, "undoc_138E6A - menu context handler (0 other callers!)"),
    (0x138F9C, "menu_field_offset_calculate - path builder (0 other callers!)"),
    (0x225B6, "op_dispatch_far_wide - extended file ops"),
    (0x13B243, "overlay_handler_2623 - 50 callers, overlay management"),
]

results = {}
for addr, desc in targets:
    print(f"Extracting {desc}...")
    info = get_func_info(addr)
    if info:
        results[desc] = info
        print(f"  Found: {info['name']}, {info['size']} bytes, {len(info['disasm'])} lines")
    else:
        print(f"  ERROR: Function not found at 0x{addr:x}")

# Save to file
output_file = "callee_analysis.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved to {output_file}")
print(f"Total functions analyzed: {len(results)}")

# Exit IDA
idc.qexit(0)
