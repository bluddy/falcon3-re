"""
Rename function at 0x17B437 to squadron_mission_file_loader
This function was previously partially named overlay_r4B_logic
Analysis showed it loads .SQUAD, .MTV, .SHP, and .TSK files during mission planning

IDA Python Script - Batch Mode
"""

import idc
import idaapi

# Wait for autoanalysis to complete
idaapi.auto_wait()

# Rename function
addr = 0x17B437
old_name = idc.get_func_name(addr)
new_name = "squadron_mission_file_loader"

print(f"Renaming function at 0x{addr:X}")
print(f"  Old name: {old_name}")
print(f"  New name: {new_name}")

success = idc.set_name(addr, new_name, idc.SN_CHECK)

if success:
    print(f"SUCCESS: Renamed to {new_name}")
else:
    print(f"FAILED: Could not rename (name might already exist or be invalid)")

# Exit IDA
idc.qexit(0)
