# Target and Mission Objective System - Findings

## Overview
Falcon 3.0's target system uses a classification scheme (CLASS A/B/C/D) to categorize ground targets. When weapons hit the ground and cause damage, the game checks if specific building/facility entities were destroyed to determine mission success.

## Target Classification

### Target Classes
The game uses a four-tier classification system:

- **CLASS A TARGET** - Highest priority (typically primary objectives)
- **CLASS B TARGET** - Secondary priority
- **CLASS C TARGET** - Tertiary priority  
- **CLASS D TARGET** - Lowest priority

### Strings Found
```
0x1509F9: "CLASS A TARGET: "
0x150A0B: "CLASS B TARGET: "
0x150A1D: "CLASS C TARGET: "
0x150A2F: "CLASS D TARGET: "
0x150BFB: "CLASS A TARGETS:"
0x150C0D: "CLASS B TARGETS:"
0x150C1F: "CLASS C TARGETS:"
0x150C31: "CLASS D TARGETS:"
```

### Score Tracking
```
0x1509DC: "GROUND TARGETS DESTROYED: 0"
0x150BE0: "GROUND TARGETS DESTROYED:"
```

## Building/Facility Types

### Known Building Types (Strings at 0x15020D-0x150293)
```
0x15020D: "HANGAR"
0x150214: "RUNWAY"
0x15022D: "BRIDGE"
0x150284: "FACTORY"
0x150293: "WAREHOUSE"
```

These are likely the building types that can be mission objectives. Notice RUNWAY is particularly important for interdiction missions.

## Mission Success/Failure

### Mission Completion Strings
```
0x189AD9: "DAMAGED A PRIMARY TARGET."
0x189AF4: "DESTROYED A PRIMARY TARGET."
0x189CE3: "MISSION SUCCESSFUL."
0x189CF7: "MISSION FAILURE."
0x189994: "PRIMARY TARGET"
```

The game distinguishes between damaging and destroying primary targets, suggesting a health/damage threshold system for buildings.

## Key Functions

### target_cycle_scan @ 0x48B05 (283 bytes)
**Purpose**: Scans entities to find valid targets for HUD display/radar

**Key Checks**:
```assembly
test word ptr [si+0CAh], DAMAGE_NAV  ; Check entity damage status
cmp byte_59380, al                    ; Some global mode flag
cmp [bx+0AEh], al                     ; Entity field at +0xAE (unknown)
mov cl, es:[bx+74h]                   ; Load status_flags (+0x74 - KNOWN FIELD!)
test cl, 1                            ; Check ACTIVE flag
test cl, 40h                          ; Check AIRCRAFT_TYPE flag (0x40)
test byte ptr es:[bx+76h], 80h       ; Check field +0x76 bit 7
```

**Findings**:
- Uses entity field +0xCAh for damage tracking (DAMAGE_STATUS_FLAGS)
- Checks entity +0x74 (status_flags) - confirms our entity structure
- Checks entity +0x76 bit 7 - new field discovery
- Checks entity +0xAE - new field discovery
- References entity table at offset 0x1734h
- Uses global word_593A6/593A4/593A8 for target tracking

### ai_target_priority_evaluator @ 0x3E96F (479 bytes)
**Purpose**: Evaluates target priority for AI decision-making

**Target Count Fields** (probably a structure with target counts):
```
[di+0B3h] - Target count field 1
[di+0B4h] - Target count field 2
[di+0B5h] - Target count field 3
[di+0B6h] - Target count field 4
[di+0B7h] - Target count field 5
[di+0B8h] - Target count field 6
[di+0BAh] - Target count field 7
[di+0BBh] - Target count field 8
[di+0BCh] - Target count field 9
[di+0BEh] - Target count field 10
[di+0BFh] - Target count field 11
```

These consecutive byte fields (0xB3-0xBF range) likely store counts of each target class remaining, allowing AI to prioritize which targets to attack.

### mission_state_initializer @ 0x32D22 (850 bytes)
**Purpose**: Initializes mission state including objectives
**Size**: 850 bytes (very large - likely loads mission data)

No string references found in disassembly, suggesting it works with binary mission data structures.

## Entity Structure Discoveries

### New Entity Fields Found

#### EntitySlotRecord +0x76 (unknown_flags_76)
- Bit 7 (0x80): Checked by target_cycle_scan
- Purpose: Unknown, but related to target selection

#### EntitySlotRecord +0xAE (unknown_field_ae)
- Type: Likely uint8
- Purpose: Checked against 0 in target scanning
- Possibly target designation or lock status

#### EntitySlotRecord +0xCA (damage_status_flags)
- Type: Bitfield (uint16)
- Purpose: Tracks entity damage state
- Known flag: DAMAGE_NAV
- Checked by target_cycle_scan to filter damaged entities

### Global Variables

```
byte_59380      - Target scanning mode flag
word_58F9A      - Current target index or type selector
word_593A0      - Counter/timer for target cycling
byte_5948E      - Target scan direction (-1, 0, +1)
word_593A6      - Current selected target entity
word_593A4      - Previous target or alternate target
word_593A8      - Maximum target count
word_593A0      - Target cycle timer
word_593B0      - Target data pointer
word_59306      - Target-related flag/counter
```

## Target Hit Detection

### Ground Collision Flow
```
entity_physics_and_ai_update @ 0x3D37F
  ↓ (calls)
entity_ground_collision_check @ 0x47787
  ↓ (checks altitude [si+8] vs terrain)
  ↓ (if hit)
store_impact_step @ 0x397FB
  ↓ (records impact, checks [di+0Ch] == 4)
  ↓ (sets [di+10h] impact state)
damage_event_dispatch_handler @ 0x2EAA7
  ↓ (determines damage to target)
[Mission objective checking]
  ↓
[Update target destruction counters]
```

### How Building Hits Are Detected

From `store_impact_step` analysis:
```assembly
cmp word ptr [di+0Ch], 4      ; Check entity sub-type field == 4
cmp byte ptr [di+10h], 0FFh   ; Check if already impacted
mov byte ptr [di+10h], 0A0h   ; Set impact state = 0xA0
or byte ptr [si+74h], 4       ; Set status_flags bit 2 (DESTROYED?)
```

**Theory**: 
1. When a bomb hits terrain, `entity_ground_collision_check` detects altitude <= terrain_height
2. `store_impact_step` is called to record the impact location
3. The game then scans nearby entities (buildings) to see if any are at the impact coordinates
4. Buildings have entity field `[di+0Ch]` == 4 (building type indicator)
5. Impact state `[di+10h]` tracks if building was already hit (0xFF = pristine, 0xA0 = impacted)
6. Entity status_flags `[si+74h]` bit 2 is set to mark entity as destroyed

### Building Entity Detection

**Question**: How does the game know which entity is a RUNWAY vs HANGAR vs WAREHOUSE?

**Possibilities**:
1. Entity type field +0x75 (weapon_type for weapons) might have different meaning for non-weapon entities
2. Building subtype stored at +0x0C (value 4 detected in store_impact_step)
3. Separate building type field not yet discovered
4. Buildings referenced by mission data structure with type information

## Mission Objectives System

### Primary Target Flow
```
Mission Start
  ↓
mission_state_initializer @ 0x32D22 (loads objectives)
  ↓
[Mission data defines primary/secondary targets]
  ↓
[Player attacks targets with A-G weapons]
  ↓
Ground collision + damage detection
  ↓
Check if hit entity is a primary/secondary objective
  ↓
Update destruction counters ([di+0B3h] - [di+0BFh])
  ↓
Check mission completion criteria
  ↓
Display "DAMAGED/DESTROYED A PRIMARY TARGET"
  ↓
If all primary targets destroyed: "MISSION SUCCESSFUL"
```

## Remaining Questions

### Critical Unknowns
1. **Building entity type encoding**: How are RUNWAY/HANGAR/etc differentiated?
   - Possibly entity field +0x75 for non-weapons
   - Possibly building subtype at +0x0C
   - Possibly separate lookup table

2. **Mission data structure**: Where are objectives defined?
   - Likely loaded by mission_state_initializer @ 0x32D22
   - Probably external mission files (.CAM files?)
   - Contains target entity IDs and success criteria

3. **Target designation in HUD**: How does CCIP know about ground targets?
   - target_cycle_scan @ 0x48B05 iterates entities
   - Filters by status_flags +0x74 (ACTIVE, AIRCRAFT_TYPE)
   - Uses damage_status_flags +0xCAh
   - Current target stored in word_593A6

4. **Blast radius calculation**: How is "near" defined for building damage?
   - store_impact_step calls `sprite_clip_bounds_check`
   - Uses entity position fields [si+50h], [si+52h]
   - Likely checks 2D distance from impact point

5. **Damage accumulation**: Can buildings survive multiple hits?
   - "DAMAGED A PRIMARY TARGET" vs "DESTROYED A PRIMARY TARGET" suggests yes
   - Building health probably stored in entity structure
   - Full analysis of damage_event_dispatch_handler @ 0x2EAA7 needed

## Next Steps

1. ✅ Find mission objective strings and classification system
2. ✅ Identify key target scanning functions  
3. ✅ Discover new entity structure fields (+0x76, +0xAE, +0xCAh)
4. ⏸️ Analyze mission_state_initializer to find objective data format
5. ⏸️ Determine building entity type encoding
6. ⏸️ Find damage calculation for area weapons (blast radius)
7. ⏸️ Map complete flow from weapon impact to mission success
8. ⏸️ Update entity structure in registry with new fields
9. ⏸️ Name all discovered functions and globals in IDA

## Entity Structure Updates Needed

```c
struct EntitySlotRecord {
    // ... (existing fields)
    uint8 status_flags;           // +0x74 (ACTIVE=1, DESTROYED=4, AIRCRAFT_TYPE=0x40)
    uint8 weapon_or_entity_type;  // +0x75 (weapons: 0x12-0x37, buildings: TBD)
    uint8 unknown_flags_76;       // +0x76 (bit 7 used in target scanning)
    // ...
    uint16 unknown_field_ae;      // +0xAE (checked in target scanning)
    // ...
    uint16 damage_status_flags;   // +0xCA (DAMAGE_NAV flag for entity damage state)
};
```

## Target Priority Structure

```c
// Structure passed to ai_target_priority_evaluator
struct TargetPriorityData {
    uint8 unknown_fields[0xB3];
    uint8 target_count_1;   // +0xB3
    uint8 target_count_2;   // +0xB4
    uint8 target_count_3;   // +0xB5
    uint8 target_count_4;   // +0xB6
    uint8 target_count_5;   // +0xB7
    uint8 target_count_6;   // +0xB8
    uint8 reserved_b9;      // +0xB9
    uint8 target_count_7;   // +0xBA
    uint8 target_count_8;   // +0xBB
    uint8 target_count_9;   // +0xBC
    uint8 reserved_bd;      // +0xBD
    uint8 target_count_10;  // +0xBE
    uint8 target_count_11;  // +0xBF
};
```

Likely these correspond to CLASS A/B/C/D target counts and subcategories.

## Summary

The target system is sophisticated:
- 4-tier classification (A/B/C/D)
- 5+ building types (HANGAR, RUNWAY, BRIDGE, FACTORY, WAREHOUSE)
- Damage vs destruction distinction for primary targets
- Target cycling for HUD/radar display
- AI target priority evaluation
- Mission success/failure based on objective completion

The connection between weapon impacts and building damage is partially understood:
1. Bomb hits ground → entity_ground_collision_check
2. Impact recorded → store_impact_step (checks entity type, sets impact state)
3. Damage calculated → damage_event_dispatch_handler
4. Mission objectives updated → (checking target destruction)

Building entity identification remains the key unknown - need to find where RUNWAY/HANGAR/etc are encoded in entity structure or mission data.
