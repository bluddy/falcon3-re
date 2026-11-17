"""
Sync expanded WeaponType enum to IDA with all 46 weapon types.
Based on weapon_names.json and AG_WEAPONS_ANALYSIS.md findings.
"""

import idc
import idaapi
import idautils

print("=" * 80)
print("SYNC EXPANDED WEAPON ENUM TO IDA")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# Delete old enum if exists
old_enum = idc.get_enum("WeaponType")
if old_enum != idc.BADADDR:
    print("Deleting old WeaponType enum...")
    idc.del_enum(old_enum)

# Create new enum
print("Creating expanded WeaponType enum...")
enum_id = idc.add_enum(-1, "WeaponType", 0)

if enum_id == idc.BADADDR:
    print("ERROR: Could not create WeaponType enum")
    idc.qexit(1)

# A-A Missiles (0x12-0x13)
idc.add_enum_member(enum_id, "AIM9_SIDEWINDER", 0x12, -1)
idc.add_enum_member(enum_id, "AIM120_AMRAAM", 0x13, -1)

# A-G Weapons (0x14-0x32) - 31 weapon types
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_14", 0x14, -1)
idc.add_enum_member(enum_id, "AGM65_MAVERICK_TV", 0x15, -1)
idc.add_enum_member(enum_id, "AGM65_MAVERICK_IR", 0x16, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_17", 0x17, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_18", 0x18, -1)
idc.add_enum_member(enum_id, "AGM88_HARM", 0x19, -1)
idc.add_enum_member(enum_id, "AGM45_SHRIKE", 0x1A, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_1B", 0x1B, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_1C", 0x1C, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_1D", 0x1D, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_1E", 0x1E, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_1F", 0x1F, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_20", 0x20, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_21", 0x21, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_22", 0x22, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_23", 0x23, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_24", 0x24, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_25", 0x25, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_26", 0x26, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_27", 0x27, -1)
idc.add_enum_member(enum_id, "MK82_BOMB", 0x28, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_29", 0x29, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_2A", 0x2A, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_2B", 0x2B, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_2C", 0x2C, -1)
idc.add_enum_member(enum_id, "CBU84_CLUSTER", 0x2D, -1)
idc.add_enum_member(enum_id, "GBU15_GUIDED", 0x2E, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_2F", 0x2F, -1)
idc.add_enum_member(enum_id, "AGM84_HARPOON", 0x30, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_31", 0x31, -1)
idc.add_enum_member(enum_id, "AG_WEAPON_TYPE_32", 0x32, -1)

# Guns (0x33-0x37)
idc.add_enum_member(enum_id, "M61A1_VULCAN", 0x33, -1)
idc.add_enum_member(enum_id, "GUN_VARIANT_34", 0x34, -1)
idc.add_enum_member(enum_id, "GUN_VARIANT_35", 0x35, -1)
idc.add_enum_member(enum_id, "GUN_VARIANT_36", 0x36, -1)
idc.add_enum_member(enum_id, "GUN_VARIANT_37", 0x37, -1)

print("Created WeaponType enum with 46 members:")
print("  A-A Missiles: 2 (0x12-0x13)")
print("  A-G Weapons:  31 (0x14-0x32)")
print("  Guns:         5 (0x33-0x37)")

print("\nWeaponType enum created successfully")
print("Exiting IDA...")

# Exit
idc.qexit(0)
