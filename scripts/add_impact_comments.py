import idc
import idaapi

print("Adding impact system comments...")
idaapi.auto_wait()

# Add critical comments to store_impact_step
key_comments = [
    (0x3983F, "*** BREAKTHROUGH: Check target object_category == 4 (BUILDING) ***"),
    (0x39844, "Check target impact_state == 0xFF (pristine)"),
    (0x3986F, "*** Set target impact_state = 0xA0 (impacted) ***"),
    (0x39874, "*** Set weapon status_flags bit 2 (DESTROYED) ***"),
    (0x39807, "Load target_slot_index from [weapon+7Ah]"),
    (0x3983A, "r12_farptr_load_thunk: loads ES:DI = target EntitySlotRecord"),
]

for addr, comment in key_comments:
    idc.set_cmt(addr, comment, 0)
    print(f"0x{addr:X}: {comment}")

# Create ObjectCategory enum
enum_id = idc.get_enum("ObjectCategory")
if enum_id != idc.BADADDR:
    idc.del_enum(enum_id)

enum_id = idc.add_enum(idc.BADADDR, "ObjectCategory", 0)
if enum_id != idc.BADADDR:
    categories = [
        (1, "AIRCRAFT"), (2, "GROUND_VEHICLE"), (3, "SHIP"),
        (4, "BUILDING"), (5, "RADAR_SITE"), (6, "SAM_SITE"),
    ]
    for val, name in categories:
        idc.add_enum_member(enum_id, name, val, idc.BADADDR)
    print(f"\nCreated ObjectCategory enum with {len(categories)} members")

print("\nDone.")
idc.qexit(0)
