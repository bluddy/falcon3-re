# Analysis Bookmarks - Functions to Revisit

## High Priority

### 1. r15_simulation_loop (0x108BAC) - **SIMULATION CORE**
**Rank**: #16, 83 callers, 717 bytes  
**Status**: Deep dive complete, but needs follow-up

**Why Revisit**:
- This is the **main simulation loop** - the heart of the flight sim
- Dual-path architecture (cockpit vs external view) needs full understanding
- 13 unique Path B functions not yet analyzed
- Understanding what sets `r15_external_view_flag` and when

**Questions to Answer**:
1. What are the 13 Path B unique functions? (stub_to_205c3, undoc_207DD, sub_128CD, etc.)
2. Who sets `r15_external_view_flag`? When does it toggle?
3. Why does Path B need `active_farptr_set/restore`?
4. What is `word_10788C` (callback iteration count)?
5. What is `byte_10788B` (early exit flag)?
6. What do far_cb_3 and far_cb_7 actually process?

**Related Systems**:
- Input handling (pre-simulation)
- Rendering finalization (post-simulation)  
- View/camera management
- EMS memory architecture

**Files**:
- `analysis/R15_SIMULATION_LOOP_ANALYSIS.md` (400+ line deep dive)
- `analysis/ida_falconcd/sim_loop_108bac_analysis.json`
- `analysis/ida_falconcd/func_108bac_full.json` (196 instructions)

**Next Steps**:
- Investigate Path B unique functions
- Trace `r15_external_view_flag` writes
- Analyze far_cb_3 and far_cb_7 dispatchers
- Map the complete simulation flow

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
