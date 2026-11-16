"""
Rename Top 300 batch 1 functions (ranks 201-230, 15 functions).
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
    print("Renaming Top 300 functions (batch 1: ranks 201-230)...")
    
    renamings = [
        # Rank #202: Overlay bridge
        (0x02C527, "overlay_bridge_to_66a3d",
         "Overlay bridge trampoline. Loads overlay and jumps to 66A3Dh."),
        
        # Rank #206: UI element renderer
        (0x11CD7F, "ui_element_render_variant_a",
         "UI element renderer variant A (48B). Calls dispatch_220ec_invoke for coordinate setup. Used by multiple overlay UI functions. Similar pattern to other element renderers but simpler implementation."),
        
        # Rank #207: UI element renderer
        (0x11CDEB, "ui_element_render_variant_b",
         "UI element renderer variant B (48B). Calls dispatch_220ec_invoke. Similar to ui_element_render_variant_a but different implementation. Used by overlays R54, R58 and other UI functions."),
        
        # Rank #208: Graphics clip processor
        (0x127EFF, "graphics_clip_processor",
         "Graphics clipping processor (162B). Calls segment_clip_test to perform view frustum clipping. Used for determining visible geometry before rendering."),
        
        # Rank #209: UI text render wrapper
        (0x129591, "ui_text_render_wrapper",
         "UI text rendering wrapper (24B). Calls ui_text_render_simple. Used by ui_loadout_menu_enter and game coordinators. Thin wrapper for text rendering with specific parameters."),
        
        # Rank #211: Large UI coordinator for R54
        (0x1941E8, "overlay_r54_ui_coordinator",
         "Overlay R54 UI coordinator (1376B, LARGE). Calls ui_element_render_variant_a and ui_element_render_variant_b to render complex UI. Main UI coordination function for overlay R54 processor."),
        
        # Rank #212: Large UI coordinator for R58
        (0x195F81, "overlay_r58_ui_coordinator",
         "Overlay R58 UI coordinator (1409B, LARGE). Calls ui_element_render_variant_a and ui_element_render_variant_b for UI rendering. Main UI coordination function for r58_line_table_entry."),
        
        # Rank #213: Simple utility
        (0x1A2B37, "overlay_r57_simple_helper",
         "Overlay R57 simple helper (26B). Used by overlay_r57_processor_2. Small utility function specific to overlay R57 logic."),
        
        # Rank #224: UI element renderer
        (0x11CC39, "ui_element_render_complex_a",
         "UI element renderer complex variant A (133B). Calls dispatch_220ec_invoke (2x), ui_text_width_calculate, and table_dispatch_interpreter. More complex than simple variants, handles multi-element rendering."),
        
        # Rank #225: UI element renderer with drawing
        (0x11D074, "ui_element_render_with_draw",
         "UI element renderer with drawing (143B). Calls dispatch_220ec_invoke (3x) and draw_coord_wrapper. Combines coordinate setup with actual drawing operations."),
        
        # Rank #226: UI element renderer
        (0x11D172, "ui_element_render_triple_dispatch",
         "UI element renderer with triple dispatch (155B). Calls dispatch_220ec_invoke three times for complex multi-element layout. Used by menu/UI systems for structured element rendering."),
        
        # Rank #227: Simple utility
        (0x13153A, "menu_simple_helper",
         "Menu system simple helper (55B). Used by menu functions sub_13ABA7, undoc_13AD67, sub_13AEC3. Small utility for menu processing."),
        
        # Rank #228: String formatter
        (0x135FCD, "ui_string_formatter_interactive",
         "Interactive UI string formatter (358B). Calls int_to_string_converter and string_concatenate to build formatted strings, mouse_gate_far_entry for input sync, op_dispatch_far_entry for rendering. Used by overlay processors."),
        
        # Rank #229: Font processor
        (0x139D85, "font_data_processor",
         "Font data processor (481B). Calls undoc_139169 for font processing. Used by msc_font_file_loader and overlay_r46_handler. Processes font file data structures."),
        
        # Rank #230: Menu processor
        (0x13AD67, "menu_queue_processor",
         "Menu/queue processor (348B). Calls sub_13B1F4 and signed_diff_abs. Used by menu_cmd_store_and_record_scan and queue processing functions. Handles menu command queuing and processing."),
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
