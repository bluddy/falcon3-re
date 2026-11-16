"""
Analyze the top uncategorized functions to determine their purpose.
Focus on Ranks #5, #7, #8, #9, #10 first.
"""

import idc
import idaapi
import idautils
import json

def get_function_callers(ea, max_callers=10):
    """Get list of functions that call this function."""
    callers = []
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            caller_func = idc.get_func_name(xref.frm)
            if caller_func and caller_func not in callers:
                callers.append(caller_func)
                if len(callers) >= max_callers:
                    break
    return callers

def get_function_callees(ea, max_callees=10):
    """Get list of functions called by this function."""
    callees = []
    func = idaapi.get_func(ea)
    if func:
        for head in idautils.Heads(func.start_ea, func.end_ea):
            if idc.is_code(idc.get_full_flags(head)):
                # Check for call instructions
                if idc.print_insn_mnem(head) in ['call', 'jmp']:
                    target = idc.get_operand_value(head, 0)
                    if target:
                        target_name = idc.get_func_name(target)
                        if target_name and target_name not in callees:
                            callees.append(target_name)
                            if len(callees) >= max_callees:
                                break
    return callees

def get_disassembly(ea, max_lines=50):
    """Get disassembly for a function."""
    func = idaapi.get_func(ea)
    if not func:
        return []
    
    lines = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            disasm = idc.generate_disasm_line(head, 0)
            lines.append(f"0x{head:06X}: {disasm}")
            if len(lines) >= max_lines:
                lines.append("... (truncated)")
                break
    return lines

def analyze_function(ea):
    """Analyze a function and extract metadata."""
    func_name = idc.get_func_name(ea)
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    size = func.end_ea - func.start_ea
    
    # Get xrefs
    xref_count = len(list(idautils.XrefsTo(ea, 0)))
    
    # Get callers and callees
    callers = get_function_callers(ea, 10)
    callees = get_function_callees(ea, 10)
    
    # Get disassembly
    disasm = get_disassembly(ea, 50)
    
    # Check for common patterns
    has_jump_table = False
    has_switch = False
    has_loop = False
    accesses_memory = False
    uses_far_calls = False
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            mnem = idc.print_insn_mnem(head)
            
            if mnem in ['jmp'] and idc.get_operand_type(head, 0) == idc.o_phrase:
                has_jump_table = True
            if mnem in ['jz', 'jnz', 'je', 'jne', 'jg', 'jl', 'jge', 'jle']:
                has_switch = True
            if mnem in ['loop', 'loope', 'loopne']:
                has_loop = True
            if mnem in ['mov', 'lea'] and '[' in idc.print_operand(head, 0):
                accesses_memory = True
            if 'far' in idc.generate_disasm_line(head, 0).lower():
                uses_far_calls = True
    
    return {
        'address': ea,
        'name': func_name,
        'size': size,
        'xrefs': xref_count,
        'callers': callers[:10],
        'callees': callees[:10],
        'patterns': {
            'has_jump_table': has_jump_table,
            'has_switch': has_switch,
            'has_loop': has_loop,
            'accesses_memory': accesses_memory,
            'uses_far_calls': uses_far_calls
        },
        'disassembly': disasm
    }

def main():
    print("Analyzing top uncategorized functions...")
    
    # Top uncategorized functions from analysis
    targets = [
        (5, 0x13DD40, 339, 67),   # Rank #5
        (7, 0x12805C, 273, 19),   # Rank #7
        (8, 0x13DD83, 254, 64),   # Rank #8
        (9, 0x02C59F, 185, 8),    # Rank #9
        (10, 0x02C4FF, 184, 8),   # Rank #10
        (19, 0x13DE3A, 106, 72),  # Rank #19
        (26, 0x088384, 74, 30),   # Rank #26
        (30, 0x02C351, 63, 8),    # Rank #30
    ]
    
    results = []
    
    for rank, addr, expected_xrefs, expected_size in targets:
        print(f"\nAnalyzing Rank #{rank}: 0x{addr:06X} ({expected_xrefs} calls, {expected_size}B)")
        
        analysis = analyze_function(addr)
        if analysis:
            analysis['rank'] = rank
            analysis['expected_xrefs'] = expected_xrefs
            analysis['expected_size'] = expected_size
            results.append(analysis)
            
            print(f"  Name: {analysis['name']}")
            print(f"  Size: {analysis['size']}B")
            print(f"  Xrefs: {analysis['xrefs']}")
            print(f"  Callers (first 5): {', '.join(analysis['callers'][:5])}")
            print(f"  Callees (first 5): {', '.join(analysis['callees'][:5])}")
            print(f"  Patterns: {analysis['patterns']}")
        else:
            print(f"  ERROR: Could not analyze function at 0x{addr:06X}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\uncategorized_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Analysis complete. Results saved to: {output_file}")
    print(f"Analyzed {len(results)} functions")

if __name__ == '__main__':
    main()
