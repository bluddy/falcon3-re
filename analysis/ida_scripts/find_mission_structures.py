#!/usr/bin/env python3
"""
Find mission data structures by searching for mission type usage.

Strategy:
1. Find mission type strings (CAP, STRIKE, CAS, SEAD, etc.)
2. Trace xrefs to find comparison/switch statements
3. Identify structure access patterns around mission types
4. Find structure sizes via multiplication patterns
"""

import idc
import idaapi
import idautils
import json
import re

def find_string_address(search_string):
    """Find a string in the database."""
    for seg_ea in idautils.Segments():
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            str_type = idc.get_str_type(ea)
            if str_type is not None:
                string_val = idc.get_strlit_contents(ea)
                if string_val and search_string.encode() in string_val:
                    return ea, string_val.decode('ascii', errors='ignore')
            ea = idc.next_head(ea, seg_end)
    
    return None, None

def analyze_xrefs_for_structure(string_addr, string_name):
    """Analyze xrefs to a string to find structure usage."""
    results = []
    
    for xref in idautils.XrefsTo(string_addr):
        func_addr = xref.frm
        func_name = idc.get_func_name(func_addr)
        
        if not func_name:
            continue
        
        # Get function
        func = idaapi.get_func(func_addr)
        if not func:
            continue
        
        # Look for structure access patterns near the xref
        # Common patterns:
        # - mov ax, [bx + offset] (field access)
        # - imul dx, SIZE (array indexing)
        # - cmp [bx + offset], value (field comparison)
        
        patterns = []
        
        # Scan 20 instructions before and after the xref
        ea = max(func.start_ea, func_addr - 100)
        end_ea = min(func.end_ea, func_addr + 100)
        
        while ea < end_ea:
            mnem = idc.print_insn_mnem(ea)
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for imul with constants (structure size)
            if mnem == 'imul':
                op1 = idc.get_operand_value(ea, 1)
                if 10 < op1 < 500:  # Reasonable structure size
                    patterns.append({
                        'addr': hex(ea),
                        'type': 'structure_size',
                        'size': op1,
                        'disasm': disasm
                    })
            
            # Look for add/mov with offsets
            elif mnem in ['add', 'mov', 'cmp', 'lea']:
                # Check for offset patterns like [bx+N]
                if '+' in disasm and ('h' in disasm or 'offset' in disasm):
                    patterns.append({
                        'addr': hex(ea),
                        'type': 'field_access',
                        'disasm': disasm
                    })
            
            ea = idc.next_head(ea, end_ea)
        
        if patterns:
            results.append({
                'function': func_name,
                'func_addr': hex(func.start_ea),
                'xref_addr': hex(func_addr),
                'string': string_name,
                'patterns': patterns[:10]  # First 10 patterns
            })
    
    return results

def find_enum_usage(enum_name):
    """Find where an enum is used in comparisons."""
    # Look for enum ID
    enum_id = idc.get_enum(enum_name)
    if enum_id == idc.BADADDR:
        return []
    
    results = []
    
    # Get enum members
    members = []
    member_id = idc.get_first_enum_member(enum_id)
    while member_id != idc.BADADDR:
        value = idc.get_enum_member_value(member_id)
        name = idc.get_enum_member_name(member_id)
        members.append({'name': name, 'value': value})
        member_id = idc.get_next_enum_member(enum_id, member_id)
    
    print(f"[*] Enum {enum_name} has {len(members)} members")
    
    # Search for comparisons with these values
    for seg_ea in idautils.Segments():
        for func_ea in idautils.Functions(seg_ea, idc.get_segm_end(seg_ea)):
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            ea = func.start_ea
            while ea < func.end_ea:
                mnem = idc.print_insn_mnem(ea)
                
                if mnem == 'cmp':
                    # Get comparison value
                    op1_val = idc.get_operand_value(ea, 1)
                    
                    # Check if it matches any enum value
                    for member in members:
                        if op1_val == member['value']:
                            disasm = idc.generate_disasm_line(ea, 0)
                            results.append({
                                'addr': hex(ea),
                                'function': idc.get_func_name(func_ea),
                                'enum_member': member['name'],
                                'value': member['value'],
                                'disasm': disasm
                            })
                            break
                
                ea = idc.next_head(ea, func.end_ea)
    
    return results

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("MISSION STRUCTURE DISCOVERY")
    print("="*80)
    print()
    
    # Strategy 1: Find mission type strings and trace usage
    print("[*] Strategy 1: Trace mission type strings...")
    print()
    
    mission_strings = ['CAP', 'STRIKE', 'CAS', 'SEAD', 'ESCORT', 'RECON']
    
    mission_string_analysis = {}
    
    for mission_type in mission_strings:
        print(f"[*] Searching for '{mission_type}' string...")
        addr, full_string = find_string_address(mission_type)
        
        if addr:
            print(f"    Found at 0x{addr:X}: \"{full_string}\"")
            
            # Analyze xrefs
            analysis = analyze_xrefs_for_structure(addr, full_string)
            
            if analysis:
                print(f"    Found {len(analysis)} functions using this string")
                mission_string_analysis[mission_type] = analysis
                
                # Show first result
                if analysis:
                    first = analysis[0]
                    print(f"    Example: {first['function']} at {first['func_addr']}")
                    if first['patterns']:
                        print(f"    Patterns found: {len(first['patterns'])}")
                        for p in first['patterns'][:3]:
                            if p['type'] == 'structure_size':
                                print(f"      Structure size: {p['size']} bytes")
        else:
            print(f"    Not found")
        
        print()
    
    # Strategy 2: Check if MissionType enum exists
    print("\n" + "="*60)
    print("Strategy 2: Check for MissionType enum")
    print("="*60)
    print()
    
    enum_id = idc.get_enum("MissionType")
    if enum_id != idc.BADADDR:
        print("[+] MissionType enum found!")
        print(f"    Enum ID: {enum_id}")
        
        # Analyze enum usage
        print("[*] Analyzing MissionType enum usage...")
        enum_usage = find_enum_usage("MissionType")
        
        print(f"[+] Found {len(enum_usage)} comparisons using MissionType")
        
        if enum_usage:
            print("\n[*] Sample comparisons:")
            for usage in enum_usage[:10]:
                print(f"    {usage['addr']}: {usage['function']}")
                print(f"      Comparing to {usage['enum_member']} ({usage['value']})")
                print(f"      {usage['disasm']}")
    else:
        print("[!] MissionType enum not found in IDA database")
    
    # Strategy 3: Look for structure size patterns
    print("\n" + "="*60)
    print("Strategy 3: Common structure size patterns")
    print("="*60)
    print()
    
    # Collect all structure sizes found
    all_sizes = {}
    for mission_type, analysis in mission_string_analysis.items():
        for func_analysis in analysis:
            for pattern in func_analysis['patterns']:
                if pattern['type'] == 'structure_size':
                    size = pattern['size']
                    if size not in all_sizes:
                        all_sizes[size] = []
                    all_sizes[size].append({
                        'mission_type': mission_type,
                        'function': func_analysis['function'],
                        'addr': pattern['addr']
                    })
    
    print(f"[+] Found structure sizes: {sorted(all_sizes.keys())}")
    print()
    
    for size in sorted(all_sizes.keys()):
        occurrences = all_sizes[size]
        print(f"[*] Size {size} bytes ({len(occurrences)} occurrences):")
        for occ in occurrences[:5]:
            print(f"    In {occ['function']} (mission: {occ['mission_type']})")
    
    # Strategy 4: Look for waypoint-related structures
    print("\n" + "="*60)
    print("Strategy 4: Waypoint structure discovery")
    print("="*60)
    print()
    
    waypoint_addr, waypoint_str = find_string_address("WAYPOINT")
    if waypoint_addr:
        print(f"[+] Found WAYPOINT string at 0x{waypoint_addr:X}")
        waypoint_analysis = analyze_xrefs_for_structure(waypoint_addr, waypoint_str)
        
        if waypoint_analysis:
            print(f"[+] Found {len(waypoint_analysis)} functions using waypoints")
            
            # Extract structure sizes
            waypoint_sizes = []
            for func_analysis in waypoint_analysis:
                for pattern in func_analysis['patterns']:
                    if pattern['type'] == 'structure_size':
                        waypoint_sizes.append(pattern['size'])
            
            if waypoint_sizes:
                from collections import Counter
                size_counts = Counter(waypoint_sizes)
                print(f"[*] Waypoint structure sizes: {dict(size_counts)}")
    
    # Save results
    result = {
        'mission_string_analysis': mission_string_analysis,
        'enum_usage': enum_usage if 'enum_usage' in locals() else [],
        'structure_sizes': {str(k): v for k, v in all_sizes.items()},
        'summary': {
            'mission_types_found': len(mission_string_analysis),
            'functions_analyzed': sum(len(v) for v in mission_string_analysis.values()),
            'structure_sizes_found': list(all_sizes.keys())
        }
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_structures_analysis.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n[+] Results saved to analysis/mission_structures_analysis.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
