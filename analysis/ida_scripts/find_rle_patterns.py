"""
Find RLE decompression patterns by looking for specific instruction sequences.
RLE typically uses:
- REP STOSB/STOSW for repeating bytes
- LODSB/LODSW for reading compressed data
- Loops with bit manipulation
- Buffer pointer manipulation
"""
import idaapi
import idc
import idautils
import json

def analyze_function_for_rle(addr):
    """Deep analysis for RLE-specific patterns."""
    patterns = {
        'rep_stosb': 0,
        'rep_stosw': 0,
        'lodsb': 0,
        'lodsw': 0,
        'stosb': 0,
        'stosw': 0,
        'movsb': 0,
        'movsw': 0,
        'read_byte_pattern': 0,  # mov al, [si]; inc si
        'write_byte_pattern': 0,  # mov [di], al; inc di
        'count_loop': 0,  # cx-based loops
        'bit_test': 0,  # test/and for flags
        'shifts': 0,
        'buffer_pointers': set(),  # di, si usage
    }
    
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    ea = func.start_ea
    prev_ea = 0
    prev_mnem = ''
    
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        if not idaapi.decode_insn(insn, ea):
            ea = idc.next_head(ea)
            continue
        
        mnem = idc.print_insn_mnem(ea).lower()
        
        # String operations
        if 'rep' in mnem:
            if 'stosb' in idc.generate_disasm_line(ea, 0).lower():
                patterns['rep_stosb'] += 1
            if 'stosw' in idc.generate_disasm_line(ea, 0).lower():
                patterns['rep_stosw'] += 1
        
        if mnem == 'stosb':
            patterns['stosb'] += 1
        if mnem == 'stosw':
            patterns['stosw'] += 1
        if mnem == 'lodsb':
            patterns['lodsb'] += 1
        if mnem == 'lodsw':
            patterns['lodsw'] += 1
        if mnem in ['movsb', 'movsw']:
            patterns['movsb'] += 1
        
        # Read byte pattern: mov al, [si]; inc si
        if mnem == 'mov':
            op0 = idc.print_operand(ea, 0).lower()
            op1 = idc.print_operand(ea, 1).lower()
            if op0 == 'al' and 'si' in op1:
                patterns['read_byte_pattern'] += 1
            if op0 == 'ax' and 'si' in op1:
                patterns['read_byte_pattern'] += 1
            if 'di' in op0:
                patterns['write_byte_pattern'] += 1
            
            # Track buffer pointers
            if 'di' in op0 or 'di' in op1:
                patterns['buffer_pointers'].add('di')
            if 'si' in op0 or 'si' in op1:
                patterns['buffer_pointers'].add('si')
        
        # Count loops (loop, jcxz, dec cx; jnz)
        if mnem in ['loop', 'jcxz'] or 'cx' in idc.print_operand(ea, 0).lower():
            patterns['count_loop'] += 1
        
        # Bit tests
        if mnem in ['test', 'and'] and prev_mnem in ['mov', 'lodsb', 'lodsw']:
            patterns['bit_test'] += 1
        
        # Shifts
        if mnem in ['shr', 'shl', 'sar', 'sal']:
            patterns['shifts'] += 1
        
        prev_ea = ea
        prev_mnem = mnem
        ea = idc.next_head(ea)
    
    # Convert set to list for JSON
    patterns['buffer_pointers'] = list(patterns['buffer_pointers'])
    
    return patterns

def score_rle_patterns(patterns):
    """Score function based on RLE-specific patterns."""
    score = 0
    
    # REP STOSB is the smoking gun for RLE
    score += patterns['rep_stosb'] * 20
    score += patterns['rep_stosw'] * 15
    
    # Regular STOSB also indicates buffer filling
    score += patterns['stosb'] * 5
    score += patterns['stosw'] * 4
    
    # LODSB for reading compressed data
    score += patterns['lodsb'] * 8
    score += patterns['lodsw'] * 6
    
    # Manual byte patterns
    score += patterns['read_byte_pattern'] * 3
    score += patterns['write_byte_pattern'] * 4
    
    # Count loops
    score += patterns['count_loop'] * 5
    
    # Bit operations
    score += patterns['bit_test'] * 2
    score += patterns['shifts'] * 1
    
    # Both SI and DI used
    if 'si' in patterns['buffer_pointers'] and 'di' in patterns['buffer_pointers']:
        score += 10
    
    return score

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("SEARCHING FOR RLE DECOMPRESSION PATTERNS")
    print("=" * 80)
    print("\nLooking for:")
    print("  - REP STOSB/STOSW (repeat byte/word)")
    print("  - LODSB/LODSW (load byte/word)")
    print("  - SI/DI buffer pointer usage")
    print("  - Count-based loops")
    print("  - Bit testing and shifts")
    
    candidates = []
    
    print("\nScanning all functions...")
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        size = func.end_ea - func.start_ea
        
        # Skip very large or very small functions
        if size < 50 or size > 2000:
            continue
        
        patterns = analyze_function_for_rle(func_ea)
        if not patterns:
            continue
        
        score = score_rle_patterns(patterns)
        
        # Only keep high-scoring candidates
        if score >= 20:
            name = idc.get_func_name(func_ea)
            candidates.append({
                'address': f"0x{func_ea:08X}",
                'name': name,
                'size': size,
                'score': score,
                'patterns': patterns
            })
    
    print(f"\nFound {len(candidates)} candidates with score >= 20")
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Save results
    import os
    output_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'rle_pattern_results.json')
    output = {
        'search_type': 'rle_pattern_matching',
        'total_candidates': len(candidates),
        'candidates': candidates
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    with open('rle_pattern_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print("TOP 30 RLE PATTERN CANDIDATES")
    print("=" * 80)
    print(f"{'#':<3} {'Address':<10} {'Name':<40} {'Score':<6} {'Size':<6} {'Key Patterns'}")
    print("-" * 100)
    
    for i, cand in enumerate(candidates[:30], 1):
        p = cand['patterns']
        key_info = []
        if p['rep_stosb'] > 0:
            key_info.append(f"REP_STOSB:{p['rep_stosb']}")
        if p['rep_stosw'] > 0:
            key_info.append(f"REP_STOSW:{p['rep_stosw']}")
        if p['lodsb'] > 0:
            key_info.append(f"LODSB:{p['lodsb']}")
        if p['stosb'] > 0:
            key_info.append(f"STOSB:{p['stosb']}")
        if p['count_loop'] > 0:
            key_info.append(f"LOOP:{p['count_loop']}")
        
        print(f"{i:<3} 0x{int(cand['address'], 16):06X}   {cand['name']:<40} "
              f"{cand['score']:<6} {cand['size']:<6} {', '.join(key_info)}")
    
    print(f"\nResults saved to rle_pattern_results.json")
    
    # Print detailed info for top 5
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS OF TOP 5 CANDIDATES")
    print("=" * 80)
    
    for i, cand in enumerate(candidates[:5], 1):
        print(f"\n{i}. {cand['name']} @ {cand['address']}")
        print(f"   Score: {cand['score']}, Size: {cand['size']} bytes")
        print(f"   Patterns:")
        p = cand['patterns']
        for key, value in p.items():
            if key == 'buffer_pointers':
                if value:
                    print(f"     {key}: {', '.join(value)}")
            elif value:
                print(f"     {key}: {value}")
    
    print("\nDone!")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
