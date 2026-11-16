"""
Analyze first batch of Top 300 new functions (ranks 201-230, 15 functions).
Focus on highest call frequency first.
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
    
    # Get key disassembly
    disasm = []
    max_lines = 50 if func.end_ea - func.start_ea < 500 else 30
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            line = idc.generate_disasm_line(head, 0)
            disasm.append(f"0x{head:06X}: {line}")
            if len(disasm) >= max_lines:
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
    print("Analyzing Top 300 new functions (batch 1: ranks 201-230)...")
    
    # First 15 functions needing work (highest priority)
    targets = [
        (202, 0x02C527, 13, 8),      # sub_2C527
        (206, 0x11CD7F, 13, 48),     # undoc_11CD7F
        (207, 0x11CDEB, 13, 48),     # undoc_11CDEB
        (208, 0x127EFF, 13, 162),    # undoc_127EFF
        (209, 0x129591, 13, 24),     # undoc_129591
        (211, 0x1941E8, 13, 1376),   # sub_1941E8 (LARGE)
        (212, 0x195F81, 13, 1409),   # sub_195F81 (LARGE)
        (213, 0x1A2B37, 13, 26),     # undoc_1A2B37
        (224, 0x11CC39, 12, 133),    # sub_11CC39
        (225, 0x11D074, 12, 143),    # sub_11D074
        (226, 0x11D172, 12, 155),    # undoc_11D172
        (227, 0x13153A, 12, 55),     # undoc_13153A
        (228, 0x135FCD, 12, 358),    # undoc_135FCD
        (229, 0x139D85, 12, 481),    # sub_139D85
        (230, 0x13AD67, 12, 348),    # undoc_13AD67
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
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top300_batch1_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()

idc.qexit(0)
