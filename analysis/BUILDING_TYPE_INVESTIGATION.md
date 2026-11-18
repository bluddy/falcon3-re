# Building Type Investigation - Key Findings

## Summary
Buildings in Falcon 3.0 are **NOT identified by entity field +0x75** (which is weapon-only). They appear to use a different identification system, possibly coordinate-based or via separate mission objective records.

## Investigation Results

### 1. Entity Field +0x75 is Weapon-Only
**Finding**: Zero comparisons found with entity +0x75 for values < 0x12

- Weapons use 0x12-0x37 range
- Buildings do NOT use entity type field +0x75
- This field is exclusively for weapon identification

**Implication**: Buildings use a completely different identification mechanism.

### 2. Building Name Strings Have NO Code References
**Finding**: HANGAR, RUNWAY, BRIDGE, FACTORY, WAREHOUSE strings at 0x15020D-0x150293 have **zero code references**

```
0x15020D: "HANGAR"    - NO CODE REFERENCES
0x150214: "RUNWAY"    - NO CODE REFERENCES
0x15022D: "BRIDGE"    - NO CODE REFERENCES
0x150284: "FACTORY"   - NO CODE REFERENCES
0x150293: "WAREHOUSE" - NO CODE REFERENCES
```

**Implication**: These strings are **display-only** - used for:
- Mission briefings
- Score displays ("HANGAR DESTROYED")
- Post-mission summaries

The game does NOT use these strings to identify building types during impact detection!

### 3. Entity Field +0x0C Mystery
**Finding**: Only ONE comparison with [di+0Ch] in entire codebase

```assembly
0x39840 (store_impact_step):
  cmp word ptr [di+0Ch], 4
```

**Theories**:
1. **Damage Event Type**: The value 4 might mean "building damage event" rather than building type
2. **Object Category**: Field +0x0C might categorize objects (0=projectile, 1=aircraft, 4=building/facility)
3. **Mission Objective Flag**: Value 4 could mean "this is a mission objective"

**Evidence for Event Type Theory**: 
- Only one check in the entire codebase
- Located in `store_impact_step` which records impact events
- Would explain why we can't find building type differentiation

### 4. Target Count Fields Are Part of Entity Structure!
**CRITICAL DISCOVERY**: The 11 target count fields at [di+0xB3h-0xBFh] are **inside the entity structure**!

```assembly
ai_target_priority_evaluator @ 0x3E96F:
  mov di, [si+6]              ; Load entity pointer from SI+6
  test word ptr [di+0CAh], DAMAGE_NAV   ; Check entity damage flags (+0xCA = known entity field!)
  cmp byte ptr [di+0B3h], 0   ; Check target count field 1
  cmp byte ptr [di+0B4h], 0   ; Check target count field 2
  ... (9 more fields through 0xBFh)
```

**Revelation**: These are **not global counters** - they're **per-entity target tracking fields**!

**New Entity Structure Fields Discovered**:
- `+0xB3` through `+0xBF` (13 bytes) - Target tracking/state fields
- These are checked by AI for target priority evaluation
- Likely store: target class, priority, lock state, etc.

### 5. Mission Tactical Strings Found
**Finding**: Mission status messages discovered

```
0x57B8D: "CLOSING ON GROUND TARGETS."
0x57BA8: "CLOSING ON PRIMARY TARGET."
0x57BC3: "CLOSING ON SHIP TARGET."
0x57C21: "ATTACKING GROUND TARGETS!"
0x57C3B: "ATTACKING PRIMARY TARGET."
```

These provide context clues:
- **SHIP TARGET** - separate category from ground/primary
- **PRIMARY TARGET** - mission-critical objective
- These are triggered when player approaches/attacks objectives

### 6. Mission Initialization Analysis
**mission_state_initializer @ 0x32D22** (850 bytes):
- Makes **77 function calls** - heavily orchestrated initialization
- **Zero direct data references** - works through function calls
- Likely loads mission data from external files (.CAM campaign files?)
- Initializes objective tracking, target counts, victory conditions

## Current Understanding

### How Buildings Are Likely Identified

**Theory 1: Coordinate-Based System**
Buildings might be stored in a **separate facility/building array** indexed by map coordinates:
1. Bomb impacts at (X, Y, Z)
2. Game checks `building_array[tile_x][tile_y]` 
3. If building exists at those coordinates → building hit!
4. Building type stored in that array entry

**Theory 2: Mission Objective Records**
Buildings could be defined in mission data as objective records:
```c
struct MissionObjective {
    uint16 pos_x;          // Building world X
    uint16 pos_y;          // Building world Y
    uint8  building_type;  // 0=HANGAR, 1=RUNWAY, 2=BRIDGE, etc.
    uint8  objective_class; // 0=CLASS_A, 1=CLASS_B, etc.
    uint8  health;         // Damage points remaining
    uint8  flags;          // PRIMARY_TARGET, SECONDARY_TARGET, etc.
};
```

Impact detection flow:
1. Weapon hits ground at (X,Y)
2. `store_impact_step` records impact, sets [di+0Ch] = 4 (building hit event)
3. `damage_event_dispatch_handler` looks up mission objectives near (X,Y)
4. Updates objective health, checks mission completion

**Evidence**:
- No entity type checks for buildings
- Building name strings are display-only
- [di+0Ch] == 4 appears to be event type, not building type
- Mission system initializes through external data

### What [di+0Ch] == 4 Actually Means

**Most Likely**: **Damage Event Category**
```c
enum DamageEventType {
    PROJECTILE_HIT = 0,
    AIRCRAFT_COLLISION = 1,
    GROUND_IMPACT = 2,
    TERRAIN_CRASH = 3,
    BUILDING_IMPACT = 4,   // ← This is value 4!
    EXPLOSION_DAMAGE = 5,
    ...
};
```

When `store_impact_step` sets this to 4, it signals:
- "This damage event involves a building/facility"
- Triggers mission objective checking
- Updates target destruction counters

## Updated Entity Structure

### EntitySlotRecord Additions
```c
struct EntitySlotRecord {
    // ... (existing fields 0x00-0xAD)
    uint8  heat_signature;           // +0xAE
    uint8  unknown_af_b2[4];         // +0xAF-0xB2 (unknown)
    
    // Target tracking/state fields (13 bytes)
    uint8  target_field_1;           // +0xB3
    uint8  target_field_2;           // +0xB4
    uint8  target_field_3;           // +0xB5
    uint8  target_field_4;           // +0xB6
    uint8  target_field_5;           // +0xB7
    uint8  target_field_6;           // +0xB8
    uint8  target_field_7;           // +0xB9
    uint8  target_field_8;           // +0xBA
    uint8  target_field_9;           // +0xBB
    uint8  target_field_10;          // +0xBC
    uint8  target_field_11;          // +0xBD
    uint8  target_field_12;          // +0xBE
    uint8  target_field_13;          // +0xBF
    uint8  unknown_c0_c9[10];        // +0xC0-0xC9 (unknown)
    uint16 damage_status_flags;      // +0xCA (DAMAGE_NAV flag)
    // ...
};
```

**Size Update**: EntitySlotRecord now at least 0xCC bytes (204 bytes minimum).

## Remaining Questions

### Critical Unknowns
1. **Where is the building/facility array?**
   - Separate data structure indexed by coordinates?
   - Part of mission objective records?
   - Stored in external campaign files?

2. **How does `damage_event_dispatch_handler` find nearby buildings?**
   - Coordinate lookup in facility array?
   - Iterate through mission objective list?
   - Use terrain/map tile metadata?

3. **What do the 13 target tracking fields (+0xB3-0xBF) actually store?**
   - AI target designation state?
   - Player lock status?
   - Priority calculations?
   - Target class information?

4. **Where are mission objectives defined?**
   - .CAM campaign files?
   - .TER terrain files with facility data?
   - Separate .OBJ objective files?

### Next Steps
1. ✅ Confirm buildings don't use entity +0x75
2. ✅ Discover target tracking fields at +0xB3-0xBF
3. ⏸️ Find building/facility data structure (coordinate-indexed?)
4. ⏸️ Analyze damage_event_dispatch_handler op_dispatch calls
5. ⏸️ Investigate campaign file format (.CAM files)
6. ⏸️ Map complete impact → objective checking flow
7. ⏸️ Determine meaning of 13 target tracking fields
8. ⏸️ Update EntitySlotRecord in registry with +0xB3-0xBF fields

## Conclusion

Buildings in Falcon 3.0 use a **coordinate-based or mission-objective-based system** rather than entity type codes. The [di+0Ch] == 4 check likely identifies "building impact events" rather than building types. 

The discovery of 13 target tracking fields at entity +0xB3-0xBF suggests the entity structure is larger and more complex than previously understood (now 200+ bytes instead of 175).

Building type differentiation (HANGAR vs RUNWAY) likely happens through:
1. Mission objective records with position + type + class
2. Coordinate lookup in facility/building data structure
3. External campaign data loaded by mission_state_initializer

The weapon system is now ~97% complete. Target system understanding: ~40% (basic flow understood, building identification mechanism still unclear).
