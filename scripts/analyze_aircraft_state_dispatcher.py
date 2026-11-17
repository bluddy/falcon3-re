import idc
import idautils
import idaapi
import json

def analyze_function_globals(func_ea, max_lines=500):
    """Analyze a function and find all data segment globals it accesses"""
    result = {
        'function': idc.get_func_name(func_ea),
        'address': hex(func_ea),
        'data_refs': [],
        'key_checks': []
    }
    
    func = idaapi.get_func(func_ea)
    if not func:
        return result
    
    data_refs_seen = set()
    
    ea = func.start_ea
    line_count = 0
    while ea < func.end_ea and line_count < max_lines:
        mnem = idc.print_insn_mnem(ea)
        
        # Check for key scancodes
        if mnem == 'cmp':
            op_type = idc.get_operand_type(ea, 1)
            if op_type == idc.o_imm:
                imm_val = idc.get_operand_value(ea, 1)
                if imm_val in [0x0E, 0x1C, 0x39, 0x2C, 0x28, 0x27]:  # Weapon keys
                    key_names = {
                        0x0E: 'Backspace (A-G select)',
                        0x1C: 'Enter (A-A select)',
                        0x39: 'Space (fire)',
                        0x2C: 'Z (radar lock)',
                        0x28: "' (ripple+)",
                        0x27: '; (ripple-)'
                    }
                    result['key_checks'].append({
                        'address': hex(ea),
                        'scancode': hex(imm_val),
                        'key': key_names.get(imm_val, 'unknown')
                    })
        
        # Track data references
        for ref in idautils.DataRefsFrom(ea):
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
                        'first_use': hex(ea)
                    })
        
        ea = idc.next_head(ea)
        line_count += 1
    
    return result

print("Analyzing aircraft_state_dispatcher...")

# aircraft_state_dispatcher @ 0x33651 (had Backspace check)
func_ea = 0x33651
analysis = analyze_function_globals(func_ea)

with open('aircraft_state_dispatcher_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"Function: {analysis['function']} @ {analysis['address']}")
print(f"Data references: {len(analysis['data_refs'])}")
print(f"Key checks: {len(analysis['key_checks'])}")

print("\nKey checks found:")
for check in analysis['key_checks']:
    print(f"  {check['address']}: {check['key']}")

print("\nData segment globals (first 20):")
for ref in analysis['data_refs'][:20]:
    print(f"  {ref['name']} @ {ref['address']} (size {ref['size']})")

idc.qexit(0)
