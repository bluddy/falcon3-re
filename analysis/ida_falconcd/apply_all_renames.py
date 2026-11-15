"""
Apply all discovered renames from this analysis session
Functions, data, and segments
"""
import idaapi
import idc
import idautils

def rename_safely(ea, new_name, item_type="item"):
    """Rename an item safely with error handling"""
    old_name = idc.get_name(ea)
    if idc.set_name(ea, new_name, idc.SN_NOWARN):
        print(f"[+] Renamed {item_type} 0x{ea:X}: {old_name} -> {new_name}")
        return True
    else:
        print(f"[-] Failed to rename {item_type} 0x{ea:X} to {new_name}")
        return False

def main():
    try:
        print("[*] Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("[+] Auto-analysis complete")
        
        print("\n=== RENAMING FUNCTIONS ===\n")
        
        # Functions from this session
        functions = [
            # Already renamed
            (0x12841F, "menu_state_init_with_random"),  # Was: undoc_12841F
            
            # New renames
            (0x1295A9, "ui_text_render_loop"),          # Was: undoc_1295A9
            (0x128518, "ui_text_render_engine"),        # Should already be named
            (0x128D5A, "ui_render_coordinator"),        # Was: utility_900
            (0x12B07D, "ui_special_element_render"),    # Was: undoc_12B07D
            (0x12BE93, "draw_primitive_mode_1"),        # Was: undoc_12BE93
            (0x12BED1, "draw_primitive_mode_2"),        # Was: undoc_12BED1
            (0x127FA7, "draw_coord_wrapper"),           # Was: undoc_127FA7
            (0x130A2F, "input_sync_and_wait"),          # Was: menu_cursor_position_set
            (0x130B39, "input_finalization"),           # Was: undoc_130B39 (called after input ready)
            
            # Related functions
            (0x68159, "ui_slot_scan_step"),             # Should already be named
            (0x2C3B5, "menu_selection_ptr_get"),        # Should already be named
        ]
        
        success_count = 0
        for addr, name in functions:
            if rename_safely(addr, name, "function"):
                success_count += 1
        
        print(f"\n[+] Successfully renamed {success_count}/{len(functions)} functions")
        
        print("\n=== RENAMING DATA ===\n")
        
        # Data items (flags, pointers, config)
        data_items = [
            # Input flags in segment 0x7894
            (0x79B68, "input_flag_pending_1"),          # Was: word_79B68
            (0x79B66, "input_flag_pending_2"),          # Was: word_79B66
            (0x79B52, "menu_state_ptr"),                # Was: dword_79B52
            (0x78940, "graphics_mode_flag"),            # Was: word_78940
            (0x79EF0, "game_status_word"),              # Was: word_79EF0
            
            # Segment 0x709F - Counter data
            (0x70A2B, "global_frame_counter"),          # Was: word_70A2A+1
            (0x70A2D, "call_counter"),                  # Was: word_70A2D
            
            # Segment 0x602E - Extended menu data
            (0x14F99C, "current_menu_slot_ptr"),        # Was: dword_14F99C
            (0x1400, "menu_random_state"),              # Was: unnamed (10-byte struct)
            (0x14E76C, "render_config_byte_1"),         # Was: byte_14E76C
            (0x14E76D, "render_config_byte_2"),         # Was: byte_14E76D
            (0x14E76E, "render_config_byte_3"),         # Was: byte_14E76E
            
            # Function pointers
            (0x22084, "vga_draw_func_ptr"),             # Was: dword_22084 (dynamic dispatch)
        ]
        
        data_success = 0
        for addr, name in data_items:
            if rename_safely(addr, name, "data"):
                data_success += 1
        
        print(f"\n[+] Successfully renamed {data_success}/{len(data_items)} data items")
        
        print("\n=== ADDING COMMENTS ===\n")
        
        # Add comments to key locations
        comments = [
            (0x128518, "Core text rendering engine for entire UI system. 70+ callers."),
            (0x130A2F, "Universal input synchronization - busy-wait on two flags. 194 callers!"),
            (0x12841F, "Initializes 10-byte random state at 0x602E:0x1400"),
            (0x1295A9, "Loops calling ui_text_render_engine N times (N from global_frame_counter)"),
            (0x128D5A, "Dispatches to mode-specific drawing primitives"),
            (0x79B68, "Input flag 1: non-zero when input is being processed"),
            (0x79B66, "Input flag 2: non-zero when input is being processed"),
            (0x78940, "Graphics mode: 0=text mode, non-zero=graphics mode"),
            (0x70A2B, "Global counter used by text render loop and menu init"),
            (0x1400, "10-byte struct: [counter:2][random1:2][random2:2][random3:2][variant:2]"),
            (0x22084, "Function pointer to VGA draw function (set at runtime by graphics mode)"),
        ]
        
        comment_count = 0
        for addr, comment in comments:
            idc.set_cmt(addr, comment, 0)  # 0 = regular comment, 1 = repeatable
            print(f"[+] Added comment at 0x{addr:X}")
            comment_count += 1
        
        print(f"\n[+] Added {comment_count} comments")
        
        # Create structures for data we've found
        print("\n=== CREATING STRUCTURES ===\n")
        
        # Try to create menu_random_state structure
        sid = idc.add_struc(-1, "menu_random_state", 0)
        if sid != idc.BADADDR and sid is not None:
            idc.add_struc_member(sid, "frame_counter", 0, idc.FF_WORD, -1, 2)
            idc.add_struc_member(sid, "random_value_1", 2, idc.FF_WORD, -1, 2)
            idc.add_struc_member(sid, "random_value_2", 4, idc.FF_WORD, -1, 2)
            idc.add_struc_member(sid, "random_value_3", 6, idc.FF_WORD, -1, 2)
            idc.add_struc_member(sid, "variant_index", 8, idc.FF_WORD, -1, 2)
            print("[+] Created structure: menu_random_state (10 bytes)")
        else:
            print("[-] Structure menu_random_state may already exist")
        
        print("\n=== SUMMARY ===")
        print(f"Functions renamed: {success_count}/{len(functions)}")
        print(f"Data renamed: {data_success}/{len(data_items)}")
        print(f"Comments added: {comment_count}")
        print(f"\n[+] All renames applied!")
        
    except Exception as e:
        print(f"[-] ERROR: {e}")
        import traceback
        traceback.print_exc()
        idc.qexit(1)

if __name__ == "__main__":
    main()
    idc.qexit(0)
