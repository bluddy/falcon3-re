import idc
import idaapi

# Rename Rank #12 function
addr = 0x1A57F0
new_name = "r57_menu_state_machine"
comment = """R57 overlay processor: 7-state menu state machine for selection/configuration UI.
Uses 130-byte (0x82) record table at dword_79BEC.
State variable: word_79F16 (0-6).
Calls input_sync_and_wait 14x across states (waiting for user input).
Calls ui_menu_transition_animate 7x (state transitions).
Heavy use of menu frame helpers (sub_2C8xx family).
Pattern: Menu selection with navigation, validation, and state transitions.
Likely: Squadron/pilot selection, loadout configuration, or campaign setup."""

func = idaapi.get_func(addr)
if func:
    old_name = idc.get_func_name(addr)
    
    # Rename function
    if idc.set_name(addr, new_name, idaapi.SN_NOWARN):
        print(f"✓ Renamed: {old_name} → {new_name}")
        
        # Set function comment
        idc.set_func_cmt(addr, comment, 0)
        print(f"✓ Added comment ({len(comment)} chars)")
        
        # Add inline comments at key locations
        inline_comments = [
            (0x1A5806, "Initialize word_79B60 = 0"),
            (0x1A5812, "Initialize word_79E86 = 0"),
            (0x1A5848, "Toggle word_14F8BE bit 3 (XOR 8)"),
            (0x1A5854, "Initialize word_79B62 = 0 (record index)"),
            (0x1A588A, "var_2 = 0 (local state counter)"),
            (0x1A5894, "word_79EA0 = 0 (menu field index)"),
            (0x1A58BC, "Loop init: var_4 = 0"),
            (0x1A58F9, "Loop condition: var_4 < 0xB (11 iterations)"),
            (0x1A58E0, "Compute record offset: var_4 * 0x1C (28 bytes)"),
            (0x1A58D2, "Initialize record far ptr to 4FC2:0A68"),
            (0x1A58EF, "Set record dword+8 to 6"),
            (0x1A5A16, "Load state variable word_79F16"),
            (0x1A5A1B, "Switch on state (0-6, 7 cases)"),
            (0x1A5A2A, "Case 0: Initial state - animate and wait for input"),
            (0x1A5A3F, "Wait for user input"),
            (0x1A5A49, "Check word_79B6C == 0x36 (key '6' or specific command)"),
            (0x1A5A62, "Adjust word_79B62 index by word_79EEC-1"),
            (0x1A5A76, "Modulo division: word_79B62 %= word[7894:15AC]"),
            (0x1A5A8A, "Compute record ptr: word_79B62 * 0x82 (130 bytes)"),
            (0x1A5A9F, "Validate: check byte at record+0x15"),
            (0x1A5AAF, "Increment word_79B62 (next record)"),
            (0x1A5B90, "Case 1: Secondary state"),
            (0x1A5CA4, "Case 2: Third state"),
            (0x1A5D72, "Case 3: Fourth state"),
            (0x1A5DBA, "Case 4: Fifth state"),
            (0x1A5FB3, "Case 5: Sixth state"),
            (0x1A5FC0, "Case 6: Final/exit state"),
        ]
        
        added = 0
        for ea, cmt in inline_comments:
            if idc.set_cmt(ea, cmt, 0):
                added += 1
        
        print(f"✓ Added {added} inline comments")
        print(f"\nFunction analysis complete:")
        print(f"  Address: 0x{addr:X}")
        print(f"  Old name: {old_name}")
        print(f"  New name: {new_name}")
        print(f"  Size: {func.end_ea - func.start_ea} bytes")
    else:
        print(f"✗ Failed to rename function")
else:
    print(f"✗ Function not found at 0x{addr:X}")

idc.qexit(0)
