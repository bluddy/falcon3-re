"""
Find ISLDAT binary file loader
"""

import idc
import idaapi
import idautils
import json

def find_isldat_string_refs():
    """Find references to 'ISLDAT' string"""
    
    print("=" * 80)
    print("SEARCHING FOR ISLDAT STRING REFERENCES")
    print("=" * 80)
    
    results = []
    
    # Search all segments for "ISLDAT" string
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        print(f"\nSearching segment: {seg_name} ({hex(seg_ea)} - {hex(seg_end)})")
        
        ea = seg_ea
        while ea < seg_end:
            # Check if it's a string
            str_type = idc.get_str_type(ea)
            if str_type is not None:
                str_val = idc.get_strlit_contents(ea)
                if str_val:
                    str_text = str_val.decode('ascii', errors='ignore')
                    if 'ISLDAT' in str_text.upper() or 'ISL' in str_text.upper():
                        print(f"  Found string @ {hex(ea)}: {str_text}")
                        
                        # Find xrefs
                        for xref in idautils.XrefsTo(ea):
                            func_ea = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
                            if func_ea != idc.BADADDR:
                                func_name = idc.get_func_name(func_ea)
                                results.append({
                                    'string': str_text,
                                    'string_addr': hex(ea),
                                    'xref_addr': hex(xref.frm),
                                    'function': func_name,
                                    'func_addr': hex(func_ea)
                                })
                                print(f"    → Used in {func_name} @ {hex(func_ea)}")
            
            ea = idc.next_head(ea)
    
    return results

def find_file_open_functions():
    """Find file open/read functions that might load ISLDAT"""
    
    print("\n" + "=" * 80)
    print("FILE I/O FUNCTIONS")
    print("=" * 80)
    
    file_patterns = ['open', 'read', 'load', 'file', 'stream', 'fopen', 'fread']
    
    file_funcs = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        name_lower = func_name.lower()
        
        if any(p in name_lower for p in file_patterns):
            size = idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            
            # Check if it references any file extension strings
            func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
            ea = func_ea
            has_ext = False
            while ea < func_end:
                if idc.print_insn_mnem(ea) in ['mov', 'lea', 'push']:
                    for i in range(3):
                        operand = idc.print_operand(ea, i)
                        if 'ISR' in operand or 'ISL' in operand or 'DAT' in operand:
                            has_ext = True
                            break
                if has_ext:
                    break
                ea = idc.next_head(ea)
            
            file_funcs.append({
                'name': func_name,
                'address': hex(func_ea),
                'size': size,
                'has_theater_ref': has_ext
            })
            
            marker = " ***" if has_ext else ""
            print(f"  {hex(func_ea):12s} {func_name:50s} ({size:4d} bytes){marker}")
    
    print(f"\nFound {len(file_funcs)} file I/O functions")
    
    return file_funcs

def find_theater_loader():
    """Find theater/map loading functions"""
    
    print("\n" + "=" * 80)
    print("THEATER/MAP LOADER FUNCTIONS")
    print("=" * 80)
    
    theater_patterns = ['theater', 'theatre', 'map', 'world', 'terrain', 'island']
    
    theater_funcs = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if not func_name:
            continue
        
        name_lower = func_name.lower()
        
        if any(p in name_lower for p in theater_patterns):
            size = idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
            theater_funcs.append({
                'name': func_name,
                'address': hex(func_ea),
                'size': size
            })
            print(f"  {hex(func_ea):12s} {func_name:50s} ({size:4d} bytes)")
    
    print(f"\nFound {len(theater_funcs)} theater functions")
    
    return theater_funcs

def search_for_binary_signature():
    """Search for code that reads the ISLDAT header (7A 1A)"""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR ISLDAT HEADER SIGNATURE (0x7A1A)")
    print("=" * 80)
    
    results = []
    
    # Search for comparisons with 0x1A7A or 0x7A1A
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
        
        ea = func_ea
        while ea < func_end:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ['cmp', 'test', 'mov']:
                for i in range(3):
                    operand = idc.print_operand(ea, i)
                    # Check for hex values
                    if '7A1Ah' in operand or '1A7Ah' in operand or '7A' in operand:
                        disasm = idc.GetDisasm(ea)
                        results.append({
                            'function': func_name,
                            'address': hex(ea),
                            'instruction': disasm
                        })
                        print(f"  {hex(ea):12s} {func_name:40s}: {disasm}")
            
            ea = idc.next_head(ea)
    
    print(f"\nFound {len(results)} potential header checks")
    
    return results

def analyze_stream_read_functions():
    """Analyze stream reading functions"""
    
    print("\n" + "=" * 80)
    print("STREAM READING FUNCTIONS")
    print("=" * 80)
    
    # Known from previous analysis
    stream_funcs = [
        ('stream_record_read', 0x12117),
        ('stream_accumulate_driver', 0x1C12F),
    ]
    
    for name, addr in stream_funcs:
        func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
        size = func_end - addr
        
        print(f"\n{name} @ {hex(addr)} ({size} bytes)")
        
        # Show first 30 lines
        ea = addr
        line_num = 1
        while ea < func_end and line_num <= 30:
            disasm = idc.GetDisasm(ea)
            print(f"  {line_num:3d}. {hex(ea):12s} {disasm}")
            line_num += 1
            ea = idc.next_head(ea)
        
        if ea < func_end:
            print(f"  ... ({(func_end - ea) // 2} more lines)")

if __name__ == '__main__':
    idaapi.auto_wait()
    
    results = {
        'isldat_refs': find_isldat_string_refs(),
        'file_io_funcs': find_file_open_functions(),
        'theater_funcs': find_theater_loader(),
        'header_checks': search_for_binary_signature(),
    }
    
    analyze_stream_read_functions()
    
    with open('isldat_loader_search.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("ISLDAT LOADER SEARCH COMPLETE")
    print("=" * 80)
