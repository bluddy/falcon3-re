import ida_auto
import ida_name
import idc
import sys

def verify_renames():
    """Verify all renames from both batches are applied"""
    
    # Redirect output to file
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\verification_report.txt"
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("VERIFYING IDA DATABASE SYNCHRONIZATION\n")
        f.write("=" * 80 + "\n\n")
        
        # All function renames from both batches
        functions = [
            # First batch (menu/rendering)
            (0x12841F, "menu_state_init_with_random"),
            (0x1295A9, "ui_text_render_loop"),
            (0x128518, "ui_text_render_engine"),
            (0x128D5A, "ui_render_coordinator"),
            (0x12BE93, "draw_primitive_mode_1"),
            (0x12BED1, "draw_primitive_mode_2"),
            (0x130A2F, "input_sync_and_wait"),
            (0x22C89, "farobj_vec3_accum_b_ret"),
            (0x130B39, "input_finalization"),
            (0x22C38, "pit_channel0_latch_read"),
            (0x127FA7, "draw_coord_wrapper"),
            (0x2C3B5, "menu_selection_ptr_get"),
            # Second batch (input callees)
            (0x130C80, "mouse_sensitivity_calculator"),
            (0x130CE7, "keyboard_state_processor"),
            (0x130E48, "joystick_position_reader"),
            (0x131001, "joystick_button_handler"),
            (0x131235, "input_region_mapper"),
            (0x1312DF, "joystick_calibration_handler"),
            (0x2BEC9, "input_overlay_bridge"),
        ]
        
        f.write("Verifying function renames:\n")
        all_ok = True
        for addr, expected_name in functions:
            try:
                current_name = idc.get_func_name(addr)
                if current_name == expected_name:
                    f.write(f"  ✓ 0x{addr:06X}: {expected_name}\n")
                else:
                    f.write(f"  ✗ 0x{addr:06X}: Expected '{expected_name}', got '{current_name}'\n")
                    all_ok = False
            except Exception as e:
                f.write(f"  ✗ 0x{addr:06X}: ERROR - {e}\n")
                all_ok = False
        
        # Check key data items
        data_items = [
            (0x79B68, "input_flag_pending_1"),
            (0x79B66, "input_flag_pending_2"),
            (0x78940, "graphics_mode_flag"),
        ]
        
        f.write("\nVerifying key data items:\n")
        for addr, expected_name in data_items:
            try:
                current_name = idc.get_name(addr)
                if current_name == expected_name:
                    f.write(f"  ✓ 0x{addr:06X}: {expected_name}\n")
                else:
                    f.write(f"  ✗ 0x{addr:06X}: Expected '{expected_name}', got '{current_name}'\n")
                    all_ok = False
            except Exception as e:
                f.write(f"  ✗ 0x{addr:06X}: ERROR - {e}\n")
                all_ok = False
        
        f.write("\n" + "=" * 80 + "\n")
        if all_ok:
            f.write("✅ ALL RENAMES VERIFIED - DATABASE UP TO DATE\n")
        else:
            f.write("❌ SOME RENAMES MISSING - DATABASE NEEDS UPDATE\n")
        f.write("=" * 80 + "\n")
    
    print(f"Verification report written to: {output_file}")
    return 0 if all_ok else 1

if __name__ == "__main__":
    ida_auto.auto_wait()
    exit_code = verify_renames()
    idc.qexit(exit_code)
