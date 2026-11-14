# Falcon 3.0 File Formats - From Modding Tools

**Date:** November 11, 2026  
**Source:** Strategic Falcon, FCE, FSM modding tools documentation  
**Status:** File format specifications extracted from editor documentation

---

## Overview

Based on documentation from three major modding tools:
1. **Strategic Falcon (SF)** - Campaign/mission editor
2. **Falcon Campaign Editor (FCE)** - Squadron/pilot/supply editor  
3. **Falcon Squadron Manager (FSM)** - Squadron roster manager

These tools reveal the structure of Falcon 3.0's mission and squadron files.

---

## Squadron Files (.SQU)

**Size:** 2,703 bytes  
**Contains:** Squadron data for campaigns

### Structure (from FCE/FSM documentation)

**Data elements:**
- Squadron name/insignia
- **30 pilots** with individual stats:
  - Pilot name/callsign
  - Rank (changeable via FCE/FSM)
  - Status: Active, KIA, MIA, Court Martialed
  - **Ability scores:**
    - Dogfighting ability (0-100)
    - Bombing ability (0-100)
    - Flying ability (0-100)
    - Fatigue level (0-100)
  - Face/portrait index
  
**File operations:**
- Created by FORM button in War Room
- Up to 6 squadrons (SQUAD0.SQU through SQUAD5.SQU)
- Can be backed up/restored
- Modified by FCE/FSM editors

**Pilot resurrection:**
- Dead pilots can be brought back via editors
- Stats may suffer when pilots die
- Roster can be re-sorted by rank

---

## Campaign Files (.CAM)

**Size:** 11,828 bytes (observed from SQUAD0.CAM)  
**Contains:** Campaign state and war progression

### Structure (from Strategic Falcon documentation)

**Data elements:**
- Theater selection (Kuwait, Israel, Panama)
- Campaign day counter
- War state (strategic target status)
- Victory/defeat conditions
- Political objectives
- **Strategic targets:**
  - Ownership (Allied/Enemy)
  - Force strength (0-100?)
  - Target type (C3, airbase, supply, etc.)
  - Victory site designation
  - Defeat site designation

**File operations:**
- Created when squadron commits to theater
- Backed up by Strategic Falcon (*.BAK files)
- Can be restored via RESTRCAM.BAT
- Modified by Strategic Falcon editor

**Campaign progression:**
- Background war continues even when not flying
- Central Command generates missions based on war state
- No fixed mission sequence (dynamic)

---

## Mission Files (.MIS)

**Size:** Variable (observed: 451-824 bytes)  
**Contains:** Current mission definition

### Structure (from Strategic Falcon documentation)

**Data elements:**
- **Flight definitions:**
  - Allied flights (your squadron)
  - Enemy flights
  - Support flights (AWACS, tankers, etc.)
- **Waypoints:**
  - Position (1-byte storage: 1/256 theater width ~= 1.25 nm precision)
  - Speed setting
  - Altitude
  - Action type (CAP, CAS, INTERCEPT, STRIKE, etc.)
  - Loiter time
- **Flight composition:**
  - Aircraft per flight
  - Pilot assignments
  - Weapon loadouts
- **ILS (Instrument Landing System) data:**
  - Which airbases have ILS enabled
  - Starting position (Flight 1, Waypoint 0)

**Waypoint storage:**
- Only 1 byte per coordinate
- Granularity: 1/256 of theater width
- Strategic Falcon snaps to nearest grid point (right and down)
- Explains why waypoints "jump" when editing

**Known waypoint actions:**
- CAP (Combat Air Patrol)
- CAS (Close Air Support)
- INTERCEPT
- STRIKE
- SEARCH & DESTROY
- LOITER
- LANDING
- SWEEP
- Escort
- SAM suppression

---

## War State Files (.WAR)

**Size:** 161 bytes  
**Contains:** Daily war status summary

### Structure (inferred)

**Likely data elements:**
- Current campaign day
- Mission counter (up to 4 per day)
- Daily casualties
- Daily mission results
- Progression toward victory/defeat

**File operations:**
- Updated after each mission
- Backed up by Strategic Falcon
- Small size suggests summary/index data

---

## Flight Data Files (.FLA)

**Size:** 1,506 bytes (observed from SQUAD0.FLA)  
**Contains:** Unknown flight-specific data

### Speculation

**Possible contents:**
- Flight recorder data?
- Mission history?
- Pilot sortie logs?
- ACMI recording data?

**Needs investigation.**

---

## MTV Files (.MTV)

**Size:** 182-202 bytes  
**Contains:** Mission descriptions (text)

### Structure (from Strategic Falcon documentation)

**Data elements:**
- **Mission description text** (editable)
- Viewable via F2 key during mission planning
- Editable with text editor

**Usage:**
- Provides mission briefing text
- Refreshes player memory about mission goals
- Can be customized by mission designers

**File operations:**
- Backed up by Strategic Falcon (becomes *.BAK)
- Plain text format (likely)

---

## Supply/Inventory Data

**Located in:** .SQU file (part of squadron data)

### Structure (from FCE documentation)

**Ordnance tracking:**
- Each weapon type has quantity (max 250)
- **Weapon types tracked:**
  - Air-to-air missiles
  - Air-to-ground missiles  
  - Bombs (various types)
  - AGM-65 Mavericks
  - CBU cluster bombs
  - Mk-82/83/84 bombs
  - **ECM pods:** Tracked separately (max 50 total)
  - **Bullets:** 20mm cannon ammunition
  - **Chaff:** Countermeasure quantity
  - **Flares:** Countermeasure quantity

**Fuel tracking:**
- Total fuel pool in pounds
- FCE resupply: 280,000 lbs total
- Per-aircraft fuel calculated by FCE:
  - Based on weight, armament, drag
  - Speed, altitude, distance of waypoints
  - Fuel burn calculations available

**Aircraft tracking:**
- Total F-16s available
- Starting count: 18 aircraft
- Can be damaged/destroyed in combat
- FCE can restore to 18

**Supply deliveries:**
- Periodic C-130 cargo flights
- Player must escort C-130s
- If C-130s destroyed: no resupply
- Wait for next supply date

---

## ILS Configuration Files

**Files:** ILS.BOS, ILS.HOK, ILS.IRQ, ILS.ISR, ILS.KOR, ILS.NEL, ILS.PAK, ILS.PAN  
**Contains:** ILS (Instrument Landing System) enabled airbases per theater

### Structure

**Data elements:**
- List of airbases with ILS available
- Per-theater configuration
- Affects starting position placement

**Known issues:**
- Strategic Falcon can remove ILS from strips
- Can cause player to spawn away from airfield
- ILSRESET.EXE restores default ILS configuration
- Strategic Falcon can "force" ILS onto specific strips

**Usage:**
- Determines where F-16 Flight 1, Waypoint 0 can start
- Affects mission planning
- Must have ILS at starting airbase

---

## Strength Files (.STR)

**Files:** BOSNIA.STR, INDIA.STR, ISRAEL.STR, JAPAN.STR, KOREA.STR, KUWAIT.STR, NELLIS.STR, PANAMA.STR  
**Contains:** Strategic target data per theater

### Structure (from FCE documentation)

**Data elements:**
- **Strategic targets** per theater
- Target properties:
  - Ownership (Allied/Enemy)
  - Force strength percentage
  - Target type
  - Victory/defeat significance
  
**Usage:**
- Defines theater layout
- Initial war state
- Victory conditions
- Strategic Falcon can edit these

---

## Squadron Names File

**File:** SQDNAMES.STR  
**Contains:** Available squadron names/insignias

### Structure

**Data elements:**
- Squadron insignia graphics reference
- Squadron name text
- Available for selection via FORM button

**Usage:**
- User cycles through with arrows
- Each insignia has associated name
- FCE can create new squadron names
- Customizable for modding

---

## Backup Files

Created by Strategic Falcon for campaign restoration:

**Format:** Original extension + .BAK
- **SQU0SQU.BAK** - Squadron backup
- **SQU0MTV.BAK** - Mission description backup
- **SQUAD0.CAM** → **.BAK** - Campaign backup
- **SQUAD0.WAR** → **.BAK** - War state backup  
- **SQUAD0.MIS** → **.BAK** - Mission backup

**Restoration:**
- RESTRCAM.BAT batch file
- Fully restores campaign state
- Restores to previous mission
- Can recover from crashes/corruption

---

## File Relationships

```
Squadron (.SQU)
├── 30 Pilots (stats, rank, status)
├── 18 Aircraft (availability)
└── Supplies (weapons, fuel, ECM, chaff, flares)

Campaign (.CAM)
├── Theater (Kuwait/Israel/Panama)
├── War State (strategic targets)
├── Day Counter
└── Victory/Defeat Conditions

Mission (.MIS)
├── Allied Flights (+ waypoints)
├── Enemy Flights (+ waypoints)
├── Support Flights
├── ILS Data
└── Flight Composition

War State (.WAR)
├── Current Day
├── Mission Counter (1-4 per day)
└── Daily Summary

Mission Description (.MTV)
└── Briefing Text (F2 to view)

Flight Data (.FLA)
└── Unknown (possibly ACMI/history)
```

---

## File I/O Patterns

**From Strategic Falcon TSR (STRTSPRT.COM):**
- Required for Falcon 3.02+ compatibility
- Intercepts file operations
- Sets read-only bits on mission files
- Prevents Falcon from overwriting during edit
- Must run CLEAR.BAT to remove protection

**Campaign crashes:**
- If crash occurs during StratFalc edit
- Mission files may be corrupted
- Use RESTRCAM.BAT to restore
- Always load STRTSPRT.COM before editing

**Version compatibility:**
- Falcon 3.01.1: No TSR required
- Falcon 3.02+: Must use STRTSPRT.COM
- FALCONCD.EXE: Special installation steps
- Disabling version check: Dangerous!

---

## Modding Tools Capabilities

### Strategic Falcon (SF.EXE)
- Edit campaign missions
- Move waypoints
- Add/remove flights
- Change flight composition
- Edit strategic target ownership/strength
- Change victory conditions
- Edit ILS configuration
- Timing trace (4-second jumps)
- Map printing

### Falcon Campaign Editor (FCE.EXE)
- DOS & Windows modes
- Edit individual pilot stats
- Resurrect dead pilots
- Change pilot ranks/names
- Resupply ammunition (+20 per type)
- Resupply fuel (280,000 lbs)
- Restore aircraft (back to 18)
- Fuel burn calculations
- Squadron roster printing
- Flight data reports
- Generate Red Flag from campaign mission
- Import Red Flag to campaign

### Falcon Squadron Manager (FSM.EXE)
- Edit squadron rosters
- Change pilot abilities
- Modify fatigue levels
- Customize wingman comments (text only)
- Change rank structures
- Squadron statistics
- Rename squadrons

---

## Data Extraction Strategy

### For .SQU Files (2,703 bytes)

**Header (estimated ~64 bytes):**
- Flags/version bytes
- Theater name (null-terminated string)
- Squadron name/insignia index

**Pilot records (30 × ~88 bytes = 2,640 bytes):**
- Callsign (16 bytes?)
- Name/nickname (16 bytes?)
- 3-letter ID code (4 bytes)
- Rank (1 byte)
- Status (1 byte: Active/KIA/MIA/CM)
- Dogfighting skill (1 byte: 0-100)
- Bombing skill (1 byte: 0-100)
- Flying skill (1 byte: 0-100)
- Fatigue (1 byte: 0-100)
- Face/portrait index (1 byte?)
- Unknown fields (~54 bytes)

**Supply data (location unclear):**
- Fuel total (4 bytes?)
- Aircraft count (1 byte?)
- Weapon quantities (n × 1-2 bytes each)

### For .CAM Files (11,828 bytes)

**Estimated structure:**
- Campaign header
- Strategic target array (n targets × m bytes each)
- War progression data
- Victory/defeat tracking
- Political objectives

### For .MIS Files (variable size)

**Estimated structure:**
- Mission header
- Flight definitions array
- Waypoint array (1 byte per coordinate)
- Weapon loadout data
- ILS configuration

---

## Next Steps

### Immediate

1. **Hex dump analysis** of SQUAD0.SQU (2,703 bytes)
   - Confirm pilot record size (~88 bytes)
   - Locate supply data
   - Map all 30 pilot records

2. **Parse .CAM file** (11,828 bytes)
   - Find strategic target array
   - Locate war state data
   - Map victory conditions

3. **Decode .MIS file** (variable size)
   - Extract flight definitions
   - Parse waypoint coordinates
   - Understand weapon loadout format

### Code Search

1. **Find file I/O code**
   - Search for "SQUAD" string references
   - Locate fopen/fread calls
   - Trace .SQU loading code

2. **Find squadron structure**
   - 30 pilot array in memory
   - Aircraft inventory tracking
   - Supply management code

3. **Find UI code**
   - War Room rendering
   - Squadron selection logic
   - Mission planning screens

---

## References

**Documentation sources:**
- `old_mods/strategic_falcon/STRAT/READ.ME`
- `old_mods/strategic_falcon/STRAT/READ.ME!`
- `old_mods/fce/FCE.TXT`
- `old_mods/fsm/FSM18.TXT`

**Key modding tools:**
- Strategic Falcon 1.21 (SF.EXE)
- Falcon Campaign Editor 1.3 (FCE.EXE)
- Falcon Squadron Manager 1.8 (FSM18A.EXE/FSM18B.EXE)

---

## Conclusion

The modding tools provide extensive documentation about Falcon 3.0's file formats. We now know:

✅ **Squadron files** contain 30 pilots with 4 ability scores  
✅ **Campaign files** track strategic targets and war state  
✅ **Mission files** use 1-byte waypoint coordinates  
✅ **Supply system** tracks weapons, fuel, aircraft  
✅ **File relationships** and backup/restore mechanisms

**Next:** Parse actual binary files to extract exact structures and confirm documentation.

---

*Created: November 11, 2026*  
*Source: Modding tool documentation analysis*
