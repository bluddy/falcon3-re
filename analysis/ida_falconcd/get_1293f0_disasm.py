import idaapi
import idautils
import idc
import json

def get_func_disasm(addr):
    """Extract full disassembly for function"""
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    result = {
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
        disasm_line = idc.generate_disasm_line(ea, 0)
        result["disasm"].append(f"{ea:08X}  {disasm_line}")
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callees
    for ea in idautils.FuncItems(addr):
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                callee_name = idc.get_func_name(xref.to)
                if callee_name:
                    result["callees"].append({
                        "addr": f"0x{xref.to:x}",
                        "name": callee_name
                    })
    
    # Get string refs
    for ea in idautils.FuncItems(addr):
        for xref in idautils.DataRefsFrom(ea):
            s = idc.get_strlit_contents(xref)
            if s:
                result["string_refs"].append({
                    "addr": f"0x{xref:x}",
                    "string": s.decode('ascii', errors='ignore')
                })
    
    result["disasm_line_count"] = len(result["disasm"])
    result["callee_count"] = len(result["callees"])
    
    return result

# Get both functions
func1 = get_func_disasm(0x1293F0)
func2 = get_func_disasm(0x129468)

output = {
    "sub_1293F0": func1,
    "undoc_129468": func2
}

output_path = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\render_helpers.json"
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)

print(f"Extracted to {output_path}")
print(f"sub_1293F0: {func1['size'] if func1 else 'NOT FOUND'} bytes, {func1['disasm_line_count'] if func1 else 0} lines")
print(f"undoc_129468: {func2['size'] if func2 else 'NOT FOUND'} bytes, {func2['disasm_line_count'] if func2 else 0} lines")
