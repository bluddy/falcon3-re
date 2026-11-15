#!/usr/bin/env python3
"""
Add the top 20 new campaign/UI functions to the registry.
Based on call graph analysis from file_io, ui, menu systems.
"""

# The top 20 new campaign functions with analysis-based names
NEW_FUNCTIONS = [
    {
        'address': '0x12a9f7',
        'name': 'ui_menu_transition_renderer',
        'system': 'ui',
        'size': 1402,
        'doc': '1402B large menu renderer, 2 callers (ui_menu_transition_animate), 41 comparisons. Renders animated menu transitions between screens. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x13667d',
        'name': 'ui_slot_record_handler',
        'system': 'ui',
        'size': 1395,
        'doc': '1395B complex handler, 4 callers (ui_slot_record_init), 52 comparisons. Manages UI slot record data structures for lists/tables. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x128598',
        'name': 'ui_text_render_engine',
        'system': 'ui',
        'size': 1282,
        'doc': '1282B high-use renderer, 25 callers (menu_page_draw_step, ui_slot_record_init, ui_loadout_menu_controller), 61 comparisons. Core text/graphics rendering engine for UI. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x1295df',
        'name': 'ui_menu_frame_loader',
        'system': 'ui',
        'size': 529,
        'doc': '529B loader, 2 callers (ui_menu_frame_enter), 4 comparisons. Loads and initializes menu frame resources. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x1632cd',
        'name': 'ui_loadout_weapon_selector',
        'system': 'menu',
        'size': 517,
        'doc': '517B selector, 1 caller (ui_loadout_menu_frame_scan), 21 comparisons. Weapon selection logic for loadout screen. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x163122',
        'name': 'ui_loadout_hardpoint_manager',
        'system': 'menu',
        'size': 427,
        'doc': '427B manager, 1 caller (ui_loadout_menu_frame_scan), 18 comparisons. Manages weapon hardpoint assignments on loadout screen. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x133adc',
        'name': 'ui_menu_panel_renderer',
        'system': 'ui',
        'size': 249,
        'doc': '249B renderer, 2 callers (ui_menu_panel_initialize), 2 comparisons. Renders menu panel graphics/borders. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x1325db',
        'name': 'ui_loadout_fuel_calculator',
        'system': 'menu',
        'size': 244,
        'doc': '244B calculator, 1 caller (ui_loadout_menu_controller), 7 comparisons. Calculates fuel consumption based on loadout weight. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x13142e',
        'name': 'font_file_parser',
        'system': 'file_io',
        'size': 243,
        'doc': '243B parser, 5 callers (madfont_idx_dat_loader), 9 comparisons. Parses font file format (IDX/DAT). conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x1395fe',
        'name': 'ui_menu_page_layout_engine',
        'system': 'ui',
        'size': 232,
        'doc': '232B layout engine, 5 callers (ui_loadout_menu_controller, ui_menu_page_args_setup, ui_menu_page_setup), 18 comparisons. Calculates menu page layout/positioning. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x136c05',
        'name': 'ui_loadout_validation_check',
        'system': 'menu',
        'size': 214,
        'doc': '214B validator, 3 callers (ui_loadout_menu_controller), 6 comparisons. Validates loadout configuration (weight, balance, compatibility). conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x1365a7',
        'name': 'ui_slot_list_builder',
        'system': 'ui',
        'size': 214,
        'doc': '214B builder, 4 callers (ui_slot_record_init), 10 comparisons. Builds slot-based lists (pilots, weapons, targets). conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x12af71',
        'name': 'ui_animation_step',
        'system': 'ui',
        'size': 144,
        'doc': '144B animator, 6 callers (ui_menu_transition_animate, ui_loadout_menu_controller), 12 comparisons. Steps UI animation frames. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x163674',
        'name': 'ui_loadout_stores_calculator',
        'system': 'menu',
        'size': 144,
        'doc': '144B calculator, 1 caller (ui_loadout_menu_frame_scan), 7 comparisons. Calculates stores weight/balance for loadout. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x130bf0',
        'name': 'ui_coordinate_transform',
        'system': 'ui',
        'size': 144,
        'doc': '144B utility, 30 callers (ui_menu_panel_initialize, ui_loadout_menu_controller), 2 comparisons. Transforms screen/menu coordinates. conf: high',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x04afbd',
        'name': 'ui_sprite_blit',
        'system': 'ui',
        'size': 139,
        'doc': '139B blitter, 1 caller, 12 comparisons. Blits sprites to screen with clipping. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x162f66',
        'name': 'ui_loadout_supply_check',
        'system': 'menu',
        'size': 137,
        'doc': '137B checker, 1 caller (ui_loadout_menu_frame_scan), 5 comparisons. Checks supply availability for loadout selection. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x1635ec',
        'name': 'ui_loadout_pylon_config',
        'system': 'menu',
        'size': 136,
        'doc': '136B configurator, 1 caller (ui_loadout_menu_frame_scan), 6 comparisons. Configures pylon weapon assignments. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x06e43b',
        'name': 'file_buffer_allocator',
        'system': 'file_io',
        'size': 133,
        'doc': '133B allocator, 1 caller, 3 comparisons. Allocates buffers for file I/O operations. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
    },
    {
        'address': '0x162ee2',
        'name': 'ui_loadout_drag_weight_calc',
        'system': 'menu',
        'size': 132,
        'doc': '132B calculator, 1 caller (ui_loadout_menu_frame_scan), 4 comparisons. Calculates aerodynamic drag from loadout. conf: medium',
        'source': 'campaign_expansion_2026-11-15 (callee analysis from file_io/ui/menu)'
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
    entries.append("\n  # CAMPAIGN/UI SYSTEM EXPANSION - 2026-11-15")
    entries.append("  # War Room, Mission Planning, Loadout screens")
    
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
    
    print(f"\nAdded {len(NEW_FUNCTIONS)} new campaign/UI functions")
    
    # Verify
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New function count: {new_count}")
    print(f"Increase: +{new_count - import_count}")
    
    # Show what was added by category
    by_system = {}
    for func in NEW_FUNCTIONS:
        sys = func['system']
        if sys not in by_system:
            by_system[sys] = []
        by_system[sys].append(func)
    
    print(f"\nAdded by system:")
    for system, funcs in sorted(by_system.items()):
        print(f"  {system}: {len(funcs)} functions")
        for func in funcs:
            print(f"    - {func['name']} ({func['size']}B)")

if __name__ == '__main__':
    add_functions_to_registry()
