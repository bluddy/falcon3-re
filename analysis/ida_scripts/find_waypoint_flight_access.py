"""
Find code that accesses waypoint (21-byte) and flight (130-byte) structures
Focus on multiplication patterns that indicate array indexing
"""

import idaapi
import idc
import idautils
import json

def find_structure_access_patterns():
    """Find array access patterns for known structures"""
    
    print("Searching for structure access patterns...")
    print("=" * 80)
    
    # Patterns to find:
    # 1. Waypoint access: imul with 0x15 (21 bytes)
    # 2. Flight access: imul with 0x82 (130 bytes)
    # 3. MissionSlot access: imul with 0x14 (20 bytes) - already known
    # 4. PilotRecord access: imul with 0x42 (66 bytes) - already known
    
    patterns = {
        'waypoint_21': 0x15,
        'flight_130': 0x82,
        'mission_slot_20': 0x14,
        'pilot_66': 0x42,
        'loadout_23': 0x17
    }
    
    results = {}
    
    for pattern_name, size_value in patterns.items():
        print(f"\nSearching for {pattern_name} (size=0x{size_value:02X}, {size_value} bytes)...")
        
        matches = []
        
        # Search entire code for "mov dx, SIZE" followed by "imul"
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            func_name = idc.get_func_name(func_ea)
            
            # Skip if not in R5X or mission-related areas
            # (Comment out to search everywhere)
            # if not ('R5' in func_name or 'mission' in func_name.lower() or 'flight' in func_name.lower()):
            #     continue
            
            ea = func.start_ea
            while ea < func.end_ea:
                # Look for: mov dx, SIZE
                if idc.print_insn_mnem(ea) == 'mov':
                    op0 = idc.print_operand(ea, 0)
                    op1 = idc.print_operand(ea, 1)
                    
                    if op0 == 'dx':
                        # Check if immediate value matches our size
                        if idc.get_operand_type(ea, 1) == idc.o_imm:
                            imm_value = idc.get_operand_value(ea, 1)
                            
                            if imm_value == size_value:
                                # Found "mov dx, SIZE"
                                # Check next few instructions for imul
                                next_ea = idc.next_head(ea, func.end_ea)
                                search_limit = 5
                                found_imul = False
                                
                                for _ in range(search_limit):
                                    if next_ea >= func.end_ea:
                                        break
                                    
                                    next_mnem = idc.print_insn_mnem(next_ea)
                                    if next_mnem == 'imul':
                                        found_imul = True
                                        
                                        # Get segment name
                                        seg = idaapi.getseg(ea)
                                        seg_name = idc.get_segm_name(seg.start_ea) if seg else "Unknown"
                                        
                                        matches.append({
                                            'addr': ea,
                                            'func': func_name,
                                            'func_addr': func_ea,
                                            'segment': seg_name,
                                            'mov_disasm': idc.GetDisasm(ea),
                                            'imul_disasm': idc.GetDisasm(next_ea),
                                            'imul_addr': next_ea
                                        })
                                        break
                                    
                                    next_ea = idc.next_head(next_ea, func.end_ea)
                
                ea = idc.next_head(ea, func.end_ea)
        
        results[pattern_name] = matches
        print(f"  Found {len(matches)} instances")
        
        if matches:
            # Show top 10
            for match in matches[:10]:
                print(f"    {match['func']} @ 0x{match['addr']:06X} in {match['segment']}")
                print(f"      {match['mov_disasm']}")
                print(f"      {match['imul_disasm']}")
    
    return results

def find_coordinate_access_patterns():
    """Find code that reads waypoint coordinates at specific offsets"""
    
    print("\n\n" + "=" * 80)
    print("Searching for waypoint coordinate access patterns...")
    print("=" * 80)
    
    # Waypoint structure:
    # +0x01-0x02: X coordinate (x_low, x_high)
    # +0x05-0x06: Y coordinate (y_low, y_high)
    
    # Look for patterns like:
    # mov al, [bx+1]   ; x_low
    # mov ah, [bx+2]   ; x_high
    # mov al, [bx+5]   ; y_low
    # mov ah, [bx+6]   ; y_high
    
    coordinate_offsets = [1, 2, 5, 6]
    results = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == 'mov':
                disasm = idc.GetDisasm(ea)
                
                # Look for [bx+offset] patterns
                for offset in coordinate_offsets:
                    if f'[bx+{offset}]' in disasm or f'[bx+{offset:X}h]' in disasm:
                        seg = idaapi.getseg(ea)
                        seg_name = idc.get_segm_name(seg.start_ea) if seg else "Unknown"
                        
                        results.append({
                            'addr': ea,
                            'func': func_name,
                            'func_addr': func_ea,
                            'segment': seg_name,
                            'offset': offset,
                            'disasm': disasm
                        })
            
            ea = idc.next_head(ea, func.end_ea)
    
    print(f"\nFound {len(results)} coordinate access patterns")
    
    # Group by function
    by_func = {}
    for r in results:
        if r['func'] not in by_func:
            by_func[r['func']] = []
        by_func[r['func']].append(r)
    
    # Show functions with multiple coordinate accesses (likely waypoint processors)
    print("\nFunctions with coordinate accesses:")
    for func_name, accesses in sorted(by_func.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
        if len(accesses) >= 2:  # At least 2 coordinate accesses
            print(f"  {func_name}: {len(accesses)} accesses")
            
            # Show what offsets
            offsets = set(a['offset'] for a in accesses)
            print(f"    Offsets: {sorted(offsets)}")
            
            # Show segment
            segs = set(a['segment'] for a in accesses)
            print(f"    Segments: {', '.join(segs)}")
    
    return results

def main():
    print("Starting waypoint and flight structure search...")
    idaapi.auto_wait()
    
    # Find structure access patterns
    struct_results = find_structure_access_patterns()
    
    # Find coordinate access
    coord_results = find_coordinate_access_patterns()
    
    # Combine results
    output = {
        'structure_patterns': struct_results,
        'coordinate_patterns': coord_results
    }
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for pattern_name, matches in struct_results.items():
        print(f"{pattern_name}: {len(matches)} instances")
        
        if matches:
            # Group by segment
            by_seg = {}
            for m in matches:
                seg = m['segment']
                if seg not in by_seg:
                    by_seg[seg] = 0
                by_seg[seg] += 1
            
            print(f"  Segments: {dict(by_seg)}")
    
    print(f"\nCoordinate access patterns: {len(coord_results)} total")
    
    # Save results
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\waypoint_flight_access.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults written to {output_path}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
