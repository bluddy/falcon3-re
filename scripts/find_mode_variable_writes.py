"""
Find where byte_595B2 and byte_59573 are written to understand mode transitions
"""

import idaapi
import idc
import idautils

idaapi.auto_wait()

def find_writes_to_variable(var_addr, var_name):
    print(f"\n=== Writes to {var_name} (0x{var_addr:X}) ===\n")
    
    writes = []
    for xref in idautils.DataRefsTo(var_addr):
        func_ea = idc.get_func_attr(xref, idc.FUNCATTR_START)
        func_name = idc.get_func_name(func_ea) if func_ea != idc.BADADDR else "unknown"
        
        # Get the instruction
        disasm = idc.generate_disasm_line(xref, 0)
        mnem = idc.print_insn_mnem(xref)
        
        # Check if it's a write (mov, or, and, xor, add, sub, inc, dec to memory)
        write_ops = ['mov', 'or', 'and', 'xor', 'add', 'sub', 'inc', 'dec', 'shl', 'shr']
        
        # For mov, check if destination is the variable
        if mnem == 'mov':
            op0 = idc.print_operand(xref, 0)
            if var_name in op0 or f"0x{var_addr:X}" in op0.upper():
                writes.append((xref, func_name, disasm))
        elif mnem in write_ops:
            writes.append((xref, func_name, disasm))
    
    # Sort by address
    writes.sort(key=lambda x: x[0])
    
    for addr, func, disasm in writes:
        print(f"0x{addr:X} in {func}:")
        print(f"  {disasm}")
        
        # Show nearby context (2 lines before and after)
        print("  Context:")
        context_start = idc.prev_head(idc.prev_head(addr))
        ea = context_start
        for i in range(5):
            marker = ">>>" if ea == addr else "   "
            print(f"    {marker} 0x{ea:X}: {idc.generate_disasm_line(ea, 0)}")
            ea = idc.next_head(ea)
        print()
    
    print(f"Total writes found: {len(writes)}\n")
    return writes

def find_comparisons_to_variable(var_addr, var_name):
    print(f"\n=== Comparisons of {var_name} (0x{var_addr:X}) ===\n")
    
    comparisons = []
    for xref in idautils.DataRefsTo(var_addr):
        func_ea = idc.get_func_attr(xref, idc.FUNCATTR_START)
        func_name = idc.get_func_name(func_ea) if func_ea != idc.BADADDR else "unknown"
        
        # Get the instruction
        disasm = idc.generate_disasm_line(xref, 0)
        mnem = idc.print_insn_mnem(xref)
        
        # Check if it's a comparison
        if mnem == 'cmp' or mnem == 'test':
            comparisons.append((xref, func_name, disasm))
    
    # Sort by address
    comparisons.sort(key=lambda x: x[0])
    
    # Group by function
    by_func = {}
    for addr, func, disasm in comparisons:
        if func not in by_func:
            by_func[func] = []
        by_func[func].append((addr, disasm))
    
    for func in sorted(by_func.keys()):
        print(f"In {func}:")
        for addr, disasm in by_func[func]:
            print(f"  0x{addr:X}: {disasm}")
        print()
    
    print(f"Total comparisons found: {len(comparisons)}\n")
    return comparisons

if __name__ == '__main__':
    # Primary mode variable
    byte_595B2 = 0x595B2
    
    # Radar type variable
    byte_59573 = 0x59573
    
    print("=" * 70)
    print("RADAR MODE VARIABLE ANALYSIS")
    print("=" * 70)
    
    writes_b2 = find_writes_to_variable(byte_595B2, "byte_595B2")
    comps_b2 = find_comparisons_to_variable(byte_595B2, "byte_595B2")
    
    writes_73 = find_writes_to_variable(byte_59573, "byte_59573")
    comps_73 = find_comparisons_to_variable(byte_59573, "byte_59573")
    
    # Also check word_5959B (target selection variable)
    word_5959B = 0x5959B
    print("\n" + "=" * 70)
    writes_9b = find_writes_to_variable(word_5959B, "word_5959B")
    
    print("\n=== SUMMARY ===")
    print(f"byte_595B2: {len(writes_b2)} writes, {len(comps_b2)} comparisons")
    print(f"byte_59573: {len(writes_73)} writes, {len(comps_73)} comparisons")
    print(f"word_5959B: {len(writes_9b)} writes")
