"""
Extract picfont_idx_dat_loader and related functions to understand sprite format.

We'll extract:
1. picfont_idx_dat_loader (0x1293F0) - main loader
2. sub_1297F0 - .IDX/.DAT generic loader (called by picfont)
3. Any decompression/decoding functions called
4. File I/O wrappers
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path
from collections import defaultdict

def get_function_detailed(addr, max_depth=2):
    """Get detailed function info including all callees recursively."""
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    result = {
        'address': hex(addr),
        'name': idc.get_func_name(addr),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'calls': [],
        'strings': [],
        'disassembly': []
    }
    
    # Track calls with depth
    call_tree = defaultdict(list)
    
    # Get all instructions in function
    for ea in idautils.FuncItems(addr):
        # Get disassembly
        disasm = idc.generate_disasm_line(ea, 0)
        result['disassembly'].append(f"{ea:08X}  {disasm}")
        
        # Check for string references
        for xref in idautils.DataRefsFrom(ea):
            s_type = idc.get_str_type(xref)
            if s_type is not None and s_type >= 0:
                s = idc.get_strlit_contents(xref)
                if s:
                    result['strings'].append({
                        'address': hex(xref),
                        'string': s.decode('ascii', errors='ignore'),
                        'ref_from': hex(ea)
                    })
        
        # Check for calls
        insn = idautils.DecodeInstruction(ea)
        if insn and insn.itype in [idaapi.NN_call, idaapi.NN_callfi, idaapi.NN_callni]:
            for xref in idautils.XrefsFrom(ea, idaapi.XREF_FAR):
                target_name = idc.get_func_name(xref.to)
                if target_name:
                    call_info = {
                        'address': hex(xref.to),
                        'name': target_name,
                        'from': hex(ea)
                    }
                    result['calls'].append(call_info)
                    call_tree[target_name].append(xref.to)
    
    # Get callee details (depth 1)
    result['callees'] = {}
    if max_depth > 0:
        for name, addrs in call_tree.items():
            addr = addrs[0]  # Use first occurrence
            # Get basic info for callee
            callee_func = idaapi.get_func(addr)
            if callee_func:
                result['callees'][name] = {
                    'address': hex(addr),
                    'size': callee_func.end_ea - callee_func.start_ea,
                    'calls_count': len([c for c in result['calls'] if c['name'] == name])
                }
    
    return result

def find_int21h_calls():
    """Find DOS INT 21h system calls (file I/O)."""
    results = []
    
    # Search for int 21h instructions
    ea = idc.get_inf_attr(idc.INF_MIN_EA)
    end_ea = idc.get_inf_attr(idc.INF_MAX_EA)
    
    while ea < end_ea:
        ea = idc.find_binary(ea, idc.SEARCH_DOWN | idc.SEARCH_NEXT, "CD 21")
        if ea == idc.BADADDR:
            break
        
        func_name = idc.get_func_name(ea)
        if func_name:
            results.append({
                'address': hex(ea),
                'function': func_name,
                'disasm': idc.generate_disasm_line(ea, 0)
            })
        
        ea = ea + 1  # Move past this instruction
    
    return results

def main():
    print("="*80)
    print("EXTRACTING PICFONT LOADER AND FILE I/O SYSTEM")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    output_dir = Path(__file__).parent.parent
    
    # Key functions to extract
    functions_to_extract = {
        'picfont_idx_dat_loader': 0x1293F0,
        'sub_1297F0': 0x1297F0,  # Generic .IDX/.DAT loader
        'file_open': 0x226BD,     # DOS open
        'file_close': 0x226E4,    # DOS close
        'file_read': 0x226F5,     # DOS read
        'file_lseek': 0x2274D,    # DOS seek
    }
    
    results = {}
    
    print("\nExtracting functions...")
    for name, addr in functions_to_extract.items():
        print(f"  Extracting {name} at 0x{addr:08X}...")
        info = get_function_detailed(addr, max_depth=1)
        if info:
            results[name] = info
            print(f"    Size: {info['size']} bytes")
            print(f"    Calls: {len(info['calls'])} functions")
            print(f"    Strings: {len(info['strings'])}")
            if info['strings']:
                for s in info['strings'][:3]:
                    print(f"      '{s['string']}'")
        else:
            print(f"    ERROR: Not a function!")
    
    # Find INT 21h calls
    print("\nSearching for DOS INT 21h calls...")
    int21_calls = find_int21h_calls()
    results['int21h_calls'] = int21_calls
    print(f"  Found {len(int21_calls)} INT 21h calls")
    
    # Show file I/O calls
    print(f"\n  Sample INT 21h calls:")
    for call in int21_calls[:10]:
        print(f"    {call['function']:30} {call['address']}")
    
    # Save results
    json_file = output_dir / "picfont_loader_extraction.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved to: {json_file}")
    
    # Create human-readable version
    txt_file = output_dir / "picfont_loader_disasm.txt"
    with open(txt_file, 'w') as f:
        for name in ['picfont_idx_dat_loader', 'sub_1297F0']:
            if name in results:
                func = results[name]
                f.write("="*80 + "\n")
                f.write(f"Function: {func['name']}\n")
                f.write(f"Address: {func['address']}\n")
                f.write(f"Size: {func['size']} bytes\n")
                f.write("="*80 + "\n\n")
                
                if func['strings']:
                    f.write("STRINGS:\n")
                    for s in func['strings']:
                        f.write(f"  {s['address']}: '{s['string']}'\n")
                    f.write("\n")
                
                if func['callees']:
                    f.write("CALLS:\n")
                    for callee_name, callee_info in func['callees'].items():
                        f.write(f"  {callee_name:40} {callee_info['address']} ({callee_info['size']}B, {callee_info['calls_count']}x)\n")
                    f.write("\n")
                
                f.write("DISASSEMBLY:\n")
                for i, line in enumerate(func['disassembly']):
                    f.write(f"{i:4d}: {line}\n")
                f.write("\n\n")
    
    print(f"Saved disassembly to: {txt_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Functions extracted: {len([k for k in results.keys() if k != 'int21h_calls'])}")
    print(f"INT 21h calls found: {len(int21_calls)}")
    
    # Show picfont loader calls
    if 'picfont_idx_dat_loader' in results:
        print("\npicfont_idx_dat_loader calls:")
        for call in results['picfont_idx_dat_loader']['calls'][:15]:
            print(f"  {call['name']}")
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    
    # Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
