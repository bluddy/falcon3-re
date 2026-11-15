#!/usr/bin/env python3
"""
Add new globals discovered during the expansion session.
"""

# New globals discovered from function analysis
NEW_GLOBALS = """
  # ===========================================================================
  # HUD SYSTEM (additional from HUD expansion)
  # ===========================================================================
  
  - address: 0x102
    name: hud_panel_transform_matrix
    size: 32
    type: matrix
    doc: Transform matrix for HUD panel coordinate transformations
    source: hud_expansion_2026-11-15
    
  - address: 0x1084C
    name: hud_timer_state_flags
    size: 2
    type: word
    doc: HUD timer state flags (blink, color, threshold warnings)
    source: hud_expansion_2026-11-15
    
  - address: 0x22220
    name: hud_brightness_level
    size: 1
    type: byte
    doc: Current HUD brightness level (0-100)
    source: hud_expansion_2026-11-15
    
  - address: 0x254A1
    name: hud_color_palette_index
    size: 1
    type: byte
    doc: Current HUD color palette index
    source: hud_expansion_2026-11-15
  
  # ===========================================================================
  # MENU / UI SYSTEM (from campaign/menu expansion)
  # ===========================================================================
  
  - address: 0x10844
    name: menu_mode_state_word
    size: 2
    type: word
    doc: Menu mode state word (0/1/2 classification)
    source: campaign_expansion_2026-11-15
    
  - address: 0x10000
    name: mouse_buttons_gate_flag
    size: 1
    type: byte
    doc: Mouse button enable gate flag (sign-extended), used by cs:10000 functions
    source: old_registry
    
  - address: 0x22124
    name: menu_cursor_x_position
    size: 2
    type: word
    doc: Current menu cursor X position
    source: menu_expansion_2026-11-15
    
  - address: 0x22126
    name: menu_cursor_y_position
    size: 2
    type: word
    doc: Current menu cursor Y position
    source: menu_expansion_2026-11-15
    
  - address: 0x26400
    name: menu_selection_index
    size: 2
    type: word
    doc: Current menu selection index (list/option)
    source: menu_expansion_2026-11-15
  
  # ===========================================================================
  # LOADOUT SYSTEM (from loadout screen analysis)
  # ===========================================================================
  
  - address: 0x5000
    name: loadout_total_weight
    size: 4
    type: dword
    doc: Total loadout weight in pounds
    source: campaign_expansion_2026-11-15
    
  - address: 0x5004
    name: loadout_fuel_capacity
    size: 2
    type: word
    doc: Current fuel capacity after weight adjustment
    source: campaign_expansion_2026-11-15
    
  - address: 0x5006
    name: loadout_drag_coefficient
    size: 2
    type: word
    doc: Aerodynamic drag coefficient from current loadout
    source: campaign_expansion_2026-11-15
    
  - address: 0x5010
    name: loadout_hardpoint_config
    size: 18
    type: array[9]
    doc: 9 hardpoint configurations (2 bytes each)
    source: campaign_expansion_2026-11-15
    
  - address: 0x5030
    name: loadout_weapon_supply
    size: 32
    type: array[16]
    doc: Weapon supply counts (2 bytes per weapon type)
    source: campaign_expansion_2026-11-15
  
  # ===========================================================================
  # PHYSICS SYSTEM (from physics expansion)
  # ===========================================================================
  
  - address: 0x3896
    name: physics_integration_state
    size: 64
    type: struct
    doc: Physics integration engine state (velocities, forces, accelerations)
    source: physics_expansion_2026-11-15
    
  - address: 0x3850
    name: physics_basis_matrix
    size: 18
    type: matrix[3x3]
    doc: 3×3 basis matrix for physics calculations
    source: physics_expansion_2026-11-15
    
  - address: 0x11C2C
    name: physics_kinematics_delta
    size: 26
    type: struct
    doc: Kinematics delta record for frame-to-frame changes
    source: physics_expansion_2026-11-15
    
  - address: 0x11C8E
    name: physics_velocity_components
    size: 12
    type: array[3]
    doc: Velocity vector components (X, Y, Z as 4-byte values)
    source: physics_expansion_2026-11-15
  
  # ===========================================================================
  # TERRAIN SYSTEM (additional from terrain expansion)
  # ===========================================================================
  
  - address: 0x11CC8
    name: terrain_current_height
    size: 2
    type: word
    doc: Current terrain height at player position
    source: terrain_expansion_2026-11-15
    
  - address: 0x11CF8
    name: terrain_position_delta
    size: 4
    type: dword
    doc: Position delta for terrain advancement
    source: terrain_expansion_2026-11-15
    
  - address: 0x11CFC
    name: terrain_tile_coordinates
    size: 4
    type: struct
    doc: Current terrain tile coordinates (X, Y)
    source: terrain_expansion_2026-11-15
    
  - address: 0x11D04
    name: terrain_matrix_current
    size: 32
    type: matrix
    doc: Current terrain transformation matrix
    source: terrain_expansion_2026-11-15
  
  # ===========================================================================
  # VIEW SYSTEM (from view seed analysis)
  # ===========================================================================
  
  - address: 0x1F702
    name: view_scroll_state
    size: 8
    type: struct
    doc: View scroll state (rotation, position)
    source: view_seeds_2026-11-15
    
  - address: 0x1F6DA
    name: view_extent_quad
    size: 16
    type: struct
    doc: View extent quadrilateral bounds
    source: view_seeds_2026-11-15
    
  - address: 0x1F73D
    name: view_projection_setup
    size: 32
    type: struct
    doc: View projection setup parameters
    source: view_seeds_2026-11-15
    
  - address: 0x3896
    name: view_projection_matrix
    size: 24
    type: matrix[3x4]
    doc: Current view projection matrix
    source: view_seeds_2026-11-15
    
  - address: 0x28E26
    name: view_bounds_shadow
    size: 16
    type: struct
    doc: Shadow copy of view bounds for restoration
    source: view_seeds_2026-11-15
  
  # ===========================================================================
  # FONT SYSTEM (from UI expansion)
  # ===========================================================================
  
  - address: 0x14E771
    name: font_picfont_idx_filename
    size: 14
    type: string
    doc: "PICFONT.IDX" filename string
    source: campaign_expansion_2026-11-15
    
  - address: 0x14E781
    name: font_picfont_dat_filename
    size: 14
    type: string
    doc: "PICFONT.DAT" filename string
    source: campaign_expansion_2026-11-15
    
  - address: 0x151AC4
    name: font_madfont_idx_filename
    size: 13
    type: string
    doc: "madfont.idx" filename string
    source: campaign_expansion_2026-11-15
    
  - address: 0x151AD4
    name: font_madfont_dat_filename
    size: 13
    type: string
    doc: "madfont.dat" filename string
    source: campaign_expansion_2026-11-15

"""

def add_globals_to_registry():
    """Add new globals to registry by appending to the file."""
    
    # Read current registry
    with open('../../registry/globals.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count current globals
    import_count = content.count('\n  - address:')
    print(f"Current globals count: {import_count}")
    
    # Append new globals
    new_content = content + NEW_GLOBALS
    
    # Write back
    with open('../../registry/globals.yaml', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Verify
    with open('../../registry/globals.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    new_count = content.count('\n  - address:')
    print(f"New globals count: {new_count}")
    print(f"Increase: +{new_count - import_count}")
    
    print(f"\nAdded global categories:")
    print(f"  • HUD System: 4 globals (timer state, brightness, colors)")
    print(f"  • Menu/UI System: 5 globals (cursor, selection, mode)")
    print(f"  • Loadout System: 5 globals (weight, fuel, drag, hardpoints)")
    print(f"  • Physics System: 4 globals (integration state, matrices)")
    print(f"  • Terrain System: 4 globals (height, delta, tile, matrix)")
    print(f"  • View System: 5 globals (scroll, extent, projection)")
    print(f"  • Font System: 4 globals (filename strings)")
    
    print(f"\nTotal: {new_count - import_count} new globals documented")

if __name__ == '__main__':
    add_globals_to_registry()
