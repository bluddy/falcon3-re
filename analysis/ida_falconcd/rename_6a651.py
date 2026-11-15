import idc
import idaapi

# Update Rank #14 function with inline comments
addr = 0x6A651
comment = """Squad and campaign file loader for mission planning.
Loads multiple file types: .SQUAD, .CAM, .SQU, .MIS, .MTV
Uses int_to_string_converter for squadron numbers.
46 file I/O operations via op_dispatch_far_entry.
Pattern: OPEN(6) → READ(10/8/12) → process → repeat
Similar to squadron_mission_file_loader (Rank #10) and theater_campaign_file_loader (Rank #11).
Part of campaign/mission data loading subsystem."""

func = idaapi.get_func(addr)
if func:
    old_name = idc.get_func_name(addr)
    
    print(f"Function: {old_name}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    # Keep existing name (already good), just update comment
    idc.set_func_cmt(addr, comment, 0)
    print(f"✓ Updated comment ({len(comment)} chars)")
    
    # Add key inline comments
    inline_comments = [
        (0x6A65A, "Clear flag 2224a"),
        (0x6A664, "Push word_13E016 (dispatch parameter)"),
        (0x6A674, "Load dword_79E60 base pointer"),
        (0x6A67D, "Add offset 0x7530 (30,000 bytes)"),
        (0x6A68C, "Load current_menu_slot_ptr (squadron selection)"),
        (0x6A697, "Convert squadron number to string (0-N)"),
        (0x6A6A2, "Target buffer at 7894:0F32"),
        (0x6A6B9, "String '.`SQUAD' / 'S-.`SQUAD'"),
        (0x6A6C3, "Concatenate: buffer + slot + 'SQUAD'"),
        (0x6A6D6, "String '.`.CAM'"),
        (0x6A6E6, "Concatenate: buffer + '.CAM'"),
        (0x6A6FA, "op_dispatch operation 6 (OPEN file)"),
        (0x6A702, "Store file handle in var_2"),
        (0x6A705, "Check if open failed (0xFFFF)"),
        (0x6A717, "op_dispatch operation 10 (READ)"),
        (0x6A72D, "op_dispatch operation 8 (READ)"),
        (0x6A735, "Set flag 2224a"),
        (0x6A744, "op_dispatch operation 4 (OPEN another file)"),
        (0x6A75B, "op_dispatch operation 12 (READ)"),
    ],
    
    added = 0
    for ea, cmt in inline_comments[0]:
        if idc.set_cmt(ea, cmt, 0):
            added += 1
    
    print(f"✓ Added {added} inline comments")
    print(f"\nFunction analysis complete:")
    print(f"  Address: 0x{addr:X}")
    print(f"  Name: {old_name}")
    print(f"  Size: {func.end_ea - func.start_ea} bytes")
    print(f"  String refs: 42 (file extensions)")
    print(f"  File I/O ops: 46")
else:
    print(f"✗ Function not found at 0x{addr:X}")

idc.qexit(0)
