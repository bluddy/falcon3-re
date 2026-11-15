"""
Search for decompression functions beyond the RLE one we found
"""
import idaapi
import idautils
import idc
import json

def find_decompressor_patterns():
    """Look for common decompression patterns"""
    results = []
    
    # Pattern 1: Functions with loops that read byte by byte and output more bytes
    # Pattern 2: Functions with bit manipulation (for Huffman, LZW, etc.)
    # Pattern 3: Functions that use LODSB/STOSB heavily
    
    print("Searching for decompression candidates...")
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        func_size = func.end_ea - func.start_ea
        
        # Skip tiny functions
        if func_size < 50:
            continue
        
        # Count specific instructions
        lodsb_count = 0
        stosb_count = 0
        shl_shr_count = 0
        loop_count = 0
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ['lodsb', 'lodsw', 'lodsd']:
                lodsb_count += 1
            elif mnem in ['stosb', 'stosw', 'stosd']:
                stosb_count += 1
            elif mnem in ['shl', 'shr', 'rol', 'ror']:
                shl_shr_count += 1
            elif mnem in ['loop', 'loope', 'loopne']:
                loop_count += 1
            
            ea = idc.next_head(ea, func.end_ea)
        
        # Score function as potential decompressor
        score = 0
        if lodsb_count >= 3:
            score += lodsb_count
        if stosb_count >= 3:
            score += stosb_count
        if shl_shr_count >= 5:
            score += shl_shr_count // 2
        if loop_count >= 2:
            score += loop_count * 2
        
        if score >= 8:
            results.append({
                'address': func_ea,
                'hex_addr': f'0x{func_ea:X}',
                'name': func_name,
                'size': func_size,
                'lodsb': lodsb_count,
                'stosb': stosb_count,
                'shifts': shl_shr_count,
                'loops': loop_count,
                'score': score
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

def main():
    print("="*60)
    print("Searching for decompression functions...")
    print("="*60)
    
    candidates = find_decompressor_patterns()
    
    print(f"\nFound {len(candidates)} candidate decompression functions")
    print("\nTop 20 candidates:")
    print("-"*60)
    
    for i, func in enumerate(candidates[:20]):
        print(f"{i+1:2d}. 0x{func['address']:06X} {func['name']:30s} "
              f"score={func['score']:2d} "
              f"(lods={func['lodsb']}, stos={func['stosb']}, "
              f"shift={func['shifts']}, loop={func['loops']})")
    
    # Save results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\decompressor_candidates.json'
    with open(output_path, 'w') as f:
        json.dump(candidates[:50], f, indent=2)
    
    print(f"\nTop 50 candidates saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
