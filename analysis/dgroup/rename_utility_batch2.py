"""
Rename utility functions batch 2 based on analysis.
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
    print("Renaming utility functions (batch 2)...")
    
    renamings = [
        # Rank #132: Mission parameter calculator
        (0x134C3A, "mission_param_calculator_large",
         "Large mission/campaign parameter calculator. Reads word_79B5E as index, accesses data at 4FC2:15Ah, performs complex calculations using signed_mul_32bit and signed_div_32bit. Similar to campaign_value_calculator but larger/more complex."),
        
        # Rank #140: UI element renderer (column 0xCC, row 0x13)
        (0x11C576, "ui_element_render_cc_13_alt",
         "UI element renderer at column 0xCC, row 0x13 (alternate variant). Calls dispatch_220ec_invoke and ui_text_width_calculate. Similar to ui_element_render_cc_13 but different implementation."),
        
        # Rank #141: UI element renderer (column 0xCC, row 0x13, another variant)
        (0x11CA9E, "ui_element_render_cc_13_var2",
         "UI element renderer at column 0xCC, row 0x13 (variant 2). Another implementation of UI rendering at same position. Calls dispatch_220ec_invoke twice."),
        
        # Rank #142: Data accessor
        (0x127FC4, "data_accessor_788d",
         "Data accessor for segment 788Dh. Loads DS with 788Dh, processes arg_0, dispatches via dispatch_220a4_stub. Used for accessing specific data structures."),
        
        # Rank #143: String width processor
        (0x135C07, "string_width_processor",
         "String width processor. Iterates through string at [bp+arg_0], temporarily nulls characters, calculates width via ui_text_width_calculate. Used for substring width calculations."),
        
        # Rank #147: UI element renderer (column 0xCC, row 0x14)
        (0x11C504, "ui_element_render_cc_14_alt",
         "UI element renderer at column 0xCC, row 0x14 (alternate variant). Similar to ui_element_render_cc_14 but different implementation. Calls dispatch_220ec_invoke and ui_text_width_calculate."),
        
        # Rank #148: String formatter/builder
        (0x13D77C, "string_format_builder",
         "String formatter/builder. Reads current_menu_slot_ptr from 602Eh, calls int_to_string_converter and string_concatenate to build formatted strings, dispatches via op_dispatch_far_entry."),
        
        # Rank #149: Conditional text renderer
        (0x167F75, "ui_text_render_conditional",
         "Conditional text renderer. Checks byte_14EC26 flag, calls ui_text_render_engine based on condition, may call overlay_bridge_to_66c9b. Used for conditional UI text display."),
        
        # Rank #158: Large data structure processor (LARGEST utility function)
        (0x133CCF, "entity_data_processor_large",
         "Large entity/object data processor (1786B). Accesses indexed data structure at 7894:79BEC with 130-byte stride (imul 0x82). Increments byte at offset 0x15, performs complex loop-based processing. Used by slope_far_call_driver and overlay handlers."),
        
        # Rank #159: UI button handler
        (0x135DF4, "ui_button_handler",
         "UI button handler. Calls mouse_gate_far_entry, accesses BUTTON1 string pointer from segment 602Eh, dispatches button events via op_dispatch_far_entry. Handles button state and rendering."),
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
