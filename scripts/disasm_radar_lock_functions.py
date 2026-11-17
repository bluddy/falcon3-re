import idc
import idautils
import idaapi
import json

def disassemble_function(func_ea, max_lines=200):
    """Disassemble a function completely"""
    result = []
    
    func = idaapi.get_func(func_ea)
    if not func:
        return result
    
    ea = func.start_ea
    line_count = 0
    
    while ea < func.end_ea and line_count < max_lines:
        disasm = idc.generate_disasm_line(ea, 0)
        result.append({
            'ea': hex(ea),
            'disasm': disasm
        })
        
        ea = idc.next_head(ea)
        line_count += 1
    
    return result

print("Disassembling radar-related functions...")

# Known radar functions from previous analysis
functions = {
    'radar_acm_target_step': 0x39E13,           # mode_stream_select_step (scans targets)
    'radar_f5f6f7_mode_dispatcher': 0x6CDA8,    # r06_mode_step_dispatch
    'radar_stt_locked_target_handler': 0x2C12B, # stub
    'radar_detection_azimuth_range_check': 0x3A9B7,  # farobj_floor_match_dispatch
    'radar_detection_range_gate': 0x3AA7E,       # bound_range_check_4aad
}

results = {}

for name, addr in functions.items():
    print(f"Disassembling {name} @ {hex(addr)}...")
    disasm = disassemble_function(addr)
    results[name] = {
        'address': hex(addr),
        'size': len(disasm),
        'disasm': disasm
    }

with open('temp/radar_functions_disasm.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nDisassembled functions:")
for name, data in results.items():
    print(f"  {name}: {data['size']} instructions")

# Also check if radar globals are properly named
print("\nVerifying radar global names in IDA...")
data_seg = None
for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    if seg and seg.type == idaapi.SEG_DATA:
        data_seg = seg
        break

if data_seg:
    data_base = data_seg.start_ea
    radar_globals = [
        (0x595B2, 'radar_mode_state'),
        (0x59573, 'radar_type_selector'),
        (0x5959B, 'radar_selected_target_index'),
        (0x4AAD, 'radar_range_max'),
        (0x4AAF, 'radar_range_min'),
    ]
    
    for offset, expected in radar_globals:
        addr = data_base + offset
        actual = idc.get_name(addr)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {expected} @ {hex(addr)} (got: {actual})")

idc.qexit(0)
