import idaapi
import idc

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Renaming functions for ranks 151-200...")

# Define renames - only for functions that need renaming
renames = [
    # Rank 153
    (0x2C4F5, "overlay_bridge_to_68428", "Overlay bridge trampoline to 68428 (8B, 16 calls)"),
    
    # Rank 155
    (0x127E5A, "table_ptr_index_calc", "Calculate indexed pointer from table (116B, 16 calls)"),
    
    # Rank 159
    (0x135DF4, "utility_135df4", "Utility function (473B, 16 calls) - needs investigation"),
    
    # Rank 160
    (0x137F93, "utility_137f93", "Utility function (38B, 16 calls) - needs investigation"),
    
    # Rank 162
    (0x13DAD0, "utility_13dad0", "Utility function (133B, 16 calls) - needs investigation"),
    
    # Rank 170
    (0x2C509, "overlay_bridge_to_6822a", "Overlay bridge trampoline to 6822A (8B, 15 calls)"),
    
    # Rank 172
    (0x11CD43, "utility_11cd43", "Utility function (60B, 15 calls) - needs investigation"),
    
    # Rank 173
    (0x11CDAF, "utility_11cdaf", "Utility function (60B, 15 calls) - needs investigation"),
    
    # Rank 175
    (0x135208, "utility_135208", "Utility function (359B, 15 calls) - needs investigation"),
    
    # Rank 185
    (0x2C761, "overlay_bridge_generic", "Overlay bridge trampoline (8B, 14 calls)"),
    
    # Rank 188
    (0x49C67, "utility_49c67", "Utility function (25B, 14 calls) - needs investigation"),
    
    # Rank 189
    (0x12BBA6, "utility_12bba6", "Utility function (169B, 14 calls) - needs investigation"),
    
    # Rank 191
    (0x1357AC, "utility_large_1357ac", "Large utility function (1021B, 14 calls) - needs investigation"),
    
    # Rank 192
    (0x138ED4, "utility_138ed4", "Utility function (200B, 14 calls) - needs investigation"),
    
    # Rank 193
    (0x1909A0, "utility_1909a0", "Utility function (308B, 14 calls) - needs investigation"),
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
    if addr == 0x127E5A:  # table_ptr_index_calc
        idc.set_cmt(0x127E5A, "Load base pointer from 7894:word_79D96", 0)
        idc.set_cmt(0x127E72, "Add offset +2", 0)
        idc.set_cmt(0x127EA4, "Multiply index by 2 (word size)", 0)
        print(f"    Added 3 inline comments")

print(f"\n[+] Batch rename complete!")
print(f"    Functions renamed: {renamed_count}")
print(f"    Comments added: {comment_count}")

# Exit IDA
idc.qexit(0)
