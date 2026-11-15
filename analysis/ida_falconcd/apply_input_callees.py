import ida_auto
import ida_name
import ida_bytes
import idc

def apply_renames():
    """Apply renames for the 7 input_poll_handler callees"""
    
    print("=" * 80)
    print("APPLYING INPUT CALLEE RENAMES")
    print("=" * 80)
    
    # Function renames
    functions = [
        (0x130C80, "mouse_sensitivity_calculator"),
        (0x130CE7, "keyboard_state_processor"),
        (0x130E48, "joystick_position_reader"),
        (0x131001, "joystick_button_handler"),
        (0x131235, "input_region_mapper"),
        (0x1312DF, "joystick_calibration_handler"),
        (0x2BEC9, "input_overlay_bridge"),
    ]
    
    print("\nRenaming functions:")
    for addr, new_name in functions:
        try:
            old_name = idc.get_func_name(addr)
            if ida_name.set_name(addr, new_name, ida_name.SN_NOWARN):
                print(f"  0x{addr:X}: {old_name} -> {new_name}")
            else:
                print(f"  0x{addr:X}: FAILED to rename to {new_name}")
        except Exception as e:
            print(f"  0x{addr:X}: ERROR - {e}")
    
    # Data items - input region table
    data_items = [
        (0x4FC27C0, "input_region_table"),  # seg:off format needs conversion
    ]
    
    print("\nRenaming data items:")
    # Note: Need to calculate linear address for segment:offset
    # Segment 0x4FC2 with offset 0x7C0
    # This is typically: seg_base + offset, but we'll use direct address if known
    # For now, let's add comments at known addresses
    
    # Add comments to document the input system
    comments = [
        (0x130C80, "Mouse acceleration: clamp(delta,1,8)*4 -> [4-32]"),
        (0x130CE7, "Keyboard state processor (inline, no calls)"),
        (0x130E48, "Reads joystick X/Y position from ports 0x201-0x203"),
        (0x131001, "Joystick button handler (inline)"),
        (0x131235, "2x3 region grid: X@100,150 Y@190 (of 255), 28B/region"),
        (0x1312DF, "Joystick calibration handler (inline)"),
        (0x2BEC9, "Bridge to overlay for extended input handling"),
        (0x12FC43, "Main input poll: keyboard->mouse->joystick->regions"),
    ]
    
    print("\nAdding comments:")
    for addr, comment in comments:
        try:
            idc.set_func_cmt(addr, comment, 0)
            print(f"  0x{addr:X}: {comment[:60]}...")
        except Exception as e:
            print(f"  0x{addr:X}: ERROR - {e}")
    
    print("\n" + "=" * 80)
    print("RENAME COMPLETE")
    print("=" * 80)
    
    # Save database
    print("\nSaving database...")
    idc.save_database(idc.get_idb_path())
    print("Database saved.")

if __name__ == "__main__":
    ida_auto.auto_wait()
    apply_renames()
    idc.qexit(0)
