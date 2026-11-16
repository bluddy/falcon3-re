"""
Analyze second batch of utility functions (10 functions, ranks #132-162).
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
    
    # Get callees (top 15)
    callees = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            mnem = idc.print_insn_mnem(head)
            if mnem in ['call', 'jmp']:
                target = idc.get_operand_value(head, 0)
                if target:
                    target_name = idc.get_func_name(target)
                    if target_name and target_name not in callees and len(callees) < 15:
                        callees.append(target_name)
    
    # Get key disassembly (first 30 lines)
    disasm = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            line = idc.generate_disasm_line(head, 0)
            disasm.append(f"0x{head:06X}: {line}")
            if len(disasm) >= 30:
                disasm.append("... (truncated)")
                break
    
    return {
        'address': ea,
        'name': func_name,
        'size': func.end_ea - func.start_ea,
        'callers': callers,
        'callees': callees,
        'disassembly': disasm
    }

def main():
    print("Analyzing utility functions (batch 2)...")
    
    # Next 10 utility functions
    targets = [
        (132, 0x134C3A, 19, 1045),  # utility_large_134c3a
        (140, 0x11C576, 18, 102),   # utility_11c576
        (141, 0x11CA9E, 18, 133),   # utility_11ca9e
        (142, 0x127FC4, 18, 50),    # utility_127fc4
        (143, 0x135C07, 18, 80),    # utility_135c07
        (147, 0x11C504, 17, 114),   # utility_11c504
        (148, 0x13D77C, 17, 237),   # utility_13d77c
        (149, 0x167F75, 17, 101),   # utility_167f75
        (158, 0x133CCF, 16, 1786),  # utility_1786_leaf
        (159, 0x135DF4, 16, 473),   # utility_135df4
    ]
    
    results = []
    for rank, addr, xrefs, size in targets:
        print(f"\nAnalyzing Rank #{rank}: 0x{addr:06X} ({xrefs} calls, {size}B)")
        analysis = get_function_analysis(addr)
        if analysis:
            analysis['rank'] = rank
            analysis['expected_xrefs'] = xrefs
            analysis['expected_size'] = size
            results.append(analysis)
            print(f"  Name: {analysis['name']}")
            print(f"  Callers (5): {', '.join(analysis['callers'][:5])}")
            print(f"  Callees (5): {', '.join(analysis['callees'][:5])}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\utility_batch2_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()

idc.qexit(0)
