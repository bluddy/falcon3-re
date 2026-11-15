#!/usr/bin/env python3
"""
Add the 6 new terrain functions to the registry.
"""

# The 6 new terrain functions with analysis-based names
NEW_FUNCTIONS = [
    {
        'address': '0x028ca1',
        'name': 'terrain_anim_line_flag_get',
        'system': 'terrain',
        'size': 3,
        'doc': '3B tiny helper, 3 callers, called by terrain_anim_line_object_draw. Likely reads a flag or small value for line animation. conf: medium',
        'source': 'terrain_expansion_2026-11-15 (callee analysis)'
    },
    {
        'address': '0x02bea1',
        'name': 'terrain_frame_counter_inc',
        'system': 'terrain',
        'size': 8,
        'doc': '8B simple helper, 2 callers, called by terrain_frame_update_driver. Likely increments frame counter or updates frame state. conf: medium',
        'source': 'terrain_expansion_2026-11-15 (callee analysis)'
    },
    {
        'address': '0x04f964',
        'name': 'terrain_vm_region_validate',
        'system': 'terrain',
        'size': 207,
        'doc': '207B complex function, 1 caller (terrain_vm_flag_gate), 15 comparisons. Validates or processes video memory regions for terrain rendering. conf: medium',
        'source': 'terrain_expansion_2026-11-15 (callee analysis)'
    },
    {
        'address': '0x04fb1c',
        'name': 'terrain_vm_buffer_index_calc',
        'system': 'terrain',
        'size': 23,
        'doc': '23B helper, 2 callers (terrain_vm_buffer_decay, terrain_vm_sweep_kick), 2 comparisons. Calculates buffer index or pointer for VM operations. conf: medium',
        'source': 'terrain_expansion_2026-11-15 (callee analysis)'
    },
    {
        'address': '0x04fd82',
        'name': 'terrain_vm_sample_offset_calc',
        'system': 'terrain',
        'size': 11,
        'doc': '11B tiny helper, 1 caller (terrain_vm_sweep_sample), 0 comparisons. Calculates sample offset for VM sweep operations. conf: medium',
        'source': 'terrain_expansion_2026-11-15 (callee analysis)'
    },
    {
        'address': '0x04fdb3',
        'name': 'terrain_vm_entry_resolve',
        'system': 'terrain',
        'size': 79,
        'doc': '79B medium function, 1 caller (terrain_vm_entry_lookup), 2 comparisons. Resolves or fetches video memory entry for terrain system. conf: medium',
        'source': 'terrain_expansion_2026-11-15 (callee analysis)'
    },
]

def add_functions_to_registry():
    """Add new functions to registry by appending to the file."""
    
    # Read current registry
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check how many we have now
    import_count = content.count('\n  - address:')
    print(f"Current function count: {import_count}")
    
    # Format new entries
    entries = []
    entries.append("\n  # TERRAIN SYSTEM EXPANSION - 2026-11-15")
    
    for func in NEW_FUNCTIONS:
        entry = f"""  - address: {func['address']}
    name: {func['name']}
    system: {func['system']}
    size: {func['size']}
    doc: '{func['doc']}'
    source: {func['source']}"""
        entries.append(entry)
    
    new_content = content + '\n'.join(entries) + '\n'
    
    # Write back
    with open('../../registry/functions.yaml', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\nAdded {len(NEW_FUNCTIONS)} new terrain functions")
    
    # Verify
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New function count: {new_count}")
    print(f"Increase: +{new_count - import_count}")

if __name__ == '__main__':
    add_functions_to_registry()
