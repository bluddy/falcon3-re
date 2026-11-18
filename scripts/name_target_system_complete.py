import idc
import idaapi
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\target_naming_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting target system comprehensive naming...")
idaapi.auto_wait()

# ============================================================================
# FUNCTION NAMING
# ============================================================================

functions = [
    (0x32D22, "mission_state_initializer", "Initializes mission state and objectives (850B)"),
    (0x3E96F, "ai_target_priority_evaluator", "Evaluates target priority for AI, checks 11 target count fields [di+0xB3-0xBF] (479B)"),
    (0x4478D, "farobj_slot_target_search", "Searches entity slots for valid targets (222B)"),
    (0x48B05, "target_cycle_scan", "Scans entities for HUD target cycling, checks status/damage/tracking flags (283B)"),
    (0x48C20, "target_processing_helper", "Helper function called by target_cycle_scan for target processing"),
]

print("=== NAMING FUNCTIONS ===\n")
for addr, name, comment in functions:
    # Set function name
    if idc.set_name(addr, name, idc.SN_CHECK):
        print(f"✓ Named function 0x{addr:X} -> {name}")
        # Set function comment
        idc.set_func_cmt(addr, comment, 0)
        print(f"  Comment: {comment}")
    else:
        existing = idc.get_name(addr)
        print(f"✗ Failed to name 0x{addr:X} (existing: {existing})")
    print()

# ============================================================================
# GLOBAL VARIABLE NAMING
# ============================================================================

globals_list = [
    (0x59380, "target_scan_mode_flag", "byte", "Target scanning mode (0=inactive)"),
    (0x593A0, "target_cycle_timer", "word", "Target cycle timer, decremented each frame"),
    (0x5948E, "target_cycle_direction", "byte", "Target cycle direction (-1/0/+1), negated when timer expires"),
    (0x593A4, "target_previous_or_alternate", "word", "Previous/alternate target index (0xFFFF=none)"),
    (0x593A6, "target_current_selected", "word", "Current selected target entity index (0xFFFF=none)"),
    (0x593A8, "target_maximum_count", "word", "Maximum target count / entity array boundary"),
    (0x593B0, "target_data_pointer", "word", "Pointer to target data structure for HUD"),
    (0x59306, "target_related_flag", "word", "Target-related flag/counter (initialized to 0)"),
    (0x58F9A, "target_type_selector", "word", "Current target type selector/index"),
]

print("\n=== NAMING GLOBAL VARIABLES ===\n")
for addr, name, type_name, comment in globals_list:
    # Calculate segment:offset for DS variables
    ds_seg = 0x54AF  # DS segment
    full_addr = (ds_seg << 4) + addr
    
    if idc.set_name(full_addr, name, idc.SN_CHECK):
        print(f"✓ Named global 0x{addr:X} (DS:0x{addr:X}) -> {name}")
        # Set comment
        idc.set_cmt(full_addr, comment, 0)
        print(f"  Type: {type_name}, Comment: {comment}")
    else:
        existing = idc.get_name(full_addr)
        print(f"✗ Failed to name 0x{addr:X} (existing: {existing})")
    print()

# ============================================================================
# ENTITY STRUCTURE FIELDS (Create Enum)
# ============================================================================

print("\n=== CREATING ENTITY FIELD ENUM (EntityFieldOffset) ===\n")

# Delete existing enum if present
enum_id = idc.get_enum("EntityFieldOffset")
if enum_id != idc.BADADDR:
    idc.del_enum(enum_id)
    print("Deleted existing EntityFieldOffset enum")

# Create new enum
enum_id = idc.add_enum(idc.BADADDR, "EntityFieldOffset", 0)
if enum_id == idc.BADADDR:
    print("ERROR: Failed to create EntityFieldOffset enum")
else:
    print(f"Created EntityFieldOffset enum (id={enum_id})")
    
    # Add enum members
    entity_fields = [
        (0x00, "HEADER", "Header fields start"),
        (0x06, "FAROBJ_SLOT", "FarObj main table slot index"),
        (0x08, "DISTANCE_LO", "Distance to player (lo word)"),
        (0x0A, "DISTANCE_HI", "Distance to player (hi word)"),
        (0x2E, "VELOCITY_COMPONENT", "Velocity component (gravity/drag applied here)"),
        (0x74, "STATUS_FLAGS", "Entity status flags (bit 0=ACTIVE, bit 2=DESTROYED, bit 6=AIRCRAFT_TYPE)"),
        (0x75, "WEAPON_TYPE", "Weapon type (WeaponType enum, 0=not a weapon)"),
        (0x76, "UNKNOWN_FLAGS_76", "Unknown flags (bit 7 checked by target scanning)"),
        (0x79, "TRACKING_FLAGS", "Tracking flags (bit 0=RADAR_VISIBLE)"),
        (0x8E, "ANGLE_AZIMUTH", "Azimuth angle from player (14-bit)"),
        (0x92, "RANGE", "Computed range to player"),
        (0x96, "POSITION_X", "World X position"),
        (0x98, "POSITION_Y", "World Y position"),
        (0x9A, "POSITION_Z", "World Z position / altitude"),
        (0xAE, "HEAT_SIGNATURE_OR_TARGET_FLAG", "IR visibility for AIM-9 / checked by target_cycle_scan"),
        (0xCA, "DAMAGE_STATUS_FLAGS", "Damage state flags (DAMAGE_NAV)"),
    ]
    
    for value, name, comment in entity_fields:
        result = idc.add_enum_member(enum_id, name, value, idc.BADADDR)
        if result == 0:
            print(f"  ✓ Added 0x{value:02X} = {name}")
            # Set member comment
            idc.set_enum_cmt(idc.get_enum_member(enum_id, value, 0, 0), comment, 0)
        else:
            print(f"  ✗ Failed to add {name} (error {result})")

# ============================================================================
# DAMAGE STATUS FLAGS ENUM
# ============================================================================

print("\n=== CREATING DAMAGE STATUS FLAGS ENUM ===\n")

enum_id = idc.get_enum("DamageStatusFlags")
if enum_id != idc.BADADDR:
    idc.del_enum(enum_id)
    print("Deleted existing DamageStatusFlags enum")

enum_id = idc.add_enum(idc.BADADDR, "DamageStatusFlags", idc.HEX_FLAG)
if enum_id == idc.BADADDR:
    print("ERROR: Failed to create DamageStatusFlags enum")
else:
    print(f"Created DamageStatusFlags enum (id={enum_id})")
    
    # We only know one flag so far
    damage_flags = [
        (0x0001, "DAMAGE_NAV", "Navigation/tracking damage flag (checked by target_cycle_scan)"),
    ]
    
    for value, name, comment in damage_flags:
        result = idc.add_enum_member(enum_id, name, value, idc.BADADDR)
        if result == 0:
            print(f"  ✓ Added 0x{value:04X} = {name}")
            idc.set_enum_cmt(idc.get_enum_member(enum_id, value, 0, 0), comment, 0)
        else:
            print(f"  ✗ Failed to add {name} (error {result})")

# ============================================================================
# STRING NAMING (Building Types and Mission Messages)
# ============================================================================

print("\n=== NAMING TARGET/MISSION STRINGS ===\n")

strings_to_name = [
    (0x55121, "str_RUNWAY", "RUNWAY"),
    (0x57BB3, "str_PRIMARY_TARGET_1", "PRIMARY TARGET."),
    (0x57C45, "str_PRIMARY_TARGET_2", "PRIMARY TARGET."),
    (0x14FF93, "str_BRIDGE_1", "BRIDGE"),
    (0x15020D, "str_HANGAR", "HANGAR"),
    (0x150214, "str_RUNWAY_2", "RUNWAY"),
    (0x15022D, "str_BRIDGE_2", "BRIDGE"),
    (0x150284, "str_FACTORY", "FACTORY"),
    (0x150293, "str_WAREHOUSE", "WAREHOUSE"),
    (0x1509DC, "str_GROUND_TARGETS_DESTROYED_1", "GROUND TARGETS DESTROYED: 0"),
    (0x1509F9, "str_CLASS_A_TARGET", "CLASS A TARGET: "),
    (0x150A0B, "str_CLASS_B_TARGET", "CLASS B TARGET: "),
    (0x150A1D, "str_CLASS_C_TARGET", "CLASS C TARGET: "),
    (0x150A2F, "str_CLASS_D_TARGET", "CLASS D TARGET: "),
    (0x150BE0, "str_GROUND_TARGETS_DESTROYED_2", "GROUND TARGETS DESTROYED:"),
    (0x150BFB, "str_CLASS_A_TARGETS", "CLASS A TARGETS:"),
    (0x150C0D, "str_CLASS_B_TARGETS", "CLASS B TARGETS:"),
    (0x150C1F, "str_CLASS_C_TARGETS", "CLASS C TARGETS:"),
    (0x150C31, "str_CLASS_D_TARGETS", "CLASS D TARGETS:"),
    (0x151221, "str_HANGAR_2", "HANGAR"),
    (0x189994, "str_PRIMARY_TARGET_3", "PRIMARY TARGET"),
    (0x189AD9, "str_DAMAGED_PRIMARY", "DAMAGED A PRIMARY TARGET."),
    (0x189AF4, "str_DESTROYED_PRIMARY", "DESTROYED A PRIMARY TARGET."),
    (0x189CE3, "str_MISSION_SUCCESSFUL_1", "MISSION SUCCESSFUL."),
    (0x189CF7, "str_MISSION_FAILURE_1", "MISSION FAILURE."),
    (0x189ED8, "str_MISSION_SUCCESSFUL_2", "MISSION SUCCESSFUL."),
    (0x189EEC, "str_MISSION_FAILURE_2", "MISSION FAILURE."),
]

for addr, name, text in strings_to_name:
    if idc.set_name(addr, name, idc.SN_CHECK):
        print(f"✓ Named string 0x{addr:X} -> {name}")
        print(f"  Text: '{text}'")
    else:
        existing = idc.get_name(addr)
        print(f"✗ Failed to name 0x{addr:X} (existing: {existing})")

# ============================================================================
# CRITICAL INSTRUCTION COMMENTS IN TARGET FUNCTIONS
# ============================================================================

print("\n\n=== ADDING COMMENTS TO TARGET SYSTEM INSTRUCTIONS ===\n")

instruction_comments = [
    # target_cycle_scan @ 0x48B05
    (0x48B09, "Check entity damage_status_flags (+0xCA) for DAMAGE_NAV flag"),
    (0x48B10, "Check target_scan_mode_flag @ DS:0x59380"),
    (0x48B1A, "Load target_type_selector @ DS:0x58F9A"),
    (0x48B1D, "Index into entity field table at +0x487Eh"),
    (0x48B23, "Check entity field +0xAE (heat_signature/target_flag) against 0"),
    (0x48B30, "Compare target_type_selector with 2 (special case)"),
    (0x48B3F, "Decrement target_cycle_timer @ DS:0x593A0"),
    (0x48B4A, "Reset target_cycle_timer to 0 when expired"),
    (0x48B4E, "Negate target_cycle_direction @ DS:0x5948E (reverse scan)"),
    (0x48B52, "Load target_current_selected @ DS:0x593A6"),
    (0x48B57, "Compare current target with 0xFFFF (no target)"),
    (0x48B5E, "Index entity table at offset 0x1734h (4-byte stride)"),
    (0x48B64, "Load entity status_flags (+0x74)"),
    (0x48B67, "Test ACTIVE flag (bit 0)"),
    (0x48B6D, "Test AIRCRAFT_TYPE flag (bit 6, value 0x40)"),
    (0x48B74, "Test entity field +0x76 bit 7 (0x80)"),
    (0x48B82, "Call far_obj_field_call with entity type"),
    (0x48B8D, "Compare returned value with 2"),
    (0x48B93, "Load target_data_pointer @ DS:0x593B0 into DI"),
    (0x48B96, "Call target_processing_helper @ 0x48C20"),
    (0x48B9B, "Store result to target_cycle_direction"),
    
    # ai_target_priority_evaluator @ 0x3E96F
    (0x3E988, "Check target_count_field_1 [di+0xBEh] == 0"),
    (0x3E9B7, "Check target_count_field_2 [di+0xBFh] == 0"),
    (0x3E9FC, "Check target_count_field_3 [di+0xB3h] == 0"),
    (0x3EA32, "Check target_count_field_4 [di+0xB4h] == 0"),
    (0x3EA61, "Check target_count_field_5 [di+0xB5h] == 0"),
    (0x3EA97, "Check target_count_field_6 [di+0xBBh] == 0"),
    (0x3EAAB, "Check target_count_field_7 [di+0xB6h] == 0"),
    (0x3EABF, "Check target_count_field_8 [di+0xB7h] == 0"),
    (0x3EAD3, "Check target_count_field_9 [di+0xB8h] == 0"),
    (0x3EAE7, "Check target_count_field_10 [di+0xBAh] == 0"),
    (0x3EB03, "Check target_count_field_11 [di+0xBCh] == 0"),
    
    # store_impact_step @ 0x397FB
    (0x39838, "Check entity subtype field [di+0Ch] == 4 (building type indicator?)"),
    (0x39844, "Check entity impact state [di+10h] == 0xFF (pristine)"),
    (0x3986D, "Set entity impact state [di+10h] = 0xA0 (impacted)"),
    (0x39872, "Set entity status_flags [si+74h] bit 2 (DESTROYED flag)"),
]

for addr, comment in instruction_comments:
    idc.set_cmt(addr, comment, 0)
    print(f"✓ Comment @ 0x{addr:X}: {comment[:60]}...")

print("\n\nTarget system comprehensive naming complete.")
output_file.close()
idc.qexit(0)
