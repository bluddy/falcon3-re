import idc
import idaapi

# Rename Rank #13 function
addr = 0x1A6F30
new_name = "r57_loadout_display_handler"
comment = """R57 overlay handler: Companion to r57_menu_state_machine (loadout menu).
String ref: "NELLIS" (Nellis AFB - campaign base).
7-state FSM matching menu state machine states.
Builds 23-byte (0x17) display records from 130-byte flight records.
Iterates through dword_79BEC table, filters by word_78910.
Stores display data in dword_79E6C table.
Calls ui_slot_scan_step 7x (once per state).
Pattern: UI display handler separate from menu logic.
Likely: Renders aircraft slots, pilot names, weapon icons on loadout screen."""

func = idaapi.get_func(addr)
if func:
    old_name = idc.get_func_name(addr)
    
    # Rename function
    if idc.set_name(addr, new_name, idaapi.SN_NOWARN):
        print(f"✓ Renamed: {old_name} → {new_name}")
        
        # Set function comment
        idc.set_func_cmt(addr, comment, 0)
        print(f"✓ Added comment ({len(comment)} chars)")
        
        # Add key inline comments
        inline_comments = [
            (0x1A6F41, "String ref: '.`NELLIS' (Nellis Air Force Base)"),
            (0x1A6F68, "Initialize word_79B60 = 0"),
            (0x1A6F74, "Initialize word_79E86 = 0"),
            (0x1A6F85, "Test word_14F8BE bit 3 (check mode flag)"),
            (0x1A6F93, "Toggle word_14F8BE bit 3 (XOR 8)"),
            (0x1A6F9F, "Access dword_79E50 (display buffer)"),
            (0x1A6FA4, "Set multiple offsets to 0x63 ('c' - likely color/attribute)"),
            (0x1A70D2, "Clear word_79F34 = 0 (display index)"),
            (0x1A70D7, "Clear word_79B62 = 0 (record index)"),
            (0x1A70EE, "Compute record offset: word_79B62 * 0x82 (130 bytes)"),
            (0x1A7106, "Read byte at record+var_4+0x05"),
            (0x1A7110, "Compare with word_78910 (filter/selection criteria)"),
            (0x1A711C, "Compute display offset: word_79F34 * 0x17 (23 bytes)"),
            (0x1A712A, "Access dword_79E6C (display record table)"),
            (0x1A7131, "Set display byte[0] = 1 (valid/visible flag)"),
            (0x1A714F, "Set display byte[0x12] = 0x1E (attribute/color)"),
            (0x1A716E, "Set display byte[0x13] = 0x1E (attribute/color)"),
            (0x1A7178, "Increment word_79F34 (next display record)"),
            (0x1A719A, "Read record[0x04] (aircraft count)"),
            (0x1A71AC, "Increment word_79B62 (next flight record)"),
            (0x1A71BF, "Compare with word_79EA4 (total record count)"),
            (0x1A73AC, "Load state variable word_79F16"),
            (0x1A73B1, "Switch on state (0-6, 7 cases)"),
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
