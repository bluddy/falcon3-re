#!/usr/bin/env python3
"""
Add the 8 new flight_physics functions to the registry.
"""

# The 8 new flight_physics functions with analysis-based names
NEW_FUNCTIONS = [
    {
        'address': '0x04113c',
        'name': 'flight_physics_integration_engine',
        'system': 'flight_physics',
        'size': 810,
        'doc': '810B complex physics core, 3 callers (flight_motion_physics_step, flight_motion_accumulate_coordinator), 56 comparisons. Main physics integration engine. conf: high',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x03b618',
        'name': 'flight_kinematics_bounds_check',
        'system': 'flight_physics',
        'size': 45,
        'doc': '45B validation function, 2 callers (flight_kinematics_record_compare, _validate), 5 comparisons. Checks if kinematics values are within acceptable bounds. conf: high',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x03b5bd',
        'name': 'flight_kinematics_delta_calc',
        'system': 'flight_physics',
        'size': 20,
        'doc': '20B helper, 2 callers (kinematics compare/validate), 2 comparisons. Calculates delta between kinematics records. conf: high',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x04179e',
        'name': 'flight_velocity_component_scale',
        'system': 'flight_physics',
        'size': 20,
        'doc': '20B utility, 4 callers (flight_motion_velocity_update), 0 comparisons. Scales velocity vector components. conf: medium',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x03b5b0',
        'name': 'flight_kinematics_field_get',
        'system': 'flight_physics',
        'size': 13,
        'doc': '13B accessor, 2 callers (kinematics compare/validate), 0 comparisons. Reads a field from kinematics record. conf: medium',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x02c149',
        'name': 'flight_motion_counter_inc',
        'system': 'flight_physics',
        'size': 8,
        'doc': '8B tiny helper, 1 caller (flight_motion_accumulate_coordinator), 0 comparisons. Increments motion accumulation counter. conf: medium',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x02c0db',
        'name': 'flight_target_slot_index_get',
        'system': 'flight_physics',
        'size': 8,
        'doc': '8B accessor, 1 caller (farobj_slot_target_bind), 0 comparisons. Gets target slot index for entity targeting. conf: medium',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
    },
    {
        'address': '0x03480a',
        'name': 'flight_motion_flag_clear',
        'system': 'flight_physics',
        'size': 5,
        'doc': '5B trivial helper, 1 caller (flight_motion_accumulate_coordinator), 0 comparisons. Clears motion processing flag. conf: medium',
        'source': 'physics_expansion_2026-11-15 (callee analysis, second pass)'
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
    entries.append("\n  # FLIGHT PHYSICS SYSTEM EXPANSION (SECOND PASS) - 2026-11-15")
    
    for func in NEW_FUNCTIONS:
        entry = f"""  - address: {func['address']}
    name: {func['name']}
    system: {func['system']}
    size: {func['size']}
    doc: '{func['doc']}'
    source: '{func['source']}'"""
        entries.append(entry)
    
    new_content = content + '\n'.join(entries) + '\n'
    
    # Write back
    with open('../../registry/functions.yaml', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\nAdded {len(NEW_FUNCTIONS)} new flight_physics functions")
    
    # Verify
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New function count: {new_count}")
    print(f"Increase: +{new_count - import_count}")
    
    # Show what was added
    print(f"\nAdded functions:")
    for i, func in enumerate(NEW_FUNCTIONS, 1):
        print(f"  {i}. {func['address']}: {func['name']} ({func['size']}B)")

if __name__ == '__main__':
    add_functions_to_registry()
