"""
Analyze isldat_state_load function - the ISLDAT file loader
"""

import idc
import idaapi
import idautils

def analyze_isldat_state_load():
    """Analyze the main ISLDAT loader"""
    
    addr = 0x12FC4
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("ISLDAT_STATE_LOAD @ 0x12FC4 - ISLDAT FILE LOADER")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (118 bytes)")
    print()
    
    # Full disassembly
    ea = addr
    line_num = 1
    while ea < func_end:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    print()
    
    # Find who calls this
    print("CALLED BY:")
    xrefs = list(idautils.XrefsTo(addr))
    for xref in xrefs:
        func_ea = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
        func_name = idc.get_func_name(func_ea)
        print(f"  {hex(xref.frm):12s} in {func_name}")
    
    print()

def analyze_worldmap_state_apply():
    """Analyze worldmap_state_apply - likely calls isldat_state_load"""
    
    addr = 0x130D5
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("WORLDMAP_STATE_APPLY @ 0x130D5")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (59 bytes)")
    print()
    
    # Full disassembly
    ea = addr
    line_num = 1
    while ea < func_end:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    print()

if __name__ == '__main__':
    idaapi.auto_wait()
    
    analyze_isldat_state_load()
    analyze_worldmap_state_apply()
    
    print("=" * 80)
    print("ISLDAT LOADER ANALYSIS COMPLETE")
    print("=" * 80)
