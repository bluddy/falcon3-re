#!/usr/bin/env python3
"""
Fast mission structure discovery - focused approach.

Look for:
1. Mission type enum usage in R53 segment only
2. Structure multiplication patterns (size indicators)
3. Known structure offsets (66, 130, etc. from our existing structures)
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("FAST MISSION STRUCTURE DISCOVERY")
    print("="*80)
    print()
    
    # Focus on R53 segment
    r53_start = None
    r53_end = None
    
    for seg_ea in idautils.Segments():
        name = idc.get_segm_name(seg_ea)
        if "R53" in name:
            r53_start = seg_ea
            r53_end = idc.get_segm_end(seg_ea)
            print(f"[+] Found R53 segment: 0x{r53_start:X} - 0x{r53_end:X}")
            break
    
    if not r53_start:
        print("[!] R53 segment not found")
        idc.qexit(1)
    
    print()
    
    # Find structure size multiplications in R53
    print("[*] Searching for structure size patterns (imul) in R53...")
    
    structure_sizes = {}
    ea = r53_start
    
    while ea < r53_end:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem == 'imul':
            # Get the multiplier
            op1 = idc.get_operand_value(ea, 1)
            
            # Look for reasonable structure sizes (10-1000 bytes)
            if 10 <= op1 <= 1000:
                if op1 not in structure_sizes:
                    structure_sizes[op1] = []
                
                disasm = idc.generate_disasm_line(ea, 0)
                func_name = idc.get_func_name(ea)
                
                structure_sizes[op1].append({
                    'addr': hex(ea),
                    'function': func_name,
                    'disasm': disasm
                })
        
        ea = idc.next_head(ea, r53_end)
    
    print(f"[+] Found {len(structure_sizes)} distinct structure sizes")
    print()
    
    # Show sizes sorted by occurrence
    print("[*] Structure sizes by frequency:")
    for size in sorted(structure_sizes.keys(), key=lambda x: len(structure_sizes[x]), reverse=True):
        occurrences = structure_sizes[size]
        print(f"    {size:4d} bytes: {len(occurrences):3d} occurrences")
        
        # Show first 3 functions using this size
        if len(occurrences) <= 5:
            for occ in occurrences:
                print(f"           in {occ['function']} at {occ['addr']}")
    
    print()
    
    # Check for known structure sizes
    print("[*] Checking for known structures:")
    known_sizes = {
        66: "PilotRecord",
        60: "SquadronHeader",
        130: "FlightRecord",
        23: "LoadoutRecord",
        28: "MenuElement"
    }
    
    for size, name in known_sizes.items():
        if size in structure_sizes:
            print(f"    ✓ {name} ({size} bytes) - {len(structure_sizes[size])} uses")
        else:
            print(f"    ✗ {name} ({size} bytes) - not found in R53")
    
    print()
    
    # Look for mission-specific sizes (new discoveries)
    print("[*] Potential mission structures (excluding known sizes):")
    
    mission_structures = {}
    for size, occurrences in structure_sizes.items():
        if size not in known_sizes and len(occurrences) >= 2:
            mission_structures[size] = occurrences
            print(f"    {size:4d} bytes: {len(occurrences):3d} uses - CANDIDATE for MissionRecord/Waypoint")
    
    print()
    
    # Check if MissionType enum exists
    print("[*] Checking for MissionType enum...")
    enum_id = idc.get_enum("MissionType")
    
    if enum_id != idc.BADADDR:
        print(f"[+] MissionType enum found (ID: {enum_id})")
        
        # Count members
        member_count = idc.get_enum_size(enum_id)
        print(f"    Members: {member_count}")
        
        # List some members
        print("    Sample values:")
        member_id = idc.get_first_enum_member(enum_id)
        count = 0
        while member_id != idc.BADADDR and count < 10:
            value = idc.get_enum_member_value(member_id)
            name = idc.get_enum_member_name(member_id)
            print(f"      {name} = {value}")
            member_id = idc.get_next_enum_member(enum_id, member_id)
            count += 1
    else:
        print("[!] MissionType enum not found")
    
    print()
    
    # Look for specific patterns in largest R53 function
    print("[*] Analyzing largest R53 function (game_mode_r53_main_coordinator)...")
    
    # Find the function
    coordinator_addr = None
    largest_size = 0
    
    for func_ea in idautils.Functions(r53_start, r53_end):
        func = idaapi.get_func(func_ea)
        if func:
            func_size = func.end_ea - func.start_ea
            if func_size > largest_size:
                largest_size = func_size
                coordinator_addr = func_ea
    
    if coordinator_addr:
        print(f"[+] Found at 0x{coordinator_addr:X}, size: {largest_size} bytes")
        
        # Look for constant comparisons (possible mission types)
        print("[*] Looking for mission type comparisons...")
        
        comparisons = []
        func = idaapi.get_func(coordinator_addr)
        ea = func.start_ea
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == 'cmp':
                op1_val = idc.get_operand_value(ea, 1)
                
                # Look for small constants (0-30 range typical for enums)
                if 0 <= op1_val <= 30:
                    disasm = idc.generate_disasm_line(ea, 0)
                    comparisons.append({
                        'addr': hex(ea),
                        'value': op1_val,
                        'disasm': disasm
                    })
            
            ea = idc.next_head(ea, func.end_ea)
        
        # Count comparison values
        from collections import Counter
        values = [c['value'] for c in comparisons]
        value_counts = Counter(values)
        
        print(f"[+] Found {len(comparisons)} comparisons in coordinator")
        print(f"[*] Most common comparison values:")
        for value, count in value_counts.most_common(10):
            print(f"      {value:2d}: {count:3d} times")
    
    print()
    
    # Save results
    result = {
        'r53_segment': {
            'start': hex(r53_start),
            'end': hex(r53_end),
            'size': r53_end - r53_start
        },
        'structure_sizes': {
            str(size): [
                {
                    'addr': occ['addr'],
                    'function': occ['function']
                }
                for occ in occurrences
            ]
            for size, occurrences in structure_sizes.items()
        },
        'known_structures_found': {
            name: size in structure_sizes
            for size, name in known_sizes.items()
        },
        'mission_structure_candidates': {
            str(size): len(occurrences)
            for size, occurrences in mission_structures.items()
        },
        'mission_type_enum_exists': enum_id != idc.BADADDR if 'enum_id' in locals() else False
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_structures_fast_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("[+] Results saved to analysis/mission_structures_fast_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
