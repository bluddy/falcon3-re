#!/usr/bin/env python3
"""
Find all functions that READ r15_external_view_flag (cs:0x107762).
If we find where it's read, we can work backwards to find where it's set.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    flag_addr = 0x107762
    flag_name = "r15_external_view_flag"
    
    print(f"[*] Finding all references to {flag_name} @ 0x{flag_addr:X}...")
    
    # Get all xrefs
    xrefs = list(idautils.XrefsTo(flag_addr))
    print(f"[+] Found {len(xrefs)} total references\n")
    
    readers = []
    writers = []
    
    for xref in xrefs:
        addr = xref.frm
        insn_text = idc.generate_disasm_line(addr, 0)
        func_name = idc.get_func_name(addr)
        func_addr = idc.get_func_attr(addr, idc.FUNCATTR_START)
        
        # Determine if it's a read or write
        is_write = False
        mnem = idc.print_insn_mnem(addr).lower()
        
        # Simple heuristic: if it's a mov and flag is destination
        if 'mov' in mnem:
            # Get operands
            op0 = idc.print_operand(addr, 0)
            if flag_name in op0:
                is_write = True
        
        entry = {
            'addr': f'0x{addr:X}',
            'func': func_name,
            'func_addr': f'0x{func_addr:X}' if func_addr != idc.BADADDR else None,
            'insn': insn_text,
            'mnem': mnem
        }
        
        if is_write:
            writers.append(entry)
            print(f"[WRITE] 0x{addr:X} in {func_name}: {insn_text}")
        else:
            readers.append(entry)
            print(f"[READ]  0x{addr:X} in {func_name}: {insn_text}")
    
    print(f"\n{'='*70}")
    print(f"Summary: {len(readers)} reads, {len(writers)} writes")
    
    # Group by function
    reader_funcs = {}
    for r in readers:
        fname = r['func']
        if fname not in reader_funcs:
            reader_funcs[fname] = []
        reader_funcs[fname].append(r)
    
    writer_funcs = {}
    for w in writers:
        fname = w['func']
        if fname not in writer_funcs:
            writer_funcs[fname] = []
        writer_funcs[fname].append(w)
    
    print(f"\nFunctions that READ the flag:")
    for fname, refs in sorted(reader_funcs.items()):
        print(f"  {fname} ({len(refs)}x)")
    
    print(f"\nFunctions that WRITE the flag:")
    for fname, refs in sorted(writer_funcs.items()):
        print(f"  {fname} ({len(refs)}x)")
    
    # Save results
    output = {
        'flag_address': f'0x{flag_addr:X}',
        'flag_name': flag_name,
        'total_refs': len(xrefs),
        'readers': readers,
        'writers': writers,
        'reader_functions': list(reader_funcs.keys()),
        'writer_functions': list(writer_funcs.keys())
    }
    
    with open(r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\flag_readers_writers.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[+] Results saved to flag_readers_writers.json")
    idc.qexit(0)

if __name__ == "__main__":
    main()
