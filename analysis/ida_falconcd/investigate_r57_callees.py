import idaapi
import idautils
import idc
import json

# Key callees to investigate from r57_menu_state_machine
callees_to_check = [
    (0x12805C, "sub_12805C", 12),      # Called 12x - HIGH
    (0x1A6AA6, "sub_1A6AA6", 7),       # Called 7x
    (0x2C905, "sub_2C905", 6),         # Called 6x
    (0x2C8D3, "sub_2C8D3", 5),         # Called 5x
    (0x2C8C9, "sub_2C8C9", 5),         # Called 5x
    (0x2C8AB, "sub_2C8AB", 5),         # Called 5x
    (0x2C919, "sub_2C919", 4),         # Called 4x
    (0x2C8FB, "sub_2C8FB", 3),         # Called 3x
    (0x2C8F1, "sub_2C8F1", 1),         # Initialization
]

def analyze_function_brief(addr):
    """Get brief analysis of a function"""
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    result = {
        "address": f"0x{addr:x}",
        "name": idc.get_func_name(addr),
        "size": func.end_ea - func.start_ea,
        "callers": len(list(idautils.CodeRefsTo(addr, 1))),
        "callees": [],
        "strings": [],
        "first_10_lines": []
    }
    
    # Get first 10 disasm lines
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 10:
        disasm_line = idc.generate_disasm_line(ea, 0)
        result["first_10_lines"].append(f"{ea:08X}  {disasm_line}")
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    # Get callees
    for ea in idautils.FuncItems(addr):
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                callee_name = idc.get_func_name(xref.to)
                if callee_name and callee_name not in [c["name"] for c in result["callees"]]:
                    result["callees"].append({
                        "addr": f"0x{xref.to:x}",
                        "name": callee_name
                    })
    
    # Get string refs
    for ea in idautils.FuncItems(addr):
        for xref in idautils.DataRefsFrom(ea):
            s = idc.get_strlit_contents(xref)
            if s:
                result["strings"].append({
                    "addr": f"0x{xref:x}",
                    "string": s.decode('ascii', errors='ignore')
                })
    
    return result

print("=" * 70)
print("R57 MENU STATE MACHINE - CALLEE INVESTIGATION")
print("=" * 70)
print()

results = {}

for addr, name, call_count in callees_to_check:
    print(f"Analyzing: {name} (0x{addr:X}) - called {call_count}x by r57...")
    
    analysis = analyze_function_brief(addr)
    if analysis:
        results[name] = analysis
        print(f"  Size: {analysis['size']} bytes")
        print(f"  Total callers: {analysis['callers']}")
        print(f"  Callees: {len(analysis['callees'])}")
        if analysis['strings']:
            print(f"  Strings: {len(analysis['strings'])}")
            for s in analysis['strings'][:3]:
                print(f"    - \"{s['string']}\"")
        print()
    else:
        print(f"  NOT FOUND")
        print()

# Save results
output_path = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\r57_callees_analysis.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print("=" * 70)
print(f"Saved to: {output_path}")
print("=" * 70)

idc.qexit(0)
