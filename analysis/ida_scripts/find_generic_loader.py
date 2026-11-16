"""
Find generic .IDX/.DAT loader that doesn't reference specific filenames.
Look for pattern: open file, read index, read data entries.
"""

import idaapi
import idautils
import idc

def find_file_io_functions():
    """Find functions that do file I/O operations."""
    print("="*80)
    print("FINDING FILE I/O FUNCTIONS")
    print("="*80)
    
    # Look for functions that call DOS interrupt 21h (file operations)
    # Or functions with names containing "file", "read", "load", "idx", "dat"
    
    file_io_keywords = ['file', 'read', 'load', 'open', 'idx', 'dat', 'disk', 'io']
    
    io_functions = {}
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea).lower()
        
        # Check if name suggests file I/O
        is_io_func = any(keyword in func_name for keyword in file_io_keywords)
        
        if is_io_func:
            func = idaapi.get_func(func_ea)
            if func:
                size = func.end_ea - func.start_ea
                io_functions[func_ea] = {
                    'name': idc.get_func_name(func_ea),
                    'size': size
                }
    
    print(f"\nFound {len(io_functions)} potential file I/O functions:")
    for addr in sorted(io_functions.keys())[:30]:
        info = io_functions[addr]
        print(f"  0x{addr:X}: {info['name']:40} ({info['size']} bytes)")
    
    if len(io_functions) > 30:
        print(f"  ... and {len(io_functions) - 30} more")
    
    return io_functions

def find_functions_with_loops_and_calls():
    """
    Generic loaders typically have:
    1. Loops (to process multiple index entries)
    2. File I/O calls
    3. Moderate size (200-2000 bytes)
    """
    print("\n" + "="*80)
    print("FINDING FUNCTIONS WITH LOADER PATTERN")
    print("="*80)
    
    candidates = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        size = func.end_ea - func.start_ea
        
        # Filter by size (loaders are typically 200-2000 bytes)
        if size < 200 or size > 2000:
            continue
        
        # Count calls
        call_count = 0
        loop_indicators = 0
        
        for ea in range(func.start_ea, func.end_ea):
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ['call', 'callf']:
                call_count += 1
            
            # Loop indicators: conditional jumps backwards
            if mnem in ['jz', 'jnz', 'jl', 'jle', 'jg', 'jge', 'jb', 'jbe', 'ja', 'jae']:
                target = idc.get_operand_value(ea, 0)
                if target < ea:  # Jump backwards = loop
                    loop_indicators += 1
        
        # Candidate if has both calls and loops
        if call_count >= 3 and loop_indicators >= 1:
            func_name = idc.get_func_name(func_ea)
            candidates.append({
                'addr': func_ea,
                'name': func_name,
                'size': size,
                'calls': call_count,
                'loops': loop_indicators
            })
    
    # Sort by combination of calls and loops
    candidates.sort(key=lambda x: x['calls'] + x['loops'] * 2, reverse=True)
    
    print(f"\nFound {len(candidates)} candidate loader functions:")
    print("\nAddr     | Name                                     | Size | Calls | Loops")
    print("-" * 90)
    
    for cand in candidates[:40]:
        print(f"0x{cand['addr']:06X} | {cand['name']:40} | {cand['size']:4} | {cand['calls']:5} | {cand['loops']:5}")
    
    return candidates

def analyze_candidate_loader(func_addr):
    """Analyze a candidate to see if it's an IDX/DAT loader."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {idc.get_func_name(func_addr)} at 0x{func_addr:X}")
    print(f"{'='*80}")
    
    func = idaapi.get_func(func_addr)
    if not func:
        return
    
    # Look for patterns suggesting IDX/DAT loading:
    # 1. Two separate file opens (IDX then DAT)
    # 2. Reading small amount first (index)
    # 3. Loop to process entries
    # 4. Reading larger chunks (data)
    
    # Find all PUSH instructions with small values (likely sizes)
    size_pushes = []
    
    for ea in range(func.start_ea, func.end_ea):
        if idc.print_insn_mnem(ea) == 'push':
            op_type = idc.get_operand_type(ea, 0)
            if op_type == idc.o_imm:
                value = idc.get_operand_value(ea, 0)
                if 4 <= value <= 10000:  # Reasonable file size range
                    size_pushes.append({
                        'addr': ea,
                        'value': value,
                        'disasm': idc.generate_disasm_line(ea, 0)
                    })
    
    if size_pushes:
        print(f"\nSize-like constants (potential read sizes):")
        for sp in size_pushes[:15]:
            print(f"  0x{sp['addr']:X}: {sp['disasm']} (= {sp['value']})")
    
    # Look for string references
    print(f"\nString references:")
    found_strings = False
    for ea in range(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(ea):
            target = xref.to
            str_type = idc.get_str_type(target)
            if str_type is not None:
                str_val = idc.get_strlit_contents(target)
                if str_val:
                    str_text = str_val.decode('ascii', errors='ignore')
                    print(f"  0x{ea:X}: {repr(str_text)}")
                    found_strings = True
    
    if not found_strings:
        print(f"  (none - this is GOOD for a generic loader!)")
    
    # Show first 30 instructions
    print(f"\nFirst 30 instructions:")
    ea = func.start_ea
    for i in range(30):
        if ea >= func.end_ea:
            break
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"  {ea:06X}: {disasm}")
        ea = idc.next_head(ea)

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("SEARCHING FOR GENERIC .IDX/.DAT LOADER")
    print("="*80)
    print()
    
    # Find file I/O functions by name
    io_functions = find_file_io_functions()
    
    # Find functions with loader patterns
    candidates = find_functions_with_loops_and_calls()
    
    # Analyze top candidates
    print("\n" + "="*80)
    print("DETAILED ANALYSIS OF TOP CANDIDATES")
    print("="*80)
    
    for cand in candidates[:10]:
        analyze_candidate_loader(cand['addr'])
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    
    print("\nNext steps:")
    print("1. Review the analyzed functions above")
    print("2. Look for functions with NO string references (generic loaders)")
    print("3. Look for functions with multiple size constants")
    print("4. Check if any reference GENBMAP, PATCHES, etc. indirectly")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
