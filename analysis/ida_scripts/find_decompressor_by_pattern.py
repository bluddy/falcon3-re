"""
Find RLE decompressor by searching for characteristic patterns:
- High bit manipulation (SHL, SHR, ROR, ROL)
- Buffer writes (STOSB, MOVSB, MOV [dest])
- Loops
- Medium size (50-500 bytes)
"""
import idaapi
import idautils
import idc

def analyze_function_pattern(func_addr):
    """Analyze function for decompressor patterns."""
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    if func_end == idc.BADADDR:
        return None
    
    func_size = func_end - func_addr
    
    if func_size < 50 or func_size > 2000:
        return None  # Skip too small or too large
    
    ea = func_addr
    count = 0
    
    bit_ops = 0
    buffer_writes = 0
    loops = 0
    calls = 0
    
    while ea < func_end and ea != idc.BADADDR and count < 1000:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ['shl', 'shr', 'rol', 'ror', 'rcl', 'rcr', 'sal', 'sar']:
            bit_ops += 1
        elif mnem in ['stosb', 'movsb', 'rep']:
            buffer_writes += 1
        elif mnem == 'loop' or 'loop' in mnem:
            loops += 1
        elif mnem in ['call', 'lcall']:
            calls += 1
        elif mnem == 'mov':
            op0 = idc.print_operand(ea, 0)
            if '[' in op0 and 'sp' not in op0.lower() and 'bp' not in op0.lower():
                buffer_writes += 1
        
        ea = idc.next_head(ea)
        count += 1
    
    # Calculate score
    score = 0
    if bit_ops >= 20:
        score += 10
    elif bit_ops >= 10:
        score += 6
    elif bit_ops >= 5:
        score += 3
    
    if buffer_writes >= 20:
        score += 10
    elif buffer_writes >= 10:
        score += 6
    elif buffer_writes >= 5:
        score += 3
    
    if loops >= 2:
        score += 5
    elif loops >= 1:
        score += 3
    
    if 100 <= func_size <= 500:
        score += 3
    
    # Penalty for too many calls (decompressors are usually self-contained)
    if calls > 10:
        score -= 5
    
    return {
        'addr': func_addr,
        'size': func_size,
        'instructions': count,
        'bit_ops': bit_ops,
        'buffer_writes': buffer_writes,
        'loops': loops,
        'calls': calls,
        'score': score
    }

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("SEARCHING FOR RLE DECOMPRESSOR BY CODE PATTERNS")
    print("=" * 80)
    print()
    print("Analyzing all functions for decompressor characteristics...")
    print()
    
    candidates = []
    
    # Scan all functions
    for func_addr in idautils.Functions():
        result = analyze_function_pattern(func_addr)
        if result and result['score'] >= 10:
            func_name = idc.get_func_name(func_addr)
            result['name'] = func_name
            candidates.append(result)
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"Found {len(candidates)} candidates with score >= 10")
    print()
    print(f"{'Rank':<6} {'Score':<7} {'Addr':<12} {'Size':<6} {'BitOps':<8} {'BufWr':<7} {'Loops':<7} {'Calls':<7} {'Function Name'}")
    print("-" * 120)
    
    for i, cand in enumerate(candidates[:30], 1):  # Top 30
        print(f"{i:<6} {cand['score']:<7} 0x{cand['addr']:08X}  {cand['size']:<6} {cand['bit_ops']:<8} {cand['buffer_writes']:<7} {cand['loops']:<7} {cand['calls']:<7} {cand['name']}")
    
    if candidates:
        print()
        print("=" * 80)
        print("TOP 5 CANDIDATES - DETAILED ANALYSIS")
        print("=" * 80)
        
        for i, cand in enumerate(candidates[:5], 1):
            print(f"\n{i}. {cand['name']} @ 0x{cand['addr']:08X}")
            print(f"   Score: {cand['score']}/30+")
            print(f"   Size: {cand['size']} bytes")
            print(f"   Bit operations: {cand['bit_ops']}")
            print(f"   Buffer writes: {cand['buffer_writes']}")
            print(f"   Loops: {cand['loops']}")
            print(f"   Function calls: {cand['calls']}")
            
            # Disassemble first 50 instructions
            print(f"   First 50 instructions:")
            ea = cand['addr']
            func_end = idc.get_func_attr(cand['addr'], idc.FUNCATTR_END)
            count = 0
            
            while ea < func_end and ea != idc.BADADDR and count < 50:
                disasm = idc.generate_disasm_line(ea, 0)
                mnem = idc.print_insn_mnem(ea)
                
                # Highlight interesting instructions
                marker = ""
                if mnem in ['shl', 'shr', 'rol', 'ror']:
                    marker = "  ; BIT"
                elif mnem in ['stosb', 'movsb', 'loop']:
                    marker = "  ; ***"
                
                print(f"     0x{ea:08X}: {disasm}{marker}")
                ea = idc.next_head(ea)
                count += 1
        
        # Save top candidate
        if candidates:
            top = candidates[0]
            with open('decompressor_top_candidate.txt', 'w') as f:
                f.write(f"Address: 0x{top['addr']:08X}\n")
                f.write(f"Function: {top['name']}\n")
                f.write(f"Score: {top['score']}\n")
                f.write(f"Size: {top['size']} bytes\n")
                f.write(f"Bit operations: {top['bit_ops']}\n")
                f.write(f"Buffer writes: {top['buffer_writes']}\n")
                f.write(f"Loops: {top['loops']}\n")
    else:
        print("\nNo strong candidates found!")
        print("RLE decompressor might be inlined or use different patterns")
    
    # Write full results
    with open('decompressor_candidates_all.txt', 'w') as f:
        f.write("RLE Decompressor Search Results\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total candidates: {len(candidates)}\n\n")
        
        for i, cand in enumerate(candidates, 1):
            f.write(f"{i}. {cand['name']} @ 0x{cand['addr']:08X}\n")
            f.write(f"   Score: {cand['score']}, Size: {cand['size']}B, ")
            f.write(f"BitOps: {cand['bit_ops']}, BufWr: {cand['buffer_writes']}, ")
            f.write(f"Loops: {cand['loops']}, Calls: {cand['calls']}\n\n")
    
    print(f"\n\nComplete results written to decompressor_candidates_all.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
