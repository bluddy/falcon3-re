"""
Analyze final batch of utility functions (10 functions, ranks #160-193).
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
    print("Analyzing utility functions (batch 3 - FINAL)...")
    
    # Final 10 utility functions
    targets = [
        (160, 0x137F93, 16, 38),    # utility_137f93
        (162, 0x13DAD0, 16, 133),   # utility_13dad0
        (172, 0x11CD43, 15, 60),    # utility_11cd43
        (173, 0x11CDAF, 15, 60),    # utility_11cdaf
        (175, 0x135208, 15, 359),   # utility_135208
        (188, 0x049C67, 14, 25),    # utility_49c67
        (189, 0x12BBA6, 14, 169),   # utility_12bba6
        (191, 0x1357AC, 14, 1021),  # utility_large_1357ac
        (192, 0x138ED4, 14, 200),   # utility_138ed4
        (193, 0x1909A0, 14, 308),   # utility_1909a0
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
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\utility_batch3_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()

idc.qexit(0)
