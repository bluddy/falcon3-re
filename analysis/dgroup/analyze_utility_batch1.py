"""
Analyze first batch of utility_ functions that need investigation.
Focus on ranks #73, #101, #102, #110, #116 (5 highest-ranked).
"""

import idc
import idaapi
import idautils
import json

def get_function_analysis(ea):
    """Get comprehensive analysis of a function."""
    func_name = idc.get_func_name(ea)
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    # Get callers (top 10)
    callers = []
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller = idc.get_func_name(xref.frm)
            if caller and caller not in callers and len(callers) < 10:
                callers.append(caller)
    
    # Get callees (top 10)
    callees = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            mnem = idc.print_insn_mnem(head)
            if mnem in ['call', 'jmp']:
                target = idc.get_operand_value(head, 0)
                if target:
                    target_name = idc.get_func_name(target)
                    if target_name and target_name not in callees and len(callees) < 10:
                        callees.append(target_name)
    
    # Get full disassembly (these are small functions)
    disasm = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            line = idc.generate_disasm_line(head, 0)
            disasm.append(f"0x{head:06X}: {line}")
    
    return {
        'address': ea,
        'name': func_name,
        'size': func.end_ea - func.start_ea,
        'callers': callers,
        'callees': callees,
        'disassembly': disasm
    }

def main():
    print("Analyzing utility_ functions (batch 1)...")
    
    # Top 5 utility functions needing investigation
    targets = [
        (73, 0x13BD06, 34, 884),   # utility_overlay_dispatcher
        (101, 0x11C884, 24, 139),  # utility_11c884
        (102, 0x11C90F, 24, 127),  # utility_11c90f
        (110, 0x11C642, 22, 197),  # utility_11c642
        (116, 0x12C2F7, 21, 176),  # utility_12c2f7
    ]
    
    results = []
    for rank, addr, xrefs, size in targets:
        print(f"\nAnalyzing Rank #{rank}: 0x{addr:06X} ({xrefs} calls, {size}B)")
        analysis = get_function_analysis(addr)
        if analysis:
            analysis['rank'] = rank
            results.append(analysis)
            print(f"  Name: {analysis['name']}")
            print(f"  Callers (5): {', '.join(analysis['callers'][:5])}")
            print(f"  Callees (5): {', '.join(analysis['callees'][:5])}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\utility_batch1_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()

idc.qexit(0)
