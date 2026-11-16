#!/usr/bin/env python3
"""
Test creating a single enum in IDA.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Testing enum creation...")
    
    # Try to create PilotRank enum
    enum_name = "PilotRank"
    
    # Check if exists
    enum_id = idc.get_enum(enum_name)
    if enum_id != idc.BADADDR:
        print(f"[*] Enum {enum_name} already exists, deleting...")
        idc.del_enum(enum_id)
    
    # Create enum
    enum_id = idc.add_enum(idc.BADADDR, enum_name, 0)
    if enum_id == idc.BADADDR:
        print(f"[!] ERROR: Failed to create enum {enum_name}")
    else:
        print(f"[+] Created enum {enum_name} with ID={enum_id}")
        
        # Add values
        values = [
            ("PILOT_RANK_LT", 0),
            ("PILOT_RANK_CAPT", 1),
            ("PILOT_RANK_MAJOR", 2),
            ("PILOT_RANK_LT_COL", 3),
            ("PILOT_RANK_COL", 4)
        ]
        
        for name, value in values:
            ret = idc.add_enum_member(enum_id, name, value, idc.BADADDR)
            if ret == 0:
                print(f"[+] Added {name} = {value}")
            else:
                print(f"[!] Failed to add {name} = {value}, error={ret}")
    
    # Verify
    enum_id_check = idc.get_enum(enum_name)
    success = enum_id_check != idc.BADADDR
    
    print(f"\n[*] Verification: {'SUCCESS' if success else 'FAILED'}")
    
    # Save result
    output = {
        'enum_name': enum_name,
        'created': success,
        'enum_id': enum_id if success else None
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\enum_test_result.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("[+] Results saved to analysis/enum_test_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
