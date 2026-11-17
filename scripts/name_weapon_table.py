"""
Name weapon name table at 0x55C55.
Contains null-terminated weapon name strings accessed by offset.
"""

import idc
import idaapi

print("=" * 80)
print("NAME WEAPON NAME TABLE")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Weapon name table address (linear address in IDA)
table_addr = 0x55C55

# Name the table start
print(f"Naming weapon_name_table @ {table_addr:#x}")
if idc.set_name(table_addr, "weapon_name_table", idaapi.SN_NOWARN):
    print("  ✓ weapon_name_table named")
else:
    print("  ✗ Failed to name weapon_name_table")

# Known weapon name offsets from weapon_names.json
weapon_strings = [
    (0x55c55, "weapon_name_aim9p"),
    (0x55c5b, "weapon_name_aim9m"),
    (0x55c61, "weapon_name_aim120"),
    (0x55c68, "weapon_name_unknown1"),
    (0x55c71, "weapon_name_agm88"),
    (0x55c77, "weapon_name_agm65b"),
    (0x55c7e, "weapon_name_agm65d"),
    (0x55c85, "weapon_name_agm45"),
    (0x55c8c, "weapon_name_unknown2"),
    (0x55c94, "weapon_name_mk82hd"),
    (0x55c9b, "weapon_name_unknown3"),
    (0x55ca5, "weapon_name_cbu84"),
    (0x55cab, "weapon_name_unknown4"),
    (0x55cb0, "weapon_name_gbu15"),
    (0x55cb7, "weapon_name_unknown5"),
    (0x55cc7, "weapon_name_agm84"),
]

print(f"\nNaming {len(weapon_strings)} weapon name strings:")

for addr, name in weapon_strings:
    # Get the actual string
    str_val = idc.get_strlit_contents(addr)
    if str_val:
        str_val = str_val.decode('ascii', errors='ignore')
    else:
        str_val = "(no string)"
    
    # Set name
    if idc.set_name(addr, name, idaapi.SN_NOWARN):
        print(f"  ✓ {name} @ {addr:#x}: '{str_val}'")
    else:
        current = idc.get_name(addr)
        print(f"  - {name} @ {addr:#x}: '{str_val}' (current: {current})")

# Make sure strings are defined as strings in IDA
print(f"\nDefining strings in IDA:")
for addr, name in weapon_strings:
    # Try to create string
    if idc.create_strlit(addr, idc.BADADDR):
        str_len = idc.get_item_size(addr)
        print(f"  ✓ String at {addr:#x} (length {str_len})")
    else:
        print(f"  - String at {addr:#x} (already defined)")

print(f"\n{'=' * 80}")
print("Weapon name table naming complete")
print("Exiting IDA...")

# Exit
idc.qexit(0)
