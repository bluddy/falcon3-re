"""
Rename the remaining 8 uncategorized functions.
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
    print("Renaming remaining uncategorized functions...")
    
    renamings = [
        # Rank #46: Text width calculator
        (0x13DE82, "ui_text_width_calculate",
         "Calculate text string width in pixels. Reads font table from segment 642Fh, sums character widths with kerning. Used for UI text centering and layout."),
        
        # Rank #47: BIOS clock read
        (0x131530, "get_system_time_bios",
         "Read system time via INT 1Ah BIOS call. Returns time of day counter in DX:AX (ticks since midnight, ~18.2 Hz)."),
        
        # Rank #54: Overlay bridge
        (0x02C58B, "overlay_bridge_to_menu_frame",
         "Overlay bridge to ui_menu_frame_enter. Loads overlay and jumps to menu frame entry point."),
        
        # Rank #84: Text line parser
        (0x135C57, "text_line_parser",
         "Parse and format text into lines. Handles newline (0x0A) and space (0x20) characters. Writes formatted output to buffer at 7894:79D3E. Used for mission briefings and multi-line text display."),
        
        # Rank #86: UI text renderer
        (0x11C707, "ui_text_render_entry",
         "UI text rendering entry point. Calls dispatch_220ec_invoke for coordinate setup, calculates text width via ui_text_width_calculate, and renders text at specified position."),
        
        # Rank #87: Menu input handler  
        (0x11D274, "menu_input_handler",
         "Menu system input handler. Checks graphics_mode_flag, synchronizes input via input_sync_and_wait, handles mouse via mouse_gate_far_entry, dispatches to render functions."),
        
        # Rank #88: Campaign value calculator
        (0x13504F, "campaign_value_calculator",
         "Campaign/mission parameter calculator. Reads indexed value from word_79B5E, accesses data table at 4FC2:15Ah, performs signed 32-bit multiply and divide operations."),
        
        # Rank #100: Overlay bridge
        (0x02C595, "overlay_bridge_to_r30_table_copy",
         "Overlay bridge to r30_table_copy_4fd5c. Loads overlay and jumps to table copy function."),
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
