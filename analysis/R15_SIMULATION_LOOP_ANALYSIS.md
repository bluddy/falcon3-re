# R15 Simulation Loop Analysis

**Function**: `r15_simulation_loop` (formerly `r15_flag_107762_body`, `r15_frame_processor`)  
**Address**: 0x108BAC  
**Size**: 717 bytes (196 instructions)  
**Overlay**: R15  
**Callers**: 83  
**Rank**: #16 in top 100 most-called functions

---

## Executive Summary

This is the **main simulation loop** for the R15 overlay - the actual game physics and logic update that runs every frame. It updates all game state: terrain collision, entity physics, AI processing, viewport projection, far object LOD/culling, and HUD rendering.

**Key Discovery**: The loop has **two distinct execution paths** controlled by `cs:byte_107762` (renamed to `r15_sim_mode_flag`):
- **Path A** (flag == 0): Standard mode, 37 function calls
- **Path B** (flag != 0): Complex mode, 46 function calls with far pointer state management

---

## Control Flow

### Entry Point (0x108BAC)
```asm
cmp     cs:byte_107762, 0    ; Check simulation mode flag
jz      loc_108BB7            ; if 0 → Path A (standard)
jmp     loc_108CDF            ; if 1 → Path B (complex)
```

### Path A: Standard Simulation (37 calls)
- Simpler execution path
- Direct function calls
- Used for standard flight simulation

### Path B: Complex Simulation (46 calls)  
- Extended execution path
- Uses `active_farptr_set`/`active_farptr_restore` for state preservation
- Additional rendering and state management
- Multiple far callback invocations (cb_7 called 3x vs 1x in Path A)
- 13 unique function calls not present in Path A

---

## Simulation Phases (Common to Both Paths)

### 1. Initialization & State Setup
```
0x108BB7 (A) / 0x108CDF (B):
- flag22220_clear: Clear coordination flag
- sub_10926B: Initialization
- fn_table_dispatch: Dispatch function table (SI=0x3A, DI=0x2E)
  → Returns BX, CX, DX stored to DS:0x3E, DS:0x3C, DS:0x3A
```

### 2. Physics Update
```
0x108BEC / 0x108D31:
- farobj_pos_wrap_update: Update entity position with world wrapping
- pos_clamp_40: Clamp position to 40-unit boundary
```

**Data Flow**:
- Source buffer: DS:0x2E (18 bytes)
- Destination: DS:0x40
- Entity pointer: DS:0x3A
- State buffer: DS:0x22

### 3. Terrain & Collision
```
0x108C1A (Path A only):
- terrain_frame_update_driver: Altitude, collision detection
- Uses entity at offset 0x22, pointer at 0x3A
```

### 4. Viewport Projection
```
0x108C22 (A):
- viewlist_project_flagged: Project visible objects
- Segment switch: ES = 54AFh for rendering

0x108C46-0x108C50:
- viewobj_table32_flag_project: 32-entry object table
- viewobj_table64_project: 64-entry object table  
- viewobj_table72_flag_project: 72-entry object table
```

### 5. Far Object Management (LOD/Culling)
```
0x108C2C / 0x108D7B:
- farobj_scan_74_timer_c: Time-based LOD check
- farobj_scan_74_gate_a: Visibility gate check
- farobj_scan_74_clear_b: Clear processed objects
- farobj_sort_and_step (Path A): Distance sort & simulate
```

### 6. AI Processing
```
0x108C56 / 0x108DA0:
- ai_context_batch_processor: Update all AI entities
```

### 7. Entity Movement & Updates
```
0x108C5B / 0x108DA5:
- entity_move_project_step: Move and project entities
- entity_state_load (Path A, 0x108C0F): Load state to buffer
```

### 8. HUD Rendering
```
0x108C78 / 0x108DC2:
- Segment switch: DS = ES = 54AFh
- r32_hud_phase_dispatch: Cockpit instruments rendering
- entity_table_gate_47a8d: Entity table processing
```

### 9. Callbacks & Batch Operations
```
Path A (1x each):
0x108C94: far_cb_3: Process 0x13F entities
0x108CA6: far_cb_7: Batch operation (word_10788C iterations)

Path B (4x far_cb_3, 3x far_cb_7):
0x108DF8: far_cb_3
0x108E0A: far_cb_7 iteration 1
0x108E1C: far_cb_7 iteration 2
0x108E2E: far_cb_7 iteration 3
0x108E40: far_cb_3 again
```

### 10. Timing & Frame Rate
```
0x108CAB / 0x108E45:
- tick_rate_compute: Calculate frame delta time
- Result stored: cs:word_107759 (frame tick rate)
```

### 11. Memory Management
```
0x108CB4 / 0x108E4E:
- ems_dual_op_44: EMS page swap operation
```

### 12. Task Scheduling
```
0x108CBE / 0x108E60:
- Check cs:byte_10788B: Early exit flag
- If set → zero_ax and return immediately

0x108CCC / 0x108E66:
- pending_task_run: Execute deferred tasks
```

### 13. Cleanup & Exit
```
0x108CD1 / 0x108E6B:
- undoc_108E79: Cleanup operation

0x108CD9 / 0x108E73:
- clip_pending_atomic_apply: Apply pending clip/view operations
- Return
```

---

## Path Comparison

### Common Functions (30)
Both paths execute these core systems:
- Physics: position wrapping, clamping
- Viewport: 3 object tables
- AI: batch processing
- Entities: movement, projection
- Far objects: timer/gate checks
- HUD: rendering phases
- Timing: tick rate
- Memory: EMS operations
- Tasks: pending queue
- Cleanup: clip operations

### Path A Unique (7 functions)
```
0x396B: near_fnptr_invoke
0x34FE: entity_state_load
0x3805: terrain_frame_update_driver  ← Terrain collision
0x0:    viewlist_project_flagged (far call)
0x7F:   loc_2F05F
0x1BA6: es_ptr_slots_init
0x1C5C: farobj_sort_and_step  ← Distance sorting
```

**Pattern**: Path A includes **terrain collision** and **distance-based sorting**

### Path B Unique (13 functions)
```
0x108D19: stub_to_205c3 (dispatch helper)
0x108D26: undoc_207DD
0x108D54: sub_128CD
0x108D59: undoc_109660
0x108D62: sub_12910
0x108D67: sub_1FE68
0x108D71: active_farptr_set      ← State save
0x108DAA: active_farptr_restore  ← State restore
0x108DB4: sub_1FE6F
0x108DD6: sub_210FE
0x108DE1: sub_1FF5D  
0x108DE4: sub_21240
0x108DE7: sub_20BCE
```

**Pattern**: Path B uses **far pointer save/restore** for complex state management and includes **additional rendering/update calls**

### Hypothesis: What Determines the Path?

The `r15_sim_mode_flag` (cs:byte_107762) likely controls:

- **Path A** (flag = 0): **Flight simulation mode**
  - Terrain collision active
  - Distance-based LOD
  - Standard cockpit view
  
- **Path B** (flag = 1): **External view / replay / multi-entity mode**
  - More entities processed (3x far_cb_7 vs 1x)
  - State preservation needed (farptr save/restore)
  - No terrain collision (player not controlling)
  - Additional view management

---

## Data Structures

### Local Buffers (DGROUP offsets)
- **0x2E**: Source buffer (18 bytes, copied to 0x40)
- **0x3A**: Entity/flight record pointer
- **0x3C, 0x3E**: fn_table_dispatch return values (CX, BX)
- **0x40**: Destination buffer (receives copy of 0x2E)
- **0x22**: Entity state buffer

### Global Variables (Code Segment)
- **cs:0x107762** (`r15_sim_mode_flag`): Simulation path selector
- **cs:0x107759** (`word_107759`): Frame tick rate (delta time)
- **cs:0x10788C** (`word_10788C`): Callback iteration count
- **cs:0x10788B** (`byte_10788B`): Early exit flag

### Viewport Tables
- **Table 32**: 32-entry projected objects
- **Table 64**: 64-entry projected objects
- **Table 72**: 72-entry projected objects

---

## Performance Characteristics

### Call Counts
- **Path A**: 37 function calls per frame
- **Path B**: 46 function calls per frame (+24%)
- **Far callbacks**: Path B executes 7 callbacks vs 2 in Path A

### Segment Switches
- Switch to **54AFh** for viewport rendering
- Switch to **54AFh** for HUD rendering (DS+ES)
- Return to original segments

### Critical Path
The simulation must complete within one frame tick (~18-60 FPS depending on mode):
1. Physics (2-3 calls)
2. Terrain (1 call, Path A only)
3. Viewport projection (3-4 calls)
4. AI batch (1 call)
5. Entity updates (2-3 calls)
6. Far object management (3-4 calls)
7. HUD rendering (2 calls)
8. Callbacks (2-7 calls)
9. Timing & cleanup (4-5 calls)

---

## Integration Points

### Called By (83 callers)
The simulation loop is invoked by:
- Main game loop coordinator
- Frame update dispatchers
- Overlay transition handlers
- Mode change handlers

### Calls (30+ subsystems)
- **Physics**: farobj_pos_wrap_update, pos_clamp_40
- **Terrain**: terrain_frame_update_driver
- **Viewport**: viewlist_project_flagged, viewobj_table* (3)
- **AI**: ai_context_batch_processor
- **Entities**: entity_state_load, entity_move_project_step
- **Far Objects**: farobj_scan_74_* (3), farobj_sort_and_step
- **HUD**: r32_hud_phase_dispatch, entity_table_gate_47a8d
- **Callbacks**: far_cb_3, far_cb_7
- **Timing**: tick_rate_compute
- **Memory**: ems_dual_op_44
- **Tasks**: pending_task_run
- **State**: active_farptr_set, active_farptr_restore (Path B)

---

## Implementation Notes

### Optimization Opportunities
1. **Dual paths suggest overhead**: Could be unified with function pointers
2. **Multiple segment switches**: Could batch operations per segment
3. **Repeated far callbacks**: Could be loop-based

### Design Pattern
This is a classic **game loop**:
```
while (running):
    input()           # Handled before this
    update()          # ← THIS FUNCTION
    render()          # Partial: viewport setup
    present()         # Handled after this
```

### Why Two Paths?
Likely reasons for dual implementation:
1. **Historical**: Path A developed first, Path B added for new features
2. **Performance**: Path A optimized for player flight, Path B for complex scenarios
3. **State isolation**: Path B needs save/restore for view switching

---

## Reverse Engineering Notes

### How We Identified This
1. **High call count** (83 callers, Rank #16) indicated core system
2. **Flag check at entry** suggested mode selection
3. **Subsystem diversity** (terrain, AI, viewport, HUD) indicated main loop
4. **Timing operations** (tick_rate_compute) confirmed frame processor
5. **Task scheduling** (pending_task_run) confirmed game loop

### Naming Evolution
1. `r15_flag_107762_body` (original IDA name)
2. `r15_frame_processor` (initial analysis)
3. `r15_simulation_loop` (final, after recognizing dual-path physics loop)

### Key Insights
- The flag `cs:byte_107762` is **not just initialization** - it's an active **simulation mode selector**
- Path B is **not identical** - it's 24% more complex with state management
- This is **the actual simulation tick** - where physics happens
- The **far callbacks** (cb_3, cb_7) are batch processors, possibly for AI or entity updates

---

## Future Work

### Questions to Answer
1. What sets `r15_sim_mode_flag`? When does it change?
2. What do the 13 Path B unique functions actually do?
3. Why does Path B call far_cb_7 three times?
4. What is `word_10788C` (callback iteration count)?
5. What is `byte_10788B` (early exit flag)?

### Functions to Investigate
- **stub_to_205c3**: Dispatch helper (18K calls!)
- **undoc_207DD**: Unknown Path B function
- **sub_108991**: Called by both paths, unknown purpose
- **undoc_108E79**: Cleanup function at end of loop

### Related Systems
- Input handling (runs before this)
- Rendering finalization (runs after this)
- Overlay coordinators that call this loop
- EMS memory management strategy

---

## Files Created

- `func_108bac_full.json`: Complete disassembly (196 instructions)
- `get_108bac_disasm.py`: Extraction script
- `rename_108bac_sim_loop.py`: Renaming script with 63 inline comments
- `analyze_108bac_sim_loop.py`: Path comparison analysis
- `sim_loop_108bac_analysis.json`: Structured analysis data
- `investigate_sim_loop_paths.py`: Path-specific function investigation
- `sim_loop_path_comparison.json`: Unique function lists

## Registry Updates

- ✅ Function renamed: `r15_flag_107762_body` → `r15_simulation_loop`
- ✅ Flag renamed: `byte_107762` → `r15_sim_mode_flag`
- ✅ System categorized: `r15_sim` (new category)
- ✅ Comprehensive documentation added
- ✅ 63 inline comments added in IDA

---

**Status**: Deep dive complete ✅  
**Progress**: 58/100 functions (58%)  
**Next**: Rank #17 - mode_axis_state_select

---

*Analysis Date*: 2026-11-11  
*Analyst*: Kiro AI + User  
*Confidence*: High (main loop identification), Medium (path purpose hypothesis)
