# Analysis Bookmarks - Functions to Revisit

## High Priority

### 1. r15_simulation_loop (0x108BAC) - **SIMULATION CORE** ✅ COMPLETE
**Rank**: #16, 83 callers, 717 bytes  
**Status**: ✅ **Deep dive complete - 100% analyzed**

**Achievement**:
- ✅ Identified as main simulation loop
- ✅ Discovered dual-path architecture (cockpit vs external view)
- ✅ All 13 Path B unique functions analyzed
- ✅ All functions renamed in IDA with descriptive names
- ✅ 38 inline comments added
- ✅ Complete understanding of external view rendering pipeline

**Path B = External View Mode** (Chase camera, flyby views):
- View transformation (world → camera space)
- Camera-based terrain rendering
- Orientation classification
- Smooth camera motion with delta vectors
- Mode-based dispatch system
- Far pointer state management

**Documentation**:
- `analysis/R15_SIMULATION_LOOP_ANALYSIS.md` (400+ lines)
- `analysis/PATH_B_ANALYSIS.md` (100% complete, all 13 functions)

**Remaining Optional Tasks**:
- ☐ Trace r15_external_view_flag writes (find view mode switching code)
- ☐ Document camera state structure details
- ☐ Map view key bindings (F2/F3/F4)

---

## Medium Priority

### 2. squadron_mission_file_loader (0x17B437) - Rank #10
**Why**: Loads .SQUAD/.MTV/.SHP/.TSK files, deep dive complete but 4 callees not fully analyzed

### 3. theater_campaign_file_loader (0x15A8B0) - Rank #11  
**Why**: Loads .THEATER/.WAR campaign data, 4 investigated callees but more to explore

### 4. r57_menu_state_machine (0x1A57F0) - Rank #12
**Why**: Weapons loadout menu, 7-state FSM, deep dive complete but state transitions merit review

---

## Context for New Sessions

When resuming work on **r15_simulation_loop**:
1. Read `analysis/R15_SIMULATION_LOOP_ANALYSIS.md` first
2. The flag is now named `r15_external_view_flag` (was `r15_sim_mode_flag`)
3. Path A = cockpit view (37 calls), Path B = external view (46 calls)
4. Focus on understanding the Path B unique functions
5. IDA has 63 inline comments documenting phases

---

*Created*: 2026-11-11  
*Last Updated*: 2026-11-11
