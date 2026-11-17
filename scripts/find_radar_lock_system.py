import idc
import idautils
import idaapi
import json

def find_radar_lock_integration():
    """Find AIM-120 radar lock system by searching for radar_mode_state STT integration"""
    results = {
        'stt_mode_checks': [],
        'radar_selected_target_refs': [],
        'type_0x13_handlers': []
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
    
    # radar_mode_state @ 0x595B2 - look for comparisons with 5 (STT mode)
    radar_mode_state_addr = data_base + 0x595B2
    
    # radar_selected_target_index @ 0x5959B
    radar_target_addr = data_base + 0x5959B
    
    # Find functions checking radar_mode_state == 5 (STT)
    for xref in idautils.XrefsTo(radar_mode_state_addr, idaapi.XREF_ALL):
        func = idaapi.get_func(xref.frm)
        if not func:
            continue
        
        func_name = idc.get_func_name(func.start_ea)
        if not func_name:
            continue
        
        # Look for comparison with 5 near this xref
        ea = xref.frm
        for _ in range(10):  # Check next 10 instructions
            mnem = idc.print_insn_mnem(ea)
            if mnem == 'cmp':
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm and idc.get_operand_value(ea, 1) == 5:
                    results['stt_mode_checks'].append({
                        'function': func_name,
                        'function_address': hex(func.start_ea),
                        'check_address': hex(ea),
                        'xref_address': hex(xref.frm)
                    })
                    break
            ea = idc.next_head(ea)
    
    # Find functions using radar_selected_target_index
    for xref in idautils.XrefsTo(radar_target_addr, idaapi.XREF_ALL):
        func = idaapi.get_func(xref.frm)
        if not func:
            continue
        
        func_name = idc.get_func_name(func.start_ea)
        if func_name:
            results['radar_selected_target_refs'].append({
                'function': func_name,
                'address': hex(func.start_ea),
                'xref_address': hex(xref.frm)
            })
    
    # Find functions handling weapon type 0x13 (AIM-120)
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Look for type 0x13 checks
        ea = func.start_ea
        has_type_13 = False
        has_radar_ref = False
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            # Check for type 0x13 comparison
            if mnem == 'cmp':
                op_type = idc.get_operand_type(ea, 1)
                if op_type == idc.o_imm and idc.get_operand_value(ea, 1) == 0x13:
                    has_type_13 = True
            
            # Check for radar globals
            for ref in idautils.DataRefsFrom(ea):
                if ref == radar_mode_state_addr or ref == radar_target_addr:
                    has_radar_ref = True
            
            ea = idc.next_head(ea)
        
        if has_type_13 and has_radar_ref:
            results['type_0x13_handlers'].append({
                'function': func_name,
                'address': hex(func_ea)
            })
    
    return results

print("Finding radar lock system integration...")
results = find_radar_lock_integration()

with open('temp/radar_lock_search.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nRadar mode STT checks (== 5): {len(results['stt_mode_checks'])}")
for check in results['stt_mode_checks'][:10]:
    print(f"  {check['function']} @ {check['check_address']}")

print(f"\nradar_selected_target_index refs: {len(results['radar_selected_target_refs'])}")
for ref in results['radar_selected_target_refs'][:10]:
    print(f"  {ref['function']}")

print(f"\nType 0x13 handlers with radar refs: {len(results['type_0x13_handlers'])}")
for handler in results['type_0x13_handlers']:
    print(f"  {handler['function']}")

idc.qexit(0)
