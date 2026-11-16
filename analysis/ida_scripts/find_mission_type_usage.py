#!/usr/bin/env python3
"""
Find MissionType enum usage and trace to mission data structures.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("MISSION TYPE ENUM USAGE ANALYSIS")
    print("="*80)
    print()
    
    # Get MissionType enum
    enum_id = idc.get_enum("MissionType")
    if enum_id == idc.BADADDR:
        print("[!] MissionType enum not found")
        idc.qexit(1)
    
    print(f"[+] MissionType enum found (ID: {enum_id})")
    
    # List all enum members
    print("\n[*] MissionType enum members:")
    members = []
    member_id = idc.get_first_enum_member(enum_id)
    
    while member_id != idc.BADADDR:
        value = idc.get_enum_member_value(member_id)
        name = idc.get_enum_member_name(member_id)
        members.append({'name': name, 'value': value})
        print(f"    {value:2d}: {name}")
        member_id = idc.get_next_enum_member(enum_id, member_id)
    
    print(f"\n[+] Total: {len(members)} mission types")
    print()
    
    # Find R53 segment for focused search
    r53_start = None
    r53_end = None
    
    for seg_ea in idautils.Segments():
        name = idc.get_segm_name(seg_ea)
        if "R53" in name:
            r53_start = seg_ea
            r53_end = idc.get_segm_end(seg_ea)
            break
    
    # Search for enum value usage in R53
    if r53_start:
        print(f"[*] Searching for mission type comparisons in R53...")
        
        enum_usage = []
        ea = r53_start
        
        while ea < r53_end:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == 'cmp':
                op1_val = idc.get_operand_value(ea, 1)
                
                # Check if value matches any enum member
                for member in members:
                    if op1_val == member['value']:
                        disasm = idc.generate_disasm_line(ea, 0)
                        func_name = idc.get_func_name(ea)
                        
                        enum_usage.append({
                            'addr': hex(ea),
                            'function': func_name,
                            'mission_type': member['name'],
                            'value': member['value'],
                            'disasm': disasm
                        })
                        break
            
            ea = idc.next_head(ea, r53_end)
        
        print(f"[+] Found {len(enum_usage)} mission type comparisons in R53")
        print()
        
        # Group by function
        by_function = {}
        for usage in enum_usage:
            func = usage['function']
            if func not in by_function:
                by_function[func] = []
            by_function[func].append(usage)
        
        print(f"[*] Usage by function ({len(by_function)} functions):")
        for func, usages in sorted(by_function.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    {func}: {len(usages)} comparisons")
            
            # Show first few
            for u in usages[:5]:
                print(f"      {u['addr']}: {u['mission_type']}")
        
        print()
        
        # Now analyze the functions that use mission types
        print("[*] Analyzing functions with mission type usage...")
        
        for func_name, usages in list(by_function.items())[:3]:
            print(f"\n[*] Function: {func_name}")
            
            # Get function address
            first_usage_addr = int(usages[0]['addr'], 16)
            func_addr = idc.get_func_attr(first_usage_addr, idc.FUNCATTR_START)
            
            if func_addr == idc.BADADDR:
                continue
            
            func = idaapi.get_func(func_addr)
            if not func:
                continue
            
            # Look for structure access patterns
            print(f"    Address: 0x{func_addr:X}")
            print(f"    Size: {func.end_ea - func_addr} bytes")
            
            # Look for data access near mission type comparisons
            print(f"    Data access patterns:")
            
            for usage in usages[:3]:
                usage_addr = int(usage['addr'], 16)
                
                # Look 10 instructions before and after
                ea = max(func.start_ea, usage_addr - 50)
                end_ea = min(func.end_ea, usage_addr + 50)
                
                data_accesses = []
                while ea < end_ea:
                    mnem = idc.print_insn_mnem(ea)
                    disasm = idc.generate_disasm_line(ea, 0)
                    
                    # Look for memory access with offsets
                    if mnem in ['mov', 'lea', 'add', 'cmp'] and '[' in disasm:
                        # Extract offset if present
                        if '+' in disasm:
                            data_accesses.append({
                                'addr': hex(ea),
                                'disasm': disasm
                            })
                    
                    ea = idc.next_head(ea, end_ea)
                
                if data_accesses:
                    print(f"      Near {usage['mission_type']} comparison:")
                    for access in data_accesses[:3]:
                        print(f"        {access['disasm']}")
    
    else:
        print("[!] R53 segment not found, searching entire database...")
        enum_usage = []
    
    # Save results
    result = {
        'enum_members': members,
        'enum_usage_count': len(enum_usage) if 'enum_usage' in locals() else 0,
        'enum_usage': enum_usage if 'enum_usage' in locals() else [],
        'functions_using_mission_types': list(by_function.keys()) if 'by_function' in locals() else []
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_usage_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n[+] Results saved to analysis/mission_type_usage_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
