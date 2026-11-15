"""
Add new menu system functions discovered from call-graph analysis (round 2).
Updates registry/functions.yaml
"""

import yaml
import sys

def add_menu_functions():
    """Add 20 new menu functions to registry."""
    
    registry_file = r'c:\Users\ybarnoy\projects\falcon3\registry\functions.yaml'
    
    # Load existing registry
    with open(registry_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    existing_addrs = {f['address'] for f in data['functions']}
    
    # New menu functions discovered from call-graph analysis
    # Format: (address, name, size, comparisons, callers, description)
    new_functions = [
        # Top priority: High caller count = fundamental utilities
        (0x161b10, 'menu_loadout_data_engine', 1423, 45, 28,
         'Core loadout menu data engine. Processes weapon/hardpoint configurations, validates loadouts'),
        
        (0x12af71, 'menu_bounds_check_clamp', 144, 12, 6,
         'Menu value bounds checking and clamping. Ensures indices/values stay within valid ranges'),
        
        # Data accessors (0 comparisons = simple getters)
        (0x2c3a1, 'menu_field_data_ptr_get', 8, 0, 5,
         'Get pointer to menu field data structure. Simple 8B accessor'),
        
        (0x2bded, 'menu_state_ptr_get', 8, 0, 5,
         'Get pointer to menu state structure. Simple 8B accessor'),
        
        (0x12fa52, 'menu_field_highlight_clear', 17, 0, 3,
         'Clear menu field highlighting. Paired with menu_field_highlight_toggle'),
        
        # Medium complexity coordinators
        (0x12a9f7, 'menu_input_state_processor', 1402, 41, 2,
         'Large input state processor. Handles complex input state transitions, key combinations'),
        
        (0x1295df, 'menu_animation_controller', 529, 4, 2,
         'Menu animation controller. Manages menu transition animations, timing'),
        
        (0x2c397, 'menu_config_ptr_get', 8, 0, 2,
         'Get pointer to menu configuration. Simple 8B accessor'),
        
        (0x2bed3, 'menu_display_ptr_get', 8, 0, 2,
         'Get pointer to menu display structure. Simple 8B accessor'),
        
        # System integration
        (0x132276, 'menu_graphics_buffer_setup', 594, 11, 1,
         'Menu graphics buffer setup and initialization. Allocates/configures display buffers'),
        
        (0x12ca0d, 'menu_input_validation_engine', 226, 12, 1,
         'Input validation engine. Validates user input against field constraints'),
        
        # More 8B accessors (all 8B, 0 comparisons, single callers)
        (0x2c33d, 'menu_panel_ptr_get', 8, 0, 1,
         'Get pointer to menu panel structure. Simple 8B accessor'),
        
        (0x2c347, 'menu_layout_ptr_get', 8, 0, 1,
         'Get pointer to menu layout structure. Simple 8B accessor'),
        
        (0x2c379, 'menu_font_ptr_get', 8, 0, 1,
         'Get pointer to menu font structure. Simple 8B accessor'),
        
        (0x2c383, 'menu_color_ptr_get', 8, 0, 1,
         'Get pointer to menu color palette. Simple 8B accessor'),
        
        (0x2c38d, 'menu_sprite_ptr_get', 8, 0, 1,
         'Get pointer to menu sprite data. Simple 8B accessor'),
        
        (0x2c3ab, 'menu_animation_ptr_get', 8, 0, 1,
         'Get pointer to menu animation data. Simple 8B accessor'),
        
        (0x2c2ed, 'menu_sound_ptr_get', 8, 0, 1,
         'Get pointer to menu sound configuration. Simple 8B accessor'),
    ]
    
    # Add functions
    added_count = 0
    for addr_int, name, size, comps, callers, desc in new_functions:
        addr = f'0x{addr_int:06x}'
        
        if addr in existing_addrs:
            print(f"SKIP: {addr} {name:40s} (already in registry)")
            continue
        
        new_entry = {
            'address': addr,
            'name': name,
            'system': 'menu',
            'size': size,
            'doc': desc,
            'source': f'IDA call-graph from menu seeds (size={size}B, comparisons={comps}, callers={callers})'
        }
        
        data['functions'].append(new_entry)
        added_count += 1
        print(f"ADD:  {addr} {name:40s} ({size:4d}B, {comps:2d} cmps, {callers:3d} callers)")
    
    # Sort by address (filter out empty entries first, handle both string and int addresses)
    data['functions'] = [f for f in data['functions'] if f]  # Remove empty entries
    data['functions'].sort(key=lambda x: int(x['address'], 16) if isinstance(x['address'], str) else x['address'])
    
    # Update header
    import datetime
    
    # Write back
    with open(registry_file, 'w', encoding='utf-8') as f:
        # Write header comment
        f.write('# Falcon 3.0 Function Registry\n')
        f.write('#\n')
        f.write(f'# UPDATED: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'# Total functions: {len(data["functions"])}\n')  # Correct count
        f.write('#\n')
        f.write('# Schema:\n')
        f.write('#   address: hex address (e.g., 0x11450)\n')
        f.write('#   name: descriptive function name\n')
        f.write('#   system: which system it belongs to\n')
        f.write('#   size: size in bytes (optional)\n')
        f.write('#   doc: description (optional)\n')
        f.write('#   source: where we learned about it (optional)\n')
        f.write('\n')
        
        # Write schema version
        f.write(f'schema: {data["schema"]}\n\n')
        
        # Write functions
        f.write('functions:\n')
        for func in data['functions']:
            f.write(f'\n  - address: {func["address"]}\n')
            f.write(f'    name: {func["name"]}\n')
            if 'system' in func:
                f.write(f'    system: {func["system"]}\n')
            if 'size' in func:
                f.write(f'    size: {func["size"]}\n')
            if 'doc' in func:
                # Escape quotes in doc
                doc = func['doc'].replace("'", "''")
                f.write(f"    doc: '{doc}'\n")
            if 'source' in func:
                source = func['source'].replace("'", "''")
                f.write(f"    source: '{source}'\n")
    
    print(f'\n[+] Added {added_count} new menu functions')
    print(f'[+] Total functions: {len(data["functions"])}')
    print(f'[+] Updated: {registry_file}')

if __name__ == '__main__':
    add_menu_functions()
