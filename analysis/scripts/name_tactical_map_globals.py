"""
Name all the unnamed globals discovered during tactical map analysis.
Syncs with IDA and updates registry/naming.yaml.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def main():
    print("=" * 80)
    print("Tactical Map Globals Naming")
    print("=" * 80)
    print()
    
    # Define all the globals we discovered
    globals_to_name = {
        # Map projection pipeline
        'word_594C8': {
            'address': 0x594C8,
            'name': 'map_view_coord_x',
            'type': 'uint16_t',
            'description': 'Map view X coordinate or bound',
            'source': 'map_view_project_pipeline sets this before drawing'
        },
        'word_594CA': {
            'address': 0x594CA,
            'name': 'map_view_bound_width',
            'type': 'uint16_t',
            'description': 'Map view width bound (185 / 0xB9)',
            'source': 'Set to 0xB9 in map_view_project_pipeline'
        },
        'word_594CC': {
            'address': 0x594CC,
            'name': 'map_view_coord_y',
            'type': 'uint16_t',
            'description': 'Map view Y coordinate or bound',
            'source': 'map_view_project_pipeline sets this before drawing'
        },
        'word_594CE': {
            'address': 0x594CE,
            'name': 'map_view_bound_height',
            'type': 'uint16_t',
            'description': 'Map view height bound (191 / 0xBF)',
            'source': 'Set to 0xBF in map_view_project_pipeline'
        },
        
        # Far object system state
        'word_7D0C2': {
            'address': 0x7D0C2,
            'segment': '0x7B0E',
            'name': 'farobj_sort_count_primary',
            'type': 'uint16_t',
            'description': 'Number of objects in primary sort list',
            'source': 'farobj_sort_and_step checks this count'
        },
        'word_7C054': {
            'address': 0x7C054,
            'segment': '0x7B0E',
            'name': 'farobj_sort_count_secondary',
            'type': 'uint16_t',
            'description': 'Number of objects in secondary sort list',
            'source': 'farobj_sort_and_step checks this count'
        },
        
        # Entity rendering state (CS segment variables)
        'byte_1F742': {
            'address': 0x1F742,
            'segment': 'cs',
            'name': 'farobj_render_lod_level',
            'type': 'uint8_t',
            'description': 'Current LOD level for entity rendering',
            'source': 'Set by farobj_record_step during LOD selection'
        },
        'byte_1F743': {
            'address': 0x1F743,
            'segment': 'cs',
            'name': 'farobj_render_scale_shift',
            'type': 'uint8_t',
            'description': 'Bit shift amount for distance scaling',
            'source': 'Used in farobj_record_step coordinate transformation'
        },
        'byte_1F73D': {
            'address': 0x1F73D,
            'segment': 'cs',
            'name': 'farobj_render_visibility_flag',
            'type': 'uint8_t',
            'description': 'Visibility flag (0xFF=visible, 0x00=hidden)',
            'source': 'Set based on entity flags bit 1'
        },
        'state_byte_1f741': {
            'address': 0x1F741,
            'segment': 'cs',
            'name': 'farobj_render_state_flag_20',
            'type': 'uint8_t',
            'description': 'Rendering state flag from entity flags bit 5',
            'source': 'Masked from entity flags & 0x20'
        },
        'byte_1F731': {
            'address': 0x1F731,
            'segment': 'cs',
            'name': 'farobj_render_color_mode_1',
            'type': 'uint8_t',
            'description': 'Color/rendering mode flag 1',
            'source': 'Saved/restored around handler call'
        },
        'byte_1F730': {
            'address': 0x1F730,
            'segment': 'cs',
            'name': 'farobj_render_color_mode_2',
            'type': 'uint8_t',
            'description': 'Color/rendering mode flag 2',
            'source': 'Saved/restored around handler call'
        },
        'byte_1F738': {
            'address': 0x1F738,
            'segment': 'cs',
            'name': 'farobj_render_alternate_color',
            'type': 'uint8_t',
            'description': 'Alternate color flag from entity flags bits 1-2',
            'source': 'Set based on entity flags & 0x06'
        },
        'state_byte_1f739': {
            'address': 0x1F739,
            'segment': 'cs',
            'name': 'farobj_render_rotation_index',
            'type': 'uint8_t',
            'description': 'Rotation index extracted from entity flags bits 3-4',
            'source': '(flags >> 3) & 3'
        },
        'byte_1F732': {
            'address': 0x1F732,
            'segment': 'cs',
            'name': 'farobj_render_force_rotation',
            'type': 'uint8_t',
            'description': 'Force rotation flag (0xFF=force)',
            'source': 'Controls whether rotation_index is calculated'
        },
        'byte_1F75E': {
            'address': 0x1F75E,
            'segment': 'cs',
            'name': 'farobj_coord_shift_amount',
            'type': 'uint8_t',
            'description': 'Coordinate shift amount for scaling',
            'source': 'Used to shift coordinate before handler call'
        },
        'word_25499': {
            'address': 0x25499,
            'segment': 'cs',
            'name': 'farobj_lod_quality_level',
            'type': 'uint16_t',
            'description': 'Graphics quality level for LOD selection (1=low, >1=high)',
            'source': 'Compared to 1 to enable LOD stepping'
        },
        
        # Display data pointers (segment 0x7894)
        'word_7A2F6': {
            'address': 0x7A2F6,
            'segment': '0x7894',
            'name': 'display_waypoint_ptr_seg',
            'type': 'uint16_t',
            'description': 'Waypoint array pointer segment',
            'source': 'Points to waypoint data for display'
        },
        'word_7A2F4': {
            'address': 0x7A2F4,
            'segment': '0x7894',
            'name': 'display_waypoint_ptr_off',
            'type': 'uint16_t',
            'description': 'Waypoint array pointer offset',
            'source': 'Together with seg forms far pointer to 0x4FC2:0x168'
        },
        'word_7A2EA': {
            'address': 0x7A2EA,
            'segment': '0x7894',
            'name': 'display_data_ptr_seg',
            'type': 'uint16_t',
            'description': 'Display data pointer segment',
            'source': 'Used in tactical screen coordinator'
        },
        'word_7A2E8': {
            'address': 0x7A2E8,
            'segment': '0x7894',
            'name': 'display_data_ptr_off',
            'type': 'uint16_t',
            'description': 'Display data pointer offset',
            'source': 'Forms far pointer with segment'
        },
        'word_7A2F2': {
            'address': 0x7A2F2,
            'segment': '0x7894',
            'name': 'display_buffer_handle',
            'type': 'uint16_t',
            'description': 'Display buffer handle or identifier',
            'source': 'Used in waypoint_coordinate_processor'
        },
        
        # Dispatch table
        'off_26426': {
            'address': 0x26426,
            'name': 'farobj_entity_type_handlers',
            'type': 'void (*[28])()',
            'description': 'Dispatch table of 28 entity type drawing handlers',
            'source': 'farobj_record_step calls cs:off_26426[type_index]'
        },
    }
    
    print(f"Identified {len(globals_to_name)} globals to name\n")
    print("=" * 80)
    print("Globals to Name")
    print("=" * 80)
    print()
    
    for old_name, info in sorted(globals_to_name.items()):
        addr = info['address']
        new_name = info['name']
        var_type = info['type']
        desc = info['description']
        
        print(f"{old_name} -> {new_name}")
        print(f"  Address: 0x{addr:X}")
        if 'segment' in info:
            print(f"  Segment: {info['segment']}")
        print(f"  Type: {var_type}")
        print(f"  Description: {desc}")
        print()
    
    # Create IDA naming script
    print("=" * 80)
    print("Generating IDA naming script...")
    print("=" * 80)
    print()
    
    script_lines = [
        '"""',
        'Name tactical map globals discovered during analysis.',
        'Generated by name_tactical_map_globals.py',
        '"""',
        '',
        'import idc',
        'import idaapi',
        '',
        'def main():',
        '    print("Naming tactical map globals...")',
        '    print()',
        '    ',
        '    named_count = 0',
        '    ',
    ]
    
    for old_name, info in sorted(globals_to_name.items()):
        addr = info['address']
        new_name = info['name']
        desc = info['description']
        
        # Add comment
        script_lines.append(f'    # {old_name} -> {new_name}')
        script_lines.append(f'    # {desc}')
        script_lines.append(f'    addr = 0x{addr:X}')
        script_lines.append(f'    idc.set_name(addr, "{new_name}", idc.SN_NOWARN)')
        script_lines.append(f'    idc.set_cmt(addr, "{desc}", 0)')
        script_lines.append(f'    print(f"Named 0x{{addr:X}}: {new_name}")')
        script_lines.append(f'    named_count += 1')
        script_lines.append('    ')
    
    script_lines.extend([
        '    print()',
        '    print(f"OK Named {named_count} globals")',
        '    idc.qexit(0)',
        '    ',
        'if __name__ == "__main__":',
        '    main()',
    ])
    
    script_path = Path(__file__).parent.parent / "ida_scripts" / "name_tactical_map_globals.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(script_lines))
    
    print(f"OK IDA script saved to: {script_path}")
    print()
    
    # Also create a reference document
    doc_lines = [
        '# Tactical Map Global Variables',
        '',
        '**Generated**: 2026-11-15',
        '**Source**: Tactical map rendering analysis',
        '',
        '## Overview',
        '',
        f'This document catalogs {len(globals_to_name)} global variables discovered during tactical map analysis.',
        '',
        '## Variables',
        '',
    ]
    
    # Group by category
    categories = {
        'Map View State': ['map_view_'],
        'Far Object Sorting': ['farobj_sort_'],
        'Entity Rendering State': ['farobj_render_'],
        'Display Pointers': ['display_'],
        'Dispatch Table': ['farobj_entity_type_'],
    }
    
    for category, prefixes in categories.items():
        doc_lines.append(f'### {category}')
        doc_lines.append('')
        
        for old_name, info in sorted(globals_to_name.items()):
            new_name = info['name']
            
            # Check if this variable matches any prefix
            matches = any(new_name.startswith(prefix) for prefix in prefixes)
            if not matches:
                continue
            
            addr = info['address']
            var_type = info['type']
            desc = info['description']
            source = info['source']
            
            doc_lines.append(f'#### {new_name}')
            doc_lines.append('')
            doc_lines.append(f'- **Address**: 0x{addr:X}')
            if 'segment' in info:
                doc_lines.append(f'- **Segment**: {info["segment"]}')
            doc_lines.append(f'- **Type**: `{var_type}`')
            doc_lines.append(f'- **Description**: {desc}')
            doc_lines.append(f'- **Source**: {source}')
            doc_lines.append('')
    
    doc_path = Path(__file__).parent.parent.parent / "docs" / "TACTICAL_MAP_GLOBALS.md"
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(doc_lines))
    
    print(f"OK Documentation saved to: {doc_path}")
    print()
    
    print("=" * 80)
    print("Next Steps")
    print("=" * 80)
    print()
    print("1. Run the IDA naming script:")
    print('   & "C:\\Program Files\\IDA Professional 9.1\\idat.exe" -A \\')
    print('     -S"analysis\\ida_scripts\\name_tactical_map_globals.py" \\')
    print('     "analysis\\ida_falconcd\\FALCONCD.EXE.i64"')
    print()
    print("2. Update registry/naming.yaml with these names")
    print()
    print("3. Verify in IDA that names were applied correctly")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
