#!/usr/bin/env python3
"""
Find mission data structures by tracking how mission type enum is loaded from memory.

Strategy:
1. Find all MOV instructions that load a value from memory into a register
2. Trace forward to see if that value is compared against MissionType enum values
3. The memory location pattern reveals the structure offset
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("FIND MISSION STRUCTURE VIA ENUM ACCESS PATTERNS")
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
    
    print(f"[+] R53 segment: {r53_seg['name']}")
    print(f"    Range: {r53_seg['start']:#x} - {r53_seg['end']:#x}")
    print()
    
    # Get MissionType enum values
    enum_id = idc.get_enum("MissionType")
    mission_values = set()
    for value in range(256):
        const_id = idc.get_enum_member(enum_id, value, 0, -1)
        if const_id != idc.BADADDR and const_id != 0xFFFFFFFF:
            name = idc.get_enum_member_name(const_id)
            if name:
                mission_values.add(value)
    
    print(f"[+] Mission type values: {sorted(mission_values)}")
    print()
    
    # Scan for patterns where a memory value is loaded then compared
    print("[*] Scanning for memory-to-register loads followed by comparisons...")
    
    patterns = []
    ea = r53_seg['start']
    
    while ea < r53_seg['end']:
        mnem = idc.print_insn_mnem(ea)
        
        # Look for MOV from memory to register
        if mnem == 'mov':
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Check if source operand is memory (contains '[')
            if '[' in disasm and ']' in disasm:
                # Get the register being loaded into (destination)
                op0_type = idc.get_operand_type(ea, 0)
                
                # Only care if destination is a register
                if op0_type == idc.o_reg:
                    dest_reg = idc.print_operand(ea, 0)
                    
                    # Look ahead for a comparison using this register
                    next_ea = idc.next_head(ea)
                    search_limit = 10  # Look ahead up to 10 instructions
                    
                    for _ in range(search_limit):
                        if next_ea == idc.BADADDR or next_ea >= r53_seg['end']:
                            break
                        
                        next_mnem = idc.print_insn_mnem(next_ea)
                        next_disasm = idc.generate_disasm_line(next_ea, 0)
                        
                        # Check if this is a comparison involving our register
                        if next_mnem in ['cmp', 'test'] and dest_reg in next_disasm:
                            # Check if comparing against a mission type value
                            cmp_val = idc.get_operand_value(next_ea, 1)
                            
                            if cmp_val in mission_values:
                                # Found it! Extract the memory pattern
                                import re
                                
                                # Try to extract pointer patterns like [bx+offset], es:[bx], etc.
                                mem_pattern = None
                                offset = None
                                
                                # Pattern: [reg+offset]
                                match = re.search(r'\[(\w+)\+([0-9A-Fa-fx]+)\]', disasm)
                                if match:
                                    base_reg = match.group(1)
                                    offset_str = match.group(2)
                                    if offset_str.startswith('0x'):
                                        offset = int(offset_str, 16)
                                    else:
                                        offset = int(offset_str, 16)
                                    mem_pattern = f"[{base_reg}+{offset:#x}]"
                                else:
                                    # Pattern: segment:[reg+offset]
                                    match = re.search(r'(\w+):\[(\w+)\+([0-9A-Fa-fx]+)\]', disasm)
                                    if match:
                                        segment = match.group(1)
                                        base_reg = match.group(2)
                                        offset_str = match.group(3)
                                        if offset_str.startswith('0x'):
                                            offset = int(offset_str, 16)
                                        else:
                                            offset = int(offset_str, 16)
                                        mem_pattern = f"{segment}:[{base_reg}+{offset:#x}]"
                                
                                if offset is not None and offset > 0 and offset < 10000:
                                    const_name = idc.get_enum_member_name(
                                        idc.get_enum_member(enum_id, cmp_val, 0, -1)
                                    )
                                    
                                    patterns.append({
                                        'load_addr': hex(ea),
                                        'load_insn': disasm,
                                        'cmp_addr': hex(next_ea),
                                        'cmp_insn': next_disasm,
                                        'mission_type': const_name,
                                        'mission_value': cmp_val,
                                        'offset': offset,
                                        'offset_hex': hex(offset),
                                        'memory_pattern': mem_pattern,
                                        'function': idc.get_func_name(ea)
                                    })
                                    
                                    print(f"[+] Found pattern at {ea:#x}:")
                                    print(f"    Load: {disasm}")
                                    print(f"    Compare: {next_disasm}")
                                    print(f"    Mission type: {const_name} (value {cmp_val})")
                                    print(f"    Offset: {offset:#x} ({offset})")
                                    print(f"    Function: {idc.get_func_name(ea)}")
                                    print()
                            
                            break  # Stop looking ahead after finding a comparison
                        
                        # If we hit certain instructions, stop looking (control flow change)
                        if next_mnem in ['jmp', 'je', 'jne', 'jz', 'jnz', 'call', 'ret']:
                            break
                        
                        next_ea = idc.next_head(next_ea)
        
        ea = idc.next_head(ea, r53_seg['end'])
    
    print()
    print(f"[+] Found {len(patterns)} memory-load patterns")
    print()
    
    # Analyze offset distribution
    if patterns:
        print("[*] Offset distribution:")
        offset_counts = {}
        for p in patterns:
            offset = p['offset']
            if offset not in offset_counts:
                offset_counts[offset] = []
            offset_counts[offset].append(p)
        
        for offset in sorted(offset_counts.keys()):
            count = len(offset_counts[offset])
            print(f"    Offset {offset:#x} ({offset}): {count} occurrences")
            for p in offset_counts[offset][:3]:  # Show first 3 examples
                print(f"        {p['function']}: {p['memory_pattern']}")
    
    # Save results
    result = {
        'r53_segment': r53_seg['name'],
        'patterns_found': len(patterns),
        'patterns': patterns,
        'unique_offsets': sorted(list(set(p['offset'] for p in patterns)))
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_structure_offsets.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n[+] Results saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
