"""
Follow ALL trampolines from operation 0xA until we find the actual RLE code.
Keep unwrapping layers until we reach real implementation.
"""
import idaapi
import idautils
import idc

def disasm_function(addr, name, max_instructions=200):
    """Disassemble function with analysis."""
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        func_end = addr + 500
    
    func_size = func_end - addr
    
    lines = []
    lines.append(f"\n{'=' * 80}")
    lines.append(f"{name} @ 0x{addr:08X} ({func_size}B)")
    lines.append("=" * 80)
    
    ea = addr
    count = 0
    
    # Track interesting patterns
    bit_ops = 0
    buffer_writes = 0
    loops = 0
    calls = 0
    far_calls = 0
    
    while ea < func_end and ea != idc.BADADDR and count < max_instructions:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.generate_disasm_line(ea, 0)
        
        lines.append(f"  0x{ea:08X}: {disasm}")
        
        # Count patterns
        if mnem in ['shl', 'shr', 'rol', 'ror', 'rcl', 'rcr']:
            bit_ops += 1
        elif mnem in ['stosb', 'movsb', 'rep']:
            buffer_writes += 1
        elif 'loop' in mnem:
            loops += 1
        elif mnem in ['call', 'lcall']:
            calls += 1
            if mnem == 'lcall':
                far_calls += 1
        elif mnem == 'mov':
            op0 = idc.print_operand(ea, 0)
            if '[' in op0:
                buffer_writes += 1
        
        ea = idc.next_head(ea)
        count += 1
    
    lines.append(f"\nStatistics:")
    lines.append(f"  Instructions: {count}")
    lines.append(f"  Bit operations: {bit_ops}")
    lines.append(f"  Buffer writes: {buffer_writes}")
    lines.append(f"  Loops: {loops}")
    lines.append(f"  Calls: {calls} (far: {far_calls})")
    
    # Score as potential decompressor
    score = 0
    if bit_ops >= 10:
        score += 5
    elif bit_ops >= 5:
        score += 3
    elif bit_ops >= 1:
        score += 1
    
    if buffer_writes >= 10:
        score += 5
    elif buffer_writes >= 5:
        score += 3
    elif buffer_writes >= 1:
        score += 1
    
    if loops >= 2:
        score += 3
    elif loops >= 1:
        score += 2
    
    if func_size >= 200:
        score += 2
    elif func_size >= 100:
        score += 1
    
    # Penalty for being just a trampoline
    if func_size < 30 and far_calls > 0:
        score = 0
        lines.append(f"  TRAMPOLINE detected (small + far call)")
    
    lines.append(f"  Decompressor score: {score}/16")
    
    return lines, score, func_size, far_calls

def resolve_far_pointer(ptr_addr):
    """Resolve a far pointer (segment:offset) to IDA address."""
    offset = idc.get_wide_word(ptr_addr)
    segment = idc.get_wide_word(ptr_addr + 2)
    
    # Try different segment bases
    candidates = []
    
    # Method 1: Search all IDA segments
    for seg_ea in idautils.Segments():
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        test_addr = seg_start + offset
        if seg_start <= test_addr < seg_end:
            if idc.is_code(idc.get_full_flags(test_addr)):
                func_name = idc.get_func_name(test_addr)
                if func_name:
                    candidates.append((test_addr, func_name, f"seg {idc.get_segm_name(seg_ea)}"))
    
    # Method 2: Real mode linear address
    linear = segment * 16 + offset
    if idc.is_code(idc.get_full_flags(linear)):
        func_name = idc.get_func_name(linear)
        if func_name:
            candidates.append((linear, func_name, "real mode linear"))
    
    return offset, segment, candidates

def main():
    idaapi.auto_wait()
    
    output = []
    output.append("=" * 80)
    output.append("COMPLETE TRAMPOLINE CHAIN ANALYSIS")
    output.append("Following operation 0xA through all layers")
    output.append("=" * 80)
    
    # Start with operation 0xA handler
    current_addr = 0x2063B  # dispatch_220b0_near
    current_name = "dispatch_220b0_near"
    
    chain = []
    max_depth = 10
    
    for depth in range(max_depth):
        output.append(f"\n{'#' * 80}")
        output.append(f"LAYER {depth}: {current_name} @ 0x{current_addr:08X}")
        output.append('#' * 80)
        
        # Disassemble current function
        disasm, score, size, far_calls = disasm_function(current_addr, current_name, max_instructions=300)
        output.extend(disasm)
        
        chain.append({
            'depth': depth,
            'addr': current_addr,
            'name': current_name,
            'size': size,
            'score': score,
            'far_calls': far_calls
        })
        
        # Check if this is the decompressor
        if score >= 10:
            output.append(f"\n*** FOUND LIKELY DECOMPRESSOR! (score {score}/16) ***")
            break
        
        # If this is a trampoline, find where it jumps
        if far_calls > 0 or size < 50:
            output.append(f"\nTRAMPOLINE - searching for next target...")
            
            # Look for FAR CALL or FAR JMP in the disassembly
            # Scan for patterns like: lcall cs:XXXXX or jmp far ptr cs:XXXXX
            ea = current_addr
            func_end = idc.get_func_attr(current_addr, idc.FUNCATTR_END)
            if func_end == idc.BADADDR:
                func_end = current_addr + 100
            
            found_next = False
            
            while ea < func_end and ea != idc.BADADDR:
                mnem = idc.print_insn_mnem(ea)
                
                if mnem in ['lcall', 'call', 'jmp', 'ljmp']:
                    operand = idc.print_operand(ea, 0)
                    
                    # Check if it's an indirect far call via memory
                    if 'cs:' in operand or '[' in operand:
                        output.append(f"  Found indirect reference: {operand}")
                        
                        # Try to extract address from operand
                        # Format examples: "cs:220B0", "cs:[220B0]", "word ptr cs:220B0"
                        import re
                        match = re.search(r'(?:cs:)?(?:\[)?([0-9A-Fa-f]+)', operand)
                        if match:
                            ptr_offset = int(match.group(1), 16)
                            
                            # Calculate pointer address in code segment
                            # Assume code segment starts at 0x20000
                            ptr_addr = 0x20000 + ptr_offset
                            
                            output.append(f"  Pointer at: 0x{ptr_addr:08X}")
                            
                            # Read far pointer
                            offset, segment, candidates = resolve_far_pointer(ptr_addr)
                            
                            output.append(f"  Far pointer: {segment:04X}:{offset:04X}")
                            output.append(f"  Candidates: {len(candidates)}")
                            
                            for target_addr, target_name, method in candidates:
                                output.append(f"    -> 0x{target_addr:08X}: {target_name} ({method})")
                                
                                # Use first valid candidate
                                if not found_next:
                                    current_addr = target_addr
                                    current_name = target_name
                                    found_next = True
                                    output.append(f"  Selecting this target for next layer")
                            
                            if found_next:
                                break
                
                ea = idc.next_head(ea)
            
            if not found_next:
                output.append(f"  Could not find next target - end of chain")
                break
        else:
            output.append(f"\nNot a trampoline (size {size}B) - this might be the implementation")
            break
    
    # Summary
    output.append(f"\n\n{'=' * 80}")
    output.append("TRAMPOLINE CHAIN SUMMARY")
    output.append("=" * 80)
    
    for entry in chain:
        indicator = " *** DECOMPRESSOR ***" if entry['score'] >= 10 else ""
        output.append(f"Layer {entry['depth']}: {entry['name']} @ 0x{entry['addr']:08X} "
                     f"(size={entry['size']}B, score={entry['score']}/16){indicator}")
    
    if chain:
        final = chain[-1]
        output.append(f"\nFinal address: 0x{final['addr']:08X}")
        output.append(f"Final function: {final['name']}")
        
        # Save final address
        with open('rle_decompressor_final.txt', 'w') as f:
            f.write(f"0x{final['addr']:08X}\n")
            f.write(f"{final['name']}\n")
            f.write(f"Chain depth: {len(chain)}\n")
            f.write(f"Score: {final['score']}/16\n")
    
    result = '\n'.join(output)
    print(result)
    
    with open('trampoline_chain_complete.txt', 'w') as f:
        f.write(result)
    
    print(f"\n\nComplete analysis written to trampoline_chain_complete.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
