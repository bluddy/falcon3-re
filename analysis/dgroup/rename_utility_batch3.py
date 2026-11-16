"""
Rename final batch of utility functions based on analysis.
This completes all 25 utility functions.
"""

import idc
import idaapi

def set_function_name_and_comment(ea, name, comment):
    """Set function name and add comment."""
    success = idc.set_name(ea, name, idc.SN_NOWARN | idc.SN_NOCHECK)
    if success:
        idc.set_func_cmt(ea, comment, 0)
        print(f"✓ 0x{ea:06X}: {name}")
    else:
        print(f"✗ 0x{ea:06X}: Failed to rename to {name}")
    return success

def main():
    print("Renaming utility functions (batch 3 - FINAL)...")
    
    renamings = [
        # Rank #160: Graphics mode query
        (0x137F93, "graphics_mode_query",
         "Graphics mode query function. Checks graphics_mode_flag from 7894h, returns byte from 709F:word_70A2A if graphics mode active, otherwise returns 0. Used by r53_map_window_quota_step and script interpreter."),
        
        # Rank #162: Score file initializer
        (0x13DAD0, "score_file_initializer",
         "Score/temp file initializer. Calls op_dispatch multiple times (0xFB, 0xA67), clears flag2224a, initializes SCORE1.TMP string. Checks byte_13DABA flag. Used by game coordinators and script interpreter."),
        
        # Rank #172: UI element renderer (column 0x12C, row 0x14)
        (0x11CD43, "ui_element_render_12c_14",
         "UI element renderer at column 0x12C, row 0x14. Calls dispatch_220ec_invoke with ES:79976 data, calls sub_12FA2A with arg 2. Part of UI rendering system."),
        
        # Rank #173: UI element renderer (column 0x12C, row 0x13)
        (0x11CDAF, "ui_element_render_12c_13",
         "UI element renderer at column 0x12C, row 0x13. Similar to ui_element_render_12c_14 but different row offset. Calls dispatch_220ec_invoke and sub_12FA2A."),
        
        # Rank #175: State configuration accessor
        (0x135208, "state_config_accessor",
         "State/configuration accessor. Reads word_79B5E and word_13E00E from multiple segments. Used by overlay coordinators (r4C, r4E, r54). Likely accesses mission or campaign configuration state."),
        
        # Rank #188: Weapon initialization helper
        (0x049C67, "weapon_init_helper",
         "Weapon initialization helper. Calls undoc_49C80 and weapon_type_initialize_dispatch. Used by weapon subsystem functions. Part of weapon loadout initialization."),
        
        # Rank #189: Graphics drawing helper
        (0x12BBA6, "graphics_draw_helper",
         "Graphics/drawing helper function. Calls sub_12D463, used by undoc_1283EB and draw_primitive_mode_1. Part of graphics primitive rendering system."),
        
        # Rank #191: Recursive vector processor (LARGE)
        (0x1357AC, "vector_processor_recursive",
         "Recursive vector/math processor (1021B). Called by vector_arithmetic_complex and itself (recursive). Performs complex vector calculations via sub_13DDC3. Handles multi-level vector transformations."),
        
        # Rank #192: Negative number formatter
        (0x138ED4, "number_formatter_signed",
         "Signed number formatter. Writes '-' character (0x2D) for negative numbers, calls signed_div_32bit for conversion. Used by sub_13296E, r4a_supply_status_screen, overlay_r4F_logic_1."),
        
        # Rank #193: Overlay R55 helper
        (0x1909A0, "overlay_r55_helper",
         "Overlay R55 helper function. Called by overlay_r55_dispatcher. Calls undoc_11CD7F and undoc_11CDEB. Specific to overlay R55 processing logic."),
    ]
    
    success_count = 0
    for ea, name, comment in renamings:
        if set_function_name_and_comment(ea, name, comment):
            success_count += 1
    
    print(f"\n✓ Successfully renamed {success_count}/{len(renamings)} functions")
    
    # Save database
    print("\nSaving IDA database...")
    idc.save_database(idc.get_idb_path(), idc.DBFL_TEMP)
    print("✓ Database saved")
    
    print("\n" + "="*60)
    print("ALL 25 UTILITY FUNCTIONS COMPLETED!")
    print("="*60)

if __name__ == '__main__':
    main()

idc.qexit(0)
