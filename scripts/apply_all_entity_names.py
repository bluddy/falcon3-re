import idc
import idaapi
import idautils
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\temp\entity_naming_complete.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Applying comprehensive entity system naming to IDA...")
idaapi.auto_wait()

success_count = 0
fail_count = 0

# ============================================================================
# DISPATCH TABLE AND FUNCTIONS
# ============================================================================

print("="*70)
print("DISPATCH TABLE NAMING")
print("="*70 + "\n")

table_addr = 0x57034
code_base = 0x3B830

# Name the dispatch table
result = idc.set_name(table_addr, "entity_dispatch_table", idc.SN_FORCE)
if result:
    print(f"✓ Named dispatch table @ 0x{table_addr:05X}")
    success_count += 1
else:
    print(f"✗ Failed to name dispatch table @ 0x{table_addr:05X}")
    fail_count += 1

# Add table comment
table_comment = """Entity function dispatch table indexed by object_category field (+0x0C).
20 word entries, each offset from code segment base 0x3B830.
Dispatched by entity_slot_update_loop @ 0x3C25D-0x3C261.

Category mappings:
  1 = PLAYER_AIRCRAFT (entity_physics_and_ai_update)
  2 = AI_FIGHTER (ai_combat_maneuver_selector)
  3 = AI_BOMBER (ai_behavior_decision_tree)
  4 = BUILDING (farobj_view_project_step)
  7 = GROUND_VEHICLE (ai_target_priority_evaluator)
  9-14,19 = PROJECTILES (hw_config_flags_build)"""

idc.set_cmt(table_addr, table_comment, 1)
print("✓ Added dispatch table comment")
success_count += 1

# Name dispatch table entries with category info
dispatch_entries = [
    (0, "ai_state_processor_core", "UNKNOWN_0"),
    (1, "entity_physics_and_ai_update", "PLAYER_AIRCRAFT"),
    (2, "ai_combat_maneuver_selector", "AI_FIGHTER"),
    (3, "ai_behavior_decision_tree", "AI_BOMBER"),
    (4, "farobj_view_project_step", "BUILDING"),
    (5, "farobj_view_project_step", "GROUND_STRUCTURE"),
    (6, "entity_slot_update_loop", "UNKNOWN_6"),
    (7, "ai_target_priority_evaluator", "GROUND_VEHICLE"),
    (8, "hud_panel_transform_step", "UNKNOWN_8"),
    (9, "hw_config_flags_build", "PROJECTILE_A"),
    (10, "hw_config_flags_build", "PROJECTILE_B"),
    (11, "hw_config_flags_build", "PROJECTILE_C"),
    (12, "hw_config_flags_build", "PROJECTILE_D"),
    (13, "hw_config_flags_build", "PROJECTILE_E"),
    (14, "hw_config_flags_build", "PROJECTILE_F"),
    (15, "sub_3E170", "UNKNOWN_15"),
    (16, "sub_40AA9", "UNKNOWN_16"),
    (17, "sub_433DC", "UNKNOWN_17"),
    (18, "NULL", "INACTIVE"),
    (19, "hw_config_flags_build", "PROJECTILE_G"),
]

for cat, func_name, cat_name in dispatch_entries:
    entry_addr = table_addr + (cat * 2)
    offset = idc.get_wide_word(entry_addr)
    abs_addr = code_base + offset if offset != 0 else 0
    
    comment = f"Category {cat} ({cat_name}): {func_name} @ 0x{abs_addr:05X}"
    idc.set_cmt(entry_addr, comment, 0)

print(f"✓ Added {len(dispatch_entries)} dispatch entry comments")
success_count += len(dispatch_entries)

# ============================================================================
# DISPATCH CALL SITE
# ============================================================================

print("\n" + "="*70)
print("DISPATCH CALL SITE NAMING")
print("="*70 + "\n")

dispatch_instructions = [
    (0x3C258, "Load object_category from entity (polymorphic type identifier)"),
    (0x3C25B, "Multiply by 2 for word table index (category * sizeof(word))"),
    (0x3C25D, "Load function offset from entity_dispatch_table[category]"),
    (0x3C261, "Polymorphic dispatch: call category-specific update function"),
]

for addr, comment in dispatch_instructions:
    idc.set_cmt(addr, comment, 0)
    print(f"✓ Comment @ 0x{addr:05X}: {comment[:50]}...")
    success_count += 1

# Add comprehensive function comment to dispatch block
dispatch_block_comment = """POLYMORPHIC ENTITY DISPATCH SYSTEM

This code implements OOP-style polymorphic dispatch for entity updates.
Each entity has object_category field (+0x0C) that indexes into a 20-entry
function table, calling specialized update code for that category:

  AIRCRAFT (1-3):   Full physics, AI, combat maneuvers
  BUILDINGS (4-5):  View projection only, no physics
  VEHICLES (7):     Ground AI, target priority
  PROJECTILES (9-14,19): Weapon physics, guidance

Pattern:
  1. Load category from [si+0Ch]
  2. Multiply by 2 (word table)
  3. Load function offset from DS:0x2544
  4. Call function via BX register

This is remarkably sophisticated for 1991 assembly - proper separation
of data structure (EntitySlotRecord) from behavior (category functions)."""

idc.set_cmt(0x3C258, dispatch_block_comment, 1)
print("✓ Added comprehensive dispatch block comment")
success_count += 1

# ============================================================================
# ENTITY STRUCTURE FIELD COMMENTS
# ============================================================================

print("\n" + "="*70)
print("ENTITY STRUCTURE FIELD COMMENTS")
print("="*70 + "\n")

# We'll add comments to key entity field accesses throughout the codebase
# Focus on object_category (+0x0C) and related fields

entity_field_comments = [
    # store_impact_step @ 0x397FB
    (0x3983F, "Check if target is BUILDING (object_category == 4)"),
    (0x39844, "Check if building is pristine (impact_state == 0xFF)"),
    (0x3986F, "Mark building as impacted (impact_state = 0xA0)"),
    (0x39874, "Set weapon DESTROYED flag (status_flags |= 4)"),
    (0x3983A, "Load target entity via target_slot_index from weapon"),
    
    # entity_physics_and_ai_update @ 0x3D37F
    (0x3D3BD, "Apply gravity/drag to velocity_component (+0x2E)"),
    
    # r12_farptr_load_thunk @ 0x41B32
    (0x41B32, "Calculate entity address: 0x386F + (index-base)*0x5C"),
]

for addr, comment in entity_field_comments:
    existing = idc.get_cmt(addr, 0)
    if not existing or len(comment) > len(existing):
        idc.set_cmt(addr, comment, 0)
        print(f"✓ Comment @ 0x{addr:05X}")
        success_count += 1

# ============================================================================
# FUNCTION RENAMING
# ============================================================================

print("\n" + "="*70)
print("FUNCTION RENAMING")
print("="*70 + "\n")

# Key functions that should have proper names
function_renames = [
    # Already named in previous sessions, verify they exist
    (0x3C1BD, "entity_slot_update_loop", "Main entity update loop, 3-pass processing"),
    (0x3D37F, "entity_physics_and_ai_update", "Category 1: Full physics and AI for player aircraft"),
    (0x397FB, "store_impact_step", "Records weapon impact on target entity"),
    (0x41B32, "r12_farptr_load_thunk", "Loads far pointer to entity by slot index"),
    (0x2EBCD, "entity_slot_create", "Allocates and initializes new entity slot"),
    (0x4C3C7, "ag_weapon_entity_initialize", "A-G weapon spawner, sets object_category"),
    
    # Category-specific update functions
    (0x3CF9D, "ai_state_processor_core", "Category 0: AI state processing"),
    (0x3E34D, "ai_combat_maneuver_selector", "Category 2: Fighter combat AI"),
    (0x3EC9E, "ai_behavior_decision_tree", "Category 3: Bomber/transport AI"),
    (0x3EFF3, "farobj_view_project_step", "Category 4: Building view projection"),
    (0x3F18D, "farobj_view_project_step_alt", "Category 5: Ground structure projection"),
    (0x3EA49, "ai_target_priority_evaluator", "Category 7: Ground vehicle AI"),
    (0x48094, "hud_panel_transform_step", "Category 8: HUD element transform"),
]

for addr, name, description in function_renames:
    # Check if function exists
    func = idaapi.get_func(addr)
    if not func:
        print(f"  Function not found @ 0x{addr:05X}, skipping {name}")
        continue
    
    # Try to set name
    current_name = idc.get_func_name(addr)
    if current_name == name:
        print(f"  Already named: {name} @ 0x{addr:05X}")
        continue
    
    result = idc.set_name(addr, name, idc.SN_FORCE)
    if result:
        print(f"✓ Renamed 0x{addr:05X}: {current_name} → {name}")
        success_count += 1
    else:
        print(f"✗ Failed to rename 0x{addr:05X} to {name}")
        fail_count += 1
    
    # Add function comment
    idc.set_func_cmt(addr, description, 1)

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================

print("\n" + "="*70)
print("GLOBAL VARIABLE NAMING")
print("="*70 + "\n")

# Key globals from registry
global_names = [
    (0x55E50, "entity_slot_index_base", "Base index for entity slot calculations"),
    (0x1356, "weapon_damage_scale", "Damage multiplier for impact calculation"),
    (0x1360, "entity_table_base_offset", "Entity table offset for validation"),
]

for addr, name, description in global_names:
    result = idc.set_name(addr, name, idc.SN_FORCE)
    if result:
        print(f"✓ Named global @ 0x{addr:05X}: {name}")
        success_count += 1
    else:
        print(f"✗ Failed to name global @ 0x{addr:05X}: {name}")
        fail_count += 1
    
    idc.set_cmt(addr, description, 1)

# ============================================================================
# ENUMS
# ============================================================================

print("\n" + "="*70)
print("ENUM UPDATES")
print("="*70 + "\n")

# Update ObjectCategory enum
enum_id = idc.get_enum("ObjectCategory")
if enum_id == idc.BADADDR:
    print("Creating ObjectCategory enum...")
    enum_id = idc.add_enum(0, "ObjectCategory", idc.hex_flag())
    success_count += 1
else:
    print("ObjectCategory enum exists, updating...")

# Define all 20 categories
category_members = [
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

for value, name in category_members:
    result = idc.add_enum_member(enum_id, name, value, -1)
    if result == 0:
        print(f"✓ Added {name} = {value}")
        success_count += 1
    elif result == idc.ENUM_MEMBER_ERROR_NAME or result == idc.ENUM_MEMBER_ERROR_VALUE:
        # Already exists
        pass
    else:
        print(f"✗ Failed to add {name} = {value}")
        fail_count += 1

# Verify ImpactState enum exists
impact_enum_id = idc.get_enum("ImpactState")
if impact_enum_id == idc.BADADDR:
    print("\nCreating ImpactState enum...")
    impact_enum_id = idc.add_enum(0, "ImpactState", idc.hex_flag())
    idc.add_enum_member(impact_enum_id, "IMPACT_PRISTINE", 0xFF, -1)
    idc.add_enum_member(impact_enum_id, "IMPACT_DAMAGED", 0xA0, -1)
    print("✓ Created ImpactState enum")
    success_count += 1

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("NAMING SUMMARY")
print("="*70 + "\n")

print(f"Successful operations: {success_count}")
print(f"Failed operations: {fail_count}")
print(f"Total operations: {success_count + fail_count}")
print()

print("Named components:")
print(f"  - Dispatch table @ 0x{table_addr:05X}")
print(f"  - {len(dispatch_entries)} dispatch table entries")
print(f"  - {len(dispatch_instructions)} dispatch instructions")
print(f"  - {len(entity_field_comments)} entity field accesses")
print(f"  - {len(function_renames)} key functions")
print(f"  - {len(global_names)} global variables")
print(f"  - {len(category_members)} ObjectCategory enum members")
print()

print("Entity dispatch system fully named in IDA!")

output_file.close()
idc.qexit(0)
