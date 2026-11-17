import idc
import idautils
import idaapi
import json

def find_loadout_weapon_supply_refs():
    """Find references to loadout_weapon_supply and nearby globals"""
    results = {
        'loadout_refs': [],
        'nearby_globals': []
    }
    
    # Get data segment
    data_seg = None
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if seg and seg.type == idaapi.SEG_DATA:
            data_seg = seg
            break
    
    if not data_seg:
        return results
    
    data_base = data_seg.start_ea
    
    # loadout_weapon_supply @ 0x5030
    loadout_addr = data_base + 0x5030
    
    # Find all xrefs to loadout area (0x5000-0x5050)
    for offset in range(0x5000, 0x5050, 2):
        addr = data_base + offset
        
        xrefs = []
        for xref in idautils.XrefsTo(addr, idaapi.XREF_ALL):
            func = idaapi.get_func(xref.frm)
            if func:
                func_name = idc.get_func_name(func.start_ea)
                if func_name:
                    xrefs.append({
                        'function': func_name,
                        'ref_ea': hex(xref.frm)
                    })
        
        if xrefs:
            var_name = idc.get_name(addr)
            if not var_name:
                var_name = f"ds_{addr:X}"
            
            results['loadout_refs'].append({
                'offset': hex(offset),
                'address': hex(addr),
                'name': var_name,
                'xrefs': xrefs[:5]  # First 5
            })
    
    # Look for single-byte or word variables around 0x5050-0x5100
    # that might be selected_weapon_type or selected_weapon_index
    for offset in range(0x5050, 0x5100):
        addr = data_base + offset
        
        xref_count = 0
        xrefs = []
        for xref in idautils.XrefsTo(addr, idaapi.XREF_ALL):
            xref_count += 1
            if xref_count <= 3:
                func = idaapi.get_func(xref.frm)
                if func:
                    func_name = idc.get_func_name(func.start_ea)
                    if func_name:
                        xrefs.append({
                            'function': func_name,
                            'ref_ea': hex(xref.frm)
                        })
        
        if xref_count >= 5:  # Variables with multiple refs
            var_name = idc.get_name(addr)
            if not var_name:
                var_name = f"ds_{addr:X}"
            
            results['nearby_globals'].append({
                'offset': hex(offset),
                'address': hex(addr),
                'name': var_name,
                'xref_count': xref_count,
                'sample_xrefs': xrefs
            })
    
    return results

def search_weapon_select_pattern():
    """Search for weapon selection by looking for Backspace/Enter handlers"""
    results = []
    
    # Backspace = 0x0E, Enter = 0x1C
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        has_backspace = False
        has_enter = False
        data_refs = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Check for key scancodes
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'cmp':
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm:
                    imm_val = idc.get_operand_value(ea, 1)
                    if imm_val == 0x0E:
                        has_backspace = True
                    elif imm_val == 0x1C:
                        has_enter = True
            
            # Track data refs
            for ref in idautils.DataRefsFrom(ea):
                seg = idaapi.getseg(ref)
                if seg and seg.type == idaapi.SEG_DATA:
                    if not any(r['address'] == hex(ref) for r in data_refs):
                        ref_name = idc.get_name(ref)
                        if not ref_name:
                            ref_name = f"ds_{ref:X}"
                        data_refs.append({
                            'address': hex(ref),
                            'name': ref_name
                        })
            
            ea = idc.next_head(ea)
        
        if (has_backspace or has_enter) and data_refs:
            results.append({
                'function': func_name,
                'address': hex(func_ea),
                'has_backspace': has_backspace,
                'has_enter': has_enter,
                'data_refs': data_refs[:10]
            })
    
    return results

print("Finding loadout_weapon_supply references...")
loadout_refs = find_loadout_weapon_supply_refs()

print("Searching for weapon select pattern (Backspace/Enter handlers)...")
weapon_select = search_weapon_select_pattern()

results = {
    'loadout_system': loadout_refs,
    'weapon_select_handlers': weapon_select
}

with open('selected_weapon_search.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nLoadout variable refs: {len(loadout_refs['loadout_refs'])}")
print(f"Nearby globals (0x5050-0x5100): {len(loadout_refs['nearby_globals'])}")
print(f"\nWeapon select handlers with data refs: {len(weapon_select)}")
for handler in weapon_select[:5]:
    print(f"  {handler['function']} - BS:{handler['has_backspace']}, ENT:{handler['has_enter']}, refs:{len(handler['data_refs'])}")

idc.qexit(0)
