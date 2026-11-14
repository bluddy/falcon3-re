#!/usr/bin/env python3
"""Simple test script"""
import idc

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/test_output.txt", "w") as f:
    f.write("IDA script ran!\n")
    f.write(f"IDB: {idc.get_idb_path()}\n")
    
    # Check if our target functions exist
    targets = [0x407BF, 0x40DDB, 0x40C69, 0x40045, 0x3FD66, 0x404F1]
    for ea in targets:
        fname = idc.get_func_name(ea)
        f.write(f"0x{ea:X}: {fname}\n")

print("Wrote test output")
idc.qexit(0)
