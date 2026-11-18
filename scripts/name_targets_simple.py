import idc
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\target_simple_naming.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Target naming starting...")

# Function naming
functions = [
    (0x32D22, "mission_state_initializer"),
    (0x3E96F, "ai_target_priority_evaluator"),
    (0x4478D, "farobj_slot_target_search"),
    (0x48B05, "target_cycle_scan"),
    (0x48C20, "target_processing_helper"),
]

print("\nNaming functions:")
for addr, name in functions:
    result = idc.set_name(addr, name, idc.SN_CHECK)
    print(f"  0x{addr:X} -> {name}: {result}")

# Create EntityFieldOffset enum
print("\nCreating EntityFieldOffset enum:")
enum_id = idc.get_enum("EntityFieldOffset")
if enum_id != idc.BADADDR:
    idc.del_enum(enum_id)
    print("  Deleted existing enum")

enum_id = idc.add_enum(idc.BADADDR, "EntityFieldOffset", 0)
print(f"  Created enum: {enum_id != idc.BADADDR}")

if enum_id != idc.BADADDR:
    fields = [
        (0x76, "UNKNOWN_FLAGS_76"),
        (0xAE, "HEAT_SIGNATURE_OR_TARGET_FLAG"),
        (0xCA, "DAMAGE_STATUS_FLAGS"),
    ]
    for val, name in fields:
        result = idc.add_enum_member(enum_id, name, val, idc.BADADDR)
        print(f"  Added 0x{val:02X} {name}: {result == 0}")

# Create DamageStatusFlags enum
print("\nCreating DamageStatusFlags enum:")
enum_id = idc.get_enum("DamageStatusFlags")
if enum_id != idc.BADADDR:
    idc.del_enum(enum_id)

enum_id = idc.add_enum(idc.BADADDR, "DamageStatusFlags", idc.HEX_FLAG)
print(f"  Created enum: {enum_id != idc.BADADDR}")

if enum_id != idc.BADADDR:
    result = idc.add_enum_member(enum_id, "DAMAGE_NAV", 0x0001, idc.BADADDR)
    print(f"  Added DAMAGE_NAV: {result == 0}")

print("\nDone.")
output_file.close()
idc.qexit(0)
