import idc
import idautils
import idaapi
import json

def find_callers(target_ea):
    """Find all functions that call a target function"""
    callers = []
    
    # Get cross-references to the function
    for xref in idautils.XrefsTo(target_ea, idaapi.XREF_ALL):
        # Get the function containing this reference
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(func.start_ea)
            if func_name:
                callers.append({
                    'function': func_name,
                    'address': hex(func.start_ea),
                    'call_site': hex(xref.frm),
                    'type': xref.type
                })
    
    return callers

def analyze_weapon_chain():
    """Analyze the weapon fire call chain"""
    
    # Known weapon functions
    weapon_spawn_gate = 0x3DC55  # weapon_spawn_gate_validate
    
    results = {
        'spawn_callers': [],
        'weapon_globals': []
    }
    
    # Find callers of weapon_spawn_gate_validate
    print(f"Finding callers of weapon_spawn_gate_validate at 0x{weapon_spawn_gate:X}...")
    callers = find_callers(weapon_spawn_gate)
    results['spawn_callers'] = callers
    
    # For each caller, find data references (globals)
    for caller in callers:
        func_ea = int(caller['address'], 16)
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Look for data segment references
            for ref in idautils.DataRefsFrom(ea):
                seg = idaapi.getseg(ref)
                if seg and seg.type == idaapi.SEG_DATA:
                    ref_name = idc.get_name(ref)
                    if not ref_name:
                        ref_name = f"ds_{ref:X}"
                    
                    # Check if we already have this global
                    if not any(g['address'] == hex(ref) for g in results['weapon_globals']):
                        results['weapon_globals'].append({
                            'address': hex(ref),
                            'name': ref_name,
                            'found_in': caller['function'],
                            'size': idc.get_item_size(ref)
                        })
            
            ea = idc.next_head(ea)
    
    return results

print("Analyzing weapon fire call chain...")
results = analyze_weapon_chain()

with open('weapon_spawn_callers.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nFound {len(results['spawn_callers'])} functions calling weapon_spawn_gate_validate:")
for caller in results['spawn_callers']:
    print(f"  {caller['function']} at {caller['address']}")

print(f"\nFound {len(results['weapon_globals'])} weapon-related globals")

idc.qexit(0)
