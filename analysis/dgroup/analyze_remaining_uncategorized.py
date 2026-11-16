"""
Analyze the remaining uncategorized functions (8 more).
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
    
    # Get callers
    callers = []
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller = idc.get_func_name(xref.frm)
            if caller and caller not in callers and len(callers) < 10:
                callers.append(caller)
    
    # Get callees
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
    
    # Get disassembly
    disasm = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            line = idc.generate_disasm_line(head, 0)
            disasm.append(f"0x{head:06X}: {line}")
            if len(disasm) >= 40:
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
    print("Analyzing remaining uncategorized functions...")
    
    # Remaining uncategorized from status
    targets = [
        (46, 0x13DE82, 44, 81),   # Rank #46
        (47, 0x131530, 43, 10),   # Rank #47
        (54, 0x02C58B, 41, 8),    # Rank #54
        (84, 0x135C57, 29, 413),  # Rank #84
        (86, 0x11C707, 28, 196),  # Rank #86
        (87, 0x11D274, 28, 210),  # Rank #87
        (88, 0x13504F, 28, 441),  # Rank #88
        (100, 0x02C595, 24, 8),   # Rank #100
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
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\remaining_uncategorized_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()

idc.qexit(0)
