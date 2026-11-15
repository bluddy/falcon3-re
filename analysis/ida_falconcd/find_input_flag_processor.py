#!/usr/bin/env python3
"""
Find where input_flag_pending_2 is READ and processed.
This should lead us to the actual view switching code.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Searching for readers of input_flag_pending_2...")
    print()
    
    # Search for the symbol
    flag_addr = idc.get_name_ea_simple("input_flag_pending_2")
    
    if flag_addr == idc.BADADDR:
        print("[!] input_flag_pending_2 not found as symbol, searching by pattern...")
        # It's at es:xxxxx in segment 7894h
        # From the disasm: mov es:input_flag_pending_2, di
        # We need to find all xrefs
        flag_addr = None
    else:
        print(f"[+] Found input_flag_pending_2 at 0x{flag_addr:X}")
    
    if flag_addr:
        xrefs = list(idautils.XrefsTo(flag_addr))
        print(f"[+] Found {len(xrefs)} references")
        print()
        
        for xref in xrefs:
            addr = xref.frm
            func_name = idc.get_func_name(addr)
            insn = idc.generate_disasm_line(addr, 0)
            mnem = idc.print_insn_mnem(addr).lower()
            
            # Check if read or write
            if 'mov' in mnem:
                op0 = idc.print_operand(addr, 0)
                if 'input_flag_pending_2' in op0:
                    access_type = "WRITE"
                else:
                    access_type = "READ"
            else:
                access_type = "USE"
            
            print(f"[{access_type:5s}] 0x{addr:X} in {func_name}")
            print(f"        {insn}")
            print()
    
    # Also search by string pattern in case symbol not found
    print("[*] Searching for 'input_flag_pending' pattern in all code...")
    
    found_refs = []
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            insn = idc.generate_disasm_line(ea, 0)
            if 'input_flag_pending' in insn:
                func_name = idc.get_func_name(ea)
                found_refs.append({
                    'addr': '0x{:X}'.format(ea),
                    'func': func_name,
                    'segment': seg_name,
                    'insn': insn
                })
                print(f"[FOUND] 0x{ea:X} in {seg_name} / {func_name}")
                print(f"        {insn}")
            
            ea = idc.next_head(ea, seg_end)
    
    # Save
    output = {
        'flag_name': 'input_flag_pending_2',
        'references': found_refs
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_flag_refs.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print()
    print(f"[+] Found {len(found_refs)} total references")
    print("[+] Results saved to input_flag_refs.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
