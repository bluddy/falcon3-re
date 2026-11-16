#!/usr/bin/env python3
"""
Find campaign and mission file loader functions.
Search for .CAM, .MSN, .TAC file operations and INT 21h file handling.
"""

import idc
import idaapi
import idautils
import json
import re

def find_string_references(search_strings):
    """Find all references to specific strings."""
    results = {}
    
    for search_term in search_strings:
        results[search_term] = []
        
        # Search all strings in database
        for s in idautils.Strings():
            string_text = str(s)
            if search_term.upper() in string_text.upper():
                # Found the string, now find xrefs
                xrefs = []
                for xref in idautils.XrefsTo(s.ea):
                    func_name = idc.get_func_name(xref.frm)
                    if func_name:
                        xrefs.append({
                            'addr': hex(xref.frm),
                            'function': func_name,
                            'type': 'code'
                        })
                
                if xrefs:
                    results[search_term].append({
                        'string': string_text,
                        'addr': hex(s.ea),
                        'xrefs': xrefs
                    })
    
    return results

def find_dos_file_operations():
    """Find DOS INT 21h file operation calls."""
    file_ops = []
    
    # Scan all code for INT 21h calls
    for seg_ea in idautils.Segments():
        seg_end = idc.get_segm_end(seg_ea)
        ea = seg_ea
        
        while ea < seg_end:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for INT 21h
            if mnem == 'int':
                op_val = idc.get_operand_value(ea, 0)
                if op_val == 0x21:
                    # Found INT 21h, check AH register (function code)
                    # Look backwards for MOV AH, xx
                    prev_ea = ea
                    for _ in range(10):  # Look back up to 10 instructions
                        prev_ea = idc.prev_head(prev_ea)
                        if prev_ea == idc.BADADDR:
                            break
                        
                        prev_mnem = idc.print_insn_mnem(prev_ea)
                        prev_disasm = idc.generate_disasm_line(prev_ea, 0)
                        
                        # Check for MOV AH, value
                        if prev_mnem == 'mov' and 'ah' in prev_disasm.lower():
                            # Extract the value
                            match = re.search(r'ah,\s*([0-9A-Fa-fx]+)', prev_disasm, re.IGNORECASE)
                            if match:
                                ah_val_str = match.group(1)
                                try:
                                    if ah_val_str.startswith('0x'):
                                        ah_val = int(ah_val_str, 16)
                                    else:
                                        ah_val = int(ah_val_str, 16)
                                    
                                    func_name = idc.get_func_name(ea)
                                    
                                    # File operation functions we care about:
                                    # 0x3C: Create file
                                    # 0x3D: Open file
                                    # 0x3E: Close file
                                    # 0x3F: Read file
                                    # 0x40: Write file
                                    # 0x41: Delete file
                                    # 0x42: Seek file
                                    
                                    if ah_val in [0x3C, 0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42]:
                                        file_ops.append({
                                            'addr': hex(ea),
                                            'function': func_name if func_name else 'unknown',
                                            'dos_function': hex(ah_val),
                                            'dos_name': {
                                                0x3C: 'Create File',
                                                0x3D: 'Open File',
                                                0x3E: 'Close File',
                                                0x3F: 'Read File',
                                                0x40: 'Write File',
                                                0x41: 'Delete File',
                                                0x42: 'Seek File'
                                            }.get(ah_val, 'Unknown')
                                        })
                                except:
                                    pass
                                break
            
            ea = idc.next_head(ea, seg_end)
    
    return file_ops

def find_dword_79e3a_writes():
    """Find where dword_79E3A is written to (mission pointer initialization)."""
    writes = []
    
    # Get address of dword_79E3A
    var_addr = idc.get_name_ea_simple("dword_79E3A")
    if var_addr == idc.BADADDR:
        return writes
    
    # Find all xrefs to this variable
    for xref in idautils.XrefsTo(var_addr):
        # Check if this is a write (not a read)
        ea = xref.frm
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for MOV instructions writing to dword_79E3A
        if mnem == 'mov' and 'dword_79E3A' in disasm:
            # Check if destination is dword_79E3A (write operation)
            op0 = idc.print_operand(ea, 0)
            if 'dword_79E3A' in op0:
                func_name = idc.get_func_name(ea)
                
                # Get surrounding context
                context_before = []
                prev_ea = ea
                for _ in range(5):
                    prev_ea = idc.prev_head(prev_ea)
                    if prev_ea != idc.BADADDR:
                        context_before.append(idc.generate_disasm_line(prev_ea, 0))
                
                writes.append({
                    'addr': hex(ea),
                    'disasm': disasm,
                    'function': func_name if func_name else 'unknown',
                    'context_before': list(reversed(context_before))
                })
    
    return writes

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("FIND MISSION/CAMPAIGN FILE LOADERS")
    print("="*80)
    print()
    
    # Search for file extension strings
    print("[*] Searching for file extension strings...")
    file_strings = ['.CAM', '.MSN', '.TAC', '.SQU', 'CAMPAIGN', 'MISSION', 
                    'THEATER', 'SQUAD', '.SAV', '.CFG']
    
    string_refs = find_string_references(file_strings)
    
    total_found = sum(len(refs) for refs in string_refs.values())
    print(f"[+] Found {total_found} string matches")
    print()
    
    for search_term, refs in string_refs.items():
        if refs:
            print(f"  {search_term}: {len(refs)} strings found")
            for ref in refs[:3]:  # Show first 3
                print(f"    \"{ref['string']}\" at {ref['addr']}")
                for xref in ref['xrefs'][:2]:
                    print(f"      -> {xref['function']} at {xref['addr']}")
    print()
    
    # Find DOS file operations
    print("[*] Searching for DOS INT 21h file operations...")
    file_ops = find_dos_file_operations()
    print(f"[+] Found {len(file_ops)} file operation calls")
    print()
    
    # Group by function
    ops_by_func = {}
    for op in file_ops:
        func = op['function']
        if func not in ops_by_func:
            ops_by_func[func] = []
        ops_by_func[func].append(op)
    
    print("[*] File operations by function:")
    for func_name in sorted(ops_by_func.keys(), key=lambda f: len(ops_by_func[f]), reverse=True)[:20]:
        ops = ops_by_func[func_name]
        print(f"  {func_name}: {len(ops)} operations")
        
        # Show operation types
        op_types = {}
        for op in ops:
            op_name = op['dos_name']
            op_types[op_name] = op_types.get(op_name, 0) + 1
        
        for op_name, count in sorted(op_types.items()):
            print(f"    - {op_name}: {count}")
    print()
    
    # Find dword_79E3A initialization
    print("[*] Searching for dword_79E3A writes (mission pointer init)...")
    dword_writes = find_dword_79e3a_writes()
    print(f"[+] Found {len(dword_writes)} writes to dword_79E3A")
    print()
    
    for write in dword_writes[:10]:  # Show first 10
        print(f"  {write['addr']} in {write['function']}")
        print(f"    {write['disasm']}")
        if write['context_before']:
            print(f"    Context:")
            for ctx in write['context_before'][-3:]:
                print(f"      {ctx}")
        print()
    
    # Save results
    result = {
        'string_references': {
            term: refs for term, refs in string_refs.items() if refs
        },
        'file_operations': {
            'total': len(file_ops),
            'by_function': {
                func: [
                    {
                        'addr': op['addr'],
                        'dos_function': op['dos_function'],
                        'dos_name': op['dos_name']
                    }
                    for op in ops
                ]
                for func, ops in ops_by_func.items()
            }
        },
        'dword_79E3A_writes': dword_writes
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\file_loaders_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Analysis saved to {output_path}")
    
    # Create summary report
    summary_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\file_loaders_summary.txt'
    with open(summary_path, 'w') as f:
        f.write("MISSION/CAMPAIGN FILE LOADERS - ANALYSIS SUMMARY\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"File Extension Strings Found: {total_found}\n")
        for term, refs in string_refs.items():
            if refs:
                f.write(f"\n{term}:\n")
                for ref in refs:
                    f.write(f"  \"{ref['string']}\" at {ref['addr']}\n")
                    for xref in ref['xrefs']:
                        f.write(f"    -> {xref['function']} at {xref['addr']}\n")
        
        f.write(f"\n\nDOS File Operations: {len(file_ops)}\n")
        f.write("-"*80 + "\n")
        for func_name in sorted(ops_by_func.keys(), key=lambda f: len(ops_by_func[f]), reverse=True):
            ops = ops_by_func[func_name]
            f.write(f"\n{func_name} ({len(ops)} operations):\n")
            for op in ops:
                f.write(f"  {op['addr']}: {op['dos_name']} ({op['dos_function']})\n")
        
        f.write(f"\n\ndword_79E3A Writes: {len(dword_writes)}\n")
        f.write("-"*80 + "\n")
        for write in dword_writes:
            f.write(f"\n{write['addr']} in {write['function']}:\n")
            f.write(f"  {write['disasm']}\n")
    
    print(f"[+] Summary saved to {summary_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
