#!/usr/bin/env python3
"""
Add top 10 new AI functions to the registry.
Skip already-named functions (sub_3F274, sub_40CB7 were named in other systems).
"""

NEW_FUNCTIONS = [
    {
        'address': '0x03eba5',
        'name': 'ai_behavior_decision_tree',
        'system': 'ai',
        'size': 814,
        'doc': '814B massive decision tree, 2 callers (ai_state_value_dispatcher), 87 comparisons. Core AI behavior decision engine. conf: high',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x03e2d3',
        'name': 'ai_combat_maneuver_selector',
        'system': 'ai',
        'size': 505,
        'doc': '505B maneuver selector, 1 caller (ai_state_range_check), 43 comparisons. Selects combat maneuvers based on tactical situation. conf: high',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x03e96f',
        'name': 'ai_target_priority_evaluator',
        'system': 'ai',
        'size': 479,
        'doc': '479B evaluator, 2 callers (ai_farobj_flag_check), 34 comparisons. Evaluates and prioritizes targets for engagement. conf: high',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x03fc66',
        'name': 'ai_distance_threshold_check',
        'system': 'ai',
        'size': 123,
        'doc': '123B checker, 6 callers, 16 comparisons. Checks distances against AI engagement thresholds. conf: high',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x04ef4e',
        'name': 'ai_formation_position_calc',
        'system': 'ai',
        'size': 45,
        'doc': '45B calculator, 4 callers, 7 comparisons. Calculates formation position for wingmen. conf: medium',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x040843',
        'name': 'ai_altitude_control_update',
        'system': 'ai',
        'size': 44,
        'doc': '44B updater, 1 caller (ai_entity_terrain_position_update), 3 comparisons. Updates altitude control for AI aircraft. conf: medium',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x040bc5',
        'name': 'ai_heading_correction_calc',
        'system': 'ai',
        'size': 41,
        'doc': '41B calculator, 0 callers (orphan), 3 comparisons. Calculates heading correction for waypoint navigation. conf: medium',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x03de4a',
        'name': 'ai_weapon_range_check',
        'system': 'ai',
        'size': 37,
        'doc': '37B checker, 1 caller (weapon_spawn_gate_validate), 6 comparisons. Checks if target is within weapon range. conf: high',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x042957',
        'name': 'ai_state_flag_set',
        'system': 'ai',
        'size': 30,
        'doc': '30B setter, 1 caller (ai_state_flag_validate), 0 comparisons. Sets AI state flags. conf: medium',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x042939',
        'name': 'ai_state_flag_clear',
        'system': 'ai',
        'size': 30,
        'doc': '30B clearer, 1 caller (ai_state_flag_validate), 0 comparisons. Clears AI state flags. conf: medium',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x04036d',
        'name': 'ai_angle_delta_normalize',
        'system': 'ai',
        'size': 29,
        'doc': '29B normalizer, 3 callers, 0 comparisons. Normalizes angle delta to -180/+180 range. conf: medium',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
    },
    {
        'address': '0x040dc5',
        'name': 'ai_record_offset_get',
        'system': 'ai',
        'size': 21,
        'doc': '21B accessor, 13 callers, 0 comparisons. Gets field offset in AI record structure. conf: high',
        'source': 'ai_expansion_2026-11-15 (callee analysis from 40 ai seeds)'
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
    entries.append("\n  # AI SYSTEM EXPANSION - 2026-11-15")
    entries.append("  # Enemy AI, Combat Maneuvers, Target Selection")
    
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
    
    print(f"\nAdded {len(NEW_FUNCTIONS)} new AI functions")
    
    # Verify
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New function count: {new_count}")
    print(f"Increase: +{new_count - import_count}")
    
    # Show what was added
    print(f"\nAdded AI functions:")
    for i, func in enumerate(NEW_FUNCTIONS, 1):
        print(f"  {i:2}. {func['name']:40} ({func['size']:4}B)")
    
    print(f"\nKey discoveries:")
    print(f"  • ai_behavior_decision_tree: 814B, 87 comparisons (massive!)")
    print(f"  • ai_combat_maneuver_selector: 505B, 43 comparisons")
    print(f"  • ai_target_priority_evaluator: 479B, 34 comparisons")
    print(f"  • ai_record_offset_get: 13 callers (high-use utility)")

if __name__ == '__main__':
    add_functions_to_registry()
