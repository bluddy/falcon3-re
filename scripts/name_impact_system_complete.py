import idc
import idaapi
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\impact_naming_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Naming impact detection system components...")
idaapi.auto_wait()

# Update EntityFieldOffset enum with new discoveries
print("=== Updating EntityFieldOffset Enum ===\n")

enum_id = idc.get_enum("EntityFieldOffset")
if enum_id == idc.BADADDR:
    print("EntityFieldOffset enum not found, creating...")
    enum_id = idc.add_enum(idc.BADADDR, "EntityFieldOffset", 0)

if enum_id != idc.BADADDR:
    # Add new fields
    new_fields = [
        (0x0C, "OBJECT_CATEGORY", "Object category: 4=building, others TBD"),
        (0x10, "IMPACT_STATE", "Impact state: 0xFF=pristine, 0xA0=impacted"),
        (0x7A, "TARGET_SLOT_INDEX", "Target entity slot index for weapon→target linkage"),
    ]
    
    for val, name, comment in new_fields:
        # Check if already exists
        member_id = idc.get_enum_member(enum_id, val, 0, 0)
        if member_id != idc.BADADDR:
            print(f"  Member 0x{val:02X} already exists, updating...")
            idc.set_enum_member_name(member_id, name)
        else:
            result = idc.add_enum_member(enum_id, name, val, idc.BADADDR)
            if result == 0:
                print(f"  ✓ Added 0x{val:02X} = {name}")
            else:
                print(f"  ✗ Failed to add {name} (error {result})")
        
        # Set comment
        member_id = idc.get_enum_member(enum_id, val, 0, 0)
        if member_id != idc.BADADDR:
            idc.set_enum_cmt(member_id, comment, 0)
            print(f"    Comment: {comment}")
else:
    print("ERROR: Could not create enum")

# Create ObjectCategory enum
print("\n\n=== Creating ObjectCategory Enum ===\n")

obj_cat_enum = idc.get_enum("ObjectCategory")
if obj_cat_enum != idc.BADADDR:
    idc.del_enum(obj_cat_enum)
    print("Deleted existing ObjectCategory enum")

obj_cat_enum = idc.add_enum(idc.BADADDR, "ObjectCategory", 0)
if obj_cat_enum != idc.BADADDR:
    print(f"Created ObjectCategory enum (id={obj_cat_enum})")
    
    categories = [
        (0, "UNKNOWN_0", "Unknown category 0"),
        (1, "AIRCRAFT", "Aircraft entities (hypothesis)"),
        (2, "GROUND_VEHICLE", "Tanks, trucks, APCs (hypothesis)"),
        (3, "SHIP", "Naval vessels (hypothesis)"),
        (4, "BUILDING", "Buildings/facilities - CONFIRMED by store_impact_step @ 0x39840"),
        (5, "RADAR_SITE", "Radar installations (hypothesis)"),
        (6, "SAM_SITE", "SAM launchers (hypothesis)"),
        (7, "AAA_SITE", "Anti-aircraft artillery (hypothesis)"),
        (8, "MISSILE_INFLIGHT", "In-flight missiles (hypothesis)"),
        (9, "BOMB_INFLIGHT", "In-flight bombs (hypothesis)"),
        (10, "PROJECTILE", "Gun rounds (hypothesis)"),
    ]
    
    for val, name, comment in categories:
        result = idc.add_enum_member(obj_cat_enum, name, val, idc.BADADDR)
        if result == 0:
            print(f"  ✓ Added {val} = {name}")
            idc.set_enum_cmt(idc.get_enum_member(obj_cat_enum, val, 0, 0), comment, 0)
        else:
            print(f"  ✗ Failed to add {name}")
else:
    print("ERROR: Could not create ObjectCategory enum")

# Add detailed comments to store_impact_step
print("\n\n=== Adding Comments to store_impact_step @ 0x397FB ===\n")

comments = [
    (0x397FB, "Impact detection entry point - called when weapon hits ground"),
    (0x39800, "Check EMS state flags"),
    (0x39807, "Load entity field +0x7A (target_slot_index)"),
    (0x3980A, "Subtract base index DS:0x1360"),
    (0x3980D, "entity_record_table_ops - validate index"),
    (0x39815, "Push SI (weapon entity)"),
    (0x39816, "Load target_slot_index from weapon entity"),
    (0x39819, "Push for later use"),
    (0x3981A, "Negate DX (damage amount?)"),
    (0x3981C, "Clamp damage to minimum 0x28"),
    (0x39824, "Clamp damage to maximum 0xFF"),
    (0x3982D, "Set damage parameters BL=0x10, BH=damage"),
    (0x39830, "BP = 0xFFFF"),
    (0x39833, "Call impact sprite/effect handler"),
    (0x39838, "Pop target index"),
    (0x39839, "Pop SI (weapon entity)"),
    (0x3983A, "*** CRITICAL: r12_farptr_load_thunk loads target entity ***"),
    (0x3983A, "Uses [weapon+7Ah] to load ES:DI = target EntitySlotRecord"),
    (0x3983F, "*** BREAKTHROUGH: Check target object_category == 4 (BUILDING) ***"),
    (0x39844, "Check target impact_state == 0xFF (pristine)"),
    (0x39848, "Set CL=0 (not already hit)"),
    (0x3984A, "If already impacted (!=0xFF), skip to 0x39853"),
    (0x3984C, "Set CL=1 (first hit on this target)"),
    (0x3984D, "Push weapon entity"),
    (0x3984E, "Push target entity"),
    (0x3984F, "Load weapon position [si+50h]"),
    (0x39852, "Load weapon position [si+52h]"),
    (0x39855, "DI=0 for sprite check"),
    (0x39857, "sprite_clip_bounds_check - check if on screen"),
    (0x3985C, "Pop target entity"),
    (0x3985D, "Pop weapon entity"),
    (0x3985E, "Re-check impact_state"),
    (0x39863, "If pristine, jump to set impact state"),
    (0x39865, "Already hit: call farobj_index_range_check"),
    (0x3986D, "Jump to clear carry and return"),
    (0x3986F, "*** CRITICAL: Set target impact_state = 0xA0 (impacted) ***"),
    (0x39874, "*** CRITICAL: Set weapon status_flags bit 2 (DESTROYED) ***"),
    (0x39877, "Clear weapon velocity [si+34h] = 0"),
    (0x3987C, "Clear weapon velocity [si+36h] = 0"),
    (0x39881, "Clear weapon velocity [si+38h] = 0"),
    (0x39886, "Load weapon field [si+14h]"),
    (0x39889, "Load damage scale DS:0x1356"),
    (0x3988D, "Multiply for damage calculation"),
    (0x3988E, "Shift left (x2)"),
    (0x39890, "Rotate carry into DX"),
    (0x39892, "Shift right (divide by 2)"),
    (0x39894, "Store result back to [si+14h]"),
    (0x39897, "Clear carry flag"),
    (0x39898, "Return from function"),
]

for addr, comment in comments:
    idc.set_cmt(addr, comment, 0)
    print(f"✓ 0x{addr:X}: {comment[:60]}...")

# Add function comment
func_comment = """Impact detection and damage application function.

INPUTS:
  SI = weapon entity (EntitySlotRecord)
  DX = damage amount (negated, clamped to 0x28-0xFF)

PROCESS:
1. Validates target index from [SI+7Ah] (target_slot_index)
2. Loads target entity via r12_farptr_load_thunk → ES:DI
3. Checks target object_category [DI+0Ch]:
   - If == 4 (BUILDING): special building impact handling
   - Else: generic impact handling
4. Checks target impact_state [DI+10h]:
   - If 0xFF (pristine): first hit, set to 0xA0 (impacted)
   - Else: already hit, skip impact processing
5. Sets weapon status_flags [SI+74h] bit 2 (DESTROYED)
6. Clears weapon velocity fields
7. Calculates and stores damage value

CRITICAL DISCOVERY:
  Both SI and DI point to EntitySlotRecord structures!
  - SI = weapon entity (bomb, missile)
  - DI = target entity (building, vehicle, ship)
  - [SI+7Ah] links weapon to target (target_slot_index)

RETURNS:
  Carry flag set if error, clear if success
"""

idc.set_func_cmt(0x397FB, func_comment, 1)
print("\n✓ Added comprehensive function comment to store_impact_step")

# Add comment to r12_farptr_load_thunk
print("\n\n=== Adding Comment to r12_farptr_load_thunk @ 0x41B32 ===\n")

thunk_comment = """Far pointer load thunk - loads EntitySlotRecord by index.

INPUT:
  AX = entity slot index

CALCULATION:
  ES:DI = EntitySlotRecord array base + (index - base_offset) * stride
  
DETAILS:
  Segment: 0x54AF
  Base offset: 0x386F
  Base index: word_55E50
  Stride: 0x5C (92 bytes)
  
FORMULA:
  linear_index = AX - word_55E50
  byte_offset = linear_index * 0x5C
  ES:DI = 0x54AF:0x386F + byte_offset

RESULT:
  ES:DI → EntitySlotRecord for the given index
  
USED BY:
  store_impact_step to load target entity from weapon's target_slot_index
  Multiple other systems for entity lookups

CRITICAL INSIGHT:
  This function proves that the mystery "DI structure" in store_impact_step
  is actually EntitySlotRecord - the same 92-byte structure used everywhere!
"""

idc.set_func_cmt(0x41B32, thunk_comment, 1)
print("✓ Added comprehensive comment to r12_farptr_load_thunk")

# Name the base index global
print("\n\n=== Naming Global Variables ===\n")

# word_55E50 is the entity index base
if idc.set_name(0x55E50, "entity_slot_index_base", idc.SN_CHECK):
    print("✓ Named 0x55E50 → entity_slot_index_base")
    idc.set_cmt(0x55E50, "Base index for entity slot array. Subtracted from slot index before multiplication by stride.", 0)
else:
    print("✗ Failed to name entity_slot_index_base")

# DS:0x1356 is damage scale
ds_seg = 0x54AF
damage_scale_addr = (ds_seg << 4) + 0x1356
if idc.set_name(damage_scale_addr, "weapon_damage_scale", idc.SN_CHECK):
    print("✓ Named DS:0x1356 → weapon_damage_scale")
    idc.set_cmt(damage_scale_addr, "Damage scale multiplier used in impact calculation", 0)
else:
    print("✗ Failed to name weapon_damage_scale")

# DS:0x1360 is entity base offset
entity_base_addr = (ds_seg << 4) + 0x1360
if idc.set_name(entity_base_addr, "entity_table_base_offset", idc.SN_CHECK):
    print("✓ Named DS:0x1360 → entity_table_base_offset")
    idc.set_cmt(entity_base_addr, "Entity table base offset for index calculations", 0)
else:
    print("✗ Failed to name entity_table_base_offset")

print("\n\nImpact system naming complete.")
output_file.close()
idc.qexit(0)
