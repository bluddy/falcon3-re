#!/usr/bin/env python3
"""
Dump all structure definitions from IDA database.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("DUMP ALL STRUCTURES")
    print("="*80)
    print()
    
    structures = []
    
    for idx in range(idc.get_struc_qty()):
        struct_id = idc.get_struc_by_idx(idx)
        struct_name = idc.get_struc_name(struct_id)
        struct_size = idc.get_struc_size(struct_id)
        
        print(f"[*] {struct_name} ({struct_size} bytes)")
        
        # Get members
        struc = idaapi.get_struc(struct_id)
        members = []
        
        if struc:
            for midx in range(struc.memqty):
                member = struc.get_member(midx)
                if member:
                    member_name = idaapi.get_member_name(member.id)
                    member_size = idaapi.get_member_size(member)
                    member_offset = member.soff
                    
                    # Get type if available
                    mti = idaapi.tinfo_t()
                    type_str = "unknown"
                    if idaapi.get_member_tinfo(mti, member):
                        type_str = str(mti)
                    
                    members.append({
                        'name': member_name,
                        'offset': member_offset,
                        'size': member_size,
                        'type': type_str
                    })
                    
                    print(f"    +{member_offset:#04x}: {member_name} ({type_str}, {member_size} bytes)")
        
        structures.append({
            'name': struct_name,
            'size': struct_size,
            'members': members
        })
        
        print()
    
    print(f"[+] Total structures: {len(structures)}")
    
    # Save
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\all_structures.json'
    with open(output_path, 'w') as f:
        json.dump(structures, f, indent=2)
    
    print(f"[+] Saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
