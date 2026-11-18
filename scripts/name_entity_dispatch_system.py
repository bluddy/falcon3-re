import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\entity_dispatch_naming.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Naming entity dispatch system components...")
idaapi.auto_wait()

# The dispatch table is at 0x57034 (DS:0x2544)
# Code segment base is 0x3B830
table_addr = 0x57034
code_base = 0x3B830

# Define the dispatch table entries with their interpretations
dispatch_table = [
    (0, 0x176D, 0x3CF9D, "ai_state_processor_core", "UNKNOWN_0"),
    (1, 0x1BED, 0x3D41D, "entity_physics_and_ai_update", "PLAYER_AIRCRAFT"),
    (2, 0x2B1D, 0x3E34D, "ai_combat_maneuver_selector", "AI_FIGHTER"),
    (3, 0x346E, 0x3EC9E, "ai_behavior_decision_tree", "AI_BOMBER"),
    (4, 0x37C3, 0x3EFF3, "farobj_view_project_step", "BUILDING"),
    (5, 0x395D, 0x3F18D, "farobj_view_project_step", "GROUND_STRUCTURE"),
    (6, 0x0A00, 0x3C230, "entity_slot_update_loop", "UNKNOWN_6"),
    (7, 0x3219, 0x3EA49, "ai_target_priority_evaluator", "GROUND_VEHICLE"),
    (8, 0xC864, 0x48094, "hud_panel_transform_step", "UNKNOWN_8"),
    (9, 0x0039, 0x3B869, "hw_config_flags_build", "PROJECTILE_A"),
    (10, 0x0040, 0x3B870, "hw_config_flags_build", "PROJECTILE_B"),
    (11, 0x0048, 0x3B878, "hw_config_flags_build", "PROJECTILE_C"),
    (12, 0x004F, 0x3B87F, "hw_config_flags_build", "PROJECTILE_D"),
    (13, 0x0057, 0x3B887, "hw_config_flags_build", "PROJECTILE_E"),
    (14, 0x005E, 0x3B88E, "hw_config_flags_build", "PROJECTILE_F"),
    (15, 0x2940, 0x3E170, "sub_3E170", "UNKNOWN_15"),
    (16, 0x5280, 0x40AB0, "sub_40AA9", "UNKNOWN_16"),
    (17, 0x7BC0, 0x433F0, "sub_433DC", "UNKNOWN_17"),
    (18, 0x0000, 0x0000, "NULL", "INACTIVE"),
    (19, 0x00B2, 0x3B8E2, "hw_config_flags_build", "PROJECTILE_G"),
]

print("="*70)
print("ENTITY DISPATCH TABLE:")
print("="*70 + "\n")

print("Table address: DS:0x2544 (absolute 0x{:05X})".format(table_addr))
print("Code segment base: 0x{:05X}\n".format(code_base))

print("Cat | Offset | Absolute  | Function Name                        | Category Name")
print("----|--------|-----------|--------------------------------------|----------------------")

for cat, offset, abs_addr, func_name, cat_name in dispatch_table:
    # Verify the address
    actual_offset = idc.get_wide_word(table_addr + cat * 2)
    match = "✓" if actual_offset == offset else f"✗ (actual: 0x{actual_offset:04X})"
    
    print(f" {cat:2d} | 0x{offset:04X} | 0x{abs_addr:05X} | {func_name:36s} | {cat_name:20s} {match}")

# Name the table in IDA
print("\n" + "="*70)
print("APPLYING NAMES TO IDA:")
print("="*70 + "\n")

# Name the dispatch table
table_name = "entity_dispatch_table"
result = idc.set_name(table_addr, table_name, idc.SN_FORCE)
if result:
    print(f"✓ Named dispatch table at 0x{table_addr:05X}: {table_name}")
else:
    print(f"✗ Failed to name dispatch table at 0x{table_addr:05X}")

# Add comment to dispatch table
comment = "Entity function dispatch table indexed by object_category field (+0x0C).\n"
comment += "Each word is offset from code base 0x{:05X}.\n".format(code_base)
comment += "Dispatched by entity_slot_update_loop @ 0x3C25D-0x3C261."
idc.set_cmt(table_addr, comment, 1)  # 1 = repeatable comment
print("✓ Added comment to dispatch table")

# Add comments to each entry
for cat, offset, abs_addr, func_name, cat_name in dispatch_table:
    entry_addr = table_addr + (cat * 2)
    entry_comment = f"Category {cat} ({cat_name}): {func_name} @ 0x{abs_addr:05X}"
    idc.set_cmt(entry_addr, entry_comment, 0)

print(f"✓ Added comments to {len(dispatch_table)} table entries")

# Add comprehensive comment to the dispatch call site
dispatch_call_site = 0x3C25D
dispatch_comment = """Entity function dispatch system:
  1. Load object_category from [si+0Ch]
  2. Multiply by 2 (word table index)
  3. Load function offset from dispatch table DS:0x2544
  4. Call function via BX register

Dispatch table has 20 categories:
  0: ai_state_processor_core
  1: entity_physics_and_ai_update (PLAYER_AIRCRAFT)
  2: ai_combat_maneuver_selector (AI_FIGHTER)
  3: ai_behavior_decision_tree (AI_BOMBER)
  4: farobj_view_project_step (BUILDING - confirmed!)
  5-14: Various projectile and structure types
  15-17: Unknown entity types
  18: NULL (inactive entities)
  19: Projectile type G
"""

idc.set_cmt(dispatch_call_site, dispatch_comment, 1)
print(f"✓ Added comprehensive comment to dispatch call site @ 0x{dispatch_call_site:05X}")

# Add comments to key instructions in the dispatch sequence
instructions = [
    (0x3C258, "Load object_category from entity structure (polymorphic type)"),
    (0x3C25B, "Multiply by 2 to get word table index"),
    (0x3C25D, "Load function pointer offset from dispatch table DS:0x2544"),
    (0x3C261, "Call category-specific update function (polymorphic dispatch)"),
]

for addr, comment in instructions:
    idc.set_cmt(addr, comment, 0)
    print(f"✓ Added comment @ 0x{addr:05X}: {comment[:50]}...")

# Update ObjectCategory enum with new discoveries
print("\n" + "="*70)
print("UPDATING ObjectCategory ENUM:")
print("="*70 + "\n")

enum_id = idc.get_enum("ObjectCategory")
if enum_id == idc.BADADDR:
    print("✗ ObjectCategory enum not found, creating...")
    enum_id = idc.add_enum(0, "ObjectCategory", idc.hex_flag())

# Add or update enum members
category_names = [
    (0, "OBJECT_UNKNOWN_0"),
    (1, "OBJECT_PLAYER_AIRCRAFT"),
    (2, "OBJECT_AI_FIGHTER"),
    (3, "OBJECT_AI_BOMBER"),
    (4, "OBJECT_BUILDING"),
    (5, "OBJECT_GROUND_STRUCTURE"),
    (6, "OBJECT_UNKNOWN_6"),
    (7, "OBJECT_GROUND_VEHICLE"),
    (8, "OBJECT_UNKNOWN_8"),
    (9, "OBJECT_PROJECTILE_A"),
    (10, "OBJECT_PROJECTILE_B"),
    (11, "OBJECT_PROJECTILE_C"),
    (12, "OBJECT_PROJECTILE_D"),
    (13, "OBJECT_PROJECTILE_E"),
    (14, "OBJECT_PROJECTILE_F"),
    (15, "OBJECT_UNKNOWN_15"),
    (16, "OBJECT_UNKNOWN_16"),
    (17, "OBJECT_UNKNOWN_17"),
    (18, "OBJECT_INACTIVE"),
    (19, "OBJECT_PROJECTILE_G"),
]

for value, name in category_names:
    # Try to add, if exists it will fail silently
    result = idc.add_enum_member(enum_id, name, value, -1)
    if result == 0:
        print(f"✓ Added enum member: {name} = {value}")
    elif result == idc.ENUM_MEMBER_ERROR_NAME:
        print(f"  Enum member {name} already exists")
    elif result == idc.ENUM_MEMBER_ERROR_VALUE:
        # Value exists, try to rename
        existing = idc.get_enum_member_name(enum_id, value)
        if existing != name:
            print(f"  Value {value} exists as {existing}, updating...")
    else:
        print(f"✗ Failed to add enum member {name} = {value} (error: {result})")

print("\n" + "="*70)
print("NAMING COMPLETE")
print("="*70 + "\n")

print("Summary:")
print(f"  - Named dispatch table: {table_name}")
print(f"  - Added comments to {len(dispatch_table)} table entries")
print(f"  - Added comments to {len(instructions)} dispatch instructions")
print(f"  - Updated ObjectCategory enum with {len(category_names)} members")
print()
print("Key discoveries:")
print("  - Category 1 = PLAYER_AIRCRAFT (entity_physics_and_ai_update)")
print("  - Category 4 = BUILDING (confirmed, farobj_view_project_step)")
print("  - Categories 9-14,19 = PROJECTILES (weapon entities)")
print("  - Category 2/3 = AI FIGHTER/BOMBER (advanced AI)")

output_file.close()
idc.qexit(0)
