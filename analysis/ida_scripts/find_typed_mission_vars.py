#!/usr/bin/env python3
"""
Find all variables/structure members that are typed as MissionType enum.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("FIND VARIABLES TYPED AS MISSIONTYPE")
    print("="*80)
    print()
    
    # Get MissionType enum ID
    enum_id = idc.get_enum("MissionType")
    if enum_id == idc.BADADDR:
        print("[!] MissionType enum not found")
        idc.qexit(1)
    
    print(f"[+] MissionType enum ID: {enum_id:#x}")
    print()
    
    # Search all data segments for references to this enum
    print("[*] Searching for enum type references...")
    
    typed_vars = []
    
    # Scan all segments
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        print(f"[*] Scanning segment {seg_name}...")
        
        ea = seg_ea
        while ea < seg_end:
            # Check if this address has a name (is a variable)
            name = idc.get_name(ea)
            if name and not name.startswith('loc_') and not name.startswith('sub_'):
                # Get type info
                tinfo = idaapi.tinfo_t()
                if idaapi.get_tinfo(tinfo, ea):
                    type_str = str(tinfo)
                    
                    # Check if type contains "MissionType"
                    if 'MissionType' in type_str or 'mission' in type_str.lower():
                        typed_vars.append({
                            'address': hex(ea),
                            'name': name,
                            'type': type_str,
                            'segment': seg_name
                        })
                        
                        print(f"    [+] {name} at {ea:#x}: {type_str}")
            
            ea = idc.next_head(ea, seg_end)
    
    print()
    print(f"[+] Found {len(typed_vars)} typed variables")
    print()
    
    # Also check all structures for MissionType fields
    print("[*] Checking structures for MissionType fields...")
    
    struct_fields = []
    
    for idx in range(idc.get_struc_qty()):
        struct_id = idc.get_struc_by_idx(idx)
        struct_name = idc.get_struc_name(struct_id)
        
        # Get structure members
        struc = idaapi.get_struc(struct_id)
        if struc:
            for midx in range(struc.memqty):
                member = struc.get_member(midx)
                if member:
                    member_name = idaapi.get_member_name(member.id)
                    
                    # Get member type
                    mti = idaapi.tinfo_t()
                    if idaapi.get_member_tinfo(mti, member):
                        type_str = str(mti)
                        
                        if 'MissionType' in type_str or 'mission' in member_name.lower():
                            struct_fields.append({
                                'struct': struct_name,
                                'offset': member.soff,
                                'offset_hex': hex(member.soff),
                                'member_name': member_name,
                                'type': type_str
                            })
                            
                            print(f"    [+] {struct_name}.{member_name} at +{member.soff:#x}: {type_str}")
    
    print()
    print(f"[+] Found {len(struct_fields)} structure fields")
    print()
    
    # Also list all known structures
    print("[*] All known structures:")
    all_structs = []
    for idx in range(idc.get_struc_qty()):
        struct_id = idc.get_struc_by_idx(idx)
        struct_name = idc.get_struc_name(struct_id)
        struct_size = idc.get_struc_size(struct_id)
        
        all_structs.append({
            'name': struct_name,
            'id': hex(struct_id),
            'size': struct_size
        })
        
        print(f"    {struct_name}: {struct_size} bytes")
    
    # Save results
    result = {
        'typed_variables': typed_vars,
        'struct_fields': struct_fields,
        'all_structures': all_structs
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\mission_type_typed_vars.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n[+] Results saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
