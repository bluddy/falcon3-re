# Ground Objects Investigation - Findings

## Summary
Ground objects (tanks, SAMs, AAA, ships, buildings) are present in Falcon 3.0 as attackable targets, but their type identification system remains elusive. They do NOT use the EntitySlotRecord +0x75 weapon_type field.

## Strings Discovered

### Ground Unit Types Found (42 strings)
```
VEHICLES:
0x55CC2:  "TANK"
0x5E976:  "TRUCK"
0x5FF6E:  "TRUCK"
0x62222:  "TRUCK"
0x5F6EE:  "BMP" (Soviet infantry fighting vehicle)

AIR DEFENSE:
0x613D6:  "SAM"
0x616DC:  "SAMSITE"
0x15024E: "SAM SITE"
0x1503A8: "SAM"
0x151927: "SAMS"
0x1503AC: "AAA" (Anti-Aircraft Artillery)
0x151443: "AAA"
0x156102: "AAA"
0x659EA:  "SAM (R) SAM (IR)APEX    MAGIC"

RADAR SYSTEMS:
0x57E33:  "RADAR CONTACT+NNN DEGREES+NN MILES."
0x14FF88: "RADAR SITE"
0x15010E: "RADAR MISSILES"
0x15023A: "RADAR"
0x1503BA: "RADAR"
0x1511A4: "RADAR ACTIVITIES."
0x1518C1: "RADAR MISSILES"

SHIPS:
0x57BCE:  "SHIP TARGET."
0x14EB06-0x14EBDA: "SHIP" (8 occurrences)
0x14FD5C: "SHIP"
0x14FD6A: "SHIP"
0x150765: "SHIPS"
0x150776: "SHIP"
0x150783: "SHIPS"
0x12B405: "CARRIER..."

FACILITIES:
0x150240: "NUCLEAR PLANT"
0x14FF93: "BRIDGE"
0x15020D: "HANGAR"
0x150214: "RUNWAY"
0x150284: "FACTORY"
0x150293: "WAREHOUSE"

MISC:
0x1502DC: "TANKER" (fuel tanker aircraft or ship?)
0x15037F: "TANKS"
0x151A00: "TANKS"
```

### Tactical Messages
```
0x57B8D: "CLOSING ON GROUND TARGETS."
0x57BA8: "CLOSING ON PRIMARY TARGET."
0x57BCE: "CLOSING ON SHIP TARGET."
0x57C21: "ATTACKING GROUND TARGETS!"
0x57C3B: "ATTACKING PRIMARY TARGET."
0x151174: "SAM THREATS."
0x15118C: "AAA THREATS."
```

## Key Observations

### 1. Three Target Categories
The tactical messages reveal **three distinct target categories**:
- **GROUND TARGETS** - General ground units/buildings
- **PRIMARY TARGET** - Mission objectives  
- **SHIP TARGET** - Naval vessels (separate category!)

**Implication**: Ships are treated differently from ground targets in the targeting system.

### 2. Ground Object Strings Have NO Code References
**Critical Finding**: Just like building strings, ALL ground object strings (TANK, SAM, AAA, SHIP) have **zero code references**.

This means:
- Strings are **display-only** (briefings, threat warnings, scoring)
- Game does NOT use string comparison for object identification
- Object types must be encoded numerically

### 3. No EntitySlotRecord +0x75 Usage for Non-Weapons
**Search Results**: Zero reads/writes/comparisons with entity field +0x75 for values outside weapon range (0x12-0x37).

**Conclusion**: EntitySlotRecord +0x75 is **exclusively** for weapon identification. Ground objects, ships, and buildings do NOT use this field.

### 4. FarObj Structure Search Failed
**Search Results**: 
- Zero comparisons with FarObj +0x14 (entity_class)
- Zero references to FarObj +0x22 (object_kind)
- Type descriptor table at 0x7B0E:0x3052 shows 0xFFFF (uninitialized/invalid)

**Possible Reasons**:
1. Field offset patterns not matching IDA's disassembly format
2. These fields accessed indirectly through pointers
3. Type identification happens through a different mechanism
4. Objects stored in a separate data structure entirely

## Current Theories

### Theory 1: Separate Ground Object Array
Ground units (tanks, SAMs, AAA) and ships might be stored in a **completely separate data structure** from aircraft entities:

```c
struct GroundUnit {
    uint16 pos_x;          // Tile/world X position
    uint16 pos_y;          // Tile/world Y position
    uint8  unit_type;      // 0=TANK, 1=SAM, 2=AAA, 3=TRUCK, etc.
    uint8  health;         // Hit points remaining
    uint8  unit_flags;     // ACTIVE, DESTROYED, THREAT_ACTIVE, etc.
    uint8  faction;        // FRIENDLY, HOSTILE, NEUTRAL
};

// Stored in tile-indexed array or linked list per theater
```

**Evidence**:
- No entity structure field matches ground object behavior
- Target messages distinguish GROUND vs SHIP (separate categories)
- Buildings already appear to be coordinate-based
- Strings have no code references (numeric type IDs used instead)

### Theory 2: FarObj Extended Types
FarObj.entity_class (+0x14) might have values like:
```c
enum EntityClass {
    AIRCRAFT = 0x12,        // Known from registry
    GROUND_VEHICLE = 0x08,  // Tanks, trucks, BMP
    AIR_DEFENSE = 0x09,     // SAM, AAA sites
    NAVAL_VESSEL = 0x0A,    // Ships, carriers
    STATIC_BUILDING = 0x0B, // Hangars, factories, etc.
    RADAR_FACILITY = 0x0C,  // Radar sites
    // ... more types
};
```

But our search patterns didn't find these - possibly due to indirect access or different assembly patterns.

### Theory 3: Map/Theater Data Structure
Ground objects could be part of **theater map data** loaded from terrain files:

```c
struct TheaterData {
    TerrainHeightmap terrain;
    BuildingArray facilities[256][256];  // Indexed by tile coords
    GroundUnitList units;                // Linked list or array
    ShipList naval_forces;               // Separate ship array
    SAMSiteArray air_defense;            // SAM/AAA coverage map
};
```

Impact detection:
1. Weapon hits at (X, Y)
2. Check `theater.facilities[tile_x][tile_y]` for building
3. Check `theater.units` for ground unit near (X, Y)
4. Check `theater.naval_forces` for ship near (X, Y)
5. Update health, check if destroyed

**Evidence**:
- "SHIP TARGET" is distinct from "GROUND TARGETS" 
- No entity fields found for ground object types
- Buildings appear coordinate-based
- Mission files likely define unit placements

## Target System Integration

### target_cycle_scan @ 0x48B05 Analysis
**21 conditional branches**, only **1 entity field comparison**: `cmp [bx+0AEh], al`

**Interpretation**: 
- Most logic is control flow, not type checking
- The function likely iterates through **multiple entity sources**:
  1. Aircraft entities (status_flags bit 6 = AIRCRAFT_TYPE)
  2. Ground unit array (separate structure)
  3. Naval vessel array (separate structure)
  4. Static facility/building array (coordinate-indexed)

This explains why we see checks for:
- entity +0x74 bit 6 (AIRCRAFT_TYPE) - filters for aircraft
- entity +0x76 bit 7 - might indicate "has ground target data"
- entity +0xAE - checked against 0 (unknown purpose)

### A-G Weapon Targeting Flow
**Current Understanding**:

1. **Player selects A-G weapon mode** (Backspace key, weapon_game_mode changes)
2. **HUD displays ground targets** via target_cycle_scan:
   - Iterates aircraft entities (for air-to-air reference)
   - Iterates ground units (tanks, SAMs) from separate array
   - Iterates ships from naval array
   - Optionally shows static buildings if mission objectives
3. **Player locks target** (Z key, detection_mode_state = 5)
4. **Weapon fires** → ag_weapon_entity_initialize spawns projectile
5. **Projectile impacts** → entity_ground_collision_check detects hit
6. **Impact processed** → store_impact_step, checks what was hit:
   - Check building array at (X, Y)
   - Check ground unit array nearby
   - Check ship array nearby
7. **Damage applied** → damage_event_dispatch_handler
8. **Mission objectives updated** if primary/secondary target hit

## Remaining Questions

### Critical Unknowns
1. **Where is the ground unit array stored?**
   - Global data segment?
   - Dynamically allocated?
   - Part of campaign/mission files?

2. **How is the ship array different from ground units?**
   - Separate structure entirely?
   - Same array with ship type flag?
   - Ships move (path following), ground units static?

3. **What are the actual entity_class values?**
   - FarObj +0x14 encoding
   - Range 0x00-0x11 for non-weapons?
   - How to find the assignments?

4. **How does CCIP predict bomb impact on moving targets?**
   - Ships move
   - Trucks might move
   - Need velocity prediction?

5. **What do the target tracking fields (+0xB3-0xBF) actually store?**
   - One field per target category?
   - Lock state for different weapon types?
   - Priority/distance/angle calculations?

## Next Steps

1. ⏸️ Find ground unit array data structure (search for arrays of 8-12 byte records)
2. ⏸️ Analyze theater/campaign file format (.CAM, .TER files)
3. ⏸️ Find ship movement/path following code
4. ⏸️ Trace target_cycle_scan disassembly in detail to find array iterations
5. ⏸️ Search for damage application to non-aircraft entities
6. ⏸️ Find SAM/AAA threat evaluation code
7. ⏸️ Investigate moving target CCIP calculations
8. ⏸️ Map complete A-G weapon → ground target → damage flow

## Conclusion

Ground objects (tanks, SAMs, AAA, ships) exist in Falcon 3.0 as distinct attackable targets with their own type system. However, they do **not** use the EntitySlotRecord +0x75 weapon_type field or any other entity field we've discovered so far.

**Most Likely**: Ground units are stored in a **separate data structure** from aircraft entities, possibly:
- Coordinate-indexed facility/building array (static objects)
- Dynamic ground unit array/list (tanks, trucks, SAMs)
- Separate naval vessel array (ships with movement)

The target system integrates all three categories (air, ground, naval) for HUD display and weapon targeting, but each uses different underlying storage.

**Ships are special**: They have their own tactical message category ("SHIP TARGET") and likely support movement along predefined paths, making them more complex than static ground units.

Further investigation requires either:
1. Finding the ground unit data structure through memory layout analysis
2. Analyzing campaign/theater file formats
3. Deep tracing of target_cycle_scan assembly to find iteration patterns
