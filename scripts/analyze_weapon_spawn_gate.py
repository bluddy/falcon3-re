import idc
import idautils
import idaapi
import json

def disassemble_with_data_refs(ea, max_lines=300):
    """Disassemble function with data references"""
    result = {'disasm': [], 'data_refs': []}
    
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

print("Analyzing weapon_spawn_gate_validate...")

# weapon_spawn_gate_validate @ 0x3DC55
func_ea = 0x3DC55
analysis = disassemble_with_data_refs(func_ea)

results = {
    'function': 'weapon_spawn_gate_validate',
    'address': hex(func_ea),
    'analysis': analysis
}

with open('weapon_spawn_gate_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Function: weapon_spawn_gate_validate @ {hex(func_ea)}")
print(f"Disassembly lines: {len(analysis['disasm'])}")
print(f"Data references: {len(analysis['data_refs'])}")
print("\nData segment globals accessed:")
for ref in analysis['data_refs']:
    print(f"  {ref['name']} @ {ref['address']} (size {ref['size']}, first use {ref['first_use']})")

idc.qexit(0)
