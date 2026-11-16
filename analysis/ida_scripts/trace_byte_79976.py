"""
Trace all writes to byte_79976 array to find sprite data source.
"""

import idaapi
import idautils
import idc

def find_array_address():
    """Find the address of byte_79976."""
    # Try to get the named location
    addr = idc.get_name_ea_simple("byte_79976")
    if addr != idc.BADADDR:
        return addr
    
    # Try variations
    for name in ["byte_79976", "_byte_79976", "byte_79976_0"]:
        addr = idc.get_name_ea_simple(name)
        if addr != idc.BADADDR:
            return addr
    
    # Manual address (from documentation)
    # Segment 7989:0976 or similar - need to calculate
    return None

def analyze_xrefs(addr, array_name):
    """Analyze all cross-references to the array."""
    print(f"\nAnalyzing cross-references to {array_name} at 0x{addr:X}")
    print("="*80)
    
    xrefs = list(idautils.XrefsTo(addr))
    print(f"Found {len(xrefs)} direct references")
    
    writes = []
    reads = []
    other = []
    
    for xref in xrefs:
        xref_type = xref.type
        xref_addr = xref.frm
        
        # Get function containing this xref
        func = idaapi.get_func(xref_addr)
        if func:
            func_name = idc.get_func_name(func.start_ea)
            func_addr = func.start_ea
        else:
            func_name = "???"
            func_addr = 0
        
        # Get instruction at xref
        disasm = idc.generate_disasm_line(xref_addr, 0)
        mnem = idc.print_insn_mnem(xref_addr)
        
        # Classify as read or write
        is_write = False
        if mnem in ['mov', 'lea', 'stosb', 'stosw', 'movsb', 'movsw']:
            # Check if destination operand references our array
            op0 = idc.print_operand(xref_addr, 0)
            if array_name in op0 or f'0x{addr:X}' in op0:
                is_write = True
        
        xref_info = {
            'addr': xref_addr,
            'func': func_addr,
            'func_name': func_name,
            'disasm': disasm,
            'mnem': mnem,
            'type': xref_type
        }
        
        if is_write:
            writes.append(xref_info)
        elif mnem in ['mov', 'lea', 'cmp', 'test', 'lodsb', 'lodsw', 'movsb', 'movsw']:
            reads.append(xref_info)
        else:
            other.append(xref_info)
    
    print(f"\nClassification:")
    print(f"  Writes: {len(writes)}")
    print(f"  Reads: {len(reads)}")
    print(f"  Other: {len(other)}")
    
    # Print ALL references first
    print(f"\n{'='*80}")
    print("ALL REFERENCES:")
    print(f"{'='*80}")
    all_refs = writes + reads + other
    for i, ref in enumerate(all_refs):
        print(f"\n[{i}] 0x{ref['addr']:X} in {ref['func_name']} (0x{ref['func']:X})")
        print(f"    {ref['disasm']}")
        print(f"    Type: {ref['type']}, Mnemonic: {ref['mnem']}")
    
    # Print writes (most important)
    if writes:
        print(f"\n{'='*80}")
        print("WRITES TO ARRAY (most important):")
        print(f"{'='*80}")
        for i, w in enumerate(writes):
            print(f"\n[{i}] 0x{w['addr']:X} in {w['func_name']} (0x{w['func']:X})")
            print(f"    {w['disasm']}")
    
    # Print reads for context
    if reads:
        print(f"\n{'='*80}")
        print("READS FROM ARRAY (for context):")
        print(f"{'='*80}")
        for i, r in enumerate(reads[:20]):  # Limit to first 20
            print(f"\n[{i}] 0x{r['addr']:X} in {r['func_name']} (0x{r['func']:X})")
            print(f"    {r['disasm']}")
        if len(reads) > 20:
            print(f"\n... and {len(reads) - 20} more reads")
    
    return writes, reads

def find_loader_functions(writes):
    """Identify likely loader functions from write references."""
    print(f"\n{'='*80}")
    print("LIKELY LOADER FUNCTIONS:")
    print(f"{'='*80}")
    
    # Group writes by function
    func_map = {}
    for w in writes:
        func_addr = w['func']
        func_name = w['func_name']
        if func_addr not in func_map:
            func_map[func_addr] = {
                'name': func_name,
                'addr': func_addr,
                'writes': []
            }
        func_map[func_addr]['writes'].append(w)
    
    # Print functions sorted by number of writes
    sorted_funcs = sorted(func_map.values(), key=lambda x: len(x['writes']), reverse=True)
    
    for i, func_info in enumerate(sorted_funcs):
        print(f"\n[{i}] {func_info['name']} at 0x{func_info['addr']:X}")
        print(f"    Writes {len(func_info['writes'])} times to array")
        
        # Show first few writes
        for w in func_info['writes'][:3]:
            print(f"      0x{w['addr']:X}: {w['disasm']}")
        if len(func_info['writes']) > 3:
            print(f"      ... and {len(func_info['writes']) - 3} more")
    
    return sorted_funcs

def search_for_file_io(loader_funcs):
    """Search loader functions for file I/O operations."""
    print(f"\n{'='*80}")
    print("SEARCHING FOR FILE I/O IN LOADERS:")
    print(f"{'='*80}")
    
    file_io_strings = [
        '.IDX', '.DAT', 'PICFONT', 'GENBMAP', 'FGENBMAP', 
        'PATCHES', 'MADFONT', 'FILE', 'LOAD', 'READ'
    ]
    
    for func_info in loader_funcs[:5]:  # Check top 5 functions
        func_addr = func_info['addr']
        func_name = func_info['name']
        
        print(f"\n{func_name} at 0x{func_addr:X}:")
        
        if func_addr == 0:
            print("  (No function found)")
            continue
        
        func = idaapi.get_func(func_addr)
        if not func:
            print("  (Cannot get function object)")
            continue
        
        # Search for string references in function
        found_strings = []
        for ea in range(func.start_ea, func.end_ea):
            # Check for string references
            for xref in idautils.XrefsFrom(ea):
                if xref.type in [idaapi.fl_F, idaapi.fl_CN, idaapi.fl_CF]:
                    # Check if target is a string
                    target = xref.to
                    str_type = idc.get_str_type(target)
                    if str_type is not None:
                        str_val = idc.get_strlit_contents(target)
                        if str_val:
                            str_text = str_val.decode('ascii', errors='ignore')
                            # Check if it matches our patterns
                            for pattern in file_io_strings:
                                if pattern.upper() in str_text.upper():
                                    found_strings.append((ea, str_text))
                                    break
        
        if found_strings:
            print(f"  Found {len(found_strings)} file-related strings:")
            for ea, s in found_strings[:10]:
                print(f"    0x{ea:X}: {repr(s)}")
        else:
            print("  No file-related strings found")
        
        # Search for calls to known file I/O functions
        file_io_funcs = [
            'op_dispatch_far_entry', 'file_open', 'file_read', 
            'idx_dat_loader', 'picfont_idx_dat_loader'
        ]
        
        found_calls = []
        for ea in range(func.start_ea, func.end_ea):
            if idc.print_insn_mnem(ea) in ['call', 'jmp']:
                target = idc.get_operand_value(ea, 0)
                if target != idc.BADADDR:
                    target_name = idc.get_func_name(target)
                    if target_name:
                        for io_func in file_io_funcs:
                            if io_func.lower() in target_name.lower():
                                found_calls.append((ea, target_name))
                                break
        
        if found_calls:
            print(f"  Found {len(found_calls)} file I/O calls:")
            for ea, name in found_calls[:10]:
                print(f"    0x{ea:X}: calls {name}")

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("TRACING byte_79976 SPRITE ARRAY")
    print("="*80)
    
    # Find the array
    addr = find_array_address()
    
    if addr is None or addr == idc.BADADDR:
        print("\nERROR: Could not find byte_79976!")
        print("Trying manual search...")
        
        # Try to find by searching for references in known functions
        known_refs = [
            ('ui_element_render_complex_a', 0x11CC39),
            ('picfont_idx_dat_loader', 0x1293F0)
        ]
        
        for func_name, func_addr in known_refs:
            print(f"\nSearching in {func_name} at 0x{func_addr:X}...")
            func = idaapi.get_func(func_addr)
            if func:
                # Look for large array accesses
                for ea in range(func.start_ea, func.end_ea):
                    for i in range(2):  # Check both operands
                        op_value = idc.get_operand_value(ea, i)
                        if 0x70000 < op_value < 0x80000:  # Likely segment:offset
                            print(f"  Found potential array ref at 0x{ea:X}: 0x{op_value:X}")
                            addr = op_value
                            break
                if addr:
                    break
    
    if addr is None or addr == idc.BADADDR:
        print("\nFailed to find byte_79976. Please provide the address manually.")
        idc.qexit(1)
        return
    
    print(f"\nFound array at 0x{addr:X}")
    
    # Analyze cross-references
    writes, reads = analyze_xrefs(addr, "byte_79976")
    
    # Find loader functions
    loader_funcs = find_loader_functions(writes)
    
    # Search for file I/O
    search_for_file_io(loader_funcs)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Examine the loader functions identified above")
    print("2. Look for file names or I/O operations in those functions")
    print("3. Trace backwards from those functions to find the ultimate data source")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
