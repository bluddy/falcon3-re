#!/usr/bin/env python3
"""
Find the main game loop or dispatcher that processes input_flag_pending_2
and calls view change handlers. Look for:
1. Functions that call input_poll_handler
2. Main loop functions in R15
3. Dispatch tables based on scan code values
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Finding main loop and input dispatchers...")
    print()
    
    # 1. Find who calls input_poll_handler
    input_poll_addr = 0x12FAC3
    print(f"[*] Finding callers of input_poll_handler @ 0x{input_poll_addr:X}...")
    print()
    
    callers = []
    for xref in idautils.XrefsTo(input_poll_addr):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call references
            caller_addr = xref.frm
            caller_func = idc.get_func_name(caller_addr)
            caller_seg = idc.get_segm_name(caller_addr)
            
            callers.append({
                'addr': '0x{:X}'.format(caller_addr),
                'func': caller_func,
                'segment': caller_seg
            })
            
            print(f"[CALLER] 0x{caller_addr:X} in {caller_seg} / {caller_func}")
    
    print(f"\nFound {len(callers)} callers of input_poll_handler")
    
    # 2. Look for r15_simulation_loop - the main dispatcher
    print()
    print("="*80)
    print("[*] Analyzing r15_simulation_loop (main dispatcher)...")
    print("="*80)
    
    sim_loop_addr = 0x108BAC
    func = idaapi.get_func(sim_loop_addr)
    
    if func:
        print(f"\nr15_simulation_loop @ 0x{sim_loop_addr:X}")
        print(f"Size: {func.end_ea - func.start_ea} bytes")
        print(f"Start: 0x{func.start_ea:X}, End: 0x{func.end_ea:X}")
        
        # Get all function calls in sim_loop
        print("\nFunction calls in r15_simulation_loop:")
        
        ea = func.start_ea
        calls = []
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea).lower() == 'call':
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target) if target != idc.BADADDR else "unknown"
                
                calls.append({
                    'from': '0x{:X}'.format(ea),
                    'to': '0x{:X}'.format(target) if target != idc.BADADDR else 'unknown',
                    'target_name': target_name
                })
                
                # Check if this calls input-related functions
                if any(kw in target_name.lower() for kw in ['input', 'key', 'poll']):
                    print(f"  >>> 0x{ea:X}: call {target_name}")
                else:
                    print(f"      0x{ea:X}: call {target_name}")
            
            ea = idc.next_head(ea, func.end_ea)
        
        print(f"\nTotal calls in r15_simulation_loop: {len(calls)}")
    
    # 3. Look for view_mode_set - where flag is initialized
    print()
    print("="*80)
    print("[*] Checking view_mode_set for clues...")
    print("="*80)
    
    view_mode_set_addr = 0x1086EC
    print(f"\nview_mode_set @ 0x{view_mode_set_addr:X}")
    print("This initializes the flag to 0. Looking for who calls it...")
    
    for xref in idautils.XrefsTo(view_mode_set_addr):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_addr = xref.frm
            caller_func = idc.get_func_name(caller_addr)
            print(f"  Called by: 0x{caller_addr:X} in {caller_func}")
    
    # 4. Search for switch/dispatch on small values (0-13)
    print()
    print("="*80)
    print("[*] Searching for dispatch tables on values 0-13...")
    print("="*80)
    
    # Look for cmp with values 0-13 followed by jumps
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if 'R15' not in seg_name and 'R29' not in seg_name:
            continue
        
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            if idc.print_insn_mnem(ea).lower() == 'cmp':
                # Get the immediate value being compared
                op1_type = idc.get_operand_type(ea, 1)
                if op1_type == idc.o_imm:
                    imm_val = idc.get_operand_value(ea, 1)
                    # Check if it's in our range (0-13)
                    if 0 <= imm_val <= 13:
                        func_name = idc.get_func_name(ea)
                        insn = idc.generate_disasm_line(ea, 0)
                        
                        # Check if there's a jump nearby
                        next_ea = idc.next_head(ea, seg_end)
                        next_mnem = idc.print_insn_mnem(next_ea).lower()
                        if next_mnem and next_mnem[0] == 'j':  # Any jump
                            print(f"[DISPATCH?] 0x{ea:X} in {func_name}: {insn}")
            
            ea = idc.next_head(ea, seg_end)
    
    # Save results
    output = {
        'input_poll_handler_callers': callers,
        'r15_simulation_loop': {
            'addr': '0x{:X}'.format(sim_loop_addr),
            'calls': calls
        }
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\main_loop_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("="*80)
    print("[+] Analysis saved to main_loop_analysis.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
