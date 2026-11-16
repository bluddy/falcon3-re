#!/usr/bin/env python3
"""
Sync all structures to IDA database.

Includes:
- PilotRecord (66 bytes) - complete
- ExtendedPilotRecord (66 bytes) - complete
- SquadronHeader (60 bytes) - complete
- SquadronFile (2703 bytes) - complete
- FlightRecord (130 bytes) - partial
- LoadoutRecord (23 bytes) - partial
"""

import idc
import idaapi
import idautils
import json

def create_enum_in_ida(enum_def):
    """Create an enum type in IDA from definition."""
    enum_name = enum_def['name']
    
    print(f"[*] Creating enum: {enum_name}")
    
    # Check if enum already exists
    enum_id = idc.get_enum(enum_name)
    if enum_id != idc.BADADDR:
        print(f"    Already exists, deleting...")
        idc.del_enum(enum_id)
    
    # Create new enum
    enum_id = idc.add_enum(idc.BADADDR, enum_name, 0)
    if enum_id == idc.BADADDR:
        print(f"    ERROR: Failed to create enum")
        return False
    
    # Add values
    for val in enum_def.get('values', []):
        value = val['value']
        name = val['name']
        ret = idc.add_enum_member(enum_id, name, value, idc.BADADDR)
        if ret != 0 and ret != 1:  # 0 = success, 1 = already exists
            print(f"    Warning: Failed to add {name} = {value}")
    
    print(f"    Created with {len(enum_def.get('values', []))} values")
    return True

def create_struct_in_ida(struct_def):
    """Create a struct type in IDA from definition."""
    struct_name = struct_def['name']
    struct_size = struct_def.get('size')
    
    print(f"[*] Creating struct: {struct_name} ({struct_size} bytes)")
    
    # Check if struct already exists
    sid = idc.get_struc_id(struct_name)
    if sid != idc.BADADDR:
        print(f"    Already exists, deleting...")
        idc.del_struc(sid)
    
    # Create new struct
    sid = idc.add_struc(idc.BADADDR, struct_name, 0)
    if sid == idc.BADADDR:
        print(f"    ERROR: Failed to create struct")
        return False
    
    # Add fields
    fields = struct_def.get('fields', [])
    known_fields = [f for f in fields if f.get('offset') is not None]
    
    if not known_fields:
        print(f"    Warning: No fields with known offsets")
        return True
    
    for field in known_fields:
        offset = field['offset']
        field_name = field['name']
        field_type = field.get('type', 'uint16_t')
        
        # Convert type string to IDA type
        if field_type == 'uint8_t':
            flag = idc.FF_BYTE | idc.FF_DATA
            size = 1
        elif field_type == 'uint16_t':
            flag = idc.FF_WORD | idc.FF_DATA
            size = 2
        elif field_type == 'uint32_t':
            flag = idc.FF_DWORD | idc.FF_DATA
            size = 4
        elif field_type.startswith('char[') or field_type.startswith('uint8_t['):
            # Array of chars or bytes
            flag = idc.FF_BYTE | idc.FF_DATA
            try:
                arr_size = int(field_type.split('[')[1].split(']')[0])
                size = arr_size
            except:
                size = 1
        else:
            # Default to word
            flag = idc.FF_WORD | idc.FF_DATA
            size = 2
        
        # Add member
        ret = idc.add_struc_member(sid, field_name, offset, flag, idc.BADADDR, size)
        if ret != 0:
            print(f"    Warning: Field {field_name} at +0x{offset:X} failed (error {ret})")
    
    print(f"    Created with {len(known_fields)} fields")
    return True

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("SYNCING ALL STRUCTURES AND ENUMS TO IDA")
    print("="*80)
    print()
    
    # Load enums from JSON
    base_path = r"C:\Users\ybarnoy\projects\falcon3"
    enums_path = base_path + r"\registry\enums.json"
    
    print("[*] Loading enums from registry...")
    with open(enums_path, 'r') as f:
        enums = json.load(f)
    print(f"[+] Loaded {len(enums)} enum definitions\n")
    
    # Define all structures inline
    structures = [
        {
            'name': 'PilotRecord',
            'size': 66,
            'description': 'Pilot record from .SQU files (66 bytes)',
            'fields': [
                {'offset': 0x00, 'name': 'status_flags', 'type': 'uint8_t[2]'},
                {'offset': 0x02, 'name': 'rank', 'type': 'uint8_t'},
                {'offset': 0x03, 'name': 'callsign', 'type': 'char[15]'},
                {'offset': 0x12, 'name': 'pad1', 'type': 'uint8_t'},
                {'offset': 0x13, 'name': 'nickname', 'type': 'char[15]'},
                {'offset': 0x22, 'name': 'id_code', 'type': 'char[4]'},
                {'offset': 0x26, 'name': 'dogfighting_skill', 'type': 'uint8_t'},
                {'offset': 0x27, 'name': 'bombing_skill', 'type': 'uint8_t'},
                {'offset': 0x28, 'name': 'flying_skill', 'type': 'uint8_t'},
                {'offset': 0x29, 'name': 'fatigue_level', 'type': 'uint8_t'},
                {'offset': 0x2A, 'name': 'mission_data', 'type': 'uint8_t[28]'}
            ]
        },
        {
            'name': 'ExtendedPilotRecord',
            'size': 66,
            'description': 'Extended pilot record for pilots 20-29 (same as PilotRecord)',
            'fields': [
                {'offset': 0x00, 'name': 'status_flags', 'type': 'uint8_t[2]'},
                {'offset': 0x02, 'name': 'rank', 'type': 'uint8_t'},
                {'offset': 0x03, 'name': 'callsign', 'type': 'char[15]'},
                {'offset': 0x12, 'name': 'pad1', 'type': 'uint8_t'},
                {'offset': 0x13, 'name': 'nickname', 'type': 'char[15]'},
                {'offset': 0x22, 'name': 'id_code', 'type': 'char[4]'},
                {'offset': 0x26, 'name': 'dogfighting_skill', 'type': 'uint8_t'},
                {'offset': 0x27, 'name': 'bombing_skill', 'type': 'uint8_t'},
                {'offset': 0x28, 'name': 'flying_skill', 'type': 'uint8_t'},
                {'offset': 0x29, 'name': 'fatigue_level', 'type': 'uint8_t'},
                {'offset': 0x2A, 'name': 'mission_data', 'type': 'uint8_t[28]'}
            ]
        },
        {
            'name': 'SquadronHeader',
            'size': 60,
            'description': 'Squadron file header (60 bytes)',
            'fields': [
                {'offset': 0x00, 'name': 'squadron_slot', 'type': 'uint8_t'},
                {'offset': 0x01, 'name': 'active_flag', 'type': 'uint8_t'},
                {'offset': 0x02, 'name': 'theater_id', 'type': 'uint8_t'},
                {'offset': 0x03, 'name': 'theater_name', 'type': 'char[12]'},
                {'offset': 0x0F, 'name': 'wing_or_type', 'type': 'uint8_t'},
                {'offset': 0x10, 'name': 'statistics', 'type': 'uint8_t[44]'}
            ]
        },
        {
            'name': 'FlightRecord',
            'size': 130,
            'description': 'Flight configuration (130 bytes)',
            'fields': [
                {'offset': 0x00, 'name': 'aircraft_count', 'type': 'uint8_t'},
                {'offset': 0x01, 'name': 'loadouts', 'type': 'uint8_t[92]'}  # 4 × 23 bytes
            ]
        },
        {
            'name': 'LoadoutRecord',
            'size': 23,
            'description': 'Aircraft weapons loadout (23 bytes)',
            'fields': [
                {'offset': 0x00, 'name': 'hardpoint_config', 'type': 'uint8_t[11]'},
                {'offset': 0x0B, 'name': 'pilot_id', 'type': 'uint16_t'}
            ]
        },
        {
            'name': 'MenuElement',
            'size': 28,
            'description': 'Menu element (28 bytes)',
            'fields': [
                {'offset': 0x00, 'name': 'data_ptr_low', 'type': 'uint16_t'},
                {'offset': 0x02, 'name': 'data_ptr_high', 'type': 'uint16_t'},
                {'offset': 0x04, 'name': 'state_or_type', 'type': 'uint16_t'}
            ]
        }
    ]
    
    print(f"[+] Defined {len(structures)} structure definitions\n")
    
    # Create enums
    print("\n" + "="*60)
    print("CREATING ENUMS")
    print("="*60 + "\n")
    
    enum_success = 0
    for enum_def in enums:
        if create_enum_in_ida(enum_def):
            enum_success += 1
    
    print(f"\n[+] Successfully created {enum_success}/{len(enums)} enums\n")
    
    # Create structures
    print("\n" + "="*60)
    print("CREATING STRUCTURES")
    print("="*60 + "\n")
    
    struct_success = 0
    for struct_def in structures:
        if create_struct_in_ida(struct_def):
            struct_success += 1
    
    print(f"\n[+] Successfully created {struct_success}/{len(structures)} structures\n")
    
    # Summary
    print("="*60)
    print("SYNC COMPLETE")
    print("="*60)
    print(f"Enums: {enum_success}/{len(enums)}")
    print(f"Structures: {struct_success}/{len(structures)}")
    
    # Save results
    result = {
        'enums_created': enum_success,
        'enums_total': len(enums),
        'structs_created': struct_success,
        'structs_total': len(structures),
        'structures': [s['name'] for s in structures]
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\sync_all_structures_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n[+] Results saved to analysis/sync_all_structures_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
