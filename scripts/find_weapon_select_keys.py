import idc
import idautils
import idaapi
import json

def find_weapon_key_handlers():
    """Find weapon selection keyboard handlers"""
    results = {
        'backspace_ag_select': [],   # Scancode 0x0E
        'enter_aa_select': [],       # Scancode 0x1C
        'space_fire': [],            # Scancode 0x39
        'z_radar_lock': [],          # Scancode 0x2C
        'apostrophe_ripple': [],     # Scancode 0x28 (')
        'semicolon_ripple': [],      # Scancode 0x27 (;)
    }
    
    # Scan codes for weapon keys
    BACKSPACE = 0x0E
    ENTER = 0x1C
    SPACE = 0x39
    Z_KEY = 0x2C
    APOSTROPHE = 0x28
    SEMICOLON = 0x27
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ['cmp', 'test', 'sub']:
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm:
                    imm_val = idc.get_operand_value(ea, 1)
                    
                    if imm_val == BACKSPACE:
                        results['backspace_ag_select'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == ENTER:
                        results['enter_aa_select'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == SPACE:
                        results['space_fire'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == Z_KEY:
                        results['z_radar_lock'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == APOSTROPHE:
                        results['apostrophe_ripple'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
                    elif imm_val == SEMICOLON:
                        results['semicolon_ripple'].append({
                            'function': func_name,
                            'address': hex(ea)
                        })
            
            ea = idc.next_head(ea)
    
    return results

def find_selected_weapon_global():
    """Search for weapon selection state by looking at weapon type constants"""
    results = []
    
    # Look for functions that reference multiple weapon types
    # These likely handle weapon selection/display
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Look for functions with "weapon" or "loadout" in name
        if not any(kw in func_name.lower() for kw in ['weapon', 'loadout', 'store', 'select']):
            continue
        
        # Find data segment references
        data_refs = []
        ea = func.start_ea
        while ea < func.end_ea:
            for ref in idautils.DataRefsFrom(ea):
                seg = idaapi.getseg(ref)
                if seg and seg.type == idaapi.SEG_DATA:
                    ref_name = idc.get_name(ref)
                    if not ref_name:
                        ref_name = f"ds_{ref:X}"
                    
                    if not any(r['address'] == hex(ref) for r in data_refs):
                        data_refs.append({
                            'address': hex(ref),
                            'name': ref_name,
                            'size': idc.get_item_size(ref)
                        })
            
            ea = idc.next_head(ea)
        
        if data_refs:
            results.append({
                'function': func_name,
                'address': hex(func_ea),
                'data_refs': data_refs[:10]  # Limit to first 10
            })
    
    return results

print("Finding weapon key handlers...")
key_handlers = find_weapon_key_handlers()

print("Finding weapon selection state globals...")
weapon_state_funcs = find_selected_weapon_global()

results = {
    'weapon_key_handlers': key_handlers,
    'weapon_state_functions': weapon_state_funcs
}

with open('weapon_select_keys.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nWeapon key handlers found:")
print(f"  Backspace (A-G select): {len(key_handlers['backspace_ag_select'])}")
print(f"  Enter (A-A select): {len(key_handlers['enter_aa_select'])}")
print(f"  Space (fire): {len(key_handlers['space_fire'])}")
print(f"  Z (radar lock): {len(key_handlers['z_radar_lock'])}")
print(f"  ' (ripple+): {len(key_handlers['apostrophe_ripple'])}")
print(f"  ; (ripple-): {len(key_handlers['semicolon_ripple'])}")

print(f"\nWeapon state functions: {len(weapon_state_funcs)}")
for func in weapon_state_funcs[:10]:
    print(f"  {func['function']} - {len(func['data_refs'])} globals")

idc.qexit(0)
