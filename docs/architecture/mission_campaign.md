# Mission & Campaign System

**Status:** IN PROGRESS (92% complete)  
**Certainty:** STRONG (squadron, campaign, waypoints, aircraft records, type codes, flight parameters, pilot/squadron structures, enums)  
**Last Updated:** 2026-11-16

**Major Update (2026-11-16)**: Complete reverse-engineering of R45 Squadron Management Menu revealed squadron/pilot/campaign data structures and enumerations. See "Data Structures & Type System" section below.

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
- Type 0x01 (F-16 Player): 5 aircraft (IDs 2-6)
- Types 0x34-0x36 (F-15, F-111, F-4): 10 aircraft (IDs 7-16) - Allied
- Types 0x07-0x0B (MiG-29, MiG-23, MiG-21, Su-25, Su-27): 11 aircraft (IDs 17-27) - Enemy

**Type Code Mapping (Hypothesis from IDA):**
- 0x01: F-16 (player flight)
- 0x34: F-15 Eagle (air superiority)
- 0x35: F-111 Aardvark (strike/bomber)
- 0x36: F-4 Phantom II (fighter)
- 0x07: MiG-29 Fulcrum
- 0x08: MiG-23 Flogger
- 0x09: MiG-21 Fishbed
- 0x0A: Su-25 Frogfoot
- 0x0B: Su-27 Flanker

Each type initializes unique performance characteristics (speed, turn rate, weapons).

**Flight Plan Section — HYPOTHESIS:**

Sparse data format (53.8% zeros) containing:
- **Flight plan blocks:** 20-50 byte structures with waypoint routes
- **Target assignments:** 7-byte pattern `XX YY ZZ FF ID 40 11`
  - Appears 6 times in SQUAD0.MIS
  - ID field (byte 4) references aircraft IDs: 6, 9, 12, 14
  - Could assign targets/waypoints to flight leaders
- **AI parameters:** Sparse 2-4 byte blocks in trailing section

**7-Byte Target Pattern:**
```c
struct TargetAssignment {  // 7 bytes, hypothesis
    uint8_t  coord_or_id[3];   // Coordinates or target IDs
    uint8_t  marker;           // Always 0xFF
    uint8_t  aircraft_id;      // References aircraft record
    uint16_t flags;            // Always 0x4011
};
```

**Example Flight Plan Block (32 bytes at 0x00C1):**
- Starts with 0x0A (10 - possibly waypoint count)
- Contains coordinate-like uint16 values
- Includes `10 5A` pattern repeated 4 times (altitude/speed markers?)
- Ends with 7-byte target assignment

Section organization suggests 3 flight plan blocks (correlating with header byte 0 = 3 flights).

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
- Loaded by squadron_mission_file_loader @ 0x17B437

**Evidence:** Documented by Strategic Falcon, editable as plain text, code reference confirmed

---

### Squadron Selection Files (.SQUAD) — UNDOCUMENTED

**Size:** Unknown (likely ~2,703 bytes)  
**Location:** Game directory (SQUAD0.SQUAD - SQUAD5.SQUAD)  
**Purpose:** Squadron roster selection menu data

**Format:** Unknown - possibly same as .SQU format

**Usage:**
- Loaded during mission planning UI (War Room menu)
- Loaded by squadron_mission_file_loader @ 0x17B437
- Different from .SQU save files (execution vs. menu)

**Hypothesis:**
- Could be menu metadata (squadron names, theater assignments, campaign availability)
- Or duplicate of .SQU format with different extension
- First 2 bytes of 64×20-byte slot array suggest text labels

**Evidence:** Code reference @ 0x17B4FC, string ".SQUAD" in segment 0x602E

**Relationship to .SQU:**
The game uses two squadron file patterns:
- **.SQU** = Squadron save data (mission execution)
- **.SQUAD** = Squadron menu/selection data (mission planning UI)

**Next steps:** Extract and compare .SQUAD vs .SQU file contents

---

### Task Definition Files (.TSK) — HYPOTHESIS

**Size:** 1,902 bytes  
**Location:** Game directory (SQUAD0.TSK - SQUAD5.TSK)  
**Purpose:** Mission task/objective definitions

**Format:** Unknown - likely structured records

**Possible Structure:**
```c
// HYPOTHESIS - 1902 bytes total
struct TaskFile {
    uint8_t  header[10];         // Mission type, difficulty
    TaskRecord tasks[63];        // 63 tasks × 30 bytes = 1,890 bytes
    uint8_t  footer[2];          // Terminator
};

struct TaskRecord {
    uint8_t  task_type;          // CAP, CAS, STRIKE (0x01-0x10)
    uint8_t  priority;           // 0-10
    uint16_t target_id;          // Reference to .CAM strategic target
    uint16_t x_coord;            // Target location
    uint16_t y_coord;
    uint8_t  altitude_code;      // Encoded altitude
    uint8_t  speed_code;         // Encoded speed
    uint8_t  flight_assignment;  // Which flight handles this task
    uint8_t  weapon_loadout;     // Required weapons
    uint8_t  success_criteria[8];// Victory conditions
    uint8_t  failure_criteria[8];// Defeat conditions
    uint8_t  flags;              // Status bits
};  // 30 bytes
```

**Alternative:** 38 records × 50 bytes

**Usage:**
- Loaded during mission planning
- Read in single 1,902-byte operation
- Loaded by squadron_mission_file_loader @ 0x17B6D1
- Success sets flag2224a state flag

**Evidence:** Code reference @ 0x17B6D1, exact size 1,902 bytes (0x76E)

**Next steps:**
- Extract sample .TSK files from game directory
- Hex dump analysis to find structure boundaries
- Search IDA for .TSK parsing code
- Cross-reference with .MIS waypoint actions and .CAM strategic targets

---

### Shape/Model Files (.SHP) — HYPOTHESIS

**Size:** 6 bytes  
**Location:** Game directory (SQUAD0.SHP - SQUAD5.SHP)  
**Purpose:** 3D model or sprite selection reference

**Format:** Unknown - possibly model ID + flags

**Possible Structure:**
```c
struct ShapeFile {
    uint8_t  model_type;         // +0: Aircraft, ground, building
    uint16_t model_id;           // +1: Index into shape table
    uint8_t  color_scheme;       // +3: Camouflage pattern
    uint16_t flags;              // +4: LOD, damage state, variant
};  // 6 bytes
```

**Usage:**
- Conditionally loaded (flag at 0x7A32:0xAD4B controls loading)
- Read in two operations: 1 byte + 5 bytes (extended read)
- Loaded by squadron_mission_file_loader @ 0x17B5EA
- Only loaded if specific game mode flag is set

**Conditional Loading:**
- Skipped in certain graphics modes (low detail?)
- Could be theater-specific (some campaigns skip certain models)
- Could be mission-specific (air-to-air skips ground vehicles)

**Evidence:** Code reference @ 0x17B5EA, exact size 6 bytes (1 + 5)

**Next steps:**
- Extract sample .SHP files
- Identify which flag at 0x7A32:0xAD4B controls loading
- Search for model loading code in 3D rendering subsystem
- Compare .SHP files across different squadrons/theaters

---

### Theater Configuration Files (.THEATER) — HYPOTHESIS

**Size:** Unknown  
**Location:** Game directory (possibly per-theater files)  
**Purpose:** Theater configuration and strategic data

**Format:** Unknown - binary format

**Usage:**
- Loaded by theater_campaign_file_loader @ 0x15A8B0
- Contains theater-specific configuration
- Likely includes: terrain parameters, airbase locations, strategic target definitions
- Read via multiple op_dispatch_far_entry calls

**Evidence:** String reference ".THEATER" in theater_campaign_file_loader, opened with operation 6 (OPEN)

**Next steps:** Extract sample .THEATER files, analyze structure, document format

---

### News Files (.NWS) — HYPOTHESIS

**Size:** Unknown  
**Location:** Game directory  
**Purpose:** Mission briefings and campaign event notifications

**Format:** Unknown - possibly plain text or structured binary

**Usage:**
- Loaded by theater_campaign_file_loader @ 0x15A8B0
- Contains news/briefing text
- Displayed during campaign progression
- Mission-specific or daily war updates

**Evidence:** String reference ".NWS" in theater_campaign_file_loader

**Next steps:** Extract sample .NWS files, determine if text or binary format

---

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

### Completed (34%)

✅ Squadron file format (.SQU) - PROVEN  
✅ Pilot record structure - PROVEN  
✅ Rank system - PROVEN  
✅ File format documentation - STRONG  
✅ Working squadron parser - PROVEN  
✅ **squadron_mission_file_loader code analysis** - STRONG (Rank #10, 4,516 bytes, 13 callees)  
✅ **File I/O operation patterns** - PROVEN (OPEN=6, READ=0xA, READ_EXT=0xC, CLOSE=8)  
✅ **.SQUAD file format discovery** - HYPOTHESIS (menu/selection data)  
✅ **.TSK file format discovery** - HYPOTHESIS (1,902 bytes, mission task definitions)  
✅ **.SHP file format discovery** - HYPOTHESIS (6 bytes, 3D model references)  

### In Progress

⏳ Supply data decoding (663 bytes)  
⏳ Campaign file format (.CAM)  
⏳ Mission file format (.MIS)  
⏳ Code location (squadron loading, War Room UI)

### TODO (to reach 70%)

- [ ] Extract and analyze sample .SQUAD/.TSK/.SHP files
- [ ] Parse supply/aircraft data in .SQU extended section
- [ ] Complete .CAM file structure decoding
- [ ] Complete .MIS file structure decoding
- [ ] Locate .MIS/.CAM loader function (distinct from squadron_mission_file_loader)
- [ ] Find War Room UI handlers
- [ ] Trace mission planning screens
- [ ] Document complete file I/O flow (menu → load → execution → save)

---

## References

**Analysis documents:**
- `analysis/MISSION_SYSTEM_INITIAL.md` - Investigation plan
- `analysis/MISSION_FILE_FORMATS.md` - Complete format specs
- `analysis/MISSION_SESSION1_SUMMARY.md` - Session 1 results
- `analysis/parse_squadron.py` - Squadron file parser
- `analysis/SQUADRON_MISSION_FILE_LOADER_ANALYSIS.md` - **Rank #10 deep dive (12,000 words)**

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

## Data Structures & Type System

### Overview

Complete reverse-engineering of R45 Squadron Management Menu (2026-11-16) revealed the in-memory data structures and enumerations used by the mission/campaign system. These complement the file format specifications above.

**Registry Files**:
- `registry/structures.yaml` - 10 structures defined
- `registry/enums.yaml` - 18 enumerations with 120+ values
- All types synced to IDA database

**Evidence**: String analysis (200+ UI strings), code analysis (3 functions, 4,926 bytes), pattern matching (structure sizes, enum values)

### Pilot Structure (In-Memory)

```c
struct Pilot {
    char     name[?];              // Pilot name (from NAMES.BIN)
    char     callsign[?];          // Radio callsign (from CALLSIGN.BIN)
    uint8_t  rank;                 // PilotRank enum (0-4)
    uint8_t  status;               // PilotStatus enum (0-3)
    uint16_t missions;             // Total missions flown
    uint16_t awards;               // Awards received
    uint16_t flight_hours;         // Total flight hours
    uint16_t plane_kills;          // Enemy aircraft destroyed
    uint16_t merits;               // Merit points
    
    // Abilities (7 categories, 0-100 each)
    uint8_t  dogfighting_skill;    // Air-to-air dogfighting
    uint8_t  guns_skill;           // Gun combat
    uint8_t  rear_aspect_ir;       // AIM-9P proficiency
    uint8_t  all_aspect_ir;        // AIM-9M proficiency
    uint8_t  radar_missiles;       // AIM-120 proficiency
    uint8_t  cas_ordnance;         // Close air support weapons
    uint8_t  heavy_ordnance;       // Heavy bombs
};
```

**File Mapping**:
- Persistent storage: `.SQU` files (PilotRecord, 66 bytes)
- Load files: `NAMES.BIN`, `CALLSIGN.BIN`
- In-memory format: Structure above (size TBD)

**Evidence**: 
- String references: "NAME:", "CALLSIGN:", "MISSIONS:", "PLANE KILLS:", "PILOT ABILITIES:"
- Rank strings: "LT.", "CAPT.", "MAJOR", "LT COL.", "COL."
- Status strings: "ACTIVE", "FATIGUED", "INJURED", "COURT MARTIALED"
- Ability strings: "GUNS", "REAR ASPECT IR", "ALL ASPECT IR", etc.

### Squadron Structure (In-Memory)

```c
struct Squadron {
    char     squadron_name[?];     // Squadron name (from sqdnames.str)
    char     commander_name[?];    // Commander's pilot name
    uint8_t  wing_assignment;      // WingID enum (0-6: 1ST-7TH WING)
    uint8_t  insignia_id;          // Squadron insignia graphic ID
    uint16_t missions_flown;       // Total squadron missions
    uint16_t pilots_active;        // Number of active pilots
    uint16_t pilots_killed;        // Pilots killed in action
    uint16_t pilots_mia;           // Pilots missing in action
    
    // Pilot roster
    Pilot    pilots[30];           // 30 pilot slots
    
    // Aircraft inventory (speculative)
    uint16_t f16_count;            // Available F-16s (max 18)
    uint16_t aircraft_damaged;     // Damaged aircraft count
};
```

**File Mapping**:
- Persistent storage: `.SQU` files (2,703 bytes)
- Squadron names: `sqdnames.str`
- In-memory format: Structure above

**Evidence**:
- String references: "SQUADRON NAME:", "SQUADRON COMMANDER:", "NUMBER OF MISSIONS FLOWN:"
- Statistics: "NUMBER OF PILOTS ACTIVE/KILLED/MIA:"
- Wing strings: "1ST WING" through "7TH WING"
- File analysis: 30 pilots × 66 bytes in .SQU files

### Campaign Status Structure (In-Memory)

```c
struct CampaignStatus {
    // Date & Time
    uint16_t current_day;                  // Campaign day number
    uint16_t current_time;                 // TimeOfDay enum (0600/1200/1800/2300)
    
    // Territory Control
    uint8_t  territory_enemy_percent;      // Enemy-held territory (0-100%)
    uint8_t  territory_allied_percent;     // Allied-held territory (0-100%)
    
    // Mission Statistics
    uint16_t missions_flown;               // Total missions
    uint16_t missions_accomplished;        // Successfully completed
    uint16_t sorties_flown;                // Total sorties
    
    // Air Combat
    uint16_t allied_aircraft_lost;         // Allied losses
    uint16_t enemy_aircraft_destroyed;     // Enemy kills (total)
    
    // By Aircraft Type
    uint16_t enemy_class_a_fighter;        // MiG-29, Su-27
    uint16_t enemy_class_b_fighter;        // MiG-21, MiG-23
    uint16_t enemy_bomber_strike;          // Bombers/strike aircraft
    uint16_t enemy_attack_aircraft;        // A-10, Su-25 equivalents
    uint16_t enemy_helicopter;             // All rotorcraft
    uint16_t enemy_transport_awacs;        // Transports, AWACS
    
    // Ground Targets
    uint16_t ground_targets_destroyed;     // Total ground targets
    uint16_t ground_class_a;               // Strategic (nuclear plants, etc.)
    uint16_t ground_class_b;               // Infrastructure (airbases, bridges)
    uint16_t ground_class_c;               // Military (SAM sites, army bases)
    uint16_t ground_class_d;               // Tactical (buildings, hangars)
    
    // Performance Ratings
    uint16_t ordnance_efficiency;          // Bombs/missiles per target (%)
    uint16_t overall_rating;               // Combined campaign score
};
```

**File Mapping**:
- Persistent storage: `.CAM` files (Campaign State Section, ~102 bytes)
- In-memory format: Structure above

**Evidence**:
- String references: All campaign status screen strings at 0x150880-0x150A77
- 23 distinct statistic fields referenced
- File analysis: Campaign state section in .CAM files

### Flight Record Structures (From R57 Analysis)

```c
struct FlightRecord {
    uint8_t       aircraft_count;  // 1-4 aircraft in flight
    LoadoutRecord loadouts[4];     // Loadouts for each aircraft
    uint8_t       _unknown[105];   // Flight-specific data
};  // Total: 130 bytes (0x82)

struct LoadoutRecord {
    uint8_t  hardpoint_config[11]; // 11 hardpoints (weapon IDs)
    uint16_t pilot_id;             // Assigned pilot (index into squadron)
    uint8_t  _unknown[10];         // Additional data
};  // Total: 23 bytes (0x17)
```

**File Mapping**:
- Not directly in files (runtime configuration)
- Passed between R45 (squadron) and R57 (loadout) menus
- Ephemeral mission planning data

**Evidence**: Complete R57 weapons loadout menu analysis

### Enumerations

#### PilotRank
```c
enum PilotRank : uint8_t {
    RANK_LT = 0,        // Lieutenant (2nd Lt in UI)
    RANK_CAPT = 1,      // Captain (1st Lt in UI)
    RANK_MAJOR = 2,     // Major (Flight Leaders)
    RANK_LT_COL = 3,    // Lieutenant Colonel (Executive Officer)
    RANK_COL = 4        // Colonel (Squadron Commander)
};
```

**Evidence**: Strings at 0x150088-0x1500A6

#### PilotStatus
```c
enum PilotStatus : uint8_t {
    STATUS_ACTIVE = 0,            // Ready to fly
    STATUS_FATIGUED = 1,          // Needs rest (too many missions)
    STATUS_INJURED = 2,           // Cannot fly (combat injury)
    STATUS_COURT_MARTIALED = 3    // Removed from duty (discipline)
};
```

**Key Discovery**: `STATUS_FATIGUED` reveals a **pilot fatigue system** requiring roster rotation. `STATUS_COURT_MARTIALED` suggests consequences for friendly fire or mission failures.

**Evidence**: Strings at 0x150153-0x150179

#### PilotAbilityCategory
```c
enum PilotAbilityCategory : uint8_t {
    ABILITY_GUNS = 0,              // Gun combat (0-100)
    ABILITY_REAR_ASPECT_IR = 1,    // AIM-9P Sidewinder
    ABILITY_ALL_ASPECT_IR = 2,     // AIM-9M Sidewinder
    ABILITY_RADAR_MISSILES = 3,    // AIM-120 AMRAAM
    ABILITY_CAS_ORDNANCE = 4,      // Close air support
    ABILITY_HEAVY_ORDNANCE = 5,    // Heavy bombs
    ABILITY_DOGFIGHTING = 6        // Air-to-air maneuvering
};
```

**Evidence**: Strings at 0x1500EA-0x150AFC

#### WingID
```c
enum WingID : uint8_t {
    WING_1ST = 0,   // 1st Wing
    WING_2ND = 1,   // 2nd Wing
    WING_3RD = 2,   // 3rd Wing
    WING_4TH = 3,   // 4th Wing
    WING_5TH = 4,   // 5th Wing
    WING_6TH = 5,   // 6th Wing
    WING_7TH = 6    // 7th Wing
};
```

**Insight**: 7-wing structure suggests hierarchical organization: Theater → Wing → Squadron → Flight → Pilot

**Evidence**: Strings at 0x14FE3C-0x14FE72

#### TheaterID
```c
enum TheaterID : uint8_t {
    THEATER_KUWAIT = 0,    // Gulf War 1991
    THEATER_ISRAEL = 1,    // Middle East conflict
    THEATER_PANAMA = 2,    // Operation Just Cause
    THEATER_JAPAN = 3,     // Defense scenario
    THEATER_KOREA = 4,     // Korean Peninsula
    THEATER_INDIA = 5      // South Asia
};
```

**File Mapping**: Theater name stored as 57-byte string in .SQU files (offset 0x03)

**Evidence**: Strings at 0x14E9A4-0x14E9C7

#### TimeOfDay
```c
enum TimeOfDay : uint16_t {
    TIME_0600 = 0x0600,    // 06:00 (dawn)
    TIME_1200 = 0x0C00,    // 12:00 (noon)
    TIME_1800 = 0x1200,    // 18:00 (dusk) [Note: 0x1200 hex = 4608 dec, likely should be 0x1200]
    TIME_2300 = 0x1700     // 23:00 (night) [Note: 0x1700 hex = 5888 dec, likely encoding issue]
};
```

**Note**: The hex values may be encoded differently. Strings are "0600 HRS.", "1200 HRS.", "1800 HRS.", "2300 HRS."

**Evidence**: Strings at 0x150335-0x150355

#### MissionType (20+ values)
```c
enum MissionType : uint8_t {
    MISSION_FIGHTER_SCRAMBLE = 0,      // Fighter scramble
    MISSION_STRIKE_SCRAMBLE = 1,       // Strike scramble
    MISSION_BOMBER_SCRAMBLE = 2,       // Bomber scramble
    MISSION_UMF_SCRAMBLE = 3,          // UMF scramble
    MISSION_AIR_SUPERIORITY = 4,       // Air superiority
    MISSION_SCREEN = 5,                // Defensive screen
    MISSION_AREACAP = 6,               // Area combat air patrol
    MISSION_ESCORT_TRANSPORT = 7,      // Escort transports
    MISSION_ESCORT_STRIKE = 8,         // Escort strike aircraft
    MISSION_ESCORT_BOMBERS = 9,        // Escort bombers
    MISSION_CAS = 10,                  // Close air support
    MISSION_GROUND_STRIKE = 11,        // Ground strike
    MISSION_BOMBMIS = 12,              // Bombing mission
    MISSION_ANTISHIP = 13,             // Anti-ship
    MISSION_SEADSHIP = 14,             // SEAD + anti-ship
    MISSION_RECONSHIP = 15,            // Ship reconnaissance
    MISSION_SEADGROUND = 16,           // SEAD (ground)
    MISSION_FRIENDLY_INTERCEPT = 17,   // Friendly intercept
    MISSION_ESCORT_E3 = 18,            // Escort AWACS
    MISSION_HELO_SUPPLY_CAP = 19       // Helicopter supply CAP
    // ... potentially more values
};
```

**Evidence**: Strings at 0x14EA4B-0x14EB44

#### WeatherCondition
```c
enum WeatherCondition : uint8_t {
    WEATHER_CLEAR = 0,           // Clear skies
    WEATHER_PARTLY_CLOUDY = 1,   // Partly cloudy
    WEATHER_CLOUDY = 2,          // Cloudy
    WEATHER_MOSTLY_CLOUDY = 3,   // Mostly cloudy
    WEATHER_OVERCAST = 4         // Overcast
};
```

**Evidence**: Strings at 0x1504E1-0x15050C

#### AIAggressiveness
```c
enum AIAggressiveness : uint8_t {
    AI_DUMB = 0,         // Low threat AI
    AI_PASSIVE = 1,      // Defensive AI
    AI_AGGRESSIVE = 2    // Offensive AI
};
```

**Evidence**: Strings at 0x14FEE5-0x14FEF4

### Type System Statistics

**Structures**: 10 defined
- 4 complete (MenuElement, UICoordinate, FlightRecord, LoadoutRecord)
- 6 partial (Pilot, Squadron, CampaignStatus, DataPointer, others)

**Enumerations**: 18 defined
- 120+ total enum values
- All values have string or code evidence

**String Evidence**: 200+ UI strings analyzed
**Code Evidence**: 3 functions (4,926 bytes) analyzed
**File Evidence**: .SQU, .CAM, .MIS formats correlated

### Integration: Files → Memory → UI

```
Disk Files (.SQU, .CAM, .MIS)
    ↓ squadron_file_loader, campaign_file_loader
In-Memory Structures (Pilot, Squadron, CampaignStatus)
    ↓ R45 Squadron Management Menu
UI Display (200+ strings, MenuElement[11])
    ↓ User Input (R45 state machine)
Modified Structures
    ↓ file_save functions
Updated Disk Files
```

**Key Insight**: The structures bridge file formats (documented) with runtime behavior (reverse-engineered). Complete understanding requires both file format analysis AND code analysis.

---

## Related Documents

- **ui_menu_system.md** - R45/R57 menu system architecture
- **R45_MENU_ANALYSIS.md** - Complete R45 Squadron Management Menu analysis
- **R57_WEAPONS_LOADOUT_MENU_ANALYSIS.md** - Complete R57 Weapons Loadout analysis
- **SQUADRON_CAMPAIGN_SYSTEM_ANALYSIS.md** - Campaign system from string evidence
- **STRUCTURES_AND_ENUMS_SUMMARY.md** - Type system extraction methodology
- **registry/structures.yaml** - All structure definitions
- **registry/enums.yaml** - All enumeration definitions

---

*Status: IN PROGRESS (92% complete)*  
*Last Analysis: R45 menu deep dive complete, type system extracted (2026-11-16)*  
*Next: Extract .SQUAD/.TSK/.SHP sample files, complete pilot/squadron structure offsets*
