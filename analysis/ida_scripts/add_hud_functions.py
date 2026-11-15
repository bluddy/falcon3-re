#!/usr/bin/env python3
"""
Add the top 15 new HUD functions to the registry.
Note: sub_4113C already named as flight_physics_integration_engine, skip it.
"""

# The top 15 new HUD functions (excluding the already-named sub_4113C)
NEW_FUNCTIONS = [
    {
        'address': '0x045074',
        'name': 'hud_state_table_processor',
        'system': 'hud',
        'size': 508,
        'doc': '508B state processor, 1 caller (hud_state_rowtable_step), 24 comparisons. Processes HUD state table rows for display updates. conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x045270',
        'name': 'hud_state_field_renderer',
        'system': 'hud',
        'size': 411,
        'doc': '411B renderer, 1 caller (hud_state_rowtable_step), 9 comparisons. Renders individual HUD state fields/values. conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x04812b',
        'name': 'hud_panel_coordinate_transform',
        'system': 'hud',
        'size': 224,
        'doc': '224B transformer, 1 caller (hud_panel_transform_step), 13 comparisons. Transforms panel coordinates for different HUD modes. conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x047162',
        'name': 'hud_track_strip_builder',
        'system': 'hud',
        'size': 215,
        'doc': '215B builder, 1 caller (hud_track_strip_pipeline), 0 comparisons. Builds HUD track display strips. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x046c72',
        'name': 'hud_rowlist_timer_formatter',
        'system': 'hud',
        'size': 208,
        'doc': '208B formatter, 3 callers (hud_rowlist_timer_step), 5 comparisons. Formats timer values for rowlist display. conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x041075',
        'name': 'hud_data_panel_slot_formatter',
        'system': 'hud',
        'size': 129,
        'doc': '129B formatter, 3 callers (hud_data_panel_gate_draw, hud_data_panel_slot_mgr), 22 comparisons. Formats data for HUD panel slots. conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x046ecf',
        'name': 'hud_track_pipeline_filter',
        'system': 'hud',
        'size': 119,
        'doc': '119B filter, 1 caller (hud_track_strip_pipeline), 4 comparisons. Filters tracks for display pipeline. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x04760f',
        'name': 'hud_panel_scale_calculator',
        'system': 'hud',
        'size': 119,
        'doc': '119B calculator, 1 caller (hud_panel_transform_step), 13 comparisons. Calculates panel scaling factors for different views. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x046fea',
        'name': 'hud_panel_visibility_check',
        'system': 'hud',
        'size': 117,
        'doc': '117B checker, 3 callers (hud_panel_transform_step), 5 comparisons. Checks if HUD panel elements are visible. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x047e43',
        'name': 'hud_timer_value_format',
        'system': 'hud',
        'size': 68,
        'doc': '68B formatter, 1 caller (hud_rowlist_timer_step), 4 comparisons. Formats timer values (MM:SS format). conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x047e87',
        'name': 'hud_timer_blink_control',
        'system': 'hud',
        'size': 63,
        'doc': '63B controller, 1 caller (hud_rowlist_timer_step), 2 comparisons. Controls timer blinking/flashing. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x047e1c',
        'name': 'hud_timer_color_select',
        'system': 'hud',
        'size': 39,
        'doc': '39B selector, 1 caller (hud_rowlist_timer_step), 0 comparisons. Selects timer color based on state. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x047df5',
        'name': 'hud_timer_threshold_check',
        'system': 'hud',
        'size': 39,
        'doc': '39B checker, 2 callers (hud_rowlist_timer_step), 6 comparisons. Checks timer against thresholds for warnings. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x0128ab',
        'name': 'hud_data_value_clamp',
        'system': 'hud',
        'size': 34,
        'doc': '34B clamper, 1 caller (hud_data_panel_draw), 0 comparisons. Clamps HUD data values to valid ranges. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x02fbe9',
        'name': 'hud_angle_normalize',
        'system': 'hud',
        'size': 20,
        'doc': '20B normalizer, 1 caller, 0 comparisons. Normalizes angles for HUD display (0-360). conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x03f274',
        'name': 'hud_digit_extract',
        'system': 'hud',
        'size': 19,
        'doc': '19B utility, 9 callers, 0 comparisons. Extracts individual digits from numbers for display. conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x040cb7',
        'name': 'hud_font_glyph_get',
        'system': 'hud',
        'size': 14,
        'doc': '14B accessor, 69 callers, 0 comparisons. Gets font glyph for character rendering (high-use utility). conf: high',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x02c031',
        'name': 'hud_color_index_get',
        'system': 'hud',
        'size': 10,
        'doc': '10B accessor, 3 callers, 0 comparisons. Gets color palette index for HUD elements. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
    },
    {
        'address': '0x02c1f3',
        'name': 'hud_brightness_scale',
        'system': 'hud',
        'size': 8,
        'doc': '8B scaler, 1 caller, 0 comparisons. Scales HUD brightness level. conf: medium',
        'source': 'hud_expansion_2026-11-15 (callee analysis from 45 hud seeds)'
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
    entries.append("\n  # HUD SYSTEM EXPANSION - 2026-11-15")
    entries.append("  # Heads-Up Display rendering, state management, timers")
    
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
    
    print(f"\nAdded {len(NEW_FUNCTIONS)} new HUD functions")
    
    # Verify
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New function count: {new_count}")
    print(f"Increase: +{new_count - import_count}")
    
    # Show what was added
    print(f"\nAdded HUD functions:")
    for i, func in enumerate(NEW_FUNCTIONS, 1):
        print(f"  {i:2}. {func['name']:40} ({func['size']:3}B)")
    
    # Show key discoveries
    print(f"\nKey discoveries:")
    print(f"  • hud_font_glyph_get: 69 callers (highest use!)")
    print(f"  • hud_state_table_processor: 508B (main state processor)")
    print(f"  • Complete timer system: 5 functions (format, blink, color, threshold, brightness)")

if __name__ == '__main__':
    add_functions_to_registry()
