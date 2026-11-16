"""
Analyze remaining 27 functions from Top 500 (ranks 429-500).
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
    disasm_count = min(func_size // 2 + 20, 150)
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
    print("TOP 500 BATCH 2 ANALYSIS - Ranks 429-500 (remaining 27)")
    print("="*70)
    
    idaapi.auto_wait()
    
    # Remaining 27 functions from top_500_functions.json that need work
    targets = [
        (0x1854CF, 'sub_1854CF', 429),
        (0x1A6AA6, 'sub_1A6AA6', 430),
        (0x1A86C6, 'sub_1A86C6', 431),
        (0x02978E, 'sub_2978E', 465),
        (0x03E01A, 'sub_3E01A', 469),
        (0x03F287, 'undoc_3F287', 470),
        (0x043842, 'undoc_43842', 475),
        (0x047B68, 'undoc_47B68', 477),
        (0x04AAA4, 'undoc_4AAA4', 480),
        (0x04AC1E, 'sub_4AC1E', 481),
        (0x04AE66, 'sub_4AE66', 482),
        (0x106B07, 'sub_106B07', 484),
        (0x11D346, 'sub_11D346', 485),
        (0x11D388, 'sub_11D388', 486),
        (0x11D3CA, 'sub_11D3CA', 487),
        (0x11FC1B, 'undoc_11FC1B', 488),
        (0x127FF6, 'undoc_127FF6', 489),
        (0x1298AB, 'undoc_1298AB', 491),
        (0x1299AE, 'sub_1299AE', 492),
        (0x129A87, 'sub_129A87', 493),
        (0x12BE93, 'undoc_12BE93', 494),
        (0x12BED1, 'undoc_12BED1', 495),
        (0x12D4E3, 'sub_12D4E3', 496),
        (0x132182, 'sub_132182', 497),
        (0x13296E, 'sub_13296E', 498),
        (0x13367B, 'undoc_13367B', 499),
        (0x136133, 'undoc_136133', 500),
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
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top500_batch2_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Analyzed {len(results)} functions")
    print(f"✓ Saved to: {output_file}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

idc.qexit(0)
