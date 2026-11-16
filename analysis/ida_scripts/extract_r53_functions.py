#!/usr/bin/env python3
"""
Extract all functions from R53 segment with call relationships and key patterns.
"""

import idc
import idaapi
import idautils
import json

def get_function_info(func_addr):
    """Get detailed information about a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    func_name = idc.get_func_name(func_addr)
    
    # Get basic info
    info = {
        'address': hex(func.start_ea),
        'name': func_name,
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea
    }
    
    # Count instructions
    insn_count = 0
    ea = func.start_ea
    while ea < func.end_ea:
        insn_count += 1
        ea = idc.next_head(ea, func.end_ea)
    info['instruction_count'] = insn_count
    
    # Find function calls (callees)
    callees = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR and target != 0:
                callee_name = idc.get_func_name(target)
                if callee_name:
                    callees.append({
                        'address': hex(target),
                        'name': callee_name,
                        'call_site': hex(ea)
                    })
        ea = idc.next_head(ea, func.end_ea)
    
    info['callees'] = callees
    info['call_count'] = len(callees)
    
    # Look for data references
    data_refs = []
    ea = func.start_ea
    ref_count = 0
    while ea < func.end_ea and ref_count < 50:  # Limit to 50 data refs per function
        # Check for data references
        for ref in idautils.DataRefsFrom(ea):
            ref_name = idc.get_name(ref)
            if ref_name and not ref_name.startswith('loc_') and not ref_name.startswith('sub_'):
                data_refs.append({
                    'address': hex(ref),
                    'name': ref_name,
                    'access_at': hex(ea)
                })
                ref_count += 1
                if ref_count >= 50:
                    break
        ea = idc.next_head(ea, func.end_ea)
    
    info['data_refs'] = data_refs
    info['data_ref_count'] = len(data_refs)
    
    # Check for string references
    strings = []
    ea = func.start_ea
    str_count = 0
    while ea < func.end_ea and str_count < 20:  # Limit to 20 strings
        str_type = idc.get_str_type(ea)
        if str_type is not None:
            string_val = idc.get_strlit_contents(ea)
            if string_val:
                try:
                    strings.append({
                        'address': hex(ea),
                        'string': string_val.decode('ascii', errors='ignore')
                    })
                    str_count += 1
                except:
                    pass
        ea = idc.next_head(ea, func.end_ea)
    
    info['strings'] = strings
    
    return info

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("EXTRACT R53 FUNCTIONS")
    print("="*80)
    print()
    
    # Find R53 segment
    r53_seg = None
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if 'R53' in seg_name:
            r53_seg = {
                'name': seg_name,
                'start': seg_ea,
                'end': idc.get_segm_end(seg_ea),
                'size': idc.get_segm_end(seg_ea) - seg_ea
            }
            break
    
    if not r53_seg:
        print("[!] R53 segment not found")
        idc.qexit(1)
    
    print(f"[+] R53 Segment: {r53_seg['name']}")
    print(f"    Address: {r53_seg['start']:#x} - {r53_seg['end']:#x}")
    print(f"    Size: {r53_seg['size']} bytes")
    print()
    
    # Find all functions in R53
    print("[*] Scanning for functions in R53...")
    
    functions = []
    ea = r53_seg['start']
    
    while ea < r53_seg['end']:
        func = idaapi.get_func(ea)
        if func and func.start_ea == ea:  # Found a function start
            func_info = get_function_info(ea)
            if func_info:
                functions.append(func_info)
                print(f"[+] {func_info['name']}")
                print(f"    Address: {func_info['start']}")
                print(f"    Size: {func_info['size']} bytes")
                print(f"    Instructions: {func_info['instruction_count']}")
                print(f"    Calls: {func_info['call_count']}")
                print(f"    Data refs: {func_info['data_ref_count']}")
                if func_info['strings']:
                    print(f"    Strings: {len(func_info['strings'])}")
                print()
            
            ea = func.end_ea  # Skip to end of function
        else:
            ea = idc.next_head(ea, r53_seg['end'])
    
    print(f"[+] Found {len(functions)} functions in R53")
    print()
    
    # Sort functions by size
    functions_by_size = sorted(functions, key=lambda x: x['size'], reverse=True)
    
    print("[*] Top 10 largest functions:")
    for i, func in enumerate(functions_by_size[:10], 1):
        print(f"{i:2d}. {func['name']}: {func['size']} bytes, {func['instruction_count']} instructions")
    print()
    
    # Sort by call count
    functions_by_calls = sorted(functions, key=lambda x: x['call_count'], reverse=True)
    
    print("[*] Top 10 functions by call count:")
    for i, func in enumerate(functions_by_calls[:10], 1):
        print(f"{i:2d}. {func['name']}: {func['call_count']} calls")
    print()
    
    # Find most called functions (build reverse call graph)
    callee_count = {}
    for func in functions:
        for callee in func['callees']:
            callee_name = callee['name']
            if callee_name not in callee_count:
                callee_count[callee_name] = []
            callee_count[callee_name].append(func['name'])
    
    print("[*] Top 10 most called functions (from R53):")
    most_called = sorted(callee_count.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (callee_name, callers) in enumerate(most_called[:10], 1):
        print(f"{i:2d}. {callee_name}: called by {len(callers)} functions")
        # Show first 5 callers
        for caller in callers[:5]:
            print(f"        <- {caller}")
        if len(callers) > 5:
            print(f"        ... and {len(callers)-5} more")
    print()
    
    # Save results
    result = {
        'r53_segment': {
            'name': r53_seg['name'],
            'start': hex(r53_seg['start']),
            'end': hex(r53_seg['end']),
            'size': r53_seg['size']
        },
        'function_count': len(functions),
        'functions': functions,
        'call_graph': {
            'callee_to_callers': {
                name: callers for name, callers in callee_count.items()
            }
        }
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_functions.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Results saved to {output_path}")
    
    # Also create a summary report
    summary_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\r53_functions_summary.txt'
    with open(summary_path, 'w') as f:
        f.write("R53 MISSION BRIEFING - FUNCTION ANALYSIS\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Segment: {r53_seg['name']}\n")
        f.write(f"Address: {r53_seg['start']:#x} - {r53_seg['end']:#x}\n")
        f.write(f"Size: {r53_seg['size']} bytes\n")
        f.write(f"Functions: {len(functions)}\n\n")
        
        f.write("ALL FUNCTIONS (by address)\n")
        f.write("-"*80 + "\n")
        for func in sorted(functions, key=lambda x: int(x['start'], 16)):
            f.write(f"{func['start']}  {func['name']:<50} {func['size']:5d} bytes  {func['instruction_count']:4d} insns  {func['call_count']:3d} calls\n")
        
        f.write("\n\nLARGEST FUNCTIONS\n")
        f.write("-"*80 + "\n")
        for func in functions_by_size[:20]:
            f.write(f"{func['name']}\n")
            f.write(f"  Address: {func['start']} - {func['end']}\n")
            f.write(f"  Size: {func['size']} bytes\n")
            f.write(f"  Instructions: {func['instruction_count']}\n")
            f.write(f"  Calls {func['call_count']} functions\n")
            if func['callees']:
                f.write(f"  Callees:\n")
                for callee in func['callees'][:10]:
                    f.write(f"    - {callee['name']}\n")
                if len(func['callees']) > 10:
                    f.write(f"    ... and {len(func['callees'])-10} more\n")
            f.write("\n")
    
    print(f"[+] Summary saved to {summary_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
