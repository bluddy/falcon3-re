#!/usr/bin/env python3
"""
Search for XOR/NOT instructions that might toggle the flag.
Also search for INC/DEC that might modify it.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    flag_addr = 0x107762
    
    print("[*] Searching for XOR/NOT/INC/DEC instructions affecting cs:0x{:X}".format(flag_addr))
    print()
    
    # Search R15 segment for toggle-style instructions
    candidates = []
    
    for func_ea in idautils.Functions(0x1078):
        func_name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea).lower()
            
            # Check for toggle-style instructions
            if mnem in ['xor', 'not', 'inc', 'dec', 'neg']:
                insn = idc.generate_disasm_line(ea, 0)
                
                # Check if it mentions our flag address or nearby
                if '107762' in insn or 'r15_external_view_flag' in insn:
                    candidates.append({
                        'addr': '0x{:X}'.format(ea),
                        'func': func_name,
                        'mnem': mnem,
                        'insn': insn
                    })
                    print("[FOUND] 0x{:X} in {}: {}".format(ea, func_name, insn))
            
            ea = idc.next_head(ea, func.end_ea)
    
    print()
    print("="*80)
    print("Found {} potential toggle instructions".format(len(candidates)))
    
    # Also search for the flag value being used as an operand
    print()
    print("[*] Searching for flag address as operand...")
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        
        if not func:
            continue
        
        ea = func.start_ea
        while ea < func.end_ea:
            # Check both operands
            for op_num in range(2):
                op_val = idc.get_operand_value(ea, op_num)
                if op_val == flag_addr:
                    insn = idc.generate_disasm_line(ea, 0)
                    mnem = idc.print_insn_mnem(ea).lower()
                    print("[OPERAND] 0x{:X} in {}: {}".format(ea, func_name, insn))
            
            ea = idc.next_head(ea, func.end_ea)
    
    # Save
    output = {
        'flag_address': '0x{:X}'.format(flag_addr),
        'toggle_candidates': candidates
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\toggle_search.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print("Results saved to toggle_search.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
