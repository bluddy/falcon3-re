"""
Rename A-G weapon initialization function and related code.
"""

import idc
import idaapi

print("=" * 80)
print("RENAME A-G WEAPON FUNCTIONS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Rename farobj_utility_1819 to ag_weapon_entity_initialize
func_addr = 0x4C3C7
old_name = idc.get_func_name(func_addr)
new_name = "ag_weapon_entity_initialize"

print(f"Renaming {old_name} @ {func_addr:#x} -> {new_name}")

if idc.set_name(func_addr, new_name, idaapi.SN_NOWARN):
    print(f"  ✓ Renamed to {new_name}")
else:
    print(f"  ✗ Failed to rename")

# Add comment
comment = """A-G weapon entity initialization dispatcher (0x14-0x32).
Handles 31 A-G weapon types: Maverick, HARM, Shrike, bombs, cluster, guided bombs, Harpoon.
Sets initial velocity (+0x8), damage (+0x23), and ballistic parameters.
Called by weapon_type_initialize_dispatch when processing A-G queue."""

idc.set_func_cmt(func_addr, comment, 1)
print(f"  ✓ Added function comment")

print(f"\n{'=' * 80}")
print("Renaming complete")
print("Exiting IDA...")

# Exit
idc.qexit(0)
