#!/usr/bin/env python3
"""
Search for ANY writes near 0x107762 (±100 bytes range).
Maybe the flag is accessed with different addressing mode.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    target_addr = 0x107762
    search_range = 100
    
    start_addr = target_addr - search_range
    end_addr = target_addr + search_range
    
    print("[*] Searching for writes in range 0x{:X} - 0x{:X}".format(start_addr, end_addr))
    print("[*] Target: 0x{:X} (r15_external_view_flag)".format(target_addr))
    print()
    
    # Search all code for writes to this range
    writes = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Only search code segments
        if not idc.get_segm_attr(seg_ea, idc.SEGATTR_PERM) & 1:  # executable
            continue
            
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea).lower()
            
            # Check for write instructions
            if mnem in ['mov', 'xor', 'or', 'and', 'inc', 'dec', 'not', 'neg']:
                # Get destination operand
                op0_type = idc.get_operand_type(ea, 0)
                
                # Check if it's a memory reference
                if op0_type in [idc.o_mem, idc.o_displ, idc.o_phrase]:
                    # Get the effective address if possible
                    op0_addr = idc.get_operand_value(ea, 0)
                    
                    # Check if in our range
                    if start_addr <= op0_addr <= end_addr:
                        func_name = idc.get_func_name(ea)
                        insn = idc.generate_disasm_line(ea, 0)
                        
                        writes.append({
                            'addr': '0x{:X}'.format(ea),
                            'target': '0x{:X}'.format(op0_addr),
                            'offset': op0_addr - target_addr,
                            'func': func_name,
                            'segment': seg_name,
                            'insn': insn,
                            'mnem': mnem
                        })
                        
                        marker = " >>> TARGET" if op0_addr == target_addr else ""
                        print("[WRITE] 0x{:X} -> 0x{:X} (offset {:+3d}) in {}{}".format(
                            ea, op0_addr, op0_addr - target_addr, func_name, marker))
                        print("        {}".format(insn))
            
            ea = idc.next_head(ea, seg_end)
    
    print()
    print("="*80)
    print("Found {} writes in range".format(len(writes)))
    
    # Save results
    output = {
        'target_address': '0x{:X}'.format(target_addr),
        'search_range': search_range,
        'start': '0x{:X}'.format(start_addr),
        'end': '0x{:X}'.format(end_addr),
        'writes': writes
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\nearby_writes.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("Results saved to nearby_writes.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
