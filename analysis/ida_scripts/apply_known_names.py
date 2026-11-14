"""
Apply all known function names, structures, and globals to IDA database.

This script synchronizes IDA with our documented knowledge from analysis.
CRITICAL: Run this regularly as we learn more, or we'll lose our knowledge!

Based on:
- FILE_IO_ANALYSIS.md
- MENU_SYSTEM_CODE_STRUCTURE.md
- AI_SYSTEM_STATUS.md
- And all other analysis documents
"""

import idc
import idaapi
import json
from pathlib import Path

# All known function names from our analysis
# CRITICAL: Keep this updated as we learn more!
KNOWN_FUNCTIONS = {
    # ===================================================================
    # FILE I/O SYSTEM (from FILE_IO_ANALYSIS.md)
    # ===================================================================
    0x226BD: "dos_file_open",           # DOS INT 21h AH=3D open file wrapper
    0x226E4: "dos_file_close",          # DOS INT 21h AH=3E close file wrapper
    0x226F5: "dos_file_read",           # DOS INT 21h AH=3F read from file
    0x2271F: "dos_file_write",          # DOS INT 21h AH=40 write to file
    0x2274D: "dos_file_lseek",          # DOS INT 21h AH=42 seek to offset
    
    # .IDX/.DAT Loaders (from FILE_IO_ANALYSIS.md)
    0x1297F0: "picfont_idx_dat_loader",     # PICFONT.IDX/.DAT loader (RENAMED ✓)
    0x1397CE: "madfont_idx_dat_loader",     # madfont.idx/.dat loader
    0x6A651: "squad_campaign_file_loader",  # SQUAD campaign file loader (46 refs!)
    0x1779A6: "harpoon_missile_dat_loader", # HARPOON.DAT missile loader
    
    # Overlay system (from FILE_IO_ANALYSIS.md)
    0x2AEA9: "overlay_file_open",   # Overlay file opener
    0x2AC4C: "overlay_segment_load", # Overlay segment loader
    
    # ===================================================================
    # MENU SYSTEM (from MENU_SYSTEM_CODE_STRUCTURE.md)
    # ===================================================================
    0x683C5: "ui_loadout_menu_controller",  # Loadout menu controller hub (4169 bytes)
    0x66E62: "ui_menu_panel_initialize",    # Common menu panel initialization
    0x6A5BD: "ui_menu_page_setup",          # Menu page setup routine
    0x6798C: "ui_loadout_slot_record_fill", # Fill aircraft loadout record
    0x67BAF: "ui_menu_transition_animate",  # Menu transition animation step
    0x4AEC4: "farobj_3d_model_rotate_step", # 3D model rotation for menu preview
    
    # ===================================================================
    # AI SYSTEM (from AI_SYSTEM_STATUS.md, docs/architecture/ai.md)
    # ===================================================================
    0x3CE92: "ai_entity_behavior_dispatcher",   # Master behavior dispatcher by type (2580B)
    0x495DF: "ai_context_batch_processor",      # Process 40 AI contexts (24B each, 1165B)
    0x3CFAA: "ai_behavior_state_machine",       # Behavior state machine entry
    0x3D180: "ai_target_tracking_update",       # Target tracking sequence update
    0x3D1C5: "ai_behavior_mirror_to_target",    # Target sync for missile tracking
    0x3DC55: "ai_weapon_spawn_gate_check",      # Weapon spawn validation (friendly fire)
    0x307A5: "ai_entity_data_load_prepare",     # Load and prepare entity data for AI
    
    # ===================================================================
    # WEAPONS SYSTEM (from WEAPONS_FINAL_ASSESSMENT.md)
    # ===================================================================
    0x4C19E: "weapon_type_initialize_dispatch", # Initialize weapon by type (AIM-9/120, 2500B)
    0x2EAA7: "damage_event_dispatch_handler",   # Damage event dispatcher by entity type (190B)
    0x32453: "entity_world_coord_transform",    # World coordinate transform (216B)
    0x32393: "explosion_visual_effect_update",  # Explosion graphics frame update (192B)
    0x327BE: "explosion_sound_effect_trigger",  # Explosion audio handler (499B, 24 entries)
    
    # ===================================================================
    # TERRAIN SYSTEM (from TERRAIN_SYSTEM_100_PERCENT_COMPLETE.md)
    # ===================================================================
    0x14956: "terrain_tile_heightmap_sample",   # Bilinear heightmap sampling (114B)
    0x361FC: "terrain_strip_project_to_screen", # 3D terrain strip projection to 2D (331B)
    0x16060: "terrain_strip_sample_and_draw",   # Terrain strip sampling with self-modifying code
    
    # ===================================================================
    # FLIGHT PHYSICS SYSTEM (from docs/architecture/flight_physics.md)
    # ===================================================================
    0x11450: "flight_control_axes_read_normalize",  # Read 4 axes, normalize to ±2048
    0x3099C: "flight_control_axes_write_to_entity", # Write control axes to entity record
    0x3B338: "flight_kinematics_position_step",     # Position integration, 26B kinematics block
    0x49546: "flight_aircraft_slot_cycle_update",   # 40×24B aircraft slot array processor
    0x4CD1D: "flight_entity_motion_accumulate",     # 40-entry motion accumulation (27B stride)
    0x3A3D6: "flight_entity_simulation_frame_step", # Per-entity simulation step (508B)
    0x3E16B: "flight_aerodynamics_force_update",    # Aerodynamic force application to velocity (865B)
    0x38CF3: "flight_aerodynamics_speed_authority", # Speed-dependent control authority (2284B)
    0x1CEA3: "flight_entity_countdown_timers",      # Entity countdown timers update (453B)
    
    # ===================================================================
    # HUD SYSTEM (from HUD_SYSTEM_100_PERCENT_COMPLETE.md)
    # ===================================================================
    0x36785: "hud_readout_render_coordinator",  # Main HUD coordinator (908B, 23 calls)
    0x36B11: "hud_field_value_draw_0c",         # HUD field value display
    0x36C0E: "hud_field_value_draw_14",         # HUD field value display
    0x36CCF: "hud_value_format_and_draw",       # Format and draw HUD value
    0x3708F: "hud_heading_tape_draw",           # Heading tape instrument
    0x35BCE: "hud_draw_chain_step",             # HUD rendering chain step
    0x35971: "hud_cockpit_mode_ratio_dispatch", # Cockpit HUD mode renderer (126B)
    0x25A56: "hud_cockpit_rect_arg_store",      # Cockpit shape drawing (28B)
    0x24DB8: "hud_external_far_callback",       # External view renderer (18B)
    0x263F0: "hud_external_vector_dispatch",    # External vector overlay (6B)
    0x11AE7: "font_glyph_bitmap_render",        # Bitmap font glyph renderer (62B)
    0x11B6A: "font_glyph_atlas_lookup",         # Font atlas character lookup (38B)
    0x28B08: "graphics_line_draw_bresenham",    # Bresenham line drawing (409B)
    0x14200: "graphics_rect_fill_tiled",        # Rectangle fill with 8×8 tiles (106B)
    0x35B2F: "graphics_sprite_offset_dispatch", # Sprite coordinate transform (20B)
    0x24D64: "graphics_pixel_plot_gateway",     # Pixel plotting gateway with shadow (60B)
    0x2D11A: "video_mode_13h_initialize",       # VGA Mode 13h setup (111B)
    0x359B2: "view_cockpit_hud_initialize",     # Cockpit view initialization (381B)
    0x35B43: "view_external_limits_install",    # External view initialization (139B)
    
    # ===================================================================
    # GRAPHICS/VIDEO SYSTEM
    # ===================================================================
    0x4F271: "vga_dac_palette_upload",      # VGA DAC palette upload (11 callers)
    
    # ===================================================================
    # GAME LOOP (from WEAPONS_FINAL_ASSESSMENT.md)
    # ===================================================================
    0x2F6D0: "main_game_loop_update",       # Main game loop frame update (1123B, 85 callees)
    0x30882: "ems_extended_memory_handler", # EMS extended memory I/O handler (282B)
    
    # ===================================================================
    # TODO: Add more systems
    # - Audio system (from docs/architecture/audio.md)
    # - Input system (from INPUT_SYSTEM.md) - some input already in flight physics
    # - Mission system
    # - Campaign system
    # ===================================================================
}

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

def add_comments(functions):
    """Add comments to functions with our knowledge."""
    print("\n" + "="*80)
    print("ADDING FUNCTION COMMENTS")
    print("="*80)
    
    comments = {
        # File I/O System
        0x1297F0: "Loads PICFONT.IDX/.DAT pair. Template pattern for all .IDX/.DAT loaders. Uses op_dispatch_far_entry for file I/O.",
        0x226BD: "DOS INT 21h AH=3D wrapper - Open file. Returns handle in AX, CF on error.",
        0x226F5: "DOS INT 21h AH=3F wrapper - Read from file handle. CX=bytes to read, returns AX=bytes read.",
        0x2274D: "DOS INT 21h AH=42 wrapper - Seek to file offset. AL=method (0=start, 1=current, 2=end).",
        0x6A651: "SQUAD campaign file loader. 46 references! Loads mission/campaign data from SQUAD*.CAM files.",
        0x1779A6: "HARPOON.DAT missile data loader. Loads AGM-84 Harpoon missile parameters.",
        
        # Menu System
        0x683C5: "Loadout menu controller hub (4169 bytes). Multiple entry points: ui_loadout_menu_enter, ui_stores_menu_enter, etc.",
        0x66E62: "Menu panel initialization. Sets up UI state, clears buffers. Tail-jumped from menu entry points.",
        0x4AEC4: "3D model rotation for menu aircraft preview. Animates selected aircraft in loadout screen.",
        
        # AI System  
        0x3CE92: "Master AI behavior dispatcher (2580B, 25 callees). Routes by entity type, executes behavior state machine.",
        0x495DF: "AI context batch processor (1165B). Processes 40×24B AI contexts at DS:0x49AB:[0xC]. Called every frame.",
        0x3D1C5: "AI target mirroring for missile tracking. Copies target orientation to missile (target sync).",
        0x3DC55: "Weapon spawn validation gate. Checks friendly fire rules, game mode flags, ammo count before spawning.",
        
        # Weapons System
        0x4C19E: "Weapon type initialization dispatcher (2500B). Routes to type-specific init: AIM-9, AIM-120, AGM-65, M61A1, bombs.",
        0x2EAA7: "Damage event dispatcher (190B). Routes damage by entity type: aircraft, ground unit, building, terrain.",
        0x327BE: "Explosion sound effect trigger (499B, 24 audio entries). Selects explosion sound by weapon type and size.",
        
        # Terrain System
        0x14956: "Terrain heightmap bilinear sampling (114B). Samples 31×31 tile grid, returns interpolated height.",
        0x361FC: "Terrain strip 3D→2D projection (331B). Perspective projection with LOD distance scaling for terrain rendering.",
        
        # Flight Physics System
        0x11450: "Read and normalize 4 flight control axes (114B). Joystick→±2048 range. Clamps to prevent overflow.",
        0x3B338: "Flight kinematics position integration (852B). Updates 26B state block at DS:[0x32], mirrors to DS:[0x66] and ES:0x7B0E:0x43BA.",
        0x38CF3: "Aerodynamic control authority vs. speed (2284B). Speed-dependent force scaling: linear at low speed, quadratic dampening at high speed.",
        0x3E16B: "Aerodynamic force→velocity update (865B). Applies force vector [FarObj+50h/52h/54h] to velocity [Entity+3Ah-44h].",
        
        # HUD System
        0x36785: "HUD readout coordinator (908B, 23 calls, 90 data refs). Main HUD render dispatcher, calls all instrument draw functions.",
        0x11AE7: "Bitmap font glyph renderer (62B). Variable-width fonts, atlas lookup, kerning. Called by 62 functions.",
        0x28B08: "Bresenham line drawing (409B). Table-based octant selection for optimized line rendering.",
        0x2D11A: "VGA Mode 13h initialization (111B). 320×200×256 color setup, disables chain-4, configures sequencer/CRT.",
        
        # Game Loop
        0x2F6D0: "Main game loop frame update (1123B, 85 callees). Input→AI→Physics→Rendering→Audio pipeline coordinator.",
    }
    
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
    print("Synchronizing IDA with documented knowledge")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Apply function names
    renamed, skipped, failed = apply_function_names(KNOWN_FUNCTIONS)
    
    # Add comments
    comments_added = add_comments(KNOWN_FUNCTIONS)
    
    # Apply data names (TODO)
    # data_renamed, data_skipped, data_failed = apply_data_names(KNOWN_DATA)
    
    # Save report
    report_file = save_naming_report(KNOWN_FUNCTIONS, renamed, skipped, failed)
    
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
    print("Add new discoveries to KNOWN_FUNCTIONS dict in this script.")
    print("="*80)
    
    # Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
