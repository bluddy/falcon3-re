#!/usr/bin/env python3
"""
Find MissionType enum references in R53 segment to locate mission structures.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("FIND MISSIONTYPE REFERENCES IN R53")
    print("="*80)
    print()
    
    # Get R53 segment
    r53_seg = None
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        if 'R53' in seg_name:
            r53_seg = {'start': seg_ea, 'end': idc.get_segm_end(seg_ea), 'name': seg_name}
            break
    
    if not r53_seg:
        print("[!] R53 segment not found")
        idc.qexit(1)
    
    print(f"[+] Found segment: {r53_seg['name']}")
    print(f"    Range: {r53_seg['start']:#x} - {r53_seg['end']:#x}")
    print(f"    Size: {r53_seg['end'] - r53_seg['start']} bytes")
    print()
    
    # Get MissionType enum members
    enum_id = idc.get_enum("MissionType")
    if enum_id == idc.BADADDR:
        print("[!] MissionType enum not found")
        idc.qexit(1)
    
    mission_types = {}
    for value in range(256):
        const_id = idc.get_enum_member(enum_id, value, 0, -1)
        if const_id != idc.BADADDR and const_id != 0xFFFFFFFF:
            name = idc.get_enum_member_name(const_id)
            if name:
                mission_types[value] = name
    
    print(f"[+] Loaded {len(mission_types)} mission type values")
    print()
    
    # Scan R53 for comparisons with these values
    print("[*] Scanning R53 for mission type comparisons...")
    
    comparisons = []
    ea = r53_seg['start']
    
    while ea < r53_seg['end']:
        # Look for CMP instructions
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ['cmp', 'test', 'and', 'or']:
            # Get operands
            op0_type = idc.get_operand_type(ea, 0)
            op1_type = idc.get_operand_type(ea, 1)
            
            op0_val = idc.get_operand_value(ea, 0)
            op1_val = idc.get_operand_value(ea, 1)
            
            # Check if either operand is a known mission type value
            for value, name in mission_types.items():
                if op1_val == value or op0_val == value:
                    # Found a comparison with mission type!
                    disasm = idc.generate_disasm_line(ea, 0)
                    func_name = idc.get_func_name(ea)
                    
                    # Look back a few instructions to find the source
                    context_before = []
                    prev_ea = idc.prev_head(ea)
                    for _ in range(5):
                        if prev_ea != idc.BADADDR:
                            context_before.append({
                                'addr': hex(prev_ea),
                                'disasm': idc.generate_disasm_line(prev_ea, 0)
                            })
                            prev_ea = idc.prev_head(prev_ea)
                    
                    comparisons.append({
                        'addr': hex(ea),
                        'disasm': disasm,
                        'function': func_name,
                        'mission_type': name,
                        'value': value,
                        'context_before': list(reversed(context_before))
                    })
                    
                    print(f"[+] Found at {ea:#x} in {func_name}")
                    print(f"    {disasm}")
                    print(f"    Mission type: {name} (value {value})")
        
        ea = idc.next_head(ea, r53_seg['end'])
    
    print()
    print(f"[+] Found {len(comparisons)} mission type comparisons")
    print()
    
    # Look for patterns that might be structure accesses
    print("[*] Analyzing comparison context for structure access patterns...")
    print()
    
    structure_patterns = []
    
    for cmp in comparisons:
        # Look for [reg+offset] patterns in context
        for ctx in cmp['context_before']:
            disasm = ctx['disasm']
            
            # Check for memory access with offset
            if '[' in disasm and '+' in disasm:
                # Extract offset if possible
                import re
                offset_match = re.search(r'\[.+?\+([0-9A-Fa-fx]+)\]', disasm)
                if offset_match:
                    offset_str = offset_match.group(1)
                    try:
                        if offset_str.startswith('0x'):
                            offset = int(offset_str, 16)
                        else:
                            offset = int(offset_str, 10)
                        
                        structure_patterns.append({
                            'comparison': cmp,
                            'access_instruction': disasm,
                            'offset': offset,
                            'offset_hex': hex(offset)
                        })
                        
                        print(f"[+] Potential structure access:")
                        print(f"    {ctx['addr']}: {disasm}")
                        print(f"    Offset: {offset} (0x{offset:x})")
                        print(f"    Followed by comparison with {cmp['mission_type']}")
                        print()
                    except:
                        pass
    
    # Save results
    result = {
        'r53_segment': {
            'name': r53_seg['name'],
            'start': hex(r53_seg['start']),
            'end': hex(r53_seg['end']),
            'size': r53_seg['end'] - r53_seg['start']
        },
        'mission_types_loaded': len(mission_types),
        'comparisons_found': len(comparisons),
        'comparisons': comparisons,
        'structure_patterns_found': len(structure_patterns),
        'structure_patterns': structure_patterns
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_refs_r53.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Results saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
