# Mission & Campaign System

**Status:** IN PROGRESS (75% complete)  
**Certainty:** STRONG (squadron, campaign, waypoints, aircraft records), HYPOTHESIS (flight plans, mission header)  
**Last Updated:** 2026-11-11

---

## Overview

Falcon 3.0's mission and campaign system manages:
- **Squadron management** - 30 pilots, 18 F-16s, supplies
- **Campaign progression** - Dynamic war simulation across 3 theaters
- **Mission planning** - Waypoints, weapon loadout, pilot assignment
- **War state tracking** - Strategic targets, victory conditions
- **File persistence** - Save/load campaign progress

**Architecture:** Data-driven system with binary file formats for squadrons, campaigns, and missions. Dynamic mission generation based on war state rather than fixed mission sequences.

---

## File Formats

### Squadron Files (.SQU) — PROVEN

**Size:** 2,703 bytes  
**Location:** Game directory (SQUAD0.SQU - SQUAD5.SQU)  
**Purpose:** Save squadron state (pilots, aircraft, supplies)

**Structure:**
```c
struct SquadronFile {
    // Header (60 bytes, 0x00-0x3B)
    uint8_t  header_flags[3];        // +0x00: Unknown flags
    char     theater_name[57];       // +0x03: Null-terminated (e.g. "Israel")
    
    // Pilot Records (1,980 bytes, 0x3C-0x7F7)
    PilotRecord pilots[30];          // 30 pilots × 66 bytes each
    
    // Extended Pilot Data (663 bytes, 0x7F8-0xA8E)
    ExtendedPilotRecord extended_pilots[10];  // Last 10 pilots (indices 20-29)
    uint8_t  footer[3];              // FF 1E 00
};  // Total: 2,703 bytes
```

**Pilot Record (66 bytes, 0x42):**
```c
struct PilotRecord {
    uint8_t  status_flags[2];        // +0x00: Unknown status
    uint8_t  rank;                   // +0x02: 0-4 (2nd Lt → Lt Col)
    char     callsign[15];           // +0x03: Radio callsign
    char     nickname[15];           // +0x13: Personal nickname
    char     id_code[4];             // +0x22: 3 letters + 'd'
    uint8_t  stats[4];               // +0x26: Abilities/fatigue (0-100 each)
    uint8_t  mission_data[28];       // +0x2A: Kills, sorties, etc.
};  // Total: 66 bytes (0x42)
```

**Extended Pilot Record (66 bytes, for pilots 20-29 only):**
```c
struct ExtendedPilotRecord {
    uint8_t  marker;                 // +0x00: Always 0xFF
    uint8_t  pilot_index;            // +0x01: 0x1D=29 down to 0x14=20
    uint8_t  status;                 // +0x02: Status flags (0x00/0x01)
    char     callsign[15];           // +0x03: Duplicate of main record
    uint8_t  pad1;                   // +0x12: Padding (0x00)
    char     nickname[15];           // +0x13: Duplicate of main record
    uint8_t  pad2;                   // +0x22: Padding (0x00)
    char     id_code[4];             // +0x23: Duplicate of main record
    uint8_t  extended_state[14];     // +0x27: Mission-specific pilot state
    uint8_t  separator[13];          // +0x35: All zeros
};  // Total: 66 bytes
```

**Rank values:**
- 4 = Squadron Commander (Lt Col)
- 3 = Executive Officer (Major)
- 2 = Flight Leaders (Captain)
- 1 = Experienced Pilots (1st Lt)
- 0 = Junior Pilots (2nd Lt)

**Stats (documented by FCE/FSM editors):**
- Dogfighting ability (0-100)
- Bombing ability (0-100)
- Flying ability (0-100)
- Fatigue level (0-100)

**Evidence:** `analysis/parse_squadron.py` successfully parses all 30 pilots from SQUAD0.SQU

**Extended Pilot Records:**

The last 663 bytes (0x7F8-0xA8E) contain extended data for the **last 10 pilots only** (pilot indices 20-29). This appears to be mission-specific runtime state that gets updated during gameplay.

Key findings:
- Each extended record duplicates the callsign, nickname, and ID from the main pilot record
- The 14-byte `extended_state` field (+0x27) is mostly zeros in fresh squadron files
- This field likely tracks: current aircraft assignment, mission status (flying/available/KIA/POW), kill counts, combat rating
- The pilot_index field counts down from 0x1D (29) to 0x14 (20)
- 3-byte footer (FF 1E 00) terminates the file

**Why only 10 pilots?** Falcon 3.0 supports up to 10 simultaneous flights per mission. The extended records likely track the pilots currently assigned to these flight slots.

---

### Campaign Files (.CAM) — STRONG (50% decoded)

**Size:** 11,828 bytes  
**Location:** Game directory (SQUAD0.CAM - SQUAD5.CAM)  
**Purpose:** Campaign state, strategic targets, and supply inventory

**File Structure:**
```
0x0000 - 0x185D   Strategic Target Array (~6,200 bytes)
                  - 24 full targets (70-73 bytes each)
                  - 20+ simplified targets (16-20 bytes each)
                  - Heavy 0xFF padding between blocks
                  
0x185E - 0x2D8D   Reserved Space (~4,700 bytes)
                  - Filled with 0x20 (space characters)
                  - Purpose: Text buffer or memory alignment
                  
0x2D8E - 0x2DCD   Supply & Inventory (~64 bytes)
                  - Weapon stockpiles (8+ types)
                  - Aircraft count (18 F-16s initially)
                  - Fuel reserves (6,030 units)
                  - Campaign counters
                  
0x2DCE - 0x2E33   Campaign State (~102 bytes)
                  - Target counts by type
                  - Victory/defeat tracking
                  - Mission statistics
                  - Status flags
```

**Strategic Target Record (70-73 bytes):**
```c
struct StrategicTarget {
    uint16_t target_id;          // +0x00: 0-863 (sparse IDs)
    uint8_t  byte_2;             // +0x02: Unknown
    uint8_t  byte_3;             // +0x03: 0-16 (ownership/type?)
    uint8_t  byte_4;             // +0x04: Usually 0x00
    uint8_t  byte_5;             // +0x05: 0-3 (subtype?)
    uint8_t  separator;          // +0x06: Always 0x3C (marker)
    uint8_t  field_7;            // +0x07: Varies 6-60
    uint8_t  array1[8];          // +0x08: Values 0-10 (strength/counts)
    uint8_t  array2[8];          // +0x10: High consistency (coordinates?)
    uint8_t  array3[8];          // +0x18: Range 190-218 (coordinates?)
    uint8_t  data[8];            // +0x20: More arrays
    // ... additional fields
    uint16_t refs[];             // +0x30+: Cross-references to other targets
};  // Total: 70-73 bytes
```

**Simplified Target Record (16-20 bytes):**
- Same structure as full targets but truncated
- Represents minor objectives (SAM sites, supply depots)
- Has 0x3C marker at byte +6

**Supply & Inventory Section (0x2D8E+, ~64 bytes):**
```c
struct SupplyInventory {
    uint8_t  header[4];          // +0x00: Unknown
    uint16_t unknown1;           // +0x04: Large value
    uint16_t flags;              // +0x06: Campaign flags
    
    // Weapon stockpiles
    uint16_t aim9_sidewinder;    // +0x08: IR missiles (258)
    uint16_t aim120_amraam;      // +0x0A: Radar missiles (188)
    uint16_t agm65_maverick;     // +0x0C: AG missiles (175)
    uint16_t agm88_harm;         // +0x0E: Anti-radar (150)
    uint16_t mk82_bombs;         // +0x10: 500lb bombs (150)
    uint16_t secondary1;         // +0x12: Unknown (302)
    uint16_t mk84_bombs;         // +0x14: 2000lb bombs (250)
    uint16_t cbu_cluster;        // +0x16: Cluster bombs (200)
    uint16_t rockets;            // +0x18: Rockets (175)
    uint16_t secondary2;         // +0x1A: Unknown (150)
    uint16_t secondary3;         // +0x1C: Unknown (250)
    uint16_t secondary4;         // +0x1E: Unknown (232)
    uint16_t secondary5;         // +0x20: Unknown (100)
    uint16_t secondary6;         // +0x22: Unknown (100)
    uint16_t secondary7;         // +0x24: Unknown (100)
    uint16_t secondary8;         // +0x26: Unknown (100)
    
    // Fuel
    uint16_t fuel1;              // +0x28: 6030 units
    uint16_t fuel2;              // +0x2A: 6030 (duplicate)
    
    // Campaign state
    uint16_t counter1;           // +0x2C: 50
    uint16_t unknown2;           // +0x2E: 52407
    uint16_t campaign_day;       // +0x30: Day 5
    uint16_t counter2;           // +0x32: 10
    
    // Aircraft inventory
    uint16_t f16_count;          // +0x34: 18 F-16s *** PRIMARY ***
    uint16_t aircraft_damaged;   // +0x36: 1
    uint16_t pilots_available;   // +0x38: 9
    uint16_t counter3;           // +0x3A: 9
    uint16_t counter4;           // +0x3C: 6
    uint16_t status_flag;        // +0x3E: 1
    
    uint16_t counter5;           // +0x42: 4
};
```

**Campaign State Section (0x2DCE+, ~102 bytes):**
- Target counts by type (8-10 values)
- Values: 29, 22, 12, 6, 2, 18, 12, 12, 13
- Likely theater-wide target counts
- Victory/defeat tracking
- Mission statistics
- Multiple 0xFF markers as boundaries

**Key Findings:**
- Target IDs are sparse (0-863 range, only 44 exist)
- Targets reference other targets (dependency network)
- Supply data was misidentified in Strategic Falcon docs
- First block is Target ID 0, not a separate header
- Heavy use of 0xFF padding between structures

**Evidence:** Successfully parsed all targets and supply data from SQUAD0.CAM

---

### Mission Files (.MIS) — STRONG

**Size:** Variable (451-824 bytes observed)  
**Location:** Game directory (SQUAD0.MIS - SQUAD5.MIS)  
**Purpose:** Current mission definition  
**Progress:** 25% decoded (waypoints confirmed, flight records in progress)

**Overview:**  
Mission files define the current mission including allied/enemy flights, waypoints, loadouts, and mission parameters. Size varies based on number of flights and waypoints. Uses highly compact encoding with 1-byte coordinates.

**Waypoint Storage Format — PROVEN:**

Each waypoint is stored as a 21-byte pair: an 11-byte version with prefix, followed by a 10-byte duplicate.

```c
// 11-byte version (with prefix marker)
struct Waypoint11 {
    uint8_t  marker;          // +0x00: Always 0x01
    uint8_t  x_low;           // +0x01: X coordinate LOW byte
    uint8_t  x_high;          // +0x02: X coordinate HIGH byte
    int16_t  marker_1;        // +0x03: Constant (-8 or -2 observed)
    uint8_t  y_low;           // +0x05: Y coordinate LOW byte
    uint8_t  y_high;          // +0x06: Y coordinate HIGH byte
    int16_t  marker_2;        // +0x07: Constant (-12 or -9 observed)
    uint16_t constant;        // +0x09: Always 16 (0x0010)
};  // 11 bytes

// 10-byte version (duplicate without prefix)
// Same structure minus the leading 0x01 marker byte
```

**16-Bit Coordinate System — PROVEN:**

Waypoints use 16-bit coordinates (0-65535) for high precision:
- **X coordinate** = (x_high << 8) | x_low  (uint16)
- **Y coordinate** = (y_high << 8) | y_low  (uint16)

The coordinate bytes are split non-contiguously in the structure, which initially made them appear to be separate "unknown" fields.

**Coordinate precision:** Full 16-bit range likely represents entire theater/world map
- Range: 0-65,535 units
- Estimated scale: ~120-240 feet per unit (assuming 250-400nm theater)
- Example: 300 unit spacing ≈ 6.7-13.5 nautical miles

**Waypoint Marker Patterns:**

Two marker patterns observed (purpose unknown):
- **Pattern A:** marker_1 = -8, marker_2 = -12 (seen in SQUAD0.MIS)
- **Pattern B:** marker_1 = -2, marker_2 = -9 (seen in SQUAD1.MIS)

Possible interpretations:
- Different waypoint action types (nav, attack, threat, patrol)
- Mission type indicators
- Altitude/speed encoding offsets
- Flight behavior modifiers

**Unknown Bytes:**

All previously "unknown" bytes are now decoded:
- Bytes at +0x02 and +0x06 are the HIGH bytes of 16-bit X/Y coordinates
- No unknown fields remain in the waypoint structure

**Waypoint Examples:**

SQUAD0.MIS (11 waypoints, 231 bytes total):
```
WP  | X_16bit | Y_16bit | Spacing | Pattern
----|---------|---------|---------|---------------------------
 0  |  50,688 |  50,832 |    -    | Perfect diagonal line
 1  |  50,988 |  51,132 |   300   | Each waypoint exactly 300
 2  |  51,288 |  51,432 |   300   | units in X and Y from the
 3  |  51,588 |  51,732 |   300   | previous waypoint
 4  |  51,888 |  52,032 |   300   | 
 5  |  52,188 |  52,332 |   300   | Diagonal distance: 424.3
 6  |  52,488 |  52,632 |   300   | units between waypoints
 7  |  52,788 |  52,932 |   300   |
 8  |  53,088 |  53,232 |   300   | Markers: -8, -12
 9  |  53,388 |  53,532 |   300   |
10  |  53,688 |  53,832 |   300   |
```

SQUAD1.MIS (1 waypoint, 21 bytes total):
```
WP  | X_16bit | Y_16bit | Markers | Notes
----|---------|---------|---------|------------------------
 0  |  38,072 |  56,024 | -2, -9  | Different coordinate
                                    range from SQUAD0
```

**Flight Records — IN PROGRESS:**

Mission files contain aircraft records after the header, before waypoints.

**Aircraft Record Format (6 bytes) — STRONG:**
```c
struct AircraftRecord {
    uint8_t  flags;           // +0x00: 0x00, 0x80, or 0x81
    uint8_t  aircraft_id;     // +0x01: Sequential ID (2-27)
    uint8_t  zero1;           // +0x02: Always 0x00
    uint8_t  type_code;       // +0x03: Aircraft/role type
    uint8_t  zero2;           // +0x04: Always 0x00
    uint8_t  subtype;         // +0x05: Variant/loadout/group
};  // 6 bytes
```

**SQUAD0.MIS Example:**
- 26 aircraft records at 0x0008-0x00A3 (156 bytes)
- IDs: 2-27 (sequential)
- Type codes: 0x01, 0x07-0x0B, 0x34-0x36
- Flags: 0x00 (player), 0x80 (allied?), 0x81 (enemy?)

**Type Distribution:**
- Type 0x01: 5 aircraft (IDs 2-6) - Player flight?
- Types 0x34-0x36: 10 aircraft (IDs 7-16) - Allied flights?
- Types 0x07-0x0B: 11 aircraft (IDs 17-27) - Enemy flights?

**Flags hypothesis:**
- 0x00: Player aircraft (first only)
- 0x80: Allied AI
- 0x81: Enemy AI

**Between aircraft and waypoints:** 429 bytes of unknown data (0x00A4-0x0250) - likely flight plans, loadouts, AI parameters.

**Next:** Decode type codes (map to aircraft names), understand flag bits, parse middle section.

**Header — IN PROGRESS:**

First few bytes show mission-level parameters:
- Byte 0: Flight count? (3 in SQUAD0, 2 in SQUAD1)
- Bytes 1-2: uint16 value (256 vs 1792 observed)
- Byte 3: Unknown (20 vs 17)
- Byte 4: Unknown (30 vs 1)

Requires further analysis to decode complete structure.

**Next Steps:**
1. ~~Decode unknown bytes in waypoint structure~~ ✓ COMPLETE (16-bit coordinates)
2. Search IDA for waypoint loading code using marker values (-8, -12, -2, -9)
3. Parse flight record section (first ~200-600 bytes)
4. Identify mission header format
5. Compare multiple mission files to understand variations
- 0x09 = Combat + Ground (SEARCH & DESTROY)

**Evidence:** Action codes match AI behavior flags (see [ai.md](ai.md)), 1-byte storage documented by Strategic Falcon

---

### War State Files (.WAR) — HYPOTHESIS

**Size:** 161 bytes  
**Location:** Game directory (SQUAD0.WAR - SQUAD5.WAR)  
**Purpose:** Daily war summary

**Likely contents:**
- Current campaign day (2 bytes)
- Mission counter (1-4 per day)
- Daily sortie count
- Daily casualties (friendly/enemy)
- Daily mission success/failure
- Supply delivery schedule

**Evidence:** File size consistent across campaigns, backed up by Strategic Falcon

---

### Mission Description Files (.MTV) — PROVEN

**Size:** 182-202 bytes  
**Location:** Game directory (SQUAD0.MTV - SQUAD5.MTV)  
**Purpose:** Mission briefing text

**Format:** Plain text, null-terminated string

**Usage:**
- Displayed via F2 key in mission planning
- Editable with text editor
- Describes mission objectives in natural language

**Evidence:** Documented by Strategic Falcon, editable as plain text

---

### Flight Data Files (.FLA) — UNKNOWN

**Size:** 1,506 bytes  
**Location:** Game directory (SQUAD0.FLA - SQUAD5.FLA)  
**Purpose:** Unknown

**Hypotheses:**
- ACMI recording data?
- Flight history/statistics?
- Pilot sortie logs?
- Needs investigation

---

## Squadron Management

### Squadron Structure

**Limits:**
- Maximum 6 squadrons (SQUAD0-SQUAD5)
- 30 pilots per squadron
- 18 F-16s initially (can be reduced by combat losses)
- Limited supplies (weapons, fuel, ECM)

**Squadron = "Saved Game"**  
Each squadron is an independent campaign save with its own:
- Pilot roster
- Aircraft inventory
- Supply levels (likely in .CAM file, not .SQU - see note below)
- Campaign progress
- War state

**Note on Supply Data:**  
The Strategic Falcon documentation mentions "supply data" (weapons, fuel, aircraft count) as being in the .SQU file, but our analysis shows the final 663 bytes contain **extended pilot records** for the last 10 pilots, not supply data. The actual supply/inventory data is likely stored in the .CAM (campaign) file instead.

### Pilot System

**30 pilots per squadron:**
- 1 Squadron Commander (rank 4)
- 1 Executive Officer (rank 3)  
- 6-8 Flight Leaders (rank 2)
- 14 Experienced Pilots (rank 1)
- 8 Junior Pilots (rank 0)

**Pilot attributes:**
- Callsign (e.g., "ANEAR", "KIRK", "KOBBERVIG")
- Nickname (e.g., "LEMONHEAD", "MOOSEHEAD", "NIGHTFOX")
- Rank (0-4)
- Status (Active, KIA, MIA, Court Martialed)
- Abilities: Dogfighting, Bombing, Flying (0-100)
- Fatigue level (0-100)

**Pilot lifecycle:**
- Skills improve with successful missions
- Skills degrade with failures
- Fatigue accumulates (4 missions per day)
- Can be killed, captured, or court martialed
- Resurrectable via FCE/FSM editors

**Player role:** Commands F-16 #1, Flight #1 in each mission

---

## Campaign System

### Three Theaters

1. **Kuwait** - Desert Storm scenario
2. **Israel** - Middle East conflict  
3. **Panama** - Central America operations

**Theater differences:**
- Geography (terrain, airbases)
- Enemy forces (aircraft types, strength)
- Victory conditions
- Political objectives

### Dynamic Campaign

**No fixed mission sequence!**

**Mission generation:**
- Central Command analyzes war state
- Generates Air Tasking Order (ATO) based on current situation
- Assigns missions to squadrons
- Player flies 1-4 missions per day
- Background war continues when not flying

**Mission types:**
- CAP (Combat Air Patrol)
- CAS (Close Air Support)
- INTERCEPT
- STRIKE
- SEARCH & DESTROY
- ESCORT
- SAM SUPPRESSION
- SUPPLY ESCORT (C-130s)

### Strategic Targets

**Target types:**
- Airbases (runways, hangars)
- Command & Control (C3)
- Radar installations
- Supply depots
- Factories
- Transportation hubs
- Ground forces (armor, infantry)

**Target properties:**
- Ownership (Allied/Enemy)
- Strength (0-100%)
- Victory site designation
- Defeat site designation

**Victory conditions:**
- Theater-specific objectives
- Capture/destroy victory sites
- Prevent loss of defeat sites
- Political considerations

---

## Supply System

### Weapon Types (30+ types tracked)

**Air-to-Air:**
- AIM-9 Sidewinder
- AIM-120 AMRAAM
- AIM-7 Sparrow

**Air-to-Ground:**
- AGM-65 Maverick
- AGM-88 HARM
- Mk-82/83/84 bombs
- CBU cluster bombs
- Laser-guided bombs

**Countermeasures:**
- ECM pods (max 50 total)
- Chaff (expendable)
- Flares (expendable)

**Ammunition:**
- 20mm cannon rounds

### Supply Limits

- Each weapon type: Max 250 units
- Fuel pool: 280,000 lbs (FCE default)
- ECM pods: Max 50
- Aircraft: 18 F-16s (can be reduced)

### Resupply

**Periodic C-130 cargo flights:**
- New pilots arrive
- New aircraft delivered
- Ammunition restocked
- Fuel replenished

**Player must escort C-130s!**
- If C-130s destroyed → No resupply
- Wait for next supply date

---

## Mission Planning

### Planning Screens (in order)

1. **War Update** - Daily briefing, objectives
2. **Campaign Information** - Date, time, weather
3. **Mission Planning:**
   - Edit flight routes
   - Add/remove waypoints
   - Assign pilots to aircraft
   - Select weapon loadouts
   - Adjust flight composition
4. **Takeoff** - Enter cockpit

### Waypoint System

**Waypoint properties:**
- Position (X, Y) - 1-byte coordinates
- Altitude (encoded)
- Speed setting
- Action (CAP, CAS, INTERCEPT, etc.)
- Loiter time (for CAP/LOITER)

**Editing constraints:**
- 1/256 theater width grid (≈1.25 nm)
- Strategic Falcon snaps to nearest grid point
- Explains waypoint "jumping" during editing

**ILS (Instrument Landing System):**
- Must start from airbase with ILS enabled
- Strategic Falcon can enable/disable ILS per base
- ILSRESET.EXE restores defaults

### Flight Composition

**Flights:**
- Player always in Flight #1, Aircraft #1
- Up to 4 aircraft per flight (typical)
- Multiple flights per mission
- Allied + Enemy + Support flights

**Pilot assignment:**
- Based on rank and ability
- Player chooses pilot for each aircraft
- AI controls wingmen

**Weapon loadout:**
- Per-aircraft configuration
- Limited by supply availability
- Weight affects fuel consumption

---

## Debriefing

### Mission Results

**Statistics tracked:**
- Kills (air-to-air, ground)
- Damage inflicted
- Targets destroyed
- Friendly losses
- Mission success/failure

**Pilot updates:**
- Ability scores adjusted (success → increase, failure → decrease)
- Fatigue accumulated
- Kills/sorties recorded
- Medals awarded

**Campaign impact:**
- Strategic target ownership changes
- War state progression
- Victory/defeat tracking

---

## File Backup & Restore

### Strategic Falcon Backup System

**Files backed up:**
- SQU0SQU.BAK (squadron)
- SQU0MTV.BAK (mission description)
- SQUAD0.CAM → .BAK (campaign)
- SQUAD0.WAR → .BAK (war state)
- SQUAD0.MIS → .BAK (mission)

**Restoration:**
```batch
RESTRCAM.BAT <squad_number>
```

**Purpose:**
- Recover from crashes
- Undo unwanted changes
- Restore to previous mission

**TSR Protection:**
- STRTSPRT.COM (for Falcon 3.02+)
- Sets read-only bits during editing
- CLEAR.BAT removes protection

---

## Code Structures (HYPOTHESIS)

### Key Functions (to be located)

**Squadron loading:**
```c
// HYPOTHESIS - structure not yet confirmed in code
void load_squadron(int squadron_num) {
    char filename[32];
    sprintf(filename, "SQUAD%d.SQU", squadron_num);
    FILE *f = fopen(filename, "rb");
    fread(&squadron_data, 2703, 1, f);
    // Parse 30 pilots @ 66 bytes each
    // Load supply data
}
```

**Master game loop:**
- sub_33443 @ 0x33443 (2,688 bytes, 137 callees)
- Likely main menu/game state coordinator
- Calls input, rendering, entity, state management

**War Room UI:**
- Squadron selection
- Theater selection  
- Button handlers (FORM, SQUAD, DEACTIVATE, THEATER, COMMIT)

**Mission planning:**
- Waypoint editor
- Pilot assignment screen
- Weapon loadout screen
- Route planner

---

## Integration with Other Systems

### AI System Integration

**Waypoint actions → AI behavior flags:**
- Mission file waypoint actions (0x01-0x10)
- Map directly to AI behavior flags (bits 0-4)
- Loaded via farptr_table_get(data_table_idx)
- See [ai.md](ai.md) for complete mapping

**Entity type → Aircraft assignment:**
- 0x10 = Missiles/weapons
- 0x16 = Friendly aircraft
- 0x33 = Player aircraft
- Loaded from entity data[+0x26]

### Entity System Integration

**Mission → Entity spawning:**
- Flight definitions → Entity creation
- Pilot stats → AI ability parameters
- Weapon loadout → Entity weapon systems
- Waypoints → AI navigation targets

---

## Modding Tools

### Strategic Falcon (SF.EXE)

**Capabilities:**
- Edit campaign missions
- Move waypoints (1.25nm grid)
- Add/remove flights
- Change strategic target ownership/strength
- Edit victory conditions
- Configure ILS
- Timing trace (4-second jumps)
- Map printing

**Version:** 1.21  
**Author:** Flying Muffin Enterprises

### Falcon Campaign Editor (FCE.EXE)

**Capabilities:**
- Edit pilot stats (all 4 abilities)
- Resurrect dead pilots
- Change ranks/names
- Resupply (+20 weapons, 280K lbs fuel, 18 aircraft)
- Fuel burn calculations
- Squadron roster printing
- Generate Red Flag from campaign mission

**Version:** 1.3  
**Author:** Frank W. Racis

### Falcon Squadron Manager (FSM.EXE)

**Capabilities:**
- Edit squadron rosters
- Modify pilot abilities/fatigue
- Customize wingman comments (text only)
- Change rank structures (USAF, RAF, RAAF)
- Squadron statistics

**Version:** 1.8  
**Author:** Richard Howard

---

## Analysis Status

### Completed (30%)

✅ Squadron file format (.SQU) - PROVEN  
✅ Pilot record structure - PROVEN  
✅ Rank system - PROVEN  
✅ File format documentation - STRONG  
✅ Working squadron parser - PROVEN

### In Progress

⏳ Supply data decoding (663 bytes)  
⏳ Campaign file format (.CAM)  
⏳ Mission file format (.MIS)  
⏳ Code location (squadron loading, War Room UI)

### TODO (to reach 70%)

- [ ] Parse supply/aircraft data
- [ ] Parse .CAM file structure
- [ ] Parse .MIS file structure
- [ ] Locate squadron loading code
- [ ] Find War Room UI handlers
- [ ] Trace mission planning screens
- [ ] Document file I/O operations
- [ ] Map data flow (files → memory → code)

---

## References

**Analysis documents:**
- `analysis/MISSION_SYSTEM_INITIAL.md` - Investigation plan
- `analysis/MISSION_FILE_FORMATS.md` - Complete format specs
- `analysis/MISSION_SESSION1_SUMMARY.md` - Session 1 results
- `analysis/parse_squadron.py` - Squadron file parser

**Modding tools:**
- `old_mods/strategic_falcon/` - Strategic Falcon editor
- `old_mods/fce/` - Falcon Campaign Editor
- `old_mods/fsm/` - Falcon Squadron Manager

**Game files:**
- `game/SQUAD*.SQU` - Squadron saves
- `game/SQUAD*.CAM` - Campaign states
- `game/SQUAD*.MIS` - Mission definitions
- `game/*.STR` - Theater strategic targets

---

*Status: IN PROGRESS*  
*Last Analysis: Session 1 complete (2026-11-11)*  
*Next: Decode supply data, parse campaign files*
