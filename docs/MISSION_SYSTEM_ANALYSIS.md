# Falcon 3.0 Mission System Analysis

**Date**: 2026-11-16  
**Status**: In Progress - Enum Extraction Complete  
**Goal**: Document mission briefing system and locate MissionRecord/WaypointRecord structures

---

## Summary

Successfully extracted complete mission briefing UI strings (272 items) and MissionType enum (20 values). R53 overlay confirmed as primary mission briefing coordinator (32KB, 48 functions). Currently searching for mission data structures via code analysis.

---

## Mission Type Enum

**Enum**: `MissionType` (20 members, 2-byte width)

| Value | Name | Description |
|-------|------|-------------|
| 0 | MISSION_FIGHTER_SCRAMBLE | Scramble fighters |
| 1 | MISSION_STRIKE_SCRAMBLE | Scramble strike aircraft |
| 2 | MISSION_BOMBER_SCRAMBLE | Scramble bombers |
| 3 | MISSION_UMF_SCRAMBLE | UMF scramble |
| 4 | MISSION_AIR_SUPERIORITY | Air superiority |
| 5 | MISSION_SCREEN | Screen mission |
| 6 | MISSION_AREACAP | Area CAP |
| 7 | MISSION_ESCORT_TRANSPORT | Escort transport |
| 8 | MISSION_ESCORT_STRIKE | Escort strike aircraft |
| 9 | MISSION_ESCORT_BOMBERS | Escort bombers |
| 10 | MISSION_CAS | Close air support |
| 11 | MISSION_GROUND_STRIKE | Ground strike |
| 12 | MISSION_BOMBMIS | Bomb mission |
| 13 | MISSION_ANTISHIP | Anti-ship |
| 14 | MISSION_SEADSHIP | SEAD ship |
| 15 | MISSION_RECONSHIP | Recon ship |
| 16 | MISSION_SEADGROUND | SEAD ground |
| 17 | MISSION_FRIENDLY_INTERCEPT | Friendly intercept |
| 18 | MISSION_ESCORT_E3 | Escort E-3 AWACS |
| 19 | MISSION_HELO_SUPPLY_CAP | Helicopter supply CAP |

**Evidence**: 
- File: `analysis/mission_type_list.json`
- Extraction script: `ida_scripts/list_mission_types_fixed.py`
- IDA enum exists and is properly defined

---

## R53 Mission Briefing Overlay

**Segment**: `R53_569Fs`  
**Address**: 0x1820b0 - 0x189f10  
**Size**: 32,352 bytes (32KB)  
**Functions**: 48 functions

### Key Functions

| Address | Name | Size | Description |
|---------|------|------|-------------|
| 0x1820b0 | game_mode_r53_main_coordinator | 12,693 bytes | Main briefing loop |
| TBD | r53_script_opcode_interpreter | 5,048 bytes | Mission script interpreter |
| TBD | r53_map_window_quota_step | 1,324 bytes | Map rendering system |
| TBD | overlay_r52_handler | 2,026 bytes | Calls R52/R57 overlays |

**Evidence**:
- File: `analysis/r53_analysis_result.json`
- Documentation: `docs/R53_MISSION_BRIEFING_ANALYSIS.md`

---

## Mission Strings Extracted

**Total**: 272 mission-related strings (from 1330 total)

### Categories

| Category | Count | Examples |
|----------|-------|----------|
| Navigation | 53 | WAYPOINT, ALTITUDE, INGRESS, EGRESS, TARGET |
| Pilot/Aircraft | 49 | PILOT, AIRCRAFT, FLIGHT, LOADOUT, WEAPONS |
| Mission Types | 40 | CAP, CAS, STRIKE, SEAD, ESCORT, RECON |
| Mission Info | 38 | MISSION, OBJECTIVE, BRIEFING, DEBRIEF |
| Threats | 28 | ENEMY, THREAT, SAM, AAA, BANDIT |
| Flight Params | 21 | SPEED, HEADING, DISTANCE, FUEL, TIME |
| UI Control | 17 | CONTINUE, CANCEL, OK, DONE |
| Results | 14 | SCORE, KILL, LOSS, DAMAGE, SUCCESS |
| Weather | 8 | WEATHER, WIND, VISIBILITY, CLOUD |
| Display | 4 | MAP, ZOOM, VIEW, SHOW |

### Most Referenced Strings

| String | References | Usage |
|--------|-----------|-------|
| `n/.`ALTITUDE` | 17 | Altitude display/input |
| `j4.`TARGET` | 12 | Target selection |
| `e1.`ENEMY AIRCRAFT` | 10 | Threat display |
| `x1.`ENEMY FORCES` | 8 | Enemy forces info |

### Menu Item Format

Pattern: `[Key][Code].`[Label]`

28 menu items identified with this format (keyboard shortcuts for UI navigation).

**Evidence**:
- File: `analysis/briefing_strings_complete.json`
- Documentation: `docs/MISSION_BRIEFING_STRINGS_COMPLETE.md`
- Extraction script: `ida_scripts/extract_all_briefing_strings.py`

---

## Mission Type Usage Analysis

### R53 Segment Scan Results

**Comparisons Found**: 740 (mostly false positives)

Many comparisons are with small values (0, 1, 2, 3, 7, 8) which could be:
- Mission type enum values
- Loop counters
- Boolean flags
- Other small integers

**Issue**: Cannot distinguish mission type comparisons from general numeric comparisons without more context.

### Memory Access Patterns

**Attempted**: Scan for memory loads followed by mission type comparisons

**Result**: No patterns found in R53

**Hypothesis**: R53 (UI layer) doesn't directly access mission structures. Mission data is likely:
1. Loaded into global state before R53 is invoked
2. Accessed through function calls (abstraction layer)
3. Stored in different segments (main data segments, not R5X overlays)

**Evidence**:
- File: `analysis/mission_type_refs_r53.json` (740 comparisons, mostly noise)
- File: `analysis/mission_structure_offsets.json` (0 patterns found)
- Scripts: `ida_scripts/find_mission_type_refs_in_r53.py`, `ida_scripts/find_mission_structure_by_enum.py`

---

## Known Related Structures

From `registry/structures.yaml`:

### FlightRecord
- **Size**: 130 bytes (0x82)
- **Source**: R57 weapons loadout menu analysis
- **Fields**:
  - aircraft_count: uint8_t - Number of aircraft in flight (1-4)
  - loadouts: LoadoutRecord[4] - Array of loadout records

### LoadoutRecord
- **Size**: 23 bytes (0x17)
- **Source**: R57 weapons loadout menu analysis  
- **Fields**:
  - hardpoint_config: uint8_t[11] - Weapon configuration
  - pilot_id: uint16_t - Assigned pilot

### SquadronHeader
- **Size**: 60 bytes (0x3C)
- **Source**: .SQU file format analysis
- **Fields**: theater_id, theater_name, statistics, etc.

### PilotRecord
- **Size**: 66 bytes (0x42)
- **Source**: .SQU file format analysis
- **Fields**: rank, callsign, nickname, skills, mission_data, etc.

---

## Missing Structures

### MissionRecord (Not Found)

**Expected Fields**:
- mission_type: MissionType enum (2 bytes)
- mission_name: char[] - Mission designation
- theater: uint8_t - Theater ID
- target_type: uint8_t - Target classification
- target_coordinates: int32_t[2] - Lat/Long or X/Y
- target_altitude: uint16_t - Target altitude
- waypoint_count: uint8_t - Number of waypoints
- waypoints: WaypointRecord[] - Array of waypoints
- flight_count: uint8_t - Number of flights
- flights: FlightRecord[] - Array of flight records
- weather: WeatherRecord - Weather conditions
- threats: ThreatInfo[] - Enemy threat data
- objective: char[] - Mission objective description
- intel: char[] - Intelligence briefing text

**Evidence for Fields**: Mission briefing strings reference all these concepts.

**Search Strategy**:
1. Find mission type enum usage in main data segments (not R53)
2. Look for structures with known sizes (FlightRecord 130 bytes, LoadoutRecord 23 bytes)
3. Trace backwards from UI rendering functions to data sources
4. Analyze mission file format (.MSN files if they exist)
5. Check campaign save game format (.TAC files)

### WaypointRecord (Not Found)

**Expected Fields**:
- waypoint_type: uint8_t - Type (IP, target, egress, etc.)
- coordinates: int32_t[2] - Lat/Long or X/Y
- altitude: uint16_t - Waypoint altitude (feet or meters)
- speed: uint16_t - Speed at waypoint
- heading: uint16_t - Heading (0-360 degrees)
- action: uint8_t - Action at waypoint (bomb, loiter, etc.)
- formation: uint8_t - Formation type
- labels: char[] - Waypoint name/label

**Evidence**: Strings reference WAYPOINT, ALTITUDE, INGRESS, EGRESS, IP, TARGET concepts.

---

## Related Overlays

| Overlay | Size | Purpose |
|---------|------|---------|
| R52 | 4,560 bytes | Pilot assignment, loadout menu |
| R53 | 32,352 bytes | Mission briefing coordinator |
| R57 | ~8KB (est.) | Weapons loadout menu |

**R52** is called by R53 for pilot/aircraft assignment.  
**R57** is called by R53 for weapons loadout configuration.

---

## Script Execution Issues Resolved

### Problem
IDA scripts were completing (Exit Code 0) but producing no output files.

### Root Cause
1. Wrong API usage for enum member iteration
2. Using `idc.get_first_enum_member()` / `idc.get_next_enum_member()` incorrectly
3. Should iterate by value range and call `idc.get_enum_member(enum_id, value, 0, -1)`

### Solution
```python
# WRONG (returns None)
member_id = idc.get_first_enum_member(enum_id)
value = idc.get_enum_member_value(member_id)  # None!

# RIGHT
for value in range(256):
    const_id = idc.get_enum_member(enum_id, value, 0, -1)
    if const_id != idc.BADADDR:
        name = idc.get_enum_member_name(const_id)
```

**Evidence**: `ida_scripts/list_mission_types_fixed.py` now works correctly.

---

## Next Steps

### 1. Search Main Data Segments
- Scan non-R5X segments for MissionType enum usage
- Look for structures containing mission type field at known offsets
- Check segment 6E1E (referenced heavily in R53)

### 2. Analyze Mission Files
- Look for .MSN mission files in game directory
- Analyze mission file format if files exist
- Compare with campaign save files (.TAC)

### 3. Trace Data Flow
- Start from mission briefing display code
- Trace backwards to find data sources
- Identify global pointers to mission data

### 4. Check Function Parameters
- Find functions that take mission type as parameter
- Analyze how mission data is passed between functions
- Look for structure pointers in function calls

### 5. Manual IDA Inspection
- Open IDA GUI
- Navigate to R53 main coordinator (0x1820b0)
- Follow data references manually
- Check cross-references to MissionType enum
- Examine segment 6E1E:0000 (appears in many accesses)

---

## Files Generated

| File | Description |
|------|-------------|
| `analysis/mission_type_list.json` | MissionType enum members (20 values) |
| `analysis/mission_type_refs_r53.json` | 740 comparisons in R53 (mostly noise) |
| `analysis/mission_structure_offsets.json` | Memory access patterns (0 found) |
| `analysis/briefing_strings_complete.json` | 272 mission strings categorized |
| `analysis/r53_analysis_result.json` | R53 segment analysis |
| `docs/R53_MISSION_BRIEFING_ANALYSIS.md` | R53 documentation |
| `docs/MISSION_BRIEFING_STRINGS_COMPLETE.md` | String extraction documentation |

---

## Conclusion

**What We Know**:
- Mission types defined (20 enum values)
- UI strings identified (272 items)
- Briefing coordinator located (R53, 32KB)
- Related structures known (FlightRecord, LoadoutRecord, PilotRecord)

**What We Need**:
- MissionRecord structure definition
- WaypointRecord structure definition
- Mission data segment location
- Mission file format (.MSN if exists)

**Why It's Hard**:
- UI layer (R53) doesn't directly access structures
- Data likely in global state, not overlay code
- Need to find where mission data is initialized/loaded
- May require analyzing campaign/mission file loaders

**Recommended Next Action**:  
Manual IDA inspection of segment 6E1E and function call tracing from R53 back to data sources.
