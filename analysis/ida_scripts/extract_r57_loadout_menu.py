"""
Extract complete R57 loadout menu system for deep dive analysis.
Get all related functions, their disassembly, and call relationships.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def get_function_disasm(func_ea, max_lines=200):
    """Get complete disassembly of a function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    lines = []
    ea = func.start_ea
    while ea < func.end_ea and len(lines) < max_lines:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    return lines

def get_function_calls(func_ea):
    """Get all functions called by this function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) in ['call', 'callf']:
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    target_name = idc.get_func_name(xref.to)
                    if target_name:
                        calls.append({
                            'address': hex(xref.to),
                            'name': target_name,
                            'from': hex(ea)
                        })
        ea = idc.next_head(ea, func.end_ea)
    
    return calls

def get_function_callers(func_ea):
    """Get all functions that call this function."""
    callers = []
    for xref in idautils.XrefsTo(func_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            caller_func = idaapi.get_func(xref.frm)
            if caller_name and caller_func:
                callers.append({
                    'address': hex(caller_func.start_ea),
                    'name': caller_name,
                    'call_site': hex(xref.frm)
                })
    return callers

def get_string_refs(func_ea):
    """Get string references in function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    strings = []
    ea = func.start_ea
    while ea < func.end_ea:
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type == idc.fl_F:  # Data reference
                str_data = idc.get_strlit_contents(xref.to)
                if str_data:
                    strings.append({
                        'address': hex(xref.to),
                        'string': str_data.decode('ascii', errors='ignore'),
                        'ref_from': hex(ea)
                    })
        ea = idc.next_head(ea, func.end_ea)
    
    return strings

def analyze_function(func_ea, func_name):
    """Complete analysis of a function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    return {
        'address': hex(func_ea),
        'name': func_name,
        'size': func.end_ea - func.start_ea,
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'disassembly': get_function_disasm(func_ea),
        'calls': get_function_calls(func_ea),
        'called_by': get_function_callers(func_ea),
        'strings': get_string_refs(func_ea)
    }

def main():
    print("="*80)
    print("R57 LOADOUT MENU SYSTEM EXTRACTION")
    print("="*80)
    
    idaapi.auto_wait()
    print("✓ Auto-analysis complete")
    
    # Core R57 functions we know about
    r57_functions = {
        # Main state machines
        'r57_menu_state_machine': 0x1A5823,
        'r57_loadout_display_handler': 0x1A7182,
        
        # Display functions (from Top 500)
        'menu_r57_flight_display_handler': 0x1A6AA6,
        'menu_r57_loadout_flight_display': 0x1A86C6,
        
        # Supporting functions (search for r57 prefix)
        # We'll find these by searching
    }
    
    # Find all functions with r57 in name
    print("\nSearching for R57-related functions...")
    all_r57_funcs = {}
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if 'r57' in func_name.lower() or func_ea in r57_functions.values():
            all_r57_funcs[func_name] = func_ea
            print(f"  Found: {func_name} @ {func_ea:#08x}")
    
    print(f"\n✓ Found {len(all_r57_funcs)} R57-related functions")
    
    # Analyze each function
    print("\nAnalyzing functions...")
    results = {}
    
    for func_name, func_ea in sorted(all_r57_funcs.items(), key=lambda x: x[1]):
        print(f"  Analyzing {func_name}...")
        analysis = analyze_function(func_ea, func_name)
        if analysis:
            results[func_name] = analysis
    
    # Save results
    output_file = Path(r'C:\Users\ybarnoy\projects\falcon3\analysis\r57_loadout_menu_complete.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✓ Analyzed {len(results)} functions")
    print(f"✓ Saved to: {output_file}")
    print(f"{'='*80}")
    
    # Summary statistics
    total_calls = sum(len(f['calls']) for f in results.values())
    total_strings = sum(len(f['strings']) for f in results.values())
    total_size = sum(f['size'] for f in results.values())
    
    print(f"\nStatistics:")
    print(f"  Total functions: {len(results)}")
    print(f"  Total size: {total_size} bytes")
    print(f"  Total calls: {total_calls}")
    print(f"  Total strings: {total_strings}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()

idc.qexit(0)
