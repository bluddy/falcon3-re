#!/usr/bin/env python3
"""Check status of the 6 target functions"""
import idc
import ida_funcs

# The 6 targets
targets = [
    (0x407BF, 0x407BE, "sub_407BF"),
    (0x40DDB, 0x40DDA, "sub_40DDB"),
    (0x40C69, 0x40C68, "sub_40C69"),
    (0x40045, 0x40044, "sub_40045"),
    (0x3FD66, 0x3FD65, "sub_3FD66"),
    (0x404F1, 0x404F0, "sub_404F1"),
]

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/function_status.txt", "w") as f:
    f.write("Checking status of 6 REBASE target functions\n")
    f.write("=" * 60 + "\n\n")
    
    for old_ea, new_ea, expected_name in targets:
        f.write(f"\n{expected_name}:\n")
        f.write(f"  Old address (0x{old_ea:X}):\n")
        
        # Check old address
        fname_old = idc.get_func_name(old_ea)
        func_old = ida_funcs.get_func(old_ea)
        if func_old:
            f.write(f"    Function: {fname_old if fname_old else '(unnamed)'}\n")
            f.write(f"    Start: 0x{func_old.start_ea:X}\n")
            f.write(f"    End: 0x{func_old.end_ea:X}\n")
        else:
            f.write(f"    No function here\n")
        
        # Check new address
        f.write(f"  New address (0x{new_ea:X}):\n")
        fname_new = idc.get_func_name(new_ea)
        func_new = ida_funcs.get_func(new_ea)
        if func_new:
            f.write(f"    Function: {fname_new if fname_new else '(unnamed)'}\n")
            f.write(f"    Start: 0x{func_new.start_ea:X}\n")
            f.write(f"    End: 0x{func_new.end_ea:X}\n")
            f.write(f"    *** ALREADY REBASED? ***\n")
        else:
            f.write(f"    No function here\n")
        
        # Check byte at new address
        byte_val = idc.get_wide_byte(new_ea)
        f.write(f"  Byte at new address: 0x{byte_val:02X}\n")

print("Status check complete - see function_status.txt")
idc.qexit(0)
