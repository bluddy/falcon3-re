"""
Simple test: rename just one function.
"""

import idc
import idaapi

print("Starting simple rename test...")

ea = 0x02C527
old_name = idc.get_func_name(ea)
new_name = "overlay_bridge_to_66a3d"

print(f"Old name: {old_name}")
print(f"Attempting to rename to: {new_name}")

success = idc.set_name(ea, new_name, idc.SN_NOWARN | idc.SN_NOCHECK)

if success:
    print(f"✓ Success!")
    actual = idc.get_func_name(ea)
    print(f"New name: {actual}")
    idc.set_func_cmt(ea, "Overlay bridge test", 0)
    idc.save_database(idc.get_idb_path(), idc.DBFL_TEMP)
    print("Database saved")
else:
    print(f"✗ Failed to rename")

idc.qexit(0)
