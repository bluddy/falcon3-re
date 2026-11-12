#!/usr/bin/env python3
"""Check what bytes are at these addresses"""
import idc

targets = [(0x407BE, 0x40843), (0x40DDA, 0x40E35)]

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/bytes_check.txt", "w") as f:
    for new_start, end in targets:
        f.write(f"\n0x{new_start:X} - 0x{end:X} ({end-new_start} bytes):\n")
        
        # Get first 32 bytes
        for i in range(min(32, end - new_start)):
            ea = new_start + i
            byte_val = idc.get_wide_byte(ea)
            f.write(f"  +{i:02X}: 0x{byte_val:02X}")
            if i % 8 == 7:
                f.write("\n")

idc.qexit(0)
