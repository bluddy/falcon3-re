"""
Disassemble op_dispatch_far_entry and analyze operation handlers.
Focus on operation 0xA (file read) which likely contains decompression.
"""
import idaapi
import idautils
import idc

def disasm_function(func_ea, max_instructions=500):
    """Disassemble a function completely."""
    func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
    
    lines = []
    ea = func_ea
    count = 0
    
    while ea < func_end and ea != idc.BADADDR and count < max_instructions:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"0x{ea:X}:  {disasm}")
        ea = idc.next_head(ea)
        count += 1
    
    return lines

def analyze_switch_table(func_ea):
    """Try to find switch/dispatch table in function."""
    func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
    
    tables = []
    ea = func_ea
    
    while ea < func_end and ea != idc.BADADDR:
        # Look for: cmp reg, immediate (checking operation code)
        if idc.print_insn_mnem(ea) == 'cmp':
            operand = idc.print_operand(ea, 1)
            if operand.isdigit() or operand.startswith('0x'):
                tables.append(f"Found comparison at 0x{ea:X}: {idc.generate_disasm_line(ea, 0)}")
        
        # Look for: jmp [table + offset] patterns
        if idc.print_insn_mnem(ea) in ['jmp', 'ljmp']:
            operand = idc.print_operand(ea, 0)
            if '[' in operand:  # Indirect jump
                tables.append(f"Found indirect jump at 0x{ea:X}: {idc.generate_disasm_line(ea, 0)}")
        
        ea = idc.next_head(ea)
    
    return tables

def find_xrefs_from(func_ea, max_xrefs=50):
    """Find functions called FROM this function."""
    callees = []
    
    for xref in idautils.XrefsFrom(func_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:  # Call near/far
            target_name = idc.get_func_name(xref.to)
            if target_name:
                callees.append((xref.frm, xref.to, target_name))
                if len(callees) >= max_xrefs:
                    break
    
    return callees

def main():
    idaapi.auto_wait()
    
    dispatch_addr = 0x2257B  # op_dispatch (the actual dispatcher!)
    dispatch_name = idc.get_func_name(dispatch_addr)
    
    if not dispatch_name:
        print(f"ERROR: No function found at 0x{dispatch_addr:X}")
        idc.qexit(1)
        return
    
    func_size = idc.get_func_attr(dispatch_addr, idc.FUNCATTR_END) - dispatch_addr
    
    output = []
    output.append(f"=== {dispatch_name} @ 0x{dispatch_addr:X} ({func_size}B) ===\n")
    
    # Disassemble function
    output.append("DISASSEMBLY:")
    output.append("=" * 80)
    disasm = disasm_function(dispatch_addr, max_instructions=1000)
    output.extend(disasm)
    output.append("\n" + "=" * 80)
    
    # Analyze switch/dispatch table
    output.append("\nSWITCH/DISPATCH TABLE ANALYSIS:")
    output.append("=" * 80)
    tables = analyze_switch_table(dispatch_addr)
    if tables:
        output.extend(tables)
    else:
        output.append("No switch table patterns found")
    output.append("")
    
    # Find callees
    output.append("\nFUNCTIONS CALLED FROM DISPATCH:")
    output.append("=" * 80)
    callees = find_xrefs_from(dispatch_addr, max_xrefs=100)
    if callees:
        # Group by target
        from collections import defaultdict
        by_target = defaultdict(list)
        for frm, to, name in callees:
            by_target[(to, name)].append(frm)
        
        output.append(f"Found {len(by_target)} unique callees:")
        for (to, name), call_sites in sorted(by_target.items()):
            output.append(f"  {name} @ 0x{to:X} (called {len(call_sites)} times)")
            if len(call_sites) <= 5:
                for site in call_sites:
                    output.append(f"    from 0x{site:X}")
    else:
        output.append("No function calls found")
    
    result = '\n'.join(output)
    print(result)
    
    # Write output
    with open('disasm_dispatch.txt', 'w') as f:
        f.write(result)
    
    print(f"\nWrote {len(disasm)} instructions to disasm_dispatch.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
