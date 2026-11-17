import idc
import idautils
import idaapi
import json

def find_weapon_type_refs():
    """Find references to weapon type values 0x12, 0x13, 0x33-0x37, 0x14-0x32"""
    results = {
        'type_0x12_refs': [],  # AIM-9
        'type_0x13_refs': [],  # AIM-120
        'type_0x33_refs': [],  # Gun
        'ag_weapon_refs': [],  # 0x14-0x32 (bombs, AGM-88, etc.)
    }
    
    # Search for immediate value comparisons
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for cmp instructions
            if mnem == 'cmp':
                # Get operand value
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm:  # Immediate value
                    imm_val = idc.get_operand_value(ea, 1)
                    
                    if imm_val == 0x12:
                        results['type_0x12_refs'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == 0x13:
                        results['type_0x13_refs'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == 0x33:
                        results['type_0x33_refs'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif 0x14 <= imm_val <= 0x32:
                        results['ag_weapon_refs'].append({
                            'function': func_name,
                            'address': hex(ea),
                            'type_value': hex(imm_val)
                        })
            
            ea = idc.next_head(ea)
    
    return results

def search_keyboard_weapon_select():
    """Search for weapon selection keyboard handlers (1-9 keys for weapons)"""
    results = []
    
    # Scan codes for 1-9: 0x02-0x0A
    weapon_select_scancodes = [0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A]
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Skip if function name suggests it's not input-related
        if 'key' not in func_name.lower() and 'input' not in func_name.lower() and 'scan' not in func_name.lower():
            continue
        
        ea = func.start_ea
        scancode_matches = []
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ['cmp', 'test']:
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm:
                    imm_val = idc.get_operand_value(ea, 1)
                    if imm_val in weapon_select_scancodes:
                        scancode_matches.append({
                            'address': hex(ea),
                            'scancode': hex(imm_val),
                            'key': str(imm_val - 1)  # 0x02 = '1', etc.
                        })
            
            ea = idc.next_head(ea)
        
        if scancode_matches:
            results.append({
                'function': func_name,
                'address': hex(func_ea),
                'scancode_checks': scancode_matches
            })
    
    return results

print("Finding weapon type references...")
type_refs = find_weapon_type_refs()

print("Searching for weapon selection keyboard handlers...")
keyboard_handlers = search_keyboard_weapon_select()

results = {
    'weapon_type_refs': type_refs,
    'keyboard_weapon_select': keyboard_handlers
}

with open('weapon_selection_search.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nWeapon type references:")
print(f"  Type 0x12 (AIM-9): {len(type_refs['type_0x12_refs'])} refs")
print(f"  Type 0x13 (AIM-120): {len(type_refs['type_0x13_refs'])} refs")
print(f"  Type 0x33 (Gun): {len(type_refs['type_0x33_refs'])} refs")
print(f"  A-G weapons (0x14-0x32): {len(type_refs['ag_weapon_refs'])} refs")

print(f"\nKeyboard weapon select handlers: {len(keyboard_handlers)}")
for handler in keyboard_handlers[:5]:
    print(f"  {handler['function']} - {len(handler['scancode_checks'])} key checks")

idc.qexit(0)
