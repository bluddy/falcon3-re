import idaapi
import idautils
import idc
import ida_funcs
import ida_xref
import json

def get_function_disassembly(func_ea):
    """Extract complete disassembly for a function"""
    func = ida_funcs.get_func(func_ea)
    if not func:
        return None
    
    result = {
        'address': hex(func_ea),
        'name': idc.get_func_name(func_ea),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'disassembly': [],
        'xrefs_to': [],
        'xrefs_from': []
    }
    
    # Get disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        disasm_line = idc.generate_disasm_line(ea, 0)
        result['disassembly'].append({
            'address': hex(ea),
            'bytes': ' '.join([f'{idc.get_wide_byte(ea + i):02X}' for i in range(idc.get_item_size(ea))]),
            'disasm': disasm_line
        })
        ea = idc.next_head(ea, func.end_ea)
    
    # Get xrefs TO this function (callers)
    for xref in idautils.XrefsTo(func_ea, 0):
        result['xrefs_to'].append({
            'from': hex(xref.frm),
            'type': xref.type
        })
    
    # Get xrefs FROM this function (calls it makes)
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.to != head + idc.get_item_size(head):  # Not just next instruction
                target_name = idc.get_func_name(xref.to) or idc.get_name(xref.to)
                result['xrefs_from'].append({
                    'from': hex(head),
                    'to': hex(xref.to),
                    'to_name': target_name,
                    'type': xref.type
                })
    
    return result

# Target function
func_ea = 0x111AF6
result = get_function_disassembly(func_ea)

if result:
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\func_111af6_full.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"SUCCESS: Extracted {len(result['disassembly'])} instructions")
    print(f"Function: {result['name']}")
    print(f"Output: {output_file}")
    print(f"Size: {result['size']} bytes")
    print(f"Callers: {len(result['xrefs_to'])}")
    
    # Show most-called functions
    calls = {}
    for xref in result['xrefs_from']:
        if xref['type'] in [17, 18, 19]:  # Call types
            name = xref['to_name']
            calls[name] = calls.get(name, 0) + 1
    
    print(f"\n=== TOP CALLEES ===")
    for name, count in sorted(calls.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {count}x {name}")
else:
    print("ERROR: Could not find function at 0x111AF6")

idc.qexit(0)
