"""
Analyze first 20 functions from Top 500 (ranks 403-431).
Extract disassembly and context for analysis.
"""

import idc
import idaapi
import idautils
import json

def get_disasm_lines(ea, count=50):
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
    
    # Get disassembly (more lines for larger functions)
    disasm_count = min(func_size // 2 + 20, 120)
    disasm = get_disasm_lines(func.start_ea, disasm_count)
    
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
    print("TOP 500 BATCH 1 ANALYSIS - Ranks 403-431 (first 20)")
    print("="*70)
    
    idaapi.auto_wait()
    
    # First 20 functions from top_500_functions.json that need work
    targets = [
        (0x03DE6F, 'undoc_3DE6F', 403),
        (0x04FECC, 'undoc_4FECC', 408),
        (0x100ACC, 'sub_100ACC', 410),
        (0x102932, 'undoc_102932', 411),
        (0x1086C1, 'sub_1086C1', 412),
        (0x11CB23, 'sub_11CB23', 413),
        (0x11CEAB, 'undoc_11CEAB', 414),
        (0x123FDD, 'undoc_123FDD', 415),
        (0x12A114, 'sub_12A114', 416),
        (0x12A908, 'sub_12A908', 417),
        (0x12BC4F, 'sub_12BC4F', 418),
        (0x12BC64, 'sub_12BC64', 419),
        (0x12BC83, 'sub_12BC83', 420),
        (0x12D4F6, 'sub_12D4F6', 421),
        (0x12D525, 'sub_12D525', 422),
        (0x139169, 'undoc_139169', 423),
        (0x13D744, 'undoc_13D744', 425),
        (0x163CCD, 'undoc_163CCD', 426),
        (0x17DF4D, 'undoc_17DF4D', 427),
        (0x1852E5, 'undoc_1852E5', 428),
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
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top500_batch1_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Analyzed {len(results)} functions")
    print(f"✓ Saved to: {output_file}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

idc.qexit(0)
