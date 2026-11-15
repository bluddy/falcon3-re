"""
Disassemble operation 0xA handler (file read + RLE decompression).
This is where the magic happens!
"""
import idaapi
import idautils
import idc

def disasm_function_detailed(func_ea, name, max_instructions=1000):
    """Disassemble function with detailed analysis."""
    func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        # Not a recognized function, guess size
        func_end = func_ea + 2000
    
    func_size = func_end - func_ea
    
    lines = []
    lines.append("=" * 80)
    lines.append(f"{name} @ 0x{func_ea:X} ({func_size}B)")
    lines.append("=" * 80)
    lines.append("")
    
    # Statistics
    bit_ops = []
    buffer_writes = []
    loops = []
    calls = []
    jumps = []
    
    ea = func_ea
    count = 0
    
    while ea < func_end and ea != idc.BADADDR and count < max_instructions:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Annotate interesting instructions
        annotation = ""
        
        if mnem in ['shl', 'shr', 'rol', 'ror']:
            bit_ops.append(ea)
            annotation = "  ; BIT SHIFT"
        elif mnem in ['test', 'and', 'or', 'xor'] and mnem != 'test':
            bit_ops.append(ea)
            annotation = "  ; BIT OPERATION"
        elif mnem in ['mov', 'movsb', 'stosb', 'rep']:
            op0 = idc.print_operand(ea, 0)
            if '[' in op0 or mnem in ['movsb', 'stosb', 'rep']:
                buffer_writes.append(ea)
                annotation = "  ; BUFFER WRITE"
        elif mnem in ['loop', 'loopne', 'loopz', 'loope']:
            loops.append(ea)
            annotation = "  ; LOOP"
        elif mnem in ['call', 'lcall']:
            calls.append(ea)
            # Get call target
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    target_name = idc.get_func_name(xref.to)
                    if target_name:
                        annotation = f"  ; CALL {target_name}"
                    break
        elif mnem in ['jmp', 'ljmp', 'jz', 'jnz', 'jb', 'jnb', 'ja', 'jna', 
                      'jbe', 'jnbe', 'je', 'jne', 'jl', 'jnl', 'jle', 'jge',
                      'js', 'jns', 'jo', 'jno', 'jc', 'jnc']:
            jumps.append(ea)
            if mnem != 'jmp':
                annotation = "  ; CONDITIONAL"
        
        lines.append(f"0x{ea:06X}:  {disasm}{annotation}")
        
        ea = idc.next_head(ea)
        count += 1
    
    # Summary statistics
    lines.append("")
    lines.append("=" * 80)
    lines.append("STATISTICS")
    lines.append("=" * 80)
    lines.append(f"Total instructions: {count}")
    lines.append(f"Bit operations: {len(bit_ops)}")
    lines.append(f"Buffer writes: {len(buffer_writes)}")
    lines.append(f"Loops: {len(loops)}")
    lines.append(f"Function calls: {len(calls)}")
    lines.append(f"Jumps: {len(jumps)}")
    
    # Score as decompressor
    score = 0
    if len(bit_ops) > 10:
        score += 5
    elif len(bit_ops) > 5:
        score += 3
    elif len(bit_ops) > 0:
        score += 1
    
    if len(buffer_writes) > 10:
        score += 4
    elif len(buffer_writes) > 5:
        score += 2
    elif len(buffer_writes) > 0:
        score += 1
    
    if len(loops) > 0:
        score += 3
    
    if func_size > 200:
        score += 2
    elif func_size > 100:
        score += 1
    
    lines.append(f"\nDecompressor likelihood: {score}/15")
    if score >= 10:
        lines.append("*** HIGH PROBABILITY - This is likely the RLE decompressor! ***")
    elif score >= 6:
        lines.append("*** MEDIUM PROBABILITY - Possible decompressor or helper ***")
    else:
        lines.append("Low probability - may be simple file read wrapper")
    
    # Analyze bit operation patterns
    if bit_ops:
        lines.append("\n" + "=" * 80)
        lines.append("BIT OPERATION DETAIL")
        lines.append("=" * 80)
        lines.append("Bit operations suggest bit-stream parsing (variable-length encoding):")
        for addr in bit_ops[:20]:  # First 20
            disasm = idc.generate_disasm_line(addr, 0)
            lines.append(f"  0x{addr:06X}: {disasm}")
    
    return lines, score

def analyze_callees(func_ea, name):
    """Analyze functions called from this function."""
    lines = []
    lines.append("\n" + "=" * 80)
    lines.append(f"FUNCTIONS CALLED FROM {name}")
    lines.append("=" * 80)
    
    callees = {}
    for xref in idautils.XrefsFrom(func_ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            target = xref.to
            target_name = idc.get_func_name(target)
            if target_name:
                if target_name not in callees:
                    callees[target_name] = []
                callees[target_name].append(xref.frm)
    
    if callees:
        for callee_name in sorted(callees.keys()):
            call_sites = callees[callee_name]
            lines.append(f"\n{callee_name} (called {len(call_sites)} times)")
            for site in call_sites[:5]:  # First 5 call sites
                lines.append(f"  from 0x{site:06X}")
    else:
        lines.append("No function calls (leaf function - good sign for low-level decompressor!)")
    
    return lines

def main():
    idaapi.auto_wait()
    
    # Read the op_0xa address
    with open('op_0xa_handler.txt', 'r') as f:
        addr_str = f.read().strip()
    
    op_a_addr = int(addr_str, 16)
    
    print("=" * 80)
    print("OPERATION 0xA HANDLER ANALYSIS")
    print("File Read + RLE Decompression")
    print("=" * 80)
    print(f"\nHandler address: 0x{op_a_addr:X}")
    
    # Disassemble
    disasm, score = disasm_function_detailed(op_a_addr, "Operation 0xA Handler", max_instructions=1000)
    
    # Analyze callees
    callees = analyze_callees(op_a_addr, "op_0xa")
    
    # Combine output
    output = disasm + callees
    
    for line in output:
        print(line)
    
    # Write to file
    with open('op_0xa_disassembly.txt', 'w') as f:
        f.write('\n'.join(output))
    
    print("\n" + "=" * 80)
    print(f"Complete disassembly written to op_0xa_disassembly.txt")
    print("=" * 80)
    
    # If high score, mark it in IDA
    if score >= 10:
        idc.set_name(op_a_addr, "op_0xa_file_read_with_rle_decompress", idc.SN_NOWARN)
        comment = """*** OPERATION 0xA: FILE READ WITH RLE DECOMPRESSION ***

This handler reads files AND decompresses them if they're .DAT graphics files.

Format: [magic 0x0400][width 2B][height 2B][RLE compressed pixels]
Compression: Bit-packed variable-length RLE (0.34%-2% ratio, ~50:1 to 300:1)

High bit operation count suggests bit-stream parsing.
This is the function we've been looking for!"""
        idc.set_func_cmt(op_a_addr, comment, 0)
        print("\nMarked function in IDA as RLE decompressor!")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
