"""
Find the connection between view mode numbers and r15_external_view_flag.

We observed handlers setting word_79F16 to values like 7, 8.
These might be view mode indices that later get translated to the external flag.

Strategy:
1. Find all writes to word_79F16
2. Find all reads of word_79F16
3. Find code that reads word_79F16 and writes to r15_external_view_flag
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("FINDING VIEW MODE TO FLAG CONNECTION")
    print("="*80)
    
    FLAG_ADDR = 0x107762
    VIEW_MODE_VAR = 0x79F16  # word_79F16
    
    print(f"\nSearching for code that:")
    print(f"  1. Reads word_79F16 (0x{VIEW_MODE_VAR:X})")
    print(f"  2. Writes r15_external_view_flag (0x{FLAG_ADDR:X})")
    print()
    
    # Find all functions that reference the view mode variable
    view_mode_refs = set()
    for xref in idautils.XrefsTo(VIEW_MODE_VAR):
        func_addr = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
        if func_addr != idc.BADADDR:
            view_mode_refs.add(func_addr)
    
    # Find all functions that reference the flag
    flag_refs = set()
    for xref in idautils.XrefsTo(FLAG_ADDR):
        func_addr = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
        if func_addr != idc.BADADDR:
            flag_refs.add(func_addr)
    
    print(f"[*] Functions referencing word_79F16: {len(view_mode_refs)}")
    print(f"[*] Functions referencing r15_external_view_flag: {len(flag_refs)}")
    
    # Find intersection
    both = view_mode_refs & flag_refs
    
    if both:
        print(f"\n[***] FOUND {len(both)} FUNCTION(S) THAT REFERENCE BOTH!")
        print()
        
        for func_addr in both:
            func_name = idc.get_func_name(func_addr)
            print(f"  {func_name} at 0x{func_addr:X}")
            
            # Show the function
            func = idaapi.get_func(func_addr)
            if func:
                print(f"    Size: {func.end_ea - func.start_ea} bytes")
                print(f"    Disassembly:")
                
                ea = func.start_ea
                for i in range(min(50, func.end_ea - func.start_ea)):
                    insn = idc.GetDisasm(ea)
                    
                    # Highlight interesting instructions
                    if '79F16' in insn:
                        print(f"      >>> 0x{ea:X}: {insn}  [VIEW_MODE_VAR]")
                    elif '107762' in insn or 'r15_external_view_flag' in insn:
                        print(f"      >>> 0x{ea:X}: {insn}  [FLAG!]")
                    else:
                        print(f"          0x{ea:X}: {insn}")
                    
                    ea = idc.next_head(ea, func.end_ea)
                    if ea >= func.end_ea:
                        break
                print()
    else:
        print(f"\n[!] No functions reference both variables")
        print(f"\n[*] This might mean:")
        print(f"    - The connection is indirect (through multiple functions)")
        print(f"    - The view mode variable controls something else")
        print(f"    - The flag is set by a different mechanism")
        
        # Show a few functions that write to the flag
        print(f"\n[*] Functions that write to r15_external_view_flag:")
        for xref in idautils.XrefsTo(FLAG_ADDR):
            mnem = idc.print_insn_mnem(xref.frm)
            if mnem in ['mov', 'xor', 'or', 'and']:
                op0_type = idc.get_operand_type(xref.frm, 0)
                if op0_type == idc.o_mem:
                    op0_addr = idc.get_operand_value(xref.frm, 0)
                    if op0_addr == FLAG_ADDR:
                        func = idc.get_func_name(xref.frm)
                        insn = idc.GetDisasm(xref.frm)
                        print(f"    {func}: {insn}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
