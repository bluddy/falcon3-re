import idc
import idautils
import idaapi
import json

def disassemble_function(ea, max_lines=200):
    """Disassemble a function"""
    result = []
    func = idaapi.get_func(ea)
    if not func:
        return result
    
    current = func.start_ea
    line_count = 0
    while current < func.end_ea and line_count < max_lines:
        disasm = idc.generate_disasm_line(current, 0)
        result.append({
            'ea': hex(current),
            'disasm': disasm
        })
        current = idc.next_head(current)
        line_count += 1
    
    return result

def analyze_fire_candidates():
    """Analyze fire button candidates to find the real handler"""
    candidates = [
        0x3A003,   # undoc_3A003
        0x3F603,   # ai_index_bounds_check
        0x4C3C7,   # farobj_utility_1819
    ]
    
    results = {}
    
    for func_ea in candidates:
        func_name = idc.get_func_name(func_ea)
        
        # Disassemble the function
        disasm = disassemble_function(func_ea, max_lines=100)
        
        # Look for calls to weapon functions
        weapon_calls = []
        for line in disasm:
            ea = int(line['ea'], 16)
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'call':
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target)
                if target_name and ('weapon' in target_name.lower() or 
                                   'fire' in target_name.lower() or
                                   'spawn' in target_name.lower()):
                    weapon_calls.append({
                        'ea': hex(ea),
                        'target': hex(target),
                        'name': target_name
                    })
        
        results[func_name] = {
            'address': hex(func_ea),
            'disasm': disasm,
            'weapon_calls': weapon_calls
        }
    
    return results

print("Analyzing fire button candidates...")
results = analyze_fire_candidates()

with open('weapon_fire_handler_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

for name, data in results.items():
    print(f"\n{name} at {data['address']}:")
    print(f"  Weapon calls: {len(data['weapon_calls'])}")
    for call in data['weapon_calls']:
        print(f"    {call['ea']}: call {call['name']}")

idc.qexit(0)
