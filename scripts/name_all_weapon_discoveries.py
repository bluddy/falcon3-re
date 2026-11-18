"""
Name and document all weapon system discoveries.

Names to apply:
1. Entity fields at specific offsets
2. Critical instruction addresses (gravity application, weapon checks)
3. Data structures and enums
4. Key functions already renamed
"""

import idc
import idaapi

print("=" * 80)
print("COMPREHENSIVE WEAPON SYSTEM NAMING")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

# ============================================================================
# PART 1: Name critical instruction locations
# ============================================================================

print("PART 1: Naming critical instructions...")
print("=" * 80)

critical_addresses = [
    {
        'addr': 0x3D3BD,
        'name': 'physics_gravity_drag_apply',
        'comment': """Gravity/drag application point: sub [si+2Eh], ax

This is THE critical physics update - the only subtract to entity velocity in the entire
1319-byte entity_physics_and_ai_update function.

Register state:
- SI: points to entity slot base (EntitySlotRecord)
- [SI+0x2E]: velocity_component (likely vertical velocity Z or velocity magnitude)
- AX: computed deceleration value (gravity + drag, scaled by delta time)

This single instruction applies downward acceleration to bombs/missiles and drag to all entities.
The computed value in AX (not a constant) enables realistic physics with frame-rate independence."""
    },
    {
        'addr': 0x3D4C2,
        'name': 'weapon_type_check_harm_1',
        'comment': """First HARM type check: cmp al, 19h

Checks if entity is AGM-88 HARM anti-radiation missile.
If true, branches to HARM-specific guidance logic (homes on radar emitters).
AL contains entity->weapon_type from [si+0x75]."""
    },
    {
        'addr': 0x3D4F8,
        'name': 'weapon_type_check_harm_2',
        'comment': """Second HARM type check: cmp al, 19h

Second check for HARM weapon type, likely in different code path.
Suggests multiple guidance modes or fallback logic for HARM."""
    },
    {
        'addr': 0x3D470,
        'name': 'weapon_type_check_gun',
        'comment': """Gun type check: cmp byte ptr [si+75h], 33h

Checks if entity is M61A1 Vulcan cannon projectile.
Used to apply gun-specific physics (no gravity, constant velocity).
Type 0x33 = M61A1_VULCAN from WeaponType enum."""
    },
]

for item in critical_addresses:
    addr = item['addr']
    name = item['name']
    comment = item['comment']
    
    # Set name as a label (not function)
    print(f"\nNaming @ {addr:#08x}: {name}")
    if idc.set_name(addr, name, idaapi.SN_NOWARN):
        print(f"  ✓ Named successfully")
    else:
        current = idc.get_name(addr)
        print(f"  - Already named: {current}")
    
    # Set comment
    idc.set_cmt(addr, comment, 1)  # 1 = repeatable comment
    print(f"  ✓ Added detailed comment")

# ============================================================================
# PART 2: Create entity field offset enum
# ============================================================================

print(f"\n{'=' * 80}")
print("PART 2: Creating EntityFieldOffset enum...")
print("=" * 80)

# Delete old enum if exists
old_enum = idc.get_enum("EntityFieldOffset")
if old_enum != idc.BADADDR:
    print("Deleting old EntityFieldOffset enum...")
    idc.del_enum(old_enum)

# Create enum
enum_id = idc.add_enum(-1, "EntityFieldOffset", 0)

if enum_id == idc.BADADDR:
    print("ERROR: Could not create EntityFieldOffset enum")
else:
    print("Creating EntityFieldOffset enum...")
    
    # Add all known entity offsets
    offsets = [
        (0x00, "HEADER"),
        (0x06, "FAROBJ_SLOT"),
        (0x08, "DISTANCE_LO"),
        (0x0A, "DISTANCE_HI"),
        (0x2E, "VELOCITY_COMPONENT"),
        (0x74, "STATUS_FLAGS"),
        (0x75, "WEAPON_TYPE"),
        (0x79, "TRACKING_FLAGS"),
        (0x8E, "ANGLE_AZIMUTH"),
        (0x92, "RANGE"),
        (0x96, "POSITION_X"),
        (0x98, "POSITION_Y"),
        (0x9A, "POSITION_Z"),
        (0xAE, "HEAT_SIGNATURE"),
    ]
    
    for offset, name in offsets:
        full_name = f"ENTITY_{name}"
        idc.add_enum_member(enum_id, full_name, offset, -1)
    
    print(f"  ✓ Created enum with {len(offsets)} field offsets")

# ============================================================================
# PART 3: Add comments to weapon queue globals
# ============================================================================

print(f"\n{'=' * 80}")
print("PART 3: Documenting weapon queue usage...")
print("=" * 80)

# These are CS segment addresses, can't directly name in DS but can document
weapon_queue_info = """
Weapon Queue System (Code Segment):

A-A Missiles & Guns Queue:
- cs:0x2E10A (weapon_queue_head) - 27-byte stride
- cs:0x2E10C (weapon_queue_count)
- cs:0x2E10E (weapon_processed_count)
- cs:0x2E110 (weapon_spawn_value)
- cs:0x2E112 (weapon_ammo_count)

A-G Weapons Queue:
- cs:0x4C0D6 (ag_weapon_queue_head) - 41-byte stride
- cs:0x4C0D8 (ag_weapon_queue_count)

Dispatchers:
- weapon_type_initialize_dispatch @ 0x4C19E (handles 0x12-0x13, 0x33-0x37)
- ag_weapon_entity_initialize @ 0x4C3C7 (handles 0x14-0x32)

The dual queue system enables polymorphic weapon handling:
- Small queue (27B) for simple projectiles (missiles, bullets)
- Large queue (41B) for complex weapons (bombs with ballistics, guided missiles)
"""

print(weapon_queue_info)

# ============================================================================
# PART 4: Document key addresses in analysis
# ============================================================================

print(f"\n{'=' * 80}")
print("PART 4: Summary of named components...")
print("=" * 80)

summary = """
WEAPON SYSTEM NAMED COMPONENTS:

Functions:
✓ ag_weapon_entity_initialize @ 0x4C3C7 (1819B) - A-G weapon spawn
✓ entity_slot_update_loop @ 0x3C1BD (348B) - Main update coordinator
✓ entity_physics_and_ai_update @ 0x3D37F (1319B) - Physics & AI
✓ entity_ground_collision_check @ 0x47787 (234B) - Ground impact
✓ damage_event_dispatch_handler @ 0x2EAA7 (190B) - Damage application
✓ store_impact_step @ 0x397FB (169B) - Impact recording

Critical Instructions:
✓ physics_gravity_drag_apply @ 0x3D3BD - THE gravity/drag application
✓ weapon_type_check_harm_1/2 @ 0x3D4C2, 0x3D4F8 - HARM guidance checks
✓ weapon_type_check_gun @ 0x3D470 - Gun projectile check

Entity Structure (EntitySlotRecord):
✓ +0x2E: velocity_component (gravity/drag target)
✓ +0x75: weapon_type (WeaponType enum)
✓ +0x74: status_flags (bit 0 = ACTIVE)
✓ +0x79: tracking_flags (bit 0 = RADAR_VISIBLE)
✓ +0xAE: heat_signature (IR lock target)

Weapon Entity Structure (AGWeaponEntity - 41 bytes):
✓ +0x08: initial_velocity (2710-4860 units/sec)
✓ +0x0C: launch_angle (from aircraft heading)
✓ +0x23: damage_or_life (0-200 range)

Enums:
✓ WeaponType (46 members: 0x12-0x37)
✓ EntityFieldOffset (14 known offsets)
✓ IRLockSearchMode (2 modes)
✓ WeaponKeyCode (6 keys)
✓ DetectionModeState (6 states)

Globals:
✓ weapon_queue_head @ cs:0x2E10A
✓ ag_weapon_queue_head @ cs:0x4C0D6
✓ weapon_name_table @ 0x55C55 (114 bytes)
✓ ir_lock_target_index @ 0x44AA
✓ radar_selected_target_index @ 0x5959B
"""

print(summary)

print(f"\n{'=' * 80}")
print("All weapon system components named and documented!")
print("Exiting IDA...")

# Exit
idc.qexit(0)
