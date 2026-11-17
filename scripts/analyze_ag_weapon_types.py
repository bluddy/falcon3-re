import idc
import idautils
import idaapi
import json

def analyze_farobj_utility_1819():
    """Analyze farobj_utility_1819 which initializes A-G weapons"""
    # This function was found in weapon_select_keys.json
    func_ea = 0x4C3C7
    
    result = {
        'function': 'farobj_utility_1819',
        'address': hex(func_ea),
        'weapon_initializers': []
    }
    
    func = idaapi.get_func(func_ea)
    if not func:
        return result
    
    ea = func.start_ea
    current_type = None
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for weapon type comparisons
        if mnem == 'cmp':
            op_type = idc.get_operand_type(ea, 1)
            if op_type == idc.o_imm:
                val = idc.get_operand_value(ea, 1)
                if 0x14 <= val <= 0x32:
                    current_type = {
                        'type': hex(val),
                        'check_address': hex(ea),
                        'initialization': []
                    }
        
        # Collect initialization code after type check
        if current_type and len(current_type['initialization']) < 20:
            current_type['initialization'].append({
                'address': hex(ea),
                'disasm': disasm
            })
            
            # Stop at next cmp or return
            if mnem in ['cmp', 'retn', 'retf'] and len(current_type['initialization']) > 5:
                result['weapon_initializers'].append(current_type)
                current_type = None
        
        ea = idc.next_head(ea)
    
    return result

def find_ag_weapon_parameters():
    """Find A-G weapon parameter patterns in initialization"""
    # weapon_type_initialize_dispatch handles 0x12-13 and 0x33-37
    # Look for gap handling (0x14-0x32)
    
    func_ea = 0x4C19E  # weapon_type_initialize_dispatch
    
    result = {
        'function': 'weapon_type_initialize_dispatch',
        'address': hex(func_ea),
        'disasm': []
    }
    
    func = idaapi.get_func(func_ea)
    if not func:
        return result
    
    ea = func.start_ea
    line_count = 0
    
    # Get first 100 instructions to see type range checks
    while ea < func.end_ea and line_count < 100:
        disasm = idc.generate_disasm_line(ea, 0)
        result['disasm'].append({
            'address': hex(ea),
            'disasm': disasm
        })
        
        ea = idc.next_head(ea)
        line_count += 1
    
    return result

def search_weapon_type_strings():
    """Search for weapon name strings that might identify types"""
    results = []
    
    # Look for common A-G weapon names in strings
    weapon_names = [
        'HARM', 'AGM-88', 'AGM88',
        'Maverick', 'AGM-65', 'AGM65',
        'Shrike', 'AGM-45', 'AGM45',
        'Mk82', 'Mk84', 'MK82', 'MK84',
        'CBU', 'LGB', 'LASER'
    ]
    
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if not seg:
            continue
        
        # Only check data segments
        if seg.type != idaapi.SEG_DATA:
            continue
        
        ea = seg.start_ea
        while ea < seg.end_ea:
            # Check if this looks like a string
            str_type = idc.get_str_type(ea)
            if str_type is not None:
                string = idc.get_strlit_contents(ea)
                if string:
                    string_decoded = string.decode('ascii', errors='ignore').upper()
                    for weapon_name in weapon_names:
                        if weapon_name in string_decoded:
                            results.append({
                                'address': hex(ea),
                                'string': string_decoded[:50],
                                'weapon': weapon_name
                            })
                            break
            
            ea = idc.next_head(ea)
    
    return results

print("Analyzing A-G weapon types...")

utility_1819 = analyze_farobj_utility_1819()
type_dispatch = find_ag_weapon_parameters()
weapon_strings = search_weapon_type_strings()

results = {
    'farobj_utility_1819': utility_1819,
    'weapon_type_initialize_dispatch': type_dispatch,
    'weapon_strings': weapon_strings
}

with open('temp/ag_weapon_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nfarobj_utility_1819 weapon initializers: {len(utility_1819['weapon_initializers'])}")
for init in utility_1819['weapon_initializers']:
    print(f"  Type {init['type']} @ {init['check_address']}")

print(f"\nWeapon name strings found: {len(weapon_strings)}")
for ws in weapon_strings:
    print(f"  {ws['weapon']}: {ws['string'][:30]}")

print(f"\nweapon_type_initialize_dispatch: {len(type_dispatch['disasm'])} instructions")

idc.qexit(0)
