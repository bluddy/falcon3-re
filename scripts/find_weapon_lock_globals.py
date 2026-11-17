import idc
import idautils
import idaapi
import json

def find_weapon_lock_globals():
    """Find globals related to weapon lock status (IR, radar, HARM)"""
    results = {
        'ir_lock_candidates': [],
        'radar_lock_candidates': [],
        'harm_lock_candidates': [],
        'weapon_fire_candidates': []
    }
    
    # Known weapon functions from previous analysis
    weapon_functions = [
        0x3DC55,  # weapon_spawn_gate_validate
        0x3DED9,  # ai_weapon_fire_check
        0x4C19E,  # weapon_type_initialize_dispatch
        0x32B8A,  # weapon_aim9_seeker_lock_check
        0x32C7F,  # weapon_ir_lock_tone_handler
    ]
    
    # Track memory references in weapon functions
    memory_refs = {}
    
    for func_ea in weapon_functions:
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
            
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Look for memory references
            for ref in idautils.DataRefsFrom(ea):
                # Filter to data segment references
                seg = idaapi.getseg(ref)
                if seg and seg.type == idaapi.SEG_DATA:
                    if ref not in memory_refs:
                        memory_refs[ref] = []
                    memory_refs[ref].append({
                        'func': func_name,
                        'func_ea': hex(func_ea),
                        'ref_ea': hex(ea)
                    })
            
            ea = idc.next_head(ea)
    
    # Analyze memory references
    for addr, refs in memory_refs.items():
        addr_name = idc.get_name(addr)
        if not addr_name:
            addr_name = f"ds_{addr:X}"
        
        # Categorize based on function context
        func_names = [r['func'] for r in refs]
        
        if any('ir' in fn.lower() or 'aim9' in fn.lower() or 'seeker' in fn.lower() for fn in func_names):
            results['ir_lock_candidates'].append({
                'address': hex(addr),
                'name': addr_name,
                'refs': refs,
                'size': idc.get_item_size(addr)
            })
        
        if any('radar' in fn.lower() or 'amraam' in fn.lower() for fn in func_names):
            results['radar_lock_candidates'].append({
                'address': hex(addr),
                'name': addr_name,
                'refs': refs,
                'size': idc.get_item_size(addr)
            })
        
        if any('harm' in fn.lower() or 'radiation' in fn.lower() for fn in func_names):
            results['harm_lock_candidates'].append({
                'address': hex(addr),
                'name': addr_name,
                'refs': refs,
                'size': idc.get_item_size(addr)
            })
    
    # Find fire button handler by searching for keyboard scan code checks
    # Space bar = scan code 0x39, likely fire button
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Look for comparison with 0x39 (space bar scan code)
            mnem = idc.print_insn_mnem(ea)
            if mnem in ['cmp', 'test']:
                op1 = idc.get_operand_value(ea, 1)
                if op1 == 0x39:  # Space bar
                    results['weapon_fire_candidates'].append({
                        'function': func_name,
                        'address': hex(func_ea),
                        'check_ea': hex(ea)
                    })
                    break
            
            ea = idc.next_head(ea)
    
    return results

print("Finding weapon lock globals...")
results = find_weapon_lock_globals()

with open('weapon_lock_globals.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Found {len(results['ir_lock_candidates'])} IR lock candidates")
print(f"Found {len(results['radar_lock_candidates'])} radar lock candidates")
print(f"Found {len(results['harm_lock_candidates'])} HARM lock candidates")
print(f"Found {len(results['weapon_fire_candidates'])} fire button handlers")

idc.qexit(0)
