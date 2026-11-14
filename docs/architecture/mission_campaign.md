# Mission & Campaign System

**Status:** IN PROGRESS (30% complete)  
**Certainty:** STRONG (file formats), HYPOTHESIS (code structures)  
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
    
    // Supply/Aircraft Data (663 bytes, 0x7F8-0xA8E)
    uint8_t  supply_data[663];       // Weapons, fuel, aircraft count
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

---

### Campaign Files (.CAM) — STRONG

**Size:** 11,828 bytes  
**Location:** Game directory (SQUAD0.CAM - SQUAD5.CAM)  
**Purpose:** Campaign state and war progression

**Contents (from Strategic Falcon documentation):**
- Theater selection (Kuwait, Israel, Panama)
- Campaign day counter
- Strategic target array (ownership, force strength)
- Victory/defeat conditions tracking
- Political objectives
- War progression state

**Strategic targets:**
```c
struct StrategicTarget {
    uint8_t  ownership;      // Allied/Enemy/Neutral
    uint8_t  strength;       // 0-100 (percent operational)
    uint8_t  type;           // Airbase, C3, Supply, Factory, etc.
    uint8_t  victory_flag;   // Is victory site?
    uint8_t  defeat_flag;    // Is defeat site?
    // ... more fields
};
```

**Theater-specific strength files:**
- ISRAEL.STR, KUWAIT.STR, PANAMA.STR
- BOSNIA.STR, INDIA.STR, JAPAN.STR, KOREA.STR, NELLIS.STR
- Define initial strategic target layout per theater

**Evidence:** File sizes confirmed, structure documented by Strategic Falcon editor

---

### Mission Files (.MIS) — STRONG

**Size:** Variable (451-824 bytes observed)  
**Location:** Game directory (SQUAD0.MIS - SQUAD5.MIS)  
**Purpose:** Current mission definition

**Contents (from Strategic Falcon documentation):**
```c
struct MissionFile {
    // Allied Flights
    Flight    allied_flights[n];
    
    // Enemy Flights
    Flight    enemy_flights[n];
    
    // Support Flights (AWACS, tankers, etc.)
    Flight    support_flights[n];
    
    // ILS Configuration
    uint8_t   ils_enabled[n_airbases];
    
    // Mission Parameters
    uint8_t   mission_type;
    uint8_t   time_of_day;
    uint8_t   weather;
};
```

**Flight definition:**
```c
struct Flight {
    uint8_t   aircraft_count;
    uint8_t   aircraft_type;
    Waypoint  waypoints[n];
    uint8_t   weapon_loadout[aircraft_count];
};
```

**Waypoint (1-byte coordinates!):**
```c
struct Waypoint {
    uint8_t   x;              // 0-255 (1/256 theater width)
    uint8_t   y;              // 0-255 (1/256 theater width)
    uint8_t   altitude;       // Encoded altitude
    uint8_t   speed;          // Speed setting
    uint8_t   action;         // CAP, CAS, INTERCEPT, etc.
    uint8_t   loiter_time;    // Minutes to loiter
};
```

**Waypoint precision:** 1 byte per coordinate = 1/256 of theater width ≈ 1.25 nm grid

**Waypoint actions:**
- 0x01 = Ground Attack (CAS, STRIKE)
- 0x02 = Landing Approach
- 0x04 = Cruise/Patrol (CAP, LOITER)
- 0x08 = Combat Mode (INTERCEPT, SWEEP)
- 0x10 = Special Mission
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
- Supply levels
- Campaign progress
- War state

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
