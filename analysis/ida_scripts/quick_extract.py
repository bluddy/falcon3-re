"""
Quick extraction script - focused on immediate needs.
1. Find string references to menu file names
2. Find INT 21h file operations
3. Exit immediately
"""

import idc
import idaapi
import idautils

def main():
    # Wait for analysis
    idaapi.auto_wait()
    
    print("\n=== STRING SEARCH ===")
    # Search for specific strings
    search_terms = [b"ARMS", b"MENU", b".IDX", b".DAT", b"COMM"]
    
    for term in search_terms:
        ea = idc.get_inf_attr(idc.INF_MIN_EA)
        while True:
            ea = idc.find_binary(ea, idc.SEARCH_DOWN | idc.SEARCH_CASE, term.hex())
            if ea == idc.BADADDR:
                break
            
            # Get string at this address
            try:
                str_val = idc.get_strlit_contents(ea)
                if str_val:
                    print(f"\nFound at {hex(ea)}: {str_val.decode('ascii', errors='ignore')}")
                    
                    # Find xrefs
                    for xref in idautils.XrefsTo(ea):
                        func = idc.get_func_name(xref.frm)
                        print(f"  -> Referenced by {func} at {hex(xref.frm)}")
            except:
                pass
            
            ea = idc.next_head(ea)
            if ea == idc.BADADDR:
                break
    
    print("\n=== INT 21h CALLS ===")
    # Find INT 21h
    ea = idc.get_inf_attr(idc.INF_MIN_EA)
    count = 0
    while ea != idc.BADADDR and count < 50:  # Limit to first 50
        if idc.print_insn_mnem(ea) == "int" and idc.get_operand_value(ea, 0) == 0x21:
            func = idc.get_func_name(ea)
            # Look for MOV AH before
            check = ea - 20
            ah_val = "?"
            while check < ea:
                if idc.print_insn_mnem(check) == "mov" and idc.print_operand(check, 0) == "ah":
                    ah_val = hex(idc.get_operand_value(check, 1))
                    break
                check = idc.next_head(check)
            
            print(f"{hex(ea)}: {func} - AH={ah_val}")
            count += 1
        
        ea = idc.next_head(ea)
    
    print("\n=== DONE ===")
    idc.qexit(0)

if __name__ == "__main__":
    main()
