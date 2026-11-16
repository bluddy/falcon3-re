#!/usr/bin/env python3
"""
List MissionType enum members - FIXED VERSION
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Listing MissionType enum...")
    
    # Get MissionType enum
    enum_id = idc.get_enum("MissionType")
    
    if enum_id == idc.BADADDR or enum_id == 0xFFFFFFFF:
        print(f"[!] MissionType enum not found (got {enum_id})")
        
        # List all enums
        print("\n[*] Available enums:")
        enum_qty = idc.get_enum_qty()
        print(f"[*] Total enums: {enum_qty}")
        
        all_enums = []
        for i in range(enum_qty):
            enum_id_i = idc.getn_enum(i)
            enum_name = idc.get_enum_name(enum_id_i)
            all_enums.append(enum_name)
            print(f"    [{i:2d}] {enum_name}")
        
        result = {
            'found': False,
            'members': [],
            'all_enums': all_enums,
            'enum_qty': enum_qty
        }
    else:
        print(f"[+] Found MissionType enum (ID: {enum_id:#x})")
        
        # Get enum size
        enum_width = idc.get_enum_width(enum_id)
        enum_size = idc.get_enum_size(enum_id)
        print(f"[*] Enum width: {enum_width}, size: {enum_size}")
        
        # List members using different API - get_enum_member
        members = []
        
        # Try iterating by value instead
        for value in range(256):  # Reasonable upper limit
            const_id = idc.get_enum_member(enum_id, value, 0, -1)
            if const_id != idc.BADADDR and const_id != 0xFFFFFFFF:
                name = idc.get_enum_member_name(const_id)
                if name:
                    members.append({'name': name, 'value': value})
                    print(f"    {value:3d} (0x{value:02X}): {name}")
        
        if not members:
            # Alternative: try get_first_serial_enum_member
            print("[*] Trying alternative enumeration method...")
            bmask = idc.get_first_bmask(enum_id)
            while bmask != idc.BADADDR:
                value = idc.get_first_enum_member(enum_id, bmask)
                while value != idc.BADADDR:
                    const_id = idc.get_enum_member(enum_id, value, 0, bmask)
                    if const_id != idc.BADADDR:
                        name = idc.get_enum_member_name(const_id)
                        if name:
                            members.append({'name': name, 'value': value})
                            print(f"    {value:3d} (0x{value:02X}): {name}")
                    value = idc.get_next_enum_member(enum_id, value, bmask)
                bmask = idc.get_next_bmask(enum_id, bmask)
        
        result = {
            'found': True,
            'members': members,
            'count': len(members),
            'enum_width': enum_width,
            'enum_size': enum_size
        }
    
    # Save
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_list.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n[+] Saved to {output_path}")
    print(f"[+] Found {len(result['members'])} enum members")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
