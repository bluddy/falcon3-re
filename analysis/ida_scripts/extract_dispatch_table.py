"""
Extract dispatch table and disassemble operation handlers.
Focus on operation 0xA (file read) which contains RLE decompression.
"""
import idaapi
import idautils
import idc

def read_dispatch_table(table_addr, max_entries=50):
    """Read dispatch table entries (word pointers)."""
    entries = []
    
    for i in range(max_entries):
        offset = table_addr + i * 2
        ptr = idc.get_wide_word(offset)
        
        if ptr == 0 or ptr == 0xFFFF:
            break
        
        # Get function name at this address
        func_name = idc.get_func_name(ptr)
        if not func_name:
            func_name = f"sub_{ptr:X}"
        
        entries.append((i, ptr, func_name))
    
    return entries

def disasm_function(func_ea, name, max_instructions=500):
    """Disassemble a function with analysis."""
    func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        func_end = func_ea + 1000  # Guess size if not a function
    
    func_size = func_end - func_ea
    
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"Operation Handler: {name} @ 0x{func_ea:X} ({func_size}B)")
    lines.append('=' * 80)
    
    ea = func_ea
    count = 0
    
    # Count interesting instructions
    bit_ops = 0
    buffer_writes = 0
    loops = 0
    calls = 0
    
    while ea < func_end and ea != idc.BADADDR and count < max_instructions:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"  0x{ea:X}: {disasm}")
        
        # Count interesting patterns
        if mnem in ['shl', 'shr', 'rol', 'ror', 'test', 'and', 'or', 'xor']:
            bit_ops += 1
        if mnem in ['mov', 'movsb', 'stosb'] and '[' in idc.print_operand(ea, 0):
            buffer_writes += 1
        if mnem in ['loop', 'loopne', 'loopz']:
            loops += 1
        if mnem in ['call', 'lcall']:
            calls += 1
        
        ea = idc.next_head(ea)
        count += 1
    
    lines.append(f"\nStatistics:")
    lines.append(f"  Instructions: {count}")
    lines.append(f"  Bit operations: {bit_ops}")
    lines.append(f"  Buffer writes: {buffer_writes}")
    lines.append(f"  Loops: {loops}")
    lines.append(f"  Function calls: {calls}")
    
    # Score as potential decompressor
    score = 0
    if bit_ops > 5:
        score += 3
    if buffer_writes > 3:
        score += 3
    if loops > 0:
        score += 2
    if func_size > 100:
        score += 1
    
    lines.append(f"  Decompressor likelihood score: {score}/9")
    
    return lines, score

def main():
    idaapi.auto_wait()
    
    # Find dispatch table address from op_dispatch function
    # The instruction is: call cs:op_dispatch_table[bx]
    # We need to find op_dispatch_table address
    
    dispatch_func = 0x2257B  # op_dispatch
    
    # Search for the table reference
    table_addr = None
    ea = dispatch_func
    for i in range(20):  # Check first 20 instructions
        if idc.print_insn_mnem(ea) == 'call':
            operand = idc.print_operand(ea, 0)
            if 'op_dispatch_table' in operand or 'cs:' in operand:
                # Try to get the address
                for xref in idautils.XrefsFrom(ea, idc.XREF_DATA):
                    table_addr = xref.to
                    break
                if table_addr:
                    break
        ea = idc.next_head(ea)
    
    if not table_addr:
        # Try searching by name
        table_addr = idc.get_name_ea_simple('op_dispatch_table')
    
    if not table_addr or table_addr == idc.BADADDR:
        print("ERROR: Could not find dispatch table address")
        print("Trying common addresses...")
        # Try some common addresses near dispatch function
        for test_addr in [0x22000, 0x22100, 0x22200, 0x22300, 0x22400, 0x22500]:
            name = idc.get_name(test_addr)
            if name and 'dispatch' in name.lower() and 'table' in name.lower():
                table_addr = test_addr
                print(f"Found table at 0x{test_addr:X}: {name}")
                break
    
    output = []
    output.append("=== DISPATCH TABLE ANALYSIS ===\n")
    
    if table_addr and table_addr != idc.BADADDR:
        output.append(f"Dispatch table found at: 0x{table_addr:X}")
        output.append(f"Table name: {idc.get_name(table_addr)}\n")
        
        # Read table entries
        entries = read_dispatch_table(table_addr, max_entries=30)
        
        output.append(f"Found {len(entries)} dispatch table entries:")
        output.append(f"{'Op':<4} {'Address':<10} {'Function Name'}")
        output.append('-' * 60)
        
        for op, addr, name in entries:
            output.append(f"{op:<4} 0x{addr:08X}  {name}")
        
        # Find operation 0xA (file read - likely contains decompression)
        target_ops = [0x6, 0x8, 0xA, 0xE]  # File operations mentioned in doc
        output.append(f"\n\nDisassembling key file I/O operations: {[hex(x) for x in target_ops]}")
        
        handlers_to_disasm = []
        for op, addr, name in entries:
            if op in target_ops or op == 10:  # 0xA = 10 decimal
                handlers_to_disasm.append((op, addr, name))
        
        # Disassemble handlers
        scored = []
        for op, addr, name in handlers_to_disasm:
            op_output, score = disasm_function(addr, f"Op {op:#x} - {name}", max_instructions=500)
            output.extend(op_output)
            scored.append((op, score, name))
        
        # Summary
        output.append(f"\n\n{'='*80}")
        output.append("DECOMPRESSOR LIKELIHOOD RANKING:")
        output.append('=' * 80)
        for op, score, name in sorted(scored, key=lambda x: x[1], reverse=True):
            output.append(f"  Op {op:#x} ({name}): {score}/9")
        
    else:
        output.append("ERROR: Could not locate dispatch table")
        output.append("Manual search required in IDA")
    
    result = '\n'.join(output)
    print(result)
    
    # Write output
    with open('dispatch_table_analysis.txt', 'w') as f:
        f.write(result)
    
    print(f"\nOutput written to dispatch_table_analysis.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
