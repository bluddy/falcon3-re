import idc
import idautils
import idaapi
import json

def disassemble_function_with_globals(ea, max_lines=200):
    """Disassemble a function and track all data segment references"""
    result = {
        'disasm': [],
        'data_refs': []
    }
    
    func = idaapi.get_func(ea)
    if not func:
        return result
    
    data_refs_seen = set()
    
    current = func.start_ea
    line_count = 0
    while current < func.end_ea and line_count < max_lines:
        disasm = idc.generate_disasm_line(current, 0)
        
        # Track data references
        for ref in idautils.DataRefsFrom(current):
            seg = idaapi.getseg(ref)
            if seg and seg.type == idaapi.SEG_DATA:
                if ref not in data_refs_seen:
                    data_refs_seen.add(ref)
                    ref_name = idc.get_name(ref)
                    if not ref_name:
                        ref_name = f"ds_{ref:X}"
                    result['data_refs'].append({
                        'address': hex(ref),
                        'name': ref_name,
                        'size': idc.get_item_size(ref),
                        'first_use': hex(current)
                    })
        
        result['disasm'].append({
            'ea': hex(current),
            'disasm': disasm
        })
        current = idc.next_head(current)
        line_count += 1
    
    return result

print("Analyzing IR lock functions...")

# Key IR lock functions
functions = {
    'weapon_aim9_seeker_lock_check': 0x32B8A,
    'weapon_ir_lock_tone_handler': 0x32C7F,
}

results = {}

for name, ea in functions.items():
    print(f"Analyzing {name} at {hex(ea)}...")
    analysis = disassemble_function_with_globals(ea)
    results[name] = {
        'address': hex(ea),
        'analysis': analysis
    }

# Also find all xrefs to these functions
for name, ea in functions.items():
    xrefs = []
    for xref in idautils.XrefsTo(ea, idaapi.XREF_ALL):
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(func.start_ea)
            if func_name:
                xrefs.append({
                    'caller': func_name,
                    'caller_address': hex(func.start_ea),
                    'call_site': hex(xref.frm)
                })
    results[name]['xrefs'] = xrefs

with open('ir_lock_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

for name, data in results.items():
    print(f"\n{name}:")
    print(f"  Data references: {len(data['analysis']['data_refs'])}")
    for ref in data['analysis']['data_refs']:
        print(f"    {ref['name']} at {ref['address']} (size {ref['size']})")
    print(f"  Called by: {len(data['xrefs'])} functions")

idc.qexit(0)
