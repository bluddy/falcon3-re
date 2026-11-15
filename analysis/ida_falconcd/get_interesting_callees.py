"""
Extract disassembly for interesting callees of theater_campaign_file_loader
Focus on undocumented functions to discover their purpose
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
    
    # Get disassembly (first 50 lines for quick analysis)
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 50:
        disasm = idc.generate_disasm_line(ea, 0)
        info["disasm"].append(f"{ea:08X}  {disasm}")
        count += 1
        ea = idc.next_head(ea)
    
    info["disasm_lines_shown"] = count
    
    # Get callees
    callee_set = set()
    ea = func.start_ea
    while ea < func.end_ea:
        for ref in idautils.CodeRefsFrom(ea, False):
            callee_name = idc.get_func_name(ref)
            if callee_name and ref != addr:
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

# Interesting undocumented callees to analyze
targets = [
    (0x13C980, "undoc_13C980 - 280B, 12 callers"),
    (0x13D6E4, "undoc_13D6E4 - 55B, 4 callers"),
    (0x15F5B8, "undoc_15F5B8 - 745B, 34 callers - HIGH TRAFFIC"),
    (0x15B2A9, "sub_15B2A9 - 430B, 17 callers"),
    (0x2C47D, "sub_2C47D - 8B, 1 caller"),
    (0x2C487, "sub_2C487 - 8B, 1 caller"),
    (0x2C491, "sub_2C491 - 8B, 1 caller"),
    (0x2C49B, "sub_2C49B - 8B, 1 caller"),
]

results = {}
for addr, desc in targets:
    print(f"Extracting {desc}...")
    info = get_func_info(addr)
    if info:
        results[desc] = info
        print(f"  {info['name']}, {info['size']} bytes, {info['callee_count']} callees")
        if info['string_refs']:
            print(f"  Strings: {[s['value'] for s in info['string_refs']]}")
    else:
        print(f"  ERROR: Not found")

# Save to file
output_file = "interesting_callees_15a8b0.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved to {output_file}")

# Exit IDA
idc.qexit(0)
