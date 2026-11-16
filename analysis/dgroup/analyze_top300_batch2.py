"""
Analyze second batch of Top 300 new functions (ranks 240-283, remaining 17 functions).
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
                    if target_name and target_name not in callees and len(callees) < 15:
                        callees.append(target_name)
    
    # Get key disassembly
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
    print("Analyzing Top 300 new functions (batch 2: ranks 240-283)...")
    
    # Remaining 17 functions
    targets = [
        (240, 0x02C4B9, 11, 8),      # sub_2C4B9
        (241, 0x02C5D1, 11, 8),      # sub_2C5D1
        (245, 0x1016A8, 11, 41),     # sub_1016A8
        (246, 0x106AD0, 11, 41),     # sub_106AD0
        (247, 0x11CE1B, 11, 48),     # undoc_11CE1B
        (248, 0x11CE7B, 11, 48),     # undoc_11CE7B
        (249, 0x13462B, 11, 221),    # sub_13462B
        (250, 0x13DDC3, 11, 20),     # sub_13DDC3
        (251, 0x160096, 11, 357),    # undoc_160096
        (275, 0x04D75F, 10, 99),     # undoc_4D75F
        (276, 0x10106C, 10, 130),    # sub_10106C
        (277, 0x1017D5, 10, 123),    # sub_1017D5
        (278, 0x106457, 10, 220),    # sub_106457
        (280, 0x11CBA8, 10, 145),    # sub_11CBA8
        (281, 0x11CE4B, 10, 48),     # undoc_11CE4B
        (282, 0x185569, 10, 179),    # undoc_185569
        (283, 0x1AAACC, 10, 498),    # sub_1AAACC
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
            print(f"  Callers (3): {', '.join(analysis['callers'][:3])}")
            print(f"  Callees (3): {', '.join(analysis['callees'][:3])}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top300_batch2_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()

idc.qexit(0)
