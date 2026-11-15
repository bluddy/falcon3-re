import idaapi
import idc

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Renaming functions for ranks 111-150...")

# Define renames - only for functions that need renaming
renames = [
    # Rank 113
    (0x15D4C6, "entity_table_flag_check", "Check flag bit in entity table structure (66B, 22 calls)"),
    
    # Rank 115  
    (0x2C559, "overlay_bridge_to_66c9b", "Overlay bridge trampoline to 66C9B (8B, 21 calls)"),
    
    # Rank 116
    (0x12C2F7, "utility_12c2f7", "Utility function (176B, 21 calls) - needs investigation"),
    
    # Rank 124
    (0x13AB62, "signed_diff_abs", "Absolute difference with sign handling (69B, 20 calls)"),
    
    # Rank 125
    (0x13DB56, "flag_13daba_set_ff", "Set CS:byte_13DABA to 0xFF (7B, 20 calls)"),
    
    # Rank 131
    (0x11CA0D, "dispatch_dual_call", "Dual dispatch_220ec calls with offsets (145B, 19 calls)"),
    
    # Rank 132
    (0x134C3A, "utility_large_134c3a", "Large utility function (1045B, 19 calls) - needs investigation"),
    
    # Rank 138
    (0x2C513, "overlay_bridge_to_66dc2", "Overlay bridge trampoline to 66DC2 (8B, 18 calls)"),
    
    # Rank 140
    (0x11C576, "utility_11c576", "Utility function (102B, 18 calls) - needs investigation"),
    
    # Rank 141
    (0x11CA9E, "utility_11ca9e", "Utility function (133B, 18 calls) - needs investigation"),
    
    # Rank 142
    (0x127FC4, "utility_127fc4", "Utility function (50B, 18 calls) - needs investigation"),
    
    # Rank 143
    (0x135C07, "utility_135c07", "Utility function (80B, 18 calls) - needs investigation"),
    
    # Rank 147
    (0x11C504, "utility_11c504", "Utility function (114B, 17 calls) - needs investigation"),
    
    # Rank 148
    (0x13D77C, "utility_13d77c", "Utility function (237B, 17 calls) - needs investigation"),
    
    # Rank 149
    (0x167F75, "utility_167f75", "Utility function (101B, 17 calls) - needs investigation"),
]

renamed_count = 0
comment_count = 0

for addr, new_name, description in renames:
    current_name = idc.get_func_name(addr)
    
    # Only rename if it's a generic sub_XXXXXX or undoc_XXXXXX name
    if current_name and (current_name.startswith('sub_') or current_name.startswith('undoc_')):
        if idc.set_name(addr, new_name, idc.SN_CHECK):
            print(f"  [+] Renamed 0x{addr:X}: {current_name} -> {new_name}")
            renamed_count += 1
        else:
            print(f"  [!] Failed to rename 0x{addr:X}")
    else:
        print(f"  [=] Kept existing name at 0x{addr:X}: {current_name}")
    
    # Set function comment
    idc.set_func_cmt(addr, description, 1)
    comment_count += 1
    
    # Add inline comments for specific functions
    if addr == 0x15D4C6:  # entity_table_flag_check
        idc.set_cmt(0x15D4C6, "Calculate table offset: arg_0 * 0x4E", 0)
        idc.set_cmt(0x15D4D6, "Load base pointer from segment 7894", 0)
        idc.set_cmt(0x15D4FA, "Test flag bit 0x80", 0)
        idc.set_cmt(0x15D504, "Return 1 if bit clear, 0 if set", 0)
        print(f"    Added 4 inline comments")
    
    elif addr == 0x13AB62:  # signed_diff_abs
        idc.set_cmt(0x13AB6D, "Check if DI negative", 0)
        idc.set_cmt(0x13AB71, "Check if SI negative", 0)
        idc.set_cmt(0x13AB75, "Compare magnitudes", 0)
        idc.set_cmt(0x13ABA1, "Calculate absolute difference", 0)
        print(f"    Added 4 inline comments")
    
    elif addr == 0x13DB56:  # flag_13daba_set_ff
        idc.set_cmt(0x13DB56, "Set flag byte to 0xFF (true/active)", 0)
        print(f"    Added 1 inline comment")

print(f"\n[+] Batch rename complete!")
print(f"    Functions renamed: {renamed_count}")
print(f"    Comments added: {comment_count}")

# Exit IDA
idc.qexit(0)
