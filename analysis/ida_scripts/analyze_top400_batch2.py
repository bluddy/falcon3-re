"""
Analyze remaining 14 functions from Top 400 (ranks 353-399).
Extract disassembly and context for analysis.
"""

import idc
import idaapi
import idautils
import json

def get_disasm_lines(ea, count=40):
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
    disasm_count = min(func_size // 2 + 20, 100)
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
    print("TOP 400 BATCH 2 ANALYSIS - Remaining 14 functions")
    print("="*70)
    
    idaapi.auto_wait()
    
    # Remaining functions from top_400_functions.json
    targets = [
        (0x128028, 'undoc_128028', 353),
        (0x128042, 'undoc_128042', 354),
        (0x130CE7, 'undoc_130CE7', 357),
        (0x133BD5, 'sub_133BD5', 358),
        (0x13ABA7, 'sub_13ABA7', 359),
        (0x1558C8, 'sub_1558C8', 360),
        (0x16F4B1, 'sub_16F4B1', 362),
        (0x172436, 'undoc_172436', 363),
        (0x17B2B6, 'sub_17B2B6', 365),
        (0x196BB9, 'sub_196BB9', 366),
        (0x19FE2D, 'undoc_19FE2D', 367),
        (0x02C185, 'sub_2C185', 393),
        (0x0345FD, 'sub_345FD', 399),
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
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top400_batch2_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Analyzed {len(results)} functions")
    print(f"✓ Saved to: {output_file}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

idc.qexit(0)
