"""
Rename all 32 new functions in Top 300 (ranks 201-300) in one batch.
Based on analysis patterns from Top 200 work.
"""

import idc
import idaapi

def set_function_name_and_comment(ea, name, comment):
    """Set function name and add comment."""
    old_name = idc.get_func_name(ea)
    success = idc.set_name(ea, name, idc.SN_NOWARN | idc.SN_NOCHECK)
    if success:
        idc.set_func_cmt(ea, comment, 0)
        print(f"✓ 0x{ea:06X}: {old_name} -> {name}")
        return True
    else:
        print(f"✗ 0x{ea:06X}: Failed to rename {old_name} to {name}")
        return False

def main():
    print("="*70)
    print("RENAMING ALL TOP 300 NEW FUNCTIONS (32 functions)")
    print("="*70)
    
    renamings = [
        # Rank #202: Overlay bridge (8B)
        (0x02C527, "overlay_bridge_to_66a3d",
         "Overlay bridge trampoline to 66A3Dh (8B)."),
        
        # Rank #206: UI renderer variant A (48B)
        (0x11CD7F, "ui_element_render_variant_a",
         "UI element renderer variant A (48B). Calls dispatch_220ec_invoke."),
        
        # Rank #207: UI renderer variant B (48B)
        (0x11CDEB, "ui_element_render_variant_b",
         "UI element renderer variant B (48B). Calls dispatch_220ec_invoke."),
        
        # Rank #208: Graphics clipping (162B)
        (0x127EFF, "graphics_clip_processor",
         "Graphics clipping processor (162B). Calls segment_clip_test."),
        
        # Rank #209: UI text wrapper (24B)
        (0x129591, "ui_text_render_wrapper",
         "UI text rendering wrapper (24B). Calls ui_text_render_simple."),
        
        # Rank #211: Large UI coordinator R54 (1376B)
        (0x1941E8, "overlay_r54_ui_coordinator",
         "Overlay R54 UI coordinator (1376B). Calls ui_element_render_variant_a/b."),
        
        # Rank #212: Large UI coordinator R58 (1409B)
        (0x195F81, "overlay_r58_ui_coordinator",
         "Overlay R58 UI coordinator (1409B). Calls ui_element_render_variant_a/b."),
        
        # Rank #213: R57 helper (26B)
        (0x1A2B37, "overlay_r57_simple_helper",
         "Overlay R57 simple helper (26B)."),
        
        # Rank #224: Complex UI renderer (133B)
        (0x11CC39, "ui_element_render_complex_a",
         "UI element renderer complex (133B). Calls dispatch_220ec_invoke, ui_text_width_calculate, table_dispatch_interpreter."),
        
        # Rank #225: UI renderer with draw (143B)
        (0x11D074, "ui_element_render_with_draw",
         "UI element renderer with draw (143B). Calls dispatch_220ec_invoke and draw_coord_wrapper."),
        
        # Rank #226: Triple dispatch renderer (155B)
        (0x11D172, "ui_element_render_triple_dispatch",
         "UI element renderer triple dispatch (155B). Calls dispatch_220ec_invoke 3x."),
        
        # Rank #227: Menu helper (55B)
        (0x13153A, "menu_simple_helper",
         "Menu system simple helper (55B)."),
        
        # Rank #228: Interactive string formatter (358B)
        (0x135FCD, "ui_string_formatter_interactive",
         "Interactive UI string formatter (358B). Calls int_to_string_converter, string_concatenate, mouse_gate_far_entry, op_dispatch_far_entry."),
        
        # Rank #229: Font processor (481B)
        (0x139D85, "font_data_processor",
         "Font data processor (481B). Processes font file data."),
        
        # Rank #230: Menu queue processor (348B)
        (0x13AD67, "menu_queue_processor",
         "Menu/queue processor (348B). Calls sub_13B1F4 and signed_diff_abs."),
        
        # Rank #240: Overlay bridge (8B)
        (0x02C4B9, "overlay_bridge_to_66988",
         "Overlay bridge trampoline to 66988h (8B)."),
        
        # Rank #241: Overlay bridge (8B)
        (0x02C5D1, "overlay_bridge_to_66ea8",
         "Overlay bridge trampoline to 66EA8h (8B)."),
        
        # Rank #245: R01 helper (41B)
        (0x1016A8, "r01_segment_helper_a",
         "R01 segment helper A (41B). Utility for overlay R01."),
        
        # Rank #246: R06 helper (41B)
        (0x106AD0, "r06_segment_helper_a",
         "R06 segment helper A (41B). Utility for overlay R06."),
        
        # Rank #247: UI renderer variant C (48B)
        (0x11CE1B, "ui_element_render_variant_c",
         "UI element renderer variant C (48B). Calls dispatch_220ec_invoke."),
        
        # Rank #248: UI renderer variant D (48B)
        (0x11CE7B, "ui_element_render_variant_d",
         "UI element renderer variant D (48B). Calls dispatch_220ec_invoke."),
        
        # Rank #249: Data structure processor (221B)
        (0x13462B, "data_structure_processor",
         "Data structure processor (221B). General data processing function."),
        
        # Rank #250: Math helper (20B)
        (0x13DDC3, "math_helper_20b",
         "Math helper function (20B). Small arithmetic utility."),
        
        # Rank #251: State processor (357B)
        (0x160096, "state_processor_large",
         "State processor (357B). Handles game state processing."),
        
        # Rank #275: Weapon helper (99B)
        (0x04D75F, "weapon_helper_4d75f",
         "Weapon system helper (99B). Part of weapon subsystem."),
        
        # Rank #276: R01 processor (130B)
        (0x10106C, "r01_processor_segment",
         "R01 processor segment function (130B). Overlay R01 processing logic."),
        
        # Rank #277: R01 helper B (123B)
        (0x1017D5, "r01_segment_helper_b",
         "R01 segment helper B (123B). Additional R01 utility."),
        
        # Rank #278: R06 processor (220B)
        (0x106457, "r06_processor_segment",
         "R06 processor segment function (220B). Overlay R06 processing logic."),
        
        # Rank #280: UI renderer complex B (145B)
        (0x11CBA8, "ui_element_render_complex_b",
         "UI element renderer complex B (145B). Similar to complex_a variant."),
        
        # Rank #281: UI renderer variant E (48B)
        (0x11CE4B, "ui_element_render_variant_e",
         "UI element renderer variant E (48B). Fifth 48B UI renderer variant."),
        
        # Rank #282: R55 helper (179B)
        (0x185569, "overlay_r55_helper_large",
         "Overlay R55 helper (179B). Additional R55 processing function."),
        
        # Rank #283: Large processor (498B)
        (0x1AAACC, "overlay_processor_large_1aaacc",
         "Large overlay processor (498B). Complex processing function."),
    ]
    
    success_count = 0
    failed = []
    
    for ea, name, comment in renamings:
        if set_function_name_and_comment(ea, name, comment):
            success_count += 1
        else:
            failed.append((ea, name))
    
    print(f"\n{'='*70}")
    print(f"✓ Successfully renamed {success_count}/{len(renamings)} functions")
    
    if failed:
        print(f"\n⚠ {len(failed)} failures:")
        for ea, name in failed:
            print(f"  0x{ea:06X}: {name}")
    
    # Save database
    print("\nSaving IDA database...")
    idc.save_database(idc.get_idb_path(), idc.DBFL_TEMP | idc.DBFL_BAK)
    print("✓ Database saved")
    
    if success_count == len(renamings):
        print("\n" + "="*70)
        print("🎯 ALL TOP 300 NEW FUNCTIONS RENAMED SUCCESSFULLY!")
        print("="*70)

if __name__ == '__main__':
    main()

idc.qexit(0)
