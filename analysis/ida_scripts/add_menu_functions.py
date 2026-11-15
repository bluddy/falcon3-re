#!/usr/bin/env python3
"""
Add the top 20 new menu functions to the registry.
Skip functions already named in previous expansions.
"""

# The top 20 new menu functions (excluding already-named ones)
NEW_FUNCTIONS = [
    {
        'address': '0x161b10',
        'name': 'menu_loadout_data_engine',
        'system': 'menu',
        'size': 1423,
        'doc': '1423B massive engine, 28 callers (ui_loadout_drag_weight_calc, ui_loadout_supply_check, ui_loadout_hardpoint_manager), 45 comparisons. Core loadout data management engine. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x163d33',
        'name': 'menu_loadout_weapon_data_get',
        'system': 'menu',
        'size': 138,
        'doc': '138B accessor, 8 callers (ui_loadout_pylon_config, ui_loadout_stores_calculator), 0 comparisons. Gets weapon data for loadout screen. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x06e43b',
        'name': 'menu_state_buffer_allocate',
        'system': 'menu',
        'size': 133,
        'doc': '133B allocator, 1 caller (menu_state_snapshot_load), 0 comparisons. Allocates buffer for menu state snapshot. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x163fdb',
        'name': 'menu_loadout_weight_table_lookup',
        'system': 'menu',
        'size': 127,
        'doc': '127B lookup, 2 callers (ui_loadout_drag_weight_calc, ui_loadout_supply_check), 0 comparisons. Looks up weapon weight from table. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x163dbd',
        'name': 'menu_loadout_hardpoint_data_get',
        'system': 'menu',
        'size': 116,
        'doc': '116B accessor, 6 callers (ui_loadout_drag_weight_calc, ui_loadout_supply_check, ui_loadout_hardpoint_manager), 0 comparisons. Gets hardpoint configuration data. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x138f9c',
        'name': 'menu_field_offset_calculate',
        'system': 'menu',
        'size': 84,
        'doc': '84B utility, 119 callers (ui_menu_transition_animate), 8 comparisons. Calculates field offsets for menu structures - HIGHEST CALLER COUNT IN MENU SYSTEM! conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x13d633',
        'name': 'menu_record_field_copy',
        'system': 'menu',
        'size': 84,
        'doc': '84B copier, 18 callers (ui_menu_panel_initialize, ui_loadout_slot_record_fill, menu_pending_task_step), 4 comparisons. Copies field data between menu records. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x138e1d',
        'name': 'menu_loadout_config_validate',
        'system': 'menu',
        'size': 77,
        'doc': '77B validator, 14 callers (ui_loadout_menu_controller), 11 comparisons. Validates loadout configuration changes. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x163c88',
        'name': 'menu_weapon_compatibility_check',
        'system': 'menu',
        'size': 69,
        'doc': '69B checker, 3 callers (ui_loadout_weapon_selector), 0 comparisons. Checks weapon-hardpoint compatibility. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x12c412',
        'name': 'menu_event_key_mapper',
        'system': 'menu',
        'size': 66,
        'doc': '66B mapper, 1 caller (menu_event_dispatch), 1 comparison. Maps keyboard events to menu actions. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x127ed2',
        'name': 'menu_panel_background_draw',
        'system': 'menu',
        'size': 45,
        'doc': '45B drawer, 4 callers (ui_menu_panel_initialize), 0 comparisons. Draws menu panel background. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x130a2f',
        'name': 'menu_cursor_position_set',
        'system': 'menu',
        'size': 42,
        'doc': '42B setter, 33 callers, 4 comparisons. Sets menu cursor position. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x04aae2',
        'name': 'menu_3d_model_frame_step',
        'system': 'menu',
        'size': 36,
        'doc': '36B stepper, 7 callers, 0 comparisons. Steps 3D model animation frame (aircraft selection). conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x137f70',
        'name': 'menu_list_index_clamp',
        'system': 'menu',
        'size': 35,
        'doc': '35B clamper, 12 callers, 0 comparisons. Clamps list index to valid range. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x16394a',
        'name': 'menu_loadout_supply_decrement',
        'system': 'menu',
        'size': 19,
        'doc': '19B decrementer, 16 callers, 2 comparisons. Decrements weapon supply count when assigned to loadout. conf: high',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x12fa41',
        'name': 'menu_field_highlight_toggle',
        'system': 'menu',
        'size': 17,
        'doc': '17B toggler, 3 callers, 0 comparisons. Toggles field highlight state. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x066b41',
        'name': 'menu_button_state_read',
        'system': 'menu',
        'size': 15,
        'doc': '15B reader, 2 callers, 0 comparisons. Reads button/key state for menu input. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x066c65',
        'name': 'menu_selection_index_get',
        'system': 'menu',
        'size': 14,
        'doc': '14B accessor, 4 callers, 0 comparisons. Gets current menu selection index. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x138630',
        'name': 'menu_row_count_get',
        'system': 'menu',
        'size': 13,
        'doc': '13B accessor, 2 callers, 0 comparisons. Gets row count for menu list. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
    },
    {
        'address': '0x1381ca',
        'name': 'menu_page_flag_check',
        'system': 'menu',
        'size': 11,
        'doc': '11B checker, 8 callers, 0 comparisons. Checks menu page status flags. conf: medium',
        'source': 'menu_expansion_2026-11-15 (callee analysis from 23 menu seeds)'
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
    entries.append("\n  # MENU SYSTEM EXPANSION - 2026-11-15")
    entries.append("  # War Room, Mission Planning, Menu Navigation")
    
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
    
    print(f"\nAdded {len(NEW_FUNCTIONS)} new menu functions")
    
    # Verify
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New function count: {new_count}")
    print(f"Increase: +{new_count - import_count}")
    
    # Show what was added
    print(f"\nAdded menu functions:")
    for i, func in enumerate(NEW_FUNCTIONS, 1):
        print(f"  {i:2}. {func['name']:45} ({func['size']:4}B)")
    
    # Show key discoveries
    print(f"\nKey discoveries:")
    print(f"  • menu_field_offset_calculate: 119 callers (HIGHEST in menu system!)")
    print(f"  • menu_loadout_data_engine: 1423B (massive core engine)")
    print(f"  • menu_cursor_position_set: 33 callers")
    print(f"  • menu_loadout_supply_decrement: 16 callers")
    print(f"  • menu_loadout_config_validate: 14 callers")

if __name__ == '__main__':
    add_functions_to_registry()
