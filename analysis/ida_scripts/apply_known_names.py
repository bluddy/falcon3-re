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
    0x226BD: "file_open",           # DOS INT 21h AH=3D wrapper
    0x226E4: "file_close",          # DOS INT 21h AH=3E wrapper
    0x226F5: "file_read",           # DOS INT 21h AH=3F wrapper
    0x2271F: "file_write",          # DOS INT 21h AH=40 wrapper
    0x2274D: "file_lseek",          # DOS INT 21h AH=42 wrapper
    
    # .IDX/.DAT Loaders (from FILE_IO_ANALYSIS.md)
    0x1297F0: "idx_dat_loader",     # PICFONT.IDX/.DAT loader (RENAMED ✓)
    0x1397CE: "madfont_idx_loader", # madfont.idx/.dat loader
    0x6A651: "squad_file_handler",  # SQUAD file handler (46 refs!)
    0x1779A6: "harpoon_dat_loader", # HARPOON.DAT loader
    
    # Overlay system (from FILE_IO_ANALYSIS.md)
    0x2AEA9: "overlay_file_open",   # Overlay file opener
    0x2AC4C: "overlay_segment_load", # Overlay loader
    
    # ===================================================================
    # MENU SYSTEM (from MENU_SYSTEM_CODE_STRUCTURE.md)
    # ===================================================================
    0x683C5: "ui_menu_controller",  # Main menu controller (4169 bytes)
    0x66E62: "ui_menu_panel_init",  # Common panel initialization
    0x6A5BD: "ui_menu_page_setup",  # Page setup routine
    0x6798C: "ui_slot_record_fill", # Fill loadout record
    0x67BAF: "ui_menu_transition_step", # Menu transitions
    0x4AEC4: "farobj_pos_move_angle_step", # 3D model rotation
    
    # ===================================================================
    # AI SYSTEM (from AI_SYSTEM_STATUS.md, docs/architecture/ai.md)
    # ===================================================================
    0x3CE92: "ai_behavior_dispatcher",    # Master entity behavior dispatcher (2580B)
    0x495DF: "ai_entity_batch_processor", # Processes 40 AI contexts (1165B)
    0x3CFAA: "ai_behavior_state_machine", # Behavior state machine (entry)
    0x3D180: "ai_target_tracking",        # Target tracking sequence
    0x3D1C5: "ai_behavior_mirroring",     # Target sync mechanism
    0x3DC55: "ai_weapon_spawn_gate",      # Weapon spawn validation gate
    0x307A5: "ai_load_target_entity",     # Load target entity data
    
    # ===================================================================
    # WEAPONS SYSTEM (from WEAPONS_FINAL_ASSESSMENT.md)
    # ===================================================================
    0x4C19E: "weapon_type_dispatcher",    # Weapon type initialization (2500B)
    0x2EAA7: "damage_event_orchestrator", # Damage event handler (190B)
    0x32453: "entity_coord_transform",    # Coordinate transform (216B)
    0x32393: "explosion_visual_update",   # Explosion graphics (192B)
    0x327BE: "explosion_audio_trigger",   # Explosion sound (499B, 24 entries)
    
    # ===================================================================
    # TERRAIN SYSTEM (from TERRAIN_SYSTEM_100_PERCENT_COMPLETE.md)
    # ===================================================================
    0x14956: "tile_quad_sample",          # Heightmap sampling (114B)
    0x361FC: "tile_strip_project_draw",   # 3D→2D projection (331B)
    0x16060: "tile_strip_sample_draw",    # Strip sampling with self-mod code
    # Note: Many more terrain functions exist, see TERRAIN_SYSTEM_100_PERCENT_COMPLETE.md
    
    # ===================================================================
    # GRAPHICS SYSTEM (from MENU_SYSTEM_CODE_STRUCTURE.md)
    # ===================================================================
    0x4F271: "vga_dac_palette_upload", # VGA palette upload (11 callers)
    0x4F3EC: "sub_4F3EC",           # Unknown graphics function (TODO: identify)
    
    # ===================================================================
    # GAME LOOP (from WEAPONS_FINAL_ASSESSMENT.md)
    # ===================================================================
    0x2F6D0: "main_game_loop",      # Main game loop (1123B, 85 callees)
    0x30882: "ems_file_io_handler", # EMS/file I/O operations (282B)
    
    # ===================================================================
    # TODO: Add more systems
    # - Physics system (from docs/architecture/flight_physics.md)
    # - HUD system (from HUD_SYSTEM_100_PERCENT_COMPLETE.md)
    # - Audio system (from docs/architecture/audio.md)
    # - Input system (from INPUT_SYSTEM.md)
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
        # File I/O
        0x1297F0: "Loads .IDX and .DAT file pairs. Template for all .IDX/.DAT loading. Uses op_dispatch_far_entry.",
        0x226BD: "DOS INT 21h AH=3D - Open file. Returns handle in AX.",
        0x226F5: "DOS INT 21h AH=3F - Read from file handle.",
        0x2274D: "DOS INT 21h AH=42 - Seek to file offset.",
        0x6A651: "SQUAD file handler. 46 references! Likely loads campaign/AI data.",
        
        # Menu System
        0x683C5: "Menu controller hub (4169 bytes). Contains multiple entry points for different menus.",
        0x66E62: "Common menu panel initialization. Called via tail-jump from menu entry points.",
        
        # AI System  
        0x3CE92: "Master AI behavior dispatcher (2580B, 25 callees). Routes by entity type, handles state machine.",
        0x495DF: "AI batch processor (1165B). Processes 40 AI contexts (24 bytes each) at 0x65A7:0x000C.",
        0x3D1C5: "AI behavior mirroring. Target sync mechanism for missiles tracking.",
        0x3DC55: "Weapon spawn gate. Validates friendly fire, game mode, ammo before spawning.",
        
        # Weapons
        0x4C19E: "Weapon type dispatcher (2500B). Initializes AIM-9, AIM-120, M61A1, etc. by type byte.",
        0x2EAA7: "Damage event orchestrator (190B). Dispatches damage handlers by entity type.",
        
        # Terrain
        0x14956: "Tile heightmap sampling (114B). Bilinear filter over 31x31 grid.",
        0x361FC: "Tile strip 3D→2D projection (331B). Perspective with LOD scaling.",
        
        # Game Loop
        0x2F6D0: "Main game loop (1123B, 85 callees). Input, timing, rendering, entity management.",
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
