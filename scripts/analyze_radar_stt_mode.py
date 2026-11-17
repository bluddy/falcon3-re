import idc
import idautils
import idaapi
import json

def find_stt_mode_functions():
    """Find functions that use radar STT mode (Single Target Track)"""
    results = {
        'radar_mode_state_functions': [],
        'radar_selected_target_functions': [],
        'stt_lock_candidates': []
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
    
    # Key radar globals
    radar_mode_state = data_base + 0x595B2  # radar_mode_state
    radar_selected_target = data_base + 0x5959B  # radar_selected_target_index
    radar_type_selector = data_base + 0x59573  # radar_type_selector
    
    # Track which functions use which globals
    mode_state_users = {}
    target_users = {}
    
    # Find all functions using radar_mode_state
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        uses_mode = False
        uses_target = False
        stt_check = None
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Check for radar_mode_state references
            for ref in idautils.DataRefsFrom(ea):
                if ref == radar_mode_state:
                    uses_mode = True
                elif ref == radar_selected_target:
                    uses_target = True
            
            # Look for comparison with 5 (STT mode)
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'cmp' and uses_mode:
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm:
                    val = idc.get_operand_value(ea, 1)
                    if val == 5:
                        stt_check = hex(ea)
            
            ea = idc.next_head(ea)
        
        if uses_mode:
            mode_state_users[func_name] = {
                'address': hex(func_ea),
                'uses_target': uses_target,
                'stt_check': stt_check
            }
        
        if uses_target:
            target_users[func_name] = {
                'address': hex(func_ea),
                'uses_mode': uses_mode
            }
        
        # Potential STT lock functions: use both mode and target, check for STT
        if uses_mode and uses_target:
            results['stt_lock_candidates'].append({
                'function': func_name,
                'address': hex(func_ea),
                'stt_check': stt_check
            })
    
    results['radar_mode_state_functions'] = [
        {'function': k, **v} for k, v in list(mode_state_users.items())[:20]
    ]
    
    results['radar_selected_target_functions'] = [
        {'function': k, **v} for k, v in list(target_users.items())[:20]
    ]
    
    return results

def analyze_mode_stream_select():
    """Analyze mode_stream_select_step which we know scans targets"""
    # This function was renamed to radar_acm_target_step @ 0x39E13
    func_ea = 0x39E13
    
    result = {
        'function': idc.get_func_name(func_ea),
        'address': hex(func_ea),
        'data_refs': []
    }
    
    func = idaapi.get_func(func_ea)
    if not func:
        return result
    
    data_refs_seen = set()
    ea = func.start_ea
    
    while ea < func.end_ea:
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
                        'name': ref_name
                    })
        
        ea = idc.next_head(ea)
    
    return result

print("Analyzing radar STT mode and lock system...")

stt_analysis = find_stt_mode_functions()
target_step = analyze_mode_stream_select()

results = {
    'stt_system': stt_analysis,
    'radar_acm_target_step': target_step
}

with open('temp/radar_stt_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nFunctions using radar_mode_state: {len(stt_analysis['radar_mode_state_functions'])}")
print(f"Functions using radar_selected_target: {len(stt_analysis['radar_selected_target_functions'])}")
print(f"STT lock candidates (use both): {len(stt_analysis['stt_lock_candidates'])}")

print("\nTop STT lock candidates:")
for candidate in stt_analysis['stt_lock_candidates'][:10]:
    stt = "✓ STT=5" if candidate['stt_check'] else ""
    print(f"  {candidate['function']} @ {candidate['address']} {stt}")

print(f"\nradar_acm_target_step data refs: {len(target_step['data_refs'])}")
for ref in target_step['data_refs'][:15]:
    print(f"  {ref['name']}")

idc.qexit(0)
