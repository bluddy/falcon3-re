"""
Sync structures and enums from registry to IDA database.

Reads:
- registry/structures.yaml
- registry/enums.yaml

Creates in IDA:
- Enum types with values
- Struct types with fields
- Applies types to known locations
"""
import idaapi
import idautils
import idc
import yaml
import os

def create_enum_in_ida(enum_def):
    """Create an enum type in IDA from YAML definition."""
    enum_name = enum_def['name']
    enum_desc = enum_def.get('description', '')
    
    print(f"Creating enum: {enum_name}")
    print(f"  Description: {enum_desc[:60]}...")
    
    # Check if enum already exists
    enum_id = idc.get_enum(enum_name)
    if enum_id != idc.BADADDR:
        print(f"  Enum {enum_name} already exists, deleting...")
        idc.del_enum(enum_id)
    
    # Create new enum
    enum_id = idc.add_enum(idc.BADADDR, enum_name, 0)
    if enum_id == idc.BADADDR:
        print(f"  ERROR: Failed to create enum {enum_name}")
        return False
    
    # Set enum comment
    if enum_desc:
        idc.set_enum_cmt(enum_id, enum_desc, 0)
    
    # Add values
    for val in enum_def.get('values', []):
        value = val['value']
        name = val['name']
        desc = val.get('description', '')
        
        # Add member
        ret = idc.add_enum_member(enum_id, name, value, idc.BADADDR)
        if ret != 0 and ret != idc.ENUM_MEMBER_ERROR_NAME:  # Allow duplicate names
            print(f"    Warning: Failed to add {name} = {value} (error {ret})")
        else:
            print(f"    Added: {name} = {value} (0x{value:X})")
            
            # Set member comment
            if desc:
                idc.set_enum_member_cmt(idc.get_enum_member_by_name(name), desc, 0)
    
    print(f"  Created enum {enum_name} with {len(enum_def.get('values', []))} values\n")
    return True

def create_struct_in_ida(struct_def):
    """Create a struct type in IDA from YAML definition."""
    struct_name = struct_def['name']
    struct_size = struct_def.get('size')
    struct_desc = struct_def.get('description', '')
    
    print(f"Creating struct: {struct_name}")
    if struct_size:
        print(f"  Size: {struct_size} bytes (0x{struct_size:X})")
    else:
        print(f"  Size: Unknown")
    print(f"  Description: {struct_desc[:60]}...")
    
    # Check if struct already exists
    sid = idc.get_struc_id(struct_name)
    if sid != idc.BADADDR:
        print(f"  Struct {struct_name} already exists, deleting...")
        idc.del_struc(sid)
    
    # Create new struct
    sid = idc.add_struc(idc.BADADDR, struct_name, 0)
    if sid == idc.BADADDR:
        print(f"  ERROR: Failed to create struct {struct_name}")
        return False
    
    # Set struct comment
    if struct_desc:
        idc.set_struc_cmt(sid, struct_desc, 0)
    
    # Add fields
    fields = struct_def.get('fields', [])
    if not fields:
        print(f"  Warning: No fields defined for {struct_name}")
        return True
    
    # Sort fields by offset (skip null offsets)
    known_fields = [f for f in fields if f.get('offset') is not None]
    known_fields.sort(key=lambda f: f['offset'])
    
    for field in known_fields:
        offset = field['offset']
        field_name = field['name']
        field_type = field.get('type', 'uint16_t')
        field_desc = field.get('description', '')
        
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
        elif field_type.startswith('char['):
            # Array of chars
            flag = idc.FF_BYTE | idc.FF_DATA
            # Try to parse size
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
            print(f"    Warning: Failed to add field {field_name} at +0x{offset:X} (error {ret})")
        else:
            print(f"    Added: +0x{offset:X} {field_type:12} {field_name}")
            
            # Set member comment
            if field_desc:
                mptr = idc.get_member_by_name(sid, field_name)
                if mptr:
                    idc.set_member_cmt(mptr, field_desc, 0)
    
    print(f"  Created struct {struct_name} with {len(known_fields)} fields\n")
    return True

def main():
    print("=== SYNCING STRUCTURES AND ENUMS TO IDA ===\n")
    
    # Load YAML files
    base_path = r"C:\Users\ybarnoy\projects\falcon3"
    
    enums_path = os.path.join(base_path, "registry", "enums.yaml")
    structs_path = os.path.join(base_path, "registry", "structures.yaml")
    
    # Load enums
    print("Loading enums from registry...")
    with open(enums_path, 'r') as f:
        enums = yaml.safe_load(f)
    print(f"Loaded {len(enums)} enum definitions\n")
    
    # Load structures
    print("Loading structures from registry...")
    with open(structs_path, 'r') as f:
        structures = yaml.safe_load(f)
    print(f"Loaded {len(structures)} structure definitions\n")
    
    # Create enums
    print("\n" + "="*60)
    print("CREATING ENUMS")
    print("="*60 + "\n")
    
    enum_success = 0
    for enum_def in enums:
        if create_enum_in_ida(enum_def):
            enum_success += 1
    
    print(f"Successfully created {enum_success}/{len(enums)} enums\n")
    
    # Create structures
    print("\n" + "="*60)
    print("CREATING STRUCTURES")
    print("="*60 + "\n")
    
    struct_success = 0
    for struct_def in structures:
        if create_struct_in_ida(struct_def):
            struct_success += 1
    
    print(f"Successfully created {struct_success}/{len(structures)} structures\n")
    
    # Summary
    print("\n" + "="*60)
    print("SYNC COMPLETE")
    print("="*60)
    print(f"Enums: {enum_success}/{len(enums)}")
    print(f"Structures: {struct_success}/{len(structures)}")
    print("\nYou can now use these types in IDA by:")
    print("  1. Right-click on a variable -> 'Convert to enum'")
    print("  2. Right-click on data -> 'Edit' -> 'Struct var'")
    print("  3. In function signatures: Edit -> 'Set function type'")

if __name__ == "__main__":
    main()
