"""
Search for RLE decompressor by looking for specific bytecode patterns.
REP STOSB bytecode is F3 AA or F3 AB (REP STOSW).
"""
import idc
import idaapi
import idautils
import json

def search_bytecode_pattern(pattern_bytes):
    """Search for bytecode pattern in all segments."""
    results = []
    
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if not seg:
            continue
        
        # Search in this segment
        ea = seg.start_ea
        while ea < seg.end_ea:
            # Try to match pattern
            match = True
            for i, byte_val in enumerate(pattern_bytes):
                if idc.get_wide_byte(ea + i) != byte_val:
                    match = False
                    break
            
            if match:
                # Found a match - get the function containing this address
                func_ea = idc.get_func_attr(ea, idc.FUNCATTR_START)
                if func_ea != idc.BADADDR:
                    results.append({
                        'address': hex(ea),
                        'func_address': hex(func_ea),
                        'func_name': idc.get_func_name(func_ea),
                        'segment': idc.get_segm_name(ea)
                    })
            
            ea += 1
    
    return results

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("SEARCHING FOR RLE BYTECODE PATTERNS")
    print("=" * 80)
    
    # Pattern 1: REP STOSB (F3 AA)
    print("\nSearching for REP STOSB (F3 AA)...")
    rep_stosb = search_bytecode_pattern([0xF3, 0xAA])
    print(f"Found {len(rep_stosb)} instances")
    
    # Pattern 2: REP STOSW (F3 AB)
    print("\nSearching for REP STOSW (F3 AB)...")
    rep_stosw = search_bytecode_pattern([0xF3, 0xAB])
    print(f"Found {len(rep_stosw)} instances")
    
    # Pattern 3: REP MOVSB (F3 A4)
    print("\nSearching for REP MOVSB (F3 A4)...")
    rep_movsb = search_bytecode_pattern([0xF3, 0xA4])
    print(f"Found {len(rep_movsb)} instances")
    
    # Pattern 4: REP MOVSW (F3 A5)
    print("\nSearching for REP MOVSW (F3 A5)...")
    rep_movsw = search_bytecode_pattern([0xF3, 0xA5])
    print(f"Found {len(rep_movsw)} instances")
    
    # Pattern 5: LODSB (AC)
    print("\nSearching for LODSB (AC)...")
    lodsb = search_bytecode_pattern([0xAC])
    print(f"Found {len(lodsb)} instances (first 50 only)")
    
    # Combine all results
    results = {
        'rep_stosb': rep_stosb,
        'rep_stosw': rep_stosw,
        'rep_movsb': rep_movsb,
        'rep_movsw': rep_movsw,
        'lodsb': lodsb[:50]  # Limit LODSB to first 50
    }
    
    # Get unique functions
    unique_funcs = set()
    for pattern_name, matches in results.items():
        for match in matches:
            if 'func_address' in match:
                unique_funcs.add((match['func_address'], match['func_name']))
    
    print(f"\n{len(unique_funcs)} unique functions contain these patterns")
    
    # Save results
    import os
    output_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'rle_bytecode_search.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"REP STOSB functions: {len(set(m['func_name'] for m in rep_stosb))}")
    print(f"REP STOSW functions: {len(set(m['func_name'] for m in rep_stosw))}")
    print(f"REP MOVSB functions: {len(set(m['func_name'] for m in rep_movsb))}")
    print(f"REP MOVSW functions: {len(set(m['func_name'] for m in rep_movsw))}")
    
    # Show functions with REP STOSB/STOSW (most likely to be RLE)
    if rep_stosb or rep_stosw:
        print("\n" + "=" * 80)
        print("FUNCTIONS WITH REP STOS (MOST LIKELY RLE CANDIDATES)")
        print("=" * 80)
        
        stos_funcs = set()
        for m in rep_stosb:
            stos_funcs.add((m['func_address'], m['func_name']))
        for m in rep_stosw:
            stos_funcs.add((m['func_address'], m['func_name']))
        
        for addr, name in sorted(stos_funcs):
            print(f"  {addr}: {name}")
    
    print("\nDone!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
