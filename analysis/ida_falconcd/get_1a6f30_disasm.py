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
    
    # Get callees with call count
    callee_dict = {}
    for ea in idautils.FuncItems(addr):
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                callee_name = idc.get_func_name(xref.to)
                if callee_name:
                    key = f"0x{xref.to:x}"
                    if key in callee_dict:
                        callee_dict[key]["count"] += 1
                    else:
                        callee_dict[key] = {
                            "addr": key,
                            "name": callee_name,
                            "count": 1
                        }
    
    result["callees"] = sorted(callee_dict.values(), key=lambda x: -x["count"])
    
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

# Extract Rank #13 function
addr = 0x1A6F30
func_data = get_func_disasm(addr)

if func_data:
    output_path = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\func_1a6f30_full.json"
    with open(output_path, 'w') as f:
        json.dump(func_data, f, indent=2)
    
    print("=" * 70)
    print(f"RANK #13 ANALYSIS: {func_data['name']}")
    print("=" * 70)
    print(f"Address: {func_data['address']}")
    print(f"Name: {func_data['name']}")
    print(f"Size: {func_data['size']} bytes")
    print(f"Disassembly lines: {func_data['disasm_line_count']}")
    print(f"Unique callees: {func_data['callee_count']}")
    print(f"String refs: {len(func_data['string_refs'])}")
    print()
    print("Top callees:")
    for i, callee in enumerate(func_data['callees'][:15], 1):
        print(f"  {i}. {callee['name']} ({callee['addr']}) - called {callee['count']}x")
    print()
    if func_data['string_refs']:
        print("String references:")
        for ref in func_data['string_refs'][:10]:
            print(f"  {ref['addr']}: \"{ref['string']}\"")
    print()
    print(f"Saved to: {output_path}")
else:
    print(f"ERROR: Function at 0x{addr:X} not found")

idc.qexit(0)
