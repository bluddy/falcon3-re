"""
Apply all known function names, structures, and globals to IDA database.

This script synchronizes IDA with our documented knowledge from analysis.
CRITICAL: Run this regularly as we learn more, or we'll lose our knowledge!

Source of truth: registry/functions.yaml, registry/globals.yaml
Based on analysis from all docs/systems/ and analysis/ documents.
"""

import idc
import idaapi
import json
import re
from pathlib import Path

def parse_simple_yaml(yaml_path):
    """
    Simple YAML parser for our function registry format.
    Doesn't need full YAML spec - just handles our specific structure.
    """
    with open(yaml_path, 'r') as f:
        lines = f.readlines()
    
    functions = []
    current_func = {}
    
    for line in lines:
        line = line.rstrip('\n\r')
        
        # Skip comments and empty lines
        if not line or line.strip().startswith('#'):
            continue
        
        # New function entry (starts with "  - address:")
        if line.startswith('  - address:'):
            # Save previous function
            if current_func:
                functions.append(current_func)
            current_func = {}
            
            # Parse address
            addr_str = line.split(':', 1)[1].strip()
            current_func['address'] = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
        
        # Parse other fields
        elif line.startswith('    ') and ':' in line:
            key, value = line.strip().split(':', 1)
            value = value.strip()
            
            if key == 'size':
                current_func[key] = int(value)
            else:
                current_func[key] = value
    
    # Add last function
    if current_func:
        functions.append(current_func)
    
    return {'functions': functions}

def load_functions_from_yaml():
    """Load functions from YAML registry."""
    yaml_path = Path(__file__).parent.parent.parent / "registry" / "functions.yaml"
    
    if not yaml_path.exists():
        print(f"ERROR: {yaml_path} not found!")
        return {}
    
    data = parse_simple_yaml(yaml_path)
    
    if not data or 'functions' not in data:
        print(f"ERROR: No functions found in {yaml_path}")
        return {}
    
    # Convert to simple dict: address -> name
    functions = {}
    for func in data['functions']:
        addr = func['address']
        name = func['name']
        functions[addr] = name
    
    print(f"Loaded {len(functions)} functions from {yaml_path}")
    return functions, data

# Known data structures and globals
KNOWN_DATA = {
    # Menu State Segments (from MENU_SYSTEM_CODE_STRUCTURE.md)
    # Segment 4FC2h addresses
    "menu_current_id": (0x4FC2, 0x4FD5E),      # Current menu ID
    "menu_previous_id": (0x4FC2, 0x4FD60),     # Previous menu (for back)
    "menu_state_1": (0x4FC2, 0x4FD74),         # Menu state
    "menu_state_2": (0x4FC2, 0x4FD72),         # Saved state
    
    # Segment 7894h addresses  
    "menu_loadout_data": (0x7894, 0x79E60),    # Loadout record data
    "menu_selection_state": (0x7894, 0x79B66), # Menu selection
    
    # String references (for documentation)
    "str_picfont_idx": 0x14E771,   # ".`PICFONT.IDX"
    "str_picfont_dat": 0x14E781,   # ".`PICFONT.DAT"
    "str_squad": 0x1512EF,         # "S-.`SQUAD"
    "str_harpoon_dat": 0x151402,   # "f..`HARPOON.DAT"
    "str_madfont_idx": 0x151AC4,   # "(5.`madfont.idx"
    "str_madfont_dat": 0x151AD4,   # "(5.`madfont.dat"
}

# Known global variables (DS-relative addresses)
KNOWN_GLOBALS = {
    # Terrain System
    0x3840: ("terrain_heightmap_31x31", 1922, "31×31 height samples for terrain"),
    0x7A0: ("terrain_lod_scale_table", 16, "8-level LOD distance scaling table"),
    
    # Flight Physics / Entity System
    0x32: ("flight_kinematics_block", 26, "26-byte flight state (pos, vel, tile)"),
    0x66: ("flight_kinematics_prev", 26, "Previous frame kinematics for delta"),
    
    # AI System
    0xC: ("ai_slot_array_base", 960, "40×24B AI/aircraft slot records"),
    
    # HUD/View System
    0x102: ("view_temp_record", 16, "Temporary view record for projection"),
    0x810: ("view_horizontal_angle", 2, "Camera horizontal angle"),
    0x814: ("view_vertical_angle", 2, "Camera vertical angle"),
    0x80E: ("view_h_direction", 1, "Horizontal direction (0=left, 1=right)"),
    0x812: ("view_v_direction", 1, "Vertical direction (0=down, 1=up)"),
    0xC55: ("view_mode_attribute", 1, "Current view mode/attribute index"),
    
    # Audio System
    0xAF90: ("audio_sbi_mode", 1, "SBI mode: 0=OPL2/AdLib, 1=SoundBlaster"),
    0xAE78: ("audio_channel_limit", 2, "Maximum audio channels"),
    0x99A7: ("audio_opl_register_table", 18, "OPL2 register table (2B per entry)"),
    0x99B9: ("audio_sb_register_table", 18, "SoundBlaster register table"),
    
    # Entity/FarObj System
    0x386F: ("entity_slot_records", 1472, "16×92B active entity slots (at segment 0x54AF)"),
    0x16F4: ("entity_type_class_table", None, "Entity type→class mapping table"),
    0x4E: ("entity_filename_buffer", 16, "Entity type filename (e.g. 'F4', 'SA')"),
    
    # Weapons/Combat
    0x15B3: ("weapon_game_mode", 1, "Game mode: 0=normal, 1+=restricted fire"),
    0x15B4: ("weapon_friendly_fire_flags", 2, "Friendly fire permission flags"),
    
    # Coordinate/World Transform
    0x7EA: ("coord_world_offset_x", 6, "World position offsets (3×word)"),
}

def apply_function_names(functions):
    """Rename functions in IDA."""
    renamed_count = 0
    failed_count = 0
    skipped_count = 0
    
    print("\n" + "="*80)
    print("APPLYING FUNCTION NAMES")
    print("="*80)
    
    for addr, name in sorted(functions.items()):
        # Check if function exists
        func = idaapi.get_func(addr)
        if not func:
            print(f"⚠ {name:30} @ {addr:#08x} - NOT A FUNCTION")
            failed_count += 1
            continue
        
        # Get current name
        current_name = idc.get_func_name(addr)
        
        # Skip if already correctly named
        if current_name == name:
            print(f"✓ {name:30} @ {addr:#08x} - already named")
            skipped_count += 1
            continue
        
        # Rename
        if idc.set_name(addr, name, idc.SN_NOWARN):
            print(f"✓ {name:30} @ {addr:#08x} - renamed from {current_name}")
            renamed_count += 1
        else:
            print(f"✗ {name:30} @ {addr:#08x} - FAILED TO RENAME")
            failed_count += 1
    
    print("\n" + "="*80)
    print(f"Functions renamed: {renamed_count}")
    print(f"Already correct: {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"Total processed: {len(functions)}")
    print("="*80)
    
    return renamed_count, skipped_count, failed_count

def apply_data_names(data):
    """Name data locations in IDA."""
    print("\n" + "="*80)
    print("APPLYING DATA NAMES")
    print("="*80)
    print("(Data naming implementation pending)")
    print("="*80)
    # TODO: Implement data naming
    # Need to figure out how to name segment:offset addresses
    return 0, 0, 0

def add_comments(functions, yaml_data):
    """Add comments to functions with our knowledge from YAML."""
    print("\n" + "="*80)
    print("ADDING FUNCTION COMMENTS")
    print("="*80)
    
    # Build dict of address -> description from YAML
    comments = {}
    for func in yaml_data.get('functions', []):
        addr = func['address']
        if isinstance(addr, str) and addr.startswith('0x'):
            addr = int(addr, 16)
        
        # Build full comment from YAML fields
        comment_parts = []
        if 'description' in func:
            comment_parts.append(func['description'])
        if 'size' in func:
            comment_parts.append(f"({func['size']}B)")
        if 'notes' in func:
            comment_parts.append(func['notes'])
        
        if comment_parts:
            comments[addr] = ". ".join(comment_parts)
    
    added_count = 0
    for addr, comment in comments.items():
        if idc.set_func_cmt(addr, comment, 0):  # 0 = regular comment
            func_name = idc.get_func_name(addr)
            print(f"✓ Added comment to {func_name}")
            added_count += 1
        else:
            print(f"✗ Failed to add comment to {addr:#08x}")
    
    print(f"\nComments added: {added_count}/{len(comments)}")
    print("="*80)
    
    return added_count

def save_naming_report(functions, renamed, skipped, failed):
    """Save report of what was renamed."""
    output_file = Path(__file__).parent.parent / "ida_naming_report.json"
    
    report = {
        "timestamp": "2026-11-14",
        "total_functions": len(functions),
        "renamed": renamed,
        "already_correct": skipped,
        "failed": failed,
        "functions": {
            hex(addr): {
                "name": name,
                "current_name": idc.get_func_name(addr),
                "exists": idaapi.get_func(addr) is not None
            }
            for addr, name in functions.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {output_file}")
    return output_file

def main():
    print("="*80)
    print("APPLYING KNOWN NAMES TO IDA DATABASE")
    print("Synchronizing IDA with documented knowledge from YAML registry")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Load functions from YAML
    functions, yaml_data = load_functions_from_yaml()
    if not functions:
        print("ERROR: No functions loaded from YAML. Exiting.")
        idc.qexit(1)
        return
    
    # Apply function names
    renamed, skipped, failed = apply_function_names(functions)
    
    # Add comments from YAML
    comments_added = add_comments(functions, yaml_data)
    
    # Apply data names (TODO)
    # data_renamed, data_skipped, data_failed = apply_data_names(KNOWN_DATA)
    
    # Save report
    report_file = save_naming_report(functions, renamed, skipped, failed)
    
    # Summary
    print("\n" + "="*80)
    print("SYNCHRONIZATION COMPLETE")
    print("="*80)
    print(f"Functions renamed: {renamed}")
    print(f"Comments added: {comments_added}")
    print(f"Failed: {failed}")
    print(f"Report: {report_file}")
    print("="*80)
    print("\nIMPORTANT: Re-run this script as we learn more function names!")
    print("Add new discoveries to registry/functions.yaml")
    print("="*80)
    
    # Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
