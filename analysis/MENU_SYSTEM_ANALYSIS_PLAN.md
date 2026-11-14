# Falcon 3.0 Menu System Analysis Plan

**Date:** 2026-11-11  
**Goal:** Analyze menu system to trace connections to AI, mission, and other core systems  
**Approach:** Menu screens touch everything - perfect integration verification point

---

## Why Menu Systems Are Valuable

Menus are **integration hubs** that connect to nearly every game system:

1. **Mission Briefing** → Mission system, waypoints, objectives
2. **Loadout Selection** → Weapons, fuel, ECM (ARMS*.DAT files!)
3. **Pilot Roster** → Squadron management, pilot records
4. **Campaign Map** → Strategic targets, war state
5. **Aircraft Selection** → AI entity types, flight models
6. **Configuration** → System initialization, data loading
7. **Debriefing** → Results, scoring, mission replay

By tracing menu code, we can discover:
- How data files are loaded (farptr_table_get usage!)
- Where behavior tables come from
- Integration points between systems
- Data structure validation

---

## Available Menu Functions (From IDA)

### High-Level Menu Controllers

**ui_menu_frame_enter** (0x6760A, 346B bytes)
- Sets 7894h:78940
- Copies menu state
- Calls vga_dac_palette_upload
- Calls ui_loadout_menu_enter

**ui_menu_panel_init** (sub_66E62, 1365B bytes)
- Shared menu/UI panel init
- 17 callers
- Initializes 4FC2h segment state
- **Confidence: HIGH**

**ui_menu_page_setup** (sub_6A5BD, 2204B bytes)
- Menu page/panel setup
- 5 callers
- Clears 7894h:79B66/79B68
- Calls current_item_check
- **Confidence: HIGH**

**ui_menu_transition_step** (sub_67BAF, 937B bytes)
- Menu state machine transitions
- 13 callers
- 4FC2h:4FD52h state machine
- Calls store_cmd_interpreter

### Specific Menu Handlers

**ui_loadout_menu_enter** (multiple refs)
- Weapon/fuel loadout selection
- **Touches ARMS*.DAT files!**
- Multiple callers throughout codebase

**ui_loadout_menu_frame_scan** (sub_162A94, 364B bytes)
- Loadout outer frame
- Reads 7894h:79B52 control byte
- Dispatches via r35_e127

**menu_list_script_step** (sub_385AD, 152B bytes)
- Menu list frame/script step
- 3 callers

**terrain_menu_triple_step** (sub_31E6D, 82B bytes)
- Terrain menu handling
- Calls farwrap_25a1c

**ui_menu_page_args_setup** (sub_69C5D, 1011B bytes)
- 9 callers including menu_event_dispatch
- Sets up farobj_arg_thunk parameters

---

## Menu Data Files

**Found in game directory:**

```
COMMMENU       9,383 bytes    Communications menu
COMMMENU.DAT   7,234 bytes    Data
COMMMENU.IDX     316 bytes    Index

DIFFMENU       8,415 bytes    Difficulty menu
DIFFMENU.DAT  28,944 bytes    Data (large!)
DIFFMENU.IDX     444 bytes    Index

SYSMENU        8,005 bytes    System menu
SYSMENU.DAT   19,445 bytes    Data
SYSMENU.IDX      356 bytes    Index

SYSMENUF       7,909 bytes    System menu F-16
SYSMENUF.DAT  18,661 bytes
SYSMENUF.IDX     356 bytes

SYSMENUM       7,832 bytes    System menu MiG-29
SYSMENUM.DAT  18,709 bytes
SYSMENUM.IDX     356 bytes

FMENU.DEF         22 bytes    Menu definition
HMENU.DEF         22 bytes    Menu definition
MENU.DEF          22 bytes    Menu definition

GENMENU.DAT       78 bytes    General menu data
```

**File structure pattern:**
- `.DEF` files: Menu definitions (22 bytes)
- Base files: Menu screens/text
- `.DAT` files: Associated data
- `.IDX` files: Index/lookup tables

---

## Analysis Strategy

### Phase 1: File Format Analysis (1-2 hours)

1. **Parse .IDX files**
   - Likely contain offset/length pairs
   - Map to corresponding .DAT entries
   - Understand lookup mechanism

2. **Analyze .DAT files**
   - DIFFMENU.DAT is largest (28KB) - good starting point
   - Look for recognizable patterns
   - Check for strings, offsets, data structures

3. **Examine .DEF files**
   - Only 22 bytes - probably simple header
   - Compare FMENU.DEF, HMENU.DEF, MENU.DEF for patterns

### Phase 2: Code Tracing (2-3 hours)

1. **Start with ui_loadout_menu_enter**
   - Most likely to touch ARMS*.DAT
   - Weapon/fuel selection = armaments
   - Should reveal data loading pattern

2. **Trace ui_menu_page_setup**
   - HIGH confidence rating
   - 5 callers - good coverage
   - See how pages are initialized

3. **Follow ui_menu_transition_step**
   - State machine implementation
   - 13 callers - heavily used
   - Shows menu flow architecture

4. **Find farptr_table_get calls in menu code**
   - Menu functions must load data
   - Could reveal table lookup patterns
   - Might show where AI behavior tables are

### Phase 3: Integration Discovery (2-3 hours)

1. **Mission briefing menus**
   - How waypoints are displayed
   - Where action codes are shown
   - Link to mission file parsing

2. **Aircraft selection**
   - Entity type selection
   - Link to AI entity types (11 types we cataloged)
   - Flight model initialization

3. **Loadout screen**
   - ARMS*.DAT file usage confirmed
   - Weapon selection logic
   - Fuel/ECM configuration

4. **Campaign map**
   - Strategic target display
   - Link to .CAM file data
   - War state integration

### Phase 4: Validation (1 hour)

1. **Cross-reference findings**
   - Do menu data structures match AI contexts?
   - Are behavior flags visible anywhere?
   - Can we trace data flow end-to-end?

2. **Document integration points**
   - Menu → Mission system
   - Menu → AI system
   - Menu → Squadron management
   - Menu → Campaign state

3. **Update system diagrams**
   - Add menu layer to architecture docs
   - Show data flow through menus
   - Highlight discovered connections

---

## Expected Discoveries

### High Probability

1. **ARMS*.DAT usage confirmed**
   - ui_loadout_menu_enter will reference these
   - Finally understand armaments data structure
   - 18-byte format decoded

2. **Menu state machine**
   - 4FC2h:4FD52h state structure
   - Transition logic
   - Page navigation

3. **Data file loading patterns**
   - .IDX as lookup table
   - .DAT as data store
   - Common loading functions

### Medium Probability

4. **farptr_table_get usage examples**
   - Menus must load data from tables
   - Could show table structure
   - Might reveal AI behavior table location

5. **Entity type selection**
   - Aircraft menu shows entity types
   - Link to 11 AI entity types
   - Initialization sequence

6. **Mission data display**
   - How waypoints/objectives shown
   - Action code presentation
   - Link to flight params structure

### Lower Probability (But Valuable)

7. **AI behavior table reference**
   - Pilot skill selection might use behavior flags
   - Campaign difficulty could modify tactical bits
   - Mission type selection might show flag values

8. **Complete data flow trace**
   - User selection → file load → system init
   - End-to-end verification
   - All systems connected

---

## Tools and Approach

### Analysis Tools

1. **Hex editor** - Examine .DAT, .IDX, .DEF files
2. **IDA disassembly** - Trace menu function calls
3. **Python scripts** - Parse file structures
4. **grep/search** - Find patterns across files

### Documentation Output

1. **MENU_SYSTEM_ARCHITECTURE.md**
   - Overall structure
   - State machine
   - Integration points

2. **MENU_DATA_FILES.md**
   - .IDX format
   - .DAT structure
   - .DEF header

3. **MENU_INTEGRATION_MAP.md**
   - Menu → AI connections
   - Menu → Mission links
   - Menu → Squadron ties
   - Menu → Campaign refs

4. **Updated system docs**
   - Add menu layer to ai.md
   - Update mission_campaign.md
   - Enhance architecture overview

---

## Success Criteria

**Minimum (good session):**
- ✅ .IDX/.DAT file format decoded
- ✅ ui_loadout_menu_enter traced to ARMS*.DAT
- ✅ Menu state machine understood
- ✅ 2-3 integration points documented

**Target (great session):**
- ✅ All above
- ✅ farptr_table_get usage examples found
- ✅ Entity type selection traced
- ✅ Mission data display mechanism clear
- ✅ 5+ integration points mapped

**Stretch (exceptional session):**
- ✅ All above
- ✅ AI behavior table location discovered via menu code
- ✅ Complete data flow traced user → system
- ✅ All major menu functions documented
- ✅ File formats fully specified

---

## Time Estimate

**Phase 1:** 1-2 hours (file formats)  
**Phase 2:** 2-3 hours (code tracing)  
**Phase 3:** 2-3 hours (integration)  
**Phase 4:** 1 hour (validation)

**Total:** 6-9 hours for complete analysis  
**Realistic single session:** 2-3 hours → Phase 1 + partial Phase 2

---

## Why This Approach Is Better

**Compared to chasing farptr_table_get:**
- ✅ Concrete starting point (menu files exist)
- ✅ Known function names and locations
- ✅ HIGH confidence ratings from IDA
- ✅ Multiple entry points (10+ menu functions)
- ✅ Guaranteed integration with other systems

**Compared to data file guessing:**
- ✅ Menu code shows actual usage
- ✅ Real data flow observed
- ✅ No need to hypothesize - just trace
- ✅ Validation built-in (menu displays data)

**Compared to runtime debugging:**
- ✅ Static analysis sufficient
- ✅ IDA already identified key functions
- ✅ File formats can be decoded offline
- ✅ No emulator setup required

---

**Ready to proceed?** Start with Phase 1 (file format analysis) or Phase 2 (ui_loadout_menu_enter trace)?
