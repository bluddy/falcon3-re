"""
Update IDA with RFM-related global and function names from registry.
"""

import idc
import idaapi

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\ida_rfm_naming_update.txt"

with open(output_file, 'w') as f:
    f.write("=== IDA RFM Naming Update ===\n\n")
    
    # Global variables to rename
    globals_to_rename = [
        (0x2F677, "word_2F677", "rfm_data_pointer"),
        (0x3B830, "word_3B830", "rfm_ai_behavior_ptr"),
        (0x3B832, "word_3B832", "rfm_related_word_2"),
        (0x3B834, "word_3B834", "rfm_related_word_3"),
        (0x2F679, "word_2F679", "rfm_related_word_4"),
    ]
    
    f.write("Renaming global variables:\n")
    f.write("-" * 80 + "\n\n")
    
    for addr, old_name, new_name in globals_to_rename:
        current_name = idc.get_name(addr)
        
        if current_name:
            # Try to rename
            success = idc.set_name(addr, new_name, idc.SN_NOWARN | idc.SN_NOCHECK)
            
            if success:
                f.write(f"✓ 0x{addr:X}: {current_name} → {new_name}\n")
            else:
                f.write(f"✗ 0x{addr:X}: Failed to rename {current_name} to {new_name}\n")
        else:
            # Try to create name
            success = idc.set_name(addr, new_name, idc.SN_NOWARN | idc.SN_NOCHECK)
            if success:
                f.write(f"✓ 0x{addr:X}: (unnamed) → {new_name}\n")
            else:
                f.write(f"✗ 0x{addr:X}: Failed to create name {new_name}\n")
    
    # Functions to update (already have names, just add comments)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("Updating function comments:\n")
    f.write("=" * 80 + "\n\n")
    
    functions_to_update = [
        (0x321C1, "mode_state_dispatch", 
         "Returns pointer to game state data. For RFM missions, returns AI behavior data pointer."),
        
        (0x3C1BD, "entity_slot_update_loop",
         "Main entity update loop. Initializes cs:word_3B830 from word_2F677 (RFM AI pointer)."),
        
        (0x419FC, "farobj_slot_table_copy",
         "Savegame restore. Restores cs:word_3B830 (RFM AI pointer) from save data."),
        
        (0x418AC, "farobj_slot_table_load",
         "Savegame save. Saves cs:word_3B830 (RFM AI pointer) to save data."),
        
        (0x3E2D3, "ai_combat_maneuver_selector",
         "Selects AI maneuvers. References cs:word_3B830 4x to index RFM behavior data."),
    ]
    
    for addr, expected_name, comment in functions_to_update:
        func = idaapi.get_func(addr)
        if func:
            current_name = idc.get_func_name(addr)
            f.write(f"\nFunction at 0x{addr:X}:\n")
            f.write(f"  Current name: {current_name}\n")
            
            # Set function comment
            success = idc.set_func_cmt(addr, comment, 0)
            if success:
                f.write(f"  ✓ Updated comment\n")
            else:
                f.write(f"  ✗ Failed to update comment\n")
        else:
            f.write(f"\n✗ No function at 0x{addr:X}\n")
    
    # Add comments to key code locations
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("Adding code comments at key locations:\n")
    f.write("=" * 80 + "\n\n")
    
    key_locations = [
        (0x2F9A8, "Store RFM pointer from mode_state_dispatch return value"),
        (0x3C1C4, "Read RFM pointer from word_2F677"),
        (0x3C1C7, "Copy RFM pointer to global cs:word_3B830"),
        (0x41A5D, "Restore RFM pointer from savegame"),
        (0x4190B, "Save RFM pointer to savegame"),
        (0x3E3CD, "Load RFM AI behavior pointer (ref 1/4)"),
        (0x3E41D, "Load RFM AI behavior pointer (ref 2/4)"),
        (0x3E454, "Load RFM AI behavior pointer (ref 3/4)"),
        (0x3E4B0, "Load RFM AI behavior pointer (ref 4/4)"),
    ]
    
    for addr, comment in key_locations:
        # Check if address exists
        if idc.get_full_flags(addr) != 0xFFFFFFFF:
            success = idc.set_cmt(addr, comment, 0)
            if success:
                f.write(f"✓ 0x{addr:X}: {comment}\n")
            else:
                f.write(f"✗ 0x{addr:X}: Failed to add comment\n")
        else:
            f.write(f"✗ 0x{addr:X}: Invalid address\n")
    
    f.write("\n\nUpdate complete!\n")

print(f"IDA naming update complete: {output_file}")
idc.qexit(0)
