"""
Analyze first 15 functions from Top 400 (ranks 307-321).
Extract disassembly and context for analysis.
"""

import idc
import idaapi
import idautils
import json

def get_disasm_lines(ea, count=30):
    """Get disassembly lines from address."""
    lines = []
    for i in range(count):
        if ea == idc.BADADDR:
            break
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea)
    return lines

def get_function_xrefs_from(func_ea):
    """Get functions this function calls."""
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
                            'type': 'near' if idc.print_insn_mnem(ea) == 'call' else 'far'
                        })
        ea = idc.next_head(ea, func.end_ea)
    return calls

def get_function_xrefs_to_list(func_ea):
    """Get list of functions calling this function."""
    callers = []
    for xref in idautils.XrefsTo(func_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                callers.append({
                    'address': hex(xref.frm),
                    'name': caller_name
                })
    return callers

def analyze_function(func_ea, func_name):
    """Analyze a single function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return None
    
    func_size = func.end_ea - func.start_ea
    
    # Get disassembly
    disasm = get_disasm_lines(func.start_ea, func_size // 2 + 10)
    
    # Get call relationships
    calls = get_function_xrefs_from(func_ea)
    callers = get_function_xrefs_to_list(func_ea)
    
    return {
        'address': hex(func_ea),
        'name': func_name,
        'size': func_size,
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'calls_count': len(calls),
        'called_by_count': len(callers),
        'calls': calls,
        'called_by': callers[:10],  # Limit to 10
        'disassembly': disasm
    }

def main():
    print("="*70)
    print("TOP 400 BATCH 1 ANALYSIS - Ranks 307-321")
    print("="*70)
    
    idaapi.auto_wait()
    
    # Functions to analyze (from top_400_functions.json)
    targets = [
        (0x02C53B, 'sub_2C53B', 307),
        (0x02C8AB, 'sub_2C8AB', 308),
        (0x02C8C9, 'sub_2C8C9', 309),
        (0x02C8D3, 'sub_2C8D3', 310),
        (0x100BD0, 'sub_100BD0', 316),
        (0x101659, 'sub_101659', 317),
        (0x12FA2A, 'sub_12FA2A', 319),
        (0x1573C3, 'undoc_1573C3', 320),
        (0x181BC7, 'undoc_181BC7', 321),
        (0x1A0A0F, 'undoc_1A0A0F', 322),
        (0x02C905, 'sub_2C905', 342),
        (0x02C919, 'sub_2C919', 343),
        (0x036FE5, 'sub_36FE5', 344),
        (0x11CF6A, 'undoc_11CF6A', 351),
        (0x122595, 'undoc_122595', 352),
    ]
    
    results = []
    
    for func_ea, func_name, rank in targets:
        print(f"\nAnalyzing rank #{rank}: {func_name} at 0x{func_ea:06X}...")
        
        analysis = analyze_function(func_ea, func_name)
        if analysis:
            analysis['rank'] = rank
            results.append(analysis)
            print(f"  ✓ {analysis['size']}B, {analysis['calls_count']} calls, {analysis['called_by_count']} callers")
        else:
            print(f"  ✗ Failed to analyze")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top400_batch1_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Analyzed {len(results)} functions")
    print(f"✓ Saved to: {output_file}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

idc.qexit(0)
