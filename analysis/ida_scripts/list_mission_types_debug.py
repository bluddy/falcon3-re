#!/usr/bin/env python3
"""
Debug version - list MissionType enum members with extensive error checking.
"""

import idc
import idaapi
import json
import sys
import traceback

try:
    print("[*] Starting script...")
    print(f"[*] Python version: {sys.version}")
    print(f"[*] IDA version: {idaapi.get_kernel_version()}")
    
    idaapi.auto_wait()
    print("[*] Auto-analysis complete")
    
    print("[*] Listing MissionType enum...")
    
    # Get MissionType enum
    enum_id = idc.get_enum("MissionType")
    
    if enum_id == idc.BADADDR or enum_id == 0xFFFFFFFF or enum_id is None:
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
            print(f"    [{i}] {enum_name} (ID: {enum_id_i})")
        
        result = {'found': False, 'members': [], 'all_enums': all_enums, 'enum_qty': enum_qty}
    else:
        print(f"[+] Found MissionType enum (ID: {enum_id:#x})")
        
        # List members
        members = []
        member_id = idc.get_first_enum_member(enum_id)
        print(f"[*] First member ID: {member_id}")
        
        count = 0
        while member_id != idc.BADADDR and member_id != 0xFFFFFFFF and count < 100:
            value = idc.get_enum_member_value(member_id)
            name = idc.get_enum_member_name(member_id)
            members.append({'name': name, 'value': value})
            print(f"    {value:2d}: {name}")
            member_id = idc.get_next_enum_member(enum_id, member_id)
            count += 1
        
        result = {'found': True, 'members': members, 'count': count}
    
    # Save
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_list_debug.json'
    print(f"\n[*] Saving to: {output_path}")
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Saved successfully ({len(json.dumps(result))} bytes)")
    
except Exception as e:
    print(f"\n[!!!] EXCEPTION: {type(e).__name__}: {e}")
    traceback.print_exc()
    
    error_result = {
        'error': str(e),
        'type': type(e).__name__,
        'traceback': traceback.format_exc()
    }
    
    try:
        with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_error.json', 'w') as f:
            json.dump(error_result, f, indent=2)
        print("[+] Error log saved")
    except:
        print("[!] Could not save error log")

finally:
    print("\n[*] Script complete, exiting...")
    idc.qexit(0)
