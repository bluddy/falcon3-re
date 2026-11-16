#!/usr/bin/env python3
"""
Simple script to list MissionType enum members.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Listing MissionType enum...")
    
    # Get MissionType enum
    enum_id = idc.get_enum("MissionType")
    
    if enum_id == idc.BADADDR:
        print("[!] MissionType enum not found")
        
        # List all enums
        print("\n[*] Available enums:")
        for i in range(idc.get_enum_qty()):
            enum_id_i = idc.getn_enum(i)
            enum_name = idc.get_enum_name(enum_id_i)
            print(f"    {enum_name}")
        
        result = {'found': False, 'members': []}
    else:
        print(f"[+] Found MissionType enum (ID: {enum_id})")
        
        # List members
        members = []
        member_id = idc.get_first_enum_member(enum_id)
        
        while member_id != idc.BADADDR:
            value = idc.get_enum_member_value(member_id)
            name = idc.get_enum_member_name(member_id)
            members.append({'name': name, 'value': value})
            print(f"    {value:2d}: {name}")
            member_id = idc.get_next_enum_member(enum_id, member_id)
        
        result = {'found': True, 'members': members}
    
    # Save
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_list.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n[+] Saved to analysis/mission_type_list.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
