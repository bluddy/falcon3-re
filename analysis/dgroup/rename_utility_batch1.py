"""
Rename first batch of utility functions based on analysis.
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
    print("Renaming utility functions (batch 1)...")
    
    renamings = [
        # Rank #73: Keep existing name but add better comment
        (0x13BD06, "overlay_dispatcher_indexed",
         "Indexed overlay dispatcher for game objects. Reads overlay table at 7894:79BEC, dispatches via overlay_tail_bridge_b based on index and type byte. Handles menu_list_index_clamp and state updates."),
        
        # Rank #101: UI element renderer (column 0xCC, row 0x14)
        (0x11C884, "ui_element_render_cc_14",
         "UI element renderer at column 0xCC, row 0x14. Calls dispatch_220ec_invoke for coordinate setup, calculates text width, renders via table_dispatch_interpreter."),
        
        # Rank #102: UI element renderer (column 0xCC, row 0x13)
        (0x11C90F, "ui_element_render_cc_13",
         "UI element renderer at column 0xCC, row 0x13. Similar pattern to ui_element_render_cc_14 but different row offset. Used for menu/UI elements."),
        
        # Rank #110: UI element renderer (column 0x102, row 0x14)
        (0x11C642, "ui_element_render_102_14",
         "UI element renderer at column 0x102, row 0x14. Calls dispatch_220ec_invoke, ui_text_width_calculate, string_copy_with_offset, table_dispatch_interpreter. More complex than cc variants."),
        
        # Rank #116: Timing/frame-rate control
        (0x12C2F7, "timing_frame_limiter",
         "Timing control and frame-rate limiter. Reads BIOS timer (ES:046Ch), checks word_709F0 mode flag, performs timing calculations and delays via OUT instruction. Returns 1 if frame should proceed, 0 to skip."),
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

if __name__ == '__main__':
    main()

idc.qexit(0)
