import idaapi
import idc

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Renaming functions for ranks 101-110...")

renames = [
    # Rank 101: sub_11C884 - Need to analyze
    (0x11C884, "utility_11c884", "Utility function (24 calls) - needs investigation"),
    
    # Rank 102: sub_11C90F - Need to analyze  
    (0x11C90F, "utility_11c90f", "Utility function (24 calls) - needs investigation"),
    
    # Rank 103: sub_13536F - Large arithmetic function
    (0x13536F, "vector_arithmetic_complex", "Complex vector/coordinate arithmetic (1085B, 24 calls)"),
    
    # Rank 104: fixed_abs_div4 - ALREADY NAMED
    # (0x22EE8, "fixed_abs_div4", "Fixed-point absolute value divided by 4"),
    
    # Rank 105: trig_table_lookup - ALREADY NAMED
    # (0x249D8, "trig_table_lookup", "Trigonometry table lookup for sin/cos"),
    
    # Rank 106: sub_13BCE5 - String terminator
    (0x13BCE5, "string_cr_null_terminate", "Append CR (0Dh) and null terminator to string"),
    
    # Rank 107: angle_xy_far - ALREADY NAMED
    # (0x23C9B, "angle_xy_far", "Calculate angle from XY delta coordinates"),
    
    # Rank 108: cs_word_store - ALREADY NAMED
    # (0x24CF7, "cs_word_store", "Store AX to CS segment word (2 bytes)"),
    
    # Rank 109: dispatch_220f4_stub - ALREADY NAMED
    # (0x25E22, "dispatch_220f4_stub", "Far call stub to dword_220F4 dispatcher"),
    
    # Rank 110: sub_11C642 - Need to analyze
    (0x11C642, "utility_11c642", "Utility function (22 calls) - needs investigation"),
]

renamed_count = 0
comment_count = 0

for addr, new_name, description in renames:
    # Set function name
    if idc.set_name(addr, new_name, idc.SN_CHECK):
        print(f"  [+] Renamed 0x{addr:X} -> {new_name}")
        renamed_count += 1
    else:
        current_name = idc.get_func_name(addr)
        print(f"  [=] Kept existing name at 0x{addr:X}: {current_name}")
    
    # Set function comment
    idc.set_func_cmt(addr, description, 1)
    comment_count += 1
    
    # Add inline comments for key functions
    if addr == 0x22EE8:  # fixed_abs_div4
        idc.set_cmt(0x22EE8, "Multiply by 4 (shift left 2)", 0)
        idc.set_cmt(0x22EED, "Sign extend AX into DX", 0)
        idc.set_cmt(0x22EEE, "Absolute value: XOR with sign, subtract sign", 0)
        idc.set_cmt(0x22EF3, "Divide by 4 (shift right 2)", 0)
        print(f"    Added 4 inline comments")
    
    elif addr == 0x13BCE5:  # string_cr_null_terminate
        idc.set_cmt(0x13BCE9, "Get string far pointer", 0)
        idc.set_cmt(0x13BCF0, "Call sub_13BCCE to find length", 0)
        idc.set_cmt(0x13BCFA, "Append 0Dh (carriage return)", 0)
        idc.set_cmt(0x13BCFF, "Append null terminator", 0)
        print(f"    Added 4 inline comments")
    
    elif addr == 0x24CF7:  # cs_word_store
        idc.set_cmt(0x24CF7, "Store AL to CS:byte_24BBA", 0)
        idc.set_cmt(0x24CFB, "Store AH to CS:byte_24BBB (forms word)", 0)
        print(f"    Added 2 inline comments")

print(f"\n[+] Batch rename complete!")
print(f"    Functions renamed: {renamed_count}")
print(f"    Comments added: {comment_count}")

# Exit IDA
idc.qexit(0)
