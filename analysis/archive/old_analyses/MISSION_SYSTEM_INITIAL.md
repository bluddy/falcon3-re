# Mission System - Initial Investigation

**Date:** November 11, 2026  
**Session:** Mission System - Session 1  
**Status:** Starting analysis

---

## Overview

The mission system in Falcon 3.0 encompasses:
1. **War Room** - Main menu and squadron management
2. **Campaign System** - Theater selection, war progression, objectives
3. **Mission Planning** - Flight routes, pilot assignment, weapon loadout
4. **Squadron Management** - 30 pilots, 18 F-16s, supplies
5. **Debriefing** - Mission results, statistics, medals

---

## Manual Overview

### War Room (Main Menu)

**Three major sections:**

1. **World Map**
   - Shows theater location (Kuwait, Israel, Panama)
   - Displays squadron info
   - Geographic box indicator

2. **Squadron Area** (lower right)
   - **FORM** - Create new squadron (up to 6 squadrons)
   - **SQUAD** - Cycle through squadrons
   - **DEACTIVATE** - Delete squadron (permanent!)
   - **THEATER** - Select campaign theater
   - **COMMIT** - Start/continue campaign
   - **Telephone** - Enter Squadron Ready Room

3. **TV Monitors**
   - **INSTANT ACTION** - Quick combat training
   - **CONFIG** - Configuration menu
   - **ACMI** - Mission replay/analysis
   - **COMMS** - Multiplayer
   - **RED FLAG** - Training missions
   - **EXIT** - Exit to DOS

### Campaign Structure

**Squadron:**
- 30 pilots with individual stats
- 18 F-16s initially (can be damaged/destroyed)
- Limited armament and supplies
- Squadrons = "saved games"

**Mission cycle:**
1. War Update screen (daily briefing)
2. Campaign Information screen (date, time, weather)
3. Mission Planning screens (route, pilots, weapons)
4. Flight execution (player flies F-16 #1 of Flight #1)
5. Debriefing (results, medals, stats)

**Missions per day:** 4 missions  
**Pilot fatigue:** Managed by squadron commander  
**Supply drops:** Periodic C-130 deliveries (must be escorted)

### Three Theaters

1. **Kuwait** - Desert Storm scenario
2. **Israel** - Middle East conflict
3. **Panama** - Central America operations

Each theater has different:
- Geography
- Enemy forces
- Victory conditions
- Political objectives

### Enemy Components

1. **Ground Forces** - Armor, infantry, artillery, AA defense
2. **Air Power** - Aircraft, runways, hangars, C&C, radar
3. **Command & Control (C3)** - Coordination infrastructure

---

## Code Investigation

### Key Functions Found

#### sub_33443: Master State Machine?
- **Address:** 0x33443
- **Size:** 2,688 bytes (massive!)
- **Level:** 19
- **Callers:** 20 functions
- **Callees:** 137 functions (!)
- **Location:** analysis/ida_falconcd/level19_batch2.txt

**Notable callees:**
- `farptr_table_get(L0)` - Data table access
- `entity_setup_step(L15)` - Entity initialization
- `entity_state_load(L6)` - Load entity state
- `game_state_setup_multi(L0)` - Multi-player game setup
- `game_setup_staged_step(L3)` - Stage game progression
- `game_setup_ramp_accum(L4)` - Game setup accumulation
- `param_table_init(L5)` - Parameter table initialization
- `key_state_machine_tick(L14)` - Keyboard input
- `hud_data_panel_draw(L6)` - HUD rendering
- `hud_value_format_draw(L5)` - HUD values
- `map_overlay_clip_frame(L18)` - Map overlay rendering
- Many entity and state management functions

**Hypothesis:** This is likely the **main game loop** or **master state machine** that coordinates:
- Menu navigation
- Mission setup
- Game state transitions
- Entity management
- Input handling
- UI rendering

**Evidence:**
- Extremely large function (2,688 bytes)
- Calls everything (137 functions)
- Mix of input, rendering, state, and entity management
- Level 19 (top-level coordinator)

---

## Search Strategy

### Targets to Find

**1. Menu/UI Functions**
- War Room screen handler
- Squadron selection logic
- Theater selection
- Button/monitor click handlers
- Screen rendering

**2. Squadron Data**
- Squadron structure (30 pilots)
- Pilot statistics
- Aircraft inventory (18 F-16s)
- Armament/supply tracking
- Squadron file format

**3. Campaign State**
- Theater data (.CAM files?)
- War progression tracking
- Victory conditions
- Day/mission counter
- Political objectives

**4. Mission Planning**
- Flight route editor
- Waypoint system
- Pilot assignment
- Weapon loadout
- Flight composition

**5. Mission Execution**
- ATO (Air Tasking Order) generation
- Mission type assignment
- Objective tracking
- Success/failure conditions

**6. Debriefing**
- Statistics collection
- Scoring system
- Medal awards
- Pilot skill updates

---

## File Formats to Investigate

**Squadron Files:**
- Likely binary format
- Contains: 30 pilot records, aircraft status, supplies
- Stored in save directory

**Campaign Files (.CAM?):**
- Theater definitions
- Victory conditions
- Enemy force composition
- Mission templates

**Tactical Files (.TAC?):**
- Waypoint definitions
- Flight assignments
- Entity placements

**Data Files (.DAT):**
- Various game data tables
- Possibly linked to `farptr_table_get()`

---

## Next Steps

### Phase 1: UI/Menu System (2-3 hours)
1. Find War Room screen handler
2. Trace button click logic
3. Locate squadron selection code
4. Map theater switching
5. Document screen rendering

### Phase 2: Squadron Management (2-3 hours)
1. Find squadron data structure
2. Locate pilot records (30 pilots)
3. Find aircraft inventory (18 F-16s)
4. Trace supply management
5. Document file format

### Phase 3: Campaign System (2-3 hours)
1. Locate campaign state data
2. Find war progression logic
3. Trace ATO generation
4. Map victory conditions
5. Document .CAM file format

### Phase 4: Mission Planning (2-3 hours)
1. Find mission planning screens
2. Trace route editor
3. Locate waypoint system
4. Find weapon loadout code
5. Document pilot assignment

---

## Questions to Answer

1. How are squadrons stored on disk?
2. How does the game track war progression?
3. Where is the ATO generated?
4. How are missions assigned to flights?
5. How do pilot skills affect performance?
6. How is scoring calculated?
7. Where are victory conditions checked?
8. How does the supply system work?
9. What triggers new pilot/aircraft deliveries?
10. How are medals awarded?

---

## Known Connections

### From AI System Analysis

**Mission data integration:**
- AI contexts reference `data_table_idx` (context[+3])
- Data loaded via `farptr_table_get(index)`
- Behavior flags from data[+6]
- Likely connected to waypoint actions

**Entity types:**
- 0x10 = Missiles/weapons
- 0x16 = Friendly aircraft
- 0x33 = Player aircraft
- These must be set during mission initialization

**Waypoint actions (from manual):**
- CAP (Combat Air Patrol)
- CAS (Close Air Support)
- INTERCEPT
- STRIKE
- SEARCH & DESTROY
- LOITER
- LANDING
- SWEEP

These must map to behavior flags (0x01-0x10)

---

## Initial Analysis Plan

**Start with:**
1. Examine `sub_33443` structure (master loop)
2. Search for "squadron" related data structures
3. Look for screen rendering functions (War Room, etc.)
4. Find file I/O operations (loading/saving squadrons)

**Tools:**
- IDA disassembly (level19_batch2.txt)
- Manual transcription (chapters 4, 5, 8)
- Memory dumps (if any mission data present)
- File search (look for .SQD, .CAM, .TAC files)

---

## Status

**Current completion:** 0%  
**Next action:** Analyze sub_33443 and search for squadron/menu code  
**Estimated time to 70%:** 6-8 hours

---

## Notes

- Mission system is the "core" of Falcon 3.0 (per manual)
- Dynamic campaign (no fixed mission sequence)
- Central Command creates missions based on war state
- Player is both squadron commander AND pilot (F-16 #1, Flight #1)
- 4 missions per day schedule
- Background war continues even when not flying
- Supply management is critical (limited resources)

**This is a complex system with many interconnected parts. Will need systematic investigation.**

---

*Session started: November 11, 2026*  
*Status: Initial investigation*
