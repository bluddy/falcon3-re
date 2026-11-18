# Mission Files (.MIS) and AI Maneuver Files (.RFM) - Status Summary

**Date**: 2026-11-18  
**Status**: Both formats partially understood, fields need decoding

---

## Mission Files (.MIS) - 70% Decoded

### What We Know

**File Details**:
- **Count**: 15 files in game directory
- **Size**: ~1,934 bytes average
- **Purpose**: Individual mission definitions (single sorties)

**Structure Discoveries**:

#### 1. MissionSlot Structure (20 bytes) ✅
Located in .CAM campaign files (64 slots × 20 bytes = 1,280 bytes)

```c
struct MissionSlot {
    char label[2];              // +0x00: Mission ID (" \0" default)
    uint8_t mission_type;       // +0x02: MissionType enum (0-19)
    uint8_t theater_id;         // +0x03: Theater ID
    uint8_t status;             // +0x04: Status (available/active/complete)
    uint8_t waypoint_count;     // +0x05: Number of waypoints
    uint8_t flight_count;       // +0x06: Number of flights
    uint8_t target_type;        // +0x07: Target classification
    uint16_t target_id;         // +0x08: Target ID or index
    uint16_t coordinates_x;     // +0x0A: Target X coordinate
    uint16_t coordinates_y;     // +0x0C: Target Y coordinate
    uint16_t altitude;          // +0x0E: Target altitude
    uint16_t date_time;         // +0x10: Mission date/time
    uint16_t reserved;          // +0x12: Reserved/flags
};
```

**Source**: `squadron_mission_file_loader` @ 0x17B437 (4,516 bytes)

#### 2. MissionType Enum (20 values) ✅

| Value | Name | Description |
|-------|------|-------------|
| 0 | MISSION_FIGHTER_SCRAMBLE | Scramble fighters |
| 1 | MISSION_STRIKE_SCRAMBLE | Scramble strike aircraft |
| 2 | MISSION_BOMBER_SCRAMBLE | Scramble bombers |
| 4 | MISSION_AIR_SUPERIORITY | Air superiority |
| 6 | MISSION_AREACAP | Area CAP |
| 7 | MISSION_ESCORT_TRANSPORT | Escort transport |
| 8 | MISSION_ESCORT_STRIKE | Escort strike |
| 10 | MISSION_CAS | Close air support |
| 11 | MISSION_GROUND_STRIKE | Ground strike |
| 12 | MISSION_BOMBMIS | Bomb mission |
| 13 | MISSION_ANTISHIP | Anti-ship |
| 14 | MISSION_SEADSHIP | SEAD ship |
| 16 | MISSION_SEADGROUND | SEAD ground |

**Full list**: See `MISSION_SYSTEM_ANALYSIS.md`

#### 3. Related Structures ✅

**FlightRecord** (130 bytes):
- aircraft_count: uint8_t
- loadouts: LoadoutRecord[4]

**LoadoutRecord** (23 bytes):
- hardpoint_config: uint8_t[11]
- pilot_id: uint16_t

**WaypointRecord** (unknown size):
- Still being searched for
- Expected: coordinates, altitude, speed, action, formation

#### 4. Mission Strings (272 extracted) ✅

Categories:
- Navigation (53): WAYPOINT, ALTITUDE, INGRESS, EGRESS, TARGET
- Pilot/Aircraft (49): PILOT, AIRCRAFT, FLIGHT, LOADOUT, WEAPONS
- Mission Types (40): CAP, CAS, STRIKE, SEAD, ESCORT, RECON
- Threats (28): ENEMY, THREAT, SAM, AAA, BANDIT

**Source**: `MISSION_BRIEFING_STRINGS_COMPLETE.md`

### What We Don't Know

1. **Individual .MIS file format** ⚠️
   - Are the 15 .MIS files templates or actual missions?
   - How do they relate to the 64 mission slots in .CAM?
   - What's the internal structure?

2. **WaypointRecord structure** ⚠️
   - Size unknown
   - Fields unknown
   - Location unknown (separate file or embedded?)

3. **Detailed mission data** ⚠️
   - Where are full waypoint arrays stored?
   - Where is briefing text stored?
   - Where is threat intel stored?

### Documentation

- `docs/MISSION_SYSTEM_ANALYSIS.md` - Complete system overview
- `docs/MISSION_LOADER_FINDINGS.md` - MissionSlot discovery
- `docs/MISSION_BRIEFING_STRINGS_COMPLETE.md` - String extraction

---

## AI Maneuver Files (.RFM) - 30% Decoded

### What We Know

**File Details**:
- **Count**: 42 files total
- **Size**: 1504 bytes (30 files) or 1496 bytes (12 files)
- **Signature**: 0x008E (142) as first word
- **Purpose**: AI Basic Fighter Maneuver (BFM) data

**Examples**:
- DEFBFM1.RFM through DEFBFM6.RFM (default maneuvers)
- Aircraft-specific variants (likely F-16, F/A-18, MiG-29)

**Structure Analysis**:

```
Header (32 bytes):
  +0x00: 0x008E (signature)
  +0x02: 0x0000
  +0x04: 0x01030303 03030303 03000000 (initialization pattern)
  +0x14: Data begins
  
Data (1472 bytes):
  - 42% null bytes (0x00) - sparse data or padding
  - Common values:
    * 0x5A (90 decimal)  - 11.3%
    * 0x8C (140 decimal) - 10.3%
    * 0xEF (239 decimal) -  8.6%
    * 0xD0 (208 decimal) -  8.5%
    * 0xAA (170 decimal) -  5.8%
```

**Value Hypothesis**:
- 90, 140, 170, 208, 239 are likely:
  - Angles in degrees (normalized to 0-255 = 0-360°)
  - Or speeds in knots (scaled)
  - Or G-force values (scaled)
  - Or state machine states

**Possible Record Structures**:

1. **16 records × 94 bytes**
   - 16 maneuver types per file
   - 94 bytes per maneuver definition

2. **32 records × 47 bytes**
   - 32 maneuver steps per sequence
   - 47 bytes per step

3. **8 records × 188 bytes**
   - 8 complete maneuver sequences
   - 188 bytes per sequence

**Pattern Observations**:
- Files are nearly identical with small variations
- Likely represent:
  - Different AI skill levels (rookie vs ace)
  - Different aircraft types (F-16 vs MiG-29)
  - Different tactical doctrines

**Related Code**:
- `ai_combat_maneuver_selector` @ 0x3E2D3 (505 bytes)
  - Selects maneuvers based on tactical situation
  - 43 comparisons found
  - Called by ai_state_range_check
  - Part of category 2 (AI_FIGHTER) entity dispatch

**String Reference**:
- "*.RFM" string exists at 0x151001 (aPRfm in IDA)
- Need to trace xrefs to find loader function

### What We Don't Know

1. **Field structure** ⚠️
   - What does each byte represent?
   - How are maneuvers encoded?
   - What are the state transitions?

2. **Maneuver types** ⚠️
   - What maneuvers are defined? (Immelmann, Split-S, etc.?)
   - How many maneuver types per file?
   - How do they map to game situations?

3. **AI decision tree** ⚠️
   - How does ai_combat_maneuver_selector choose maneuvers?
   - What inputs affect the choice?
   - How are skill levels implemented?

4. **File naming convention** ⚠️
   - DEFBFM = Default BFM
   - Are there aircraft-specific files?
   - How are they selected at runtime?

### Documentation

- `docs/FILE_FORMATS_COMPLETE.md` - File catalog entry
- `temp/analyze_rfm_format.py` - Structure analysis script
- `temp/rfm_analysis_output.txt` - Detailed byte frequency analysis

---

## Comparison: .MIS vs .RFM

| Aspect | .MIS Mission Files | .RFM Maneuver Files |
|--------|-------------------|---------------------|
| **Count** | 15 files | 42 files |
| **Size** | ~1,934 bytes (variable) | 1504/1496 bytes (fixed) |
| **Understanding** | 70% (structure known) | 30% (format identified) |
| **Purpose** | Mission definitions | AI behavior data |
| **Related Code** | squadron_mission_file_loader | ai_combat_maneuver_selector |
| **Key Challenge** | WaypointRecord location | Field meanings |
| **Impact** | Enables mission editing | Enables AI modding |

---

## Next Steps

### Mission Files (.MIS)

1. **Analyze actual .MIS files** 🔥 HIGH PRIORITY
   - Read 15 .MIS files from game directory
   - Compare with MissionSlot structure
   - Identify file format patterns

2. **Find WaypointRecord structure**
   - Continue disassembling squadron_mission_file_loader
   - Search for waypoint array parsing
   - Map waypoint field offsets

3. **Complete MissionSlot fields**
   - Verify hypothesis for each field
   - Test by modifying .CAM files
   - Document confirmed structure

### AI Maneuver Files (.RFM)

1. **Find RFM loader function** 🔥 HIGH PRIORITY
   - Trace "*.RFM" string xref
   - Disassemble loader
   - Map file read operations to structure

2. **Analyze ai_combat_maneuver_selector**
   - Understand input parameters
   - Map decision tree logic
   - Identify how .RFM data is used

3. **Decode maneuver encoding**
   - Test hypothesis: angles, speeds, G-forces?
   - Map byte values to game behavior
   - Create decoder tool

4. **Compare files**
   - DEFBFM1 vs DEFBFM2 vs DEFBFM3
   - Identify what varies (skill level? doctrine?)
   - Map variations to observable AI behavior

---

## Tools Needed

### Mission Files
- **.MIS file reader** - Parse 15 mission files
- **MissionSlot viewer** - Display .CAM mission slots
- **Mission editor** - Modify missions in .CAM files
- **Waypoint mapper** - Visualize waypoint paths

### AI Maneuver Files
- **.RFM parser** - Decode file structure
- **Maneuver visualizer** - Display maneuver sequences
- **AI behavior logger** - Record in-game maneuver selection
- **Comparison tool** - Diff .RFM files to find patterns

---

## Critical Unknowns

### Blocking Mission Modding
1. WaypointRecord structure and location
2. Individual .MIS file format
3. How to link missions to campaigns

### Blocking AI Modding
1. .RFM field meanings (angles, speeds, states)
2. How maneuvers are selected at runtime
3. Relationship between file and ai_combat_maneuver_selector

---

## Research Questions

### Mission System
1. Are the 15 .MIS files templates or actual missions?
2. How do .MIS files relate to the 64 mission slots in .CAM?
3. Where is briefing text stored? (in .MIS? separate files?)
4. How are waypoints stored? (array in .MIS? separate file?)

### AI Maneuver System
1. What do the byte values represent?
   - 0x5A (90) = 90° turn?
   - 0x8C (140) = 140 knots?
   - 0xAA (170) = 17.0 G-force?
2. How many distinct maneuvers per file?
3. Are maneuvers sequences or lookup tables?
4. How does skill level affect maneuver selection?

---

## Code Analysis Targets

### Functions to Disassemble

**Mission System**:
1. `squadron_mission_file_loader` @ 0x17B437 (partially done)
2. Mission type comparison functions (740 found in R53)
3. Waypoint parsing functions (not yet found)

**AI Maneuver System**:
1. .RFM file loader (not yet found - trace "*.RFM" xref)
2. `ai_combat_maneuver_selector` @ 0x3E2D3 (505 bytes)
3. Maneuver execution functions (callees of selector)

---

## Success Criteria

### Mission Files
✅ MissionSlot structure mapped (20 bytes)  
✅ MissionType enum extracted (20 values)  
✅ Mission strings identified (272 strings)  
⚠️ WaypointRecord not found  
⚠️ .MIS file format unknown  
⚠️ Waypoint storage location unknown

**Overall**: 70% complete

### AI Maneuver Files
✅ File structure identified (1504/1496 bytes)  
✅ Signature confirmed (0x008E)  
✅ Byte patterns analyzed  
✅ Related code found (ai_combat_maneuver_selector)  
⚠️ Field meanings unknown  
⚠️ Loader function not found  
⚠️ Maneuver encoding not decoded

**Overall**: 30% complete

---

## Conclusion

We have **strong structural understanding** of both formats but need **field-level decoding** to enable modding:

**Mission Files**: Can view mission slots, but can't create new missions without WaypointRecord and .MIS format.

**AI Maneuver Files**: Can identify files and structure, but can't modify AI behavior without understanding field meanings.

**Next Critical Step**: 
1. Analyze actual .MIS files (read 15 files, compare structures)
2. Find .RFM loader (trace string xref, disassemble)

Both are achievable with targeted IDA analysis.
