import idc
import idautils
import idaapi
import json

def find_code_segment_globals():
    """Find weapon-related globals in code segment"""
    results = {
        'code_segment_weapon_vars': [],
        'data_segment_weapon_vars': []
    }
    
    # Search code segment for known weapon offsets from WEAPON_TYPES_DECODED.md
    known_offsets = [
        0x2E10A,  # weapon_queue_head
        0x2E10C,  # weapon_queue_count
        0x2E10E,  # weapon_processed_count
        0x2E110,  # unknown weapon var
        0x2E112,  # weapon_ammo_count
    ]
    
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if not seg:
            continue
        
        seg_name = idc.get_segm_name(seg_ea)
        
        # Check code segment for the known offsets
        if seg.type == idaapi.SEG_CODE:
            for offset in known_offsets:
                # Get the full address in this segment
                addr = seg_ea + offset
                if addr >= seg.start_ea and addr < seg.end_ea:
                    var_name = idc.get_name(addr)
                    if not var_name:
                        var_name = f"cs_{offset:X}"
                    
                    # Find cross-references
                    xrefs = []
                    for xref in idautils.XrefsTo(addr, idaapi.XREF_ALL):
                        func = idaapi.get_func(xref.frm)
                        if func:
                            func_name = idc.get_func_name(func.start_ea)
                            if func_name:
                                xrefs.append({
                                    'function': func_name,
                                    'address': hex(xref.frm)
                                })
                    
                    results['code_segment_weapon_vars'].append({
                        'offset': hex(offset),
                        'address': hex(addr),
                        'segment': seg_name,
                        'name': var_name,
                        'xrefs': xrefs[:10]  # Limit to 10 xrefs
                    })
    
    # Search for IR/radar lock in data segment by looking for byte/word variables
    # accessed by weapon functions
    weapon_functions = [
        0x32B8A,  # weapon_aim9_seeker_lock_check
        0x32C7F,  # weapon_ir_lock_tone_handler
    ]
    
    for func_ea in weapon_functions:
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Look for data references
            for ref in idautils.DataRefsFrom(ea):
                seg = idaapi.getseg(ref)
                if seg and seg.type == idaapi.SEG_DATA:
                    ref_name = idc.get_name(ref)
                    if not ref_name:
                        ref_name = f"ds_{ref:X}"
                    
                    # Check if we already have this
                    if not any(v['address'] == hex(ref) for v in results['data_segment_weapon_vars']):
                        results['data_segment_weapon_vars'].append({
                            'address': hex(ref),
                            'name': ref_name,
                            'found_in_function': func_name,
                            'size': idc.get_item_size(ref)
                        })
            
            ea = idc.next_head(ea)
    
    return results

print("Finding weapon lock globals...")
results = find_code_segment_globals()

with open('weapon_lock_globals_v2.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nFound {len(results['code_segment_weapon_vars'])} code segment weapon vars")
print(f"Found {len(results['data_segment_weapon_vars'])} data segment weapon vars")

for var in results['data_segment_weapon_vars']:
    print(f"  {var['name']} at {var['address']} (in {var['found_in_function']})")

idc.qexit(0)
