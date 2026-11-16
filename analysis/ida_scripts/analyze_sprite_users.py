"""
Analyze the three functions that use byte_79976.
"""

import idaapi
import idautils
import idc

def analyze_function(func_addr, func_name):
    """Analyze a function that uses byte_79976."""
    print(f"\n{'='*80}")
    print(f"FUNCTION: {func_name} at 0x{func_addr:X}")
    print(f"{'='*80}")
    
    func = idaapi.get_func(func_addr)
    if not func:
        print("  ERROR: Cannot get function")
        return
    
    func_end = func.end_ea
    size = func_end - func_addr
    print(f"Size: {size} bytes (0x{size:X})")
    
    # Get function calls
    calls = []
    for ea in range(func.start_ea, func.end_ea):
        if idc.print_insn_mnem(ea) in ['call']:
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR:
                target_name = idc.get_func_name(target)
                if not target_name:
                    target_name = f"sub_{target:X}"
                calls.append((ea, target, target_name))
    
    print(f"\nCalls {len(calls)} functions:")
    for ea, target, name in calls[:15]:
        print(f"  0x{ea:X}: {name} at 0x{target:X}")
    if len(calls) > 15:
        print(f"  ... and {len(calls) - 15} more")
    
    # Look for string references
    strings = []
    for ea in range(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(ea):
            target = xref.to
            str_type = idc.get_str_type(target)
            if str_type is not None:
                str_val = idc.get_strlit_contents(target)
                if str_val:
                    str_text = str_val.decode('ascii', errors='ignore')
                    strings.append((ea, str_text))
    
    if strings:
        print(f"\nString references:")
        for ea, s in strings:
            print(f"  0x{ea:X}: {repr(s)}")
    else:
        print("\nNo string references")
    
    # Get first 50 instructions for context
    print(f"\nFirst 50 instructions:")
    ea = func.start_ea
    for i in range(50):
        if ea >= func.end_ea:
            break
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"  {ea:06X}: {disasm}")
        ea = idc.next_head(ea)

def find_writes_to_pointer_target():
    """
    byte_79976 is a pointer. Find where the target of that pointer is written.
    """
    print(f"\n{'='*80}")
    print("FINDING WHERE POINTER TARGET IS WRITTEN")
    print(f"{'='*80}")
    
    # byte_79976 is at segment:offset, likely a far pointer
    # The value AT byte_79976 points to the actual array
    # We need to find where data is written through this pointer
    
    byte_79976_addr = 0x79976
    
    # Read the value (segment:offset pointer)
    # This requires knowing how IDA stores this
    print(f"\nReading pointer value at 0x{byte_79976_addr:X}...")
    
    # Get the dword value (segment:offset)
    ptr_value = idc.get_wide_dword(byte_79976_addr)
    if ptr_value != idc.BADADDR and ptr_value != 0:
        print(f"  Pointer value: 0x{ptr_value:08X}")
        
        # Try to interpret as segment:offset
        segment = (ptr_value >> 16) & 0xFFFF
        offset = ptr_value & 0xFFFF
        linear = (segment << 4) + offset
        
        print(f"  Segment:Offset = {segment:04X}:{offset:04X}")
        print(f"  Linear address = 0x{linear:X}")
        
        # Look for xrefs to this address
        print(f"\nLooking for writes to target array...")
        xrefs = list(idautils.XrefsTo(linear))
        print(f"  Found {len(xrefs)} references to 0x{linear:X}")
        
        for i, xref in enumerate(xrefs[:20]):
            func = idaapi.get_func(xref.frm)
            func_name = idc.get_func_name(func.start_ea) if func else "???"
            disasm = idc.generate_disasm_line(xref.frm, 0)
            print(f"  [{i}] 0x{xref.frm:X} in {func_name}: {disasm}")
    else:
        print(f"  Could not read pointer value (got 0x{ptr_value:08X})")

def search_for_picfont_loader():
    """Search for picfont_idx_dat_loader and see where it stores data."""
    print(f"\n{'='*80}")
    print("ANALYZING picfont_idx_dat_loader")
    print(f"{'='*80}")
    
    # Known address from registry
    loader_addr = 0x1293F0
    
    func = idaapi.get_func(loader_addr)
    if not func:
        print("  ERROR: Cannot find picfont_idx_dat_loader")
        return
    
    func_name = idc.get_func_name(func.start_ea)
    print(f"Function: {func_name} at 0x{loader_addr:X}")
    
    # Look for mov/lea instructions that set up pointers
    print("\nLooking for pointer assignments...")
    for ea in range(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(ea)
        if mnem in ['mov', 'lea']:
            op0 = idc.print_operand(ea, 0)
            op1 = idc.print_operand(ea, 1)
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for assignments to memory locations
            if 'byte_' in op0 or 'word_' in op0 or 'dword_' in op0:
                print(f"  0x{ea:X}: {disasm}")

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("ANALYZING SPRITE ARRAY USAGE")
    print("="*80)
    
    # Analyze the three functions that reference byte_79976
    functions = [
        (0x11C576, "undoc_11C576"),
        (0x11C90F, "utility_11c90f"),
        (0x11CA9E, "sub_11CA9E")
    ]
    
    for addr, name in functions:
        analyze_function(addr, name)
    
    # Try to find where the pointer target is written
    find_writes_to_pointer_target()
    
    # Analyze the loader
    search_for_picfont_loader()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
