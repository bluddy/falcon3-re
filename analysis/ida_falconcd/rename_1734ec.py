import idc
import idaapi

# Rename Rank #15 function
addr = 0x1734EC
new_name = "r4a_supply_status_screen"
comment = """R4A overlay: Supply status screen handler for campaign logistics.
String: "SUPPLY STATUS" - displays ammunition, fuel, equipment levels.
Heavy text processing: int_to_string_converter (21x), string_concatenate (11x).
Calls sub_13DE3A 44x (likely text rendering/positioning function).
Pattern: Divide by 2, subtract from 100 (0x64) - text centering calculation.
Uses menu_state_ptr, dword_79D92 for state management.
Typical overlay handler with UI rendering focus."""

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
            (0x1734F6, "Load dword_79D92 (state pointer)"),
            (0x173504, "dispatch_220ec_invoke with 0,0 params"),
            (0x17350C, "Push 3 (text attribute/color?)"),
            (0x173513, "Load word_150F0C (string pointer)"),
            (0x17351D, "Call sub_13DE82 (text measurement?)"),
            (0x173525, "Divide by 2 (center calculation)"),
            (0x17352B, "0x64 = 100 (screen width or column count)"),
            (0x17352E, "Subtract to center: 100 - (width/2)"),
            (0x173546, "Call sub_13DE3A (text render - called 44x!)"),
            (0x173553, "Load menu_state_ptr"),
            (0x173558, "Read menu state value"),
            (0x17355B, "Shift right by 2 (divide by 4)"),
            (0x17355E, "Increment (adjust index)"),
            (0x173568, "Convert number to string"),
            (0x17358B, "Concatenate strings for display"),
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
