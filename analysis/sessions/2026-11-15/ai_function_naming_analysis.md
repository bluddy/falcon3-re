# AI Function Naming Analysis
**Date:** 2026-11-15
**Goal:** Name 83 new AI functions discovered through call graph tracing

## Analysis Results

### sub_3D37F (1,319 bytes) - COMPLEX AI HANDLER

**Characteristics:**
- Largest function (1,319 bytes)
- Called by only 1 function (likely a main dispatcher)
- Calls 29 other functions
- Array/memory iteration (SI/DI registers)
- Heavily accesses: `word_3B832`, `word_3B830`, `word_3B834`
- Has timer/counter logic: `dec byte ptr [si+11h]` (decrement field)
- Multiple conditional branches based on `[si+2Eh]` field

**Pattern Recognition:**
- Decrement counter at [si+11h]
- Check field at [si+2Eh] with multiple branches (negative, zero, positive)
- Accesses same data as sub_3CF9D (related functions)
- SI register used as structure pointer

**Likely Purpose:** Main AI update/step function for entity
**Proposed Name:** `ai_entity_update_step` or `ai_behavior_execute_frame`

---

### sub_3CF9D (886 bytes) - AI STATE PROCESSOR

**Characteristics:**
- 886 bytes (second largest)
- Called by 2 functions (broader use)
- Calls 29 functions (same as 3D37F - shared helper set)
- Array/memory iteration
- Accesses: `word_3B830` (shared with other AI functions)

**Pattern Recognition:**
- Same data access pattern as sub_3D37F
- Called from ai_behavior_state_machine, ai_target_tracking_update, ai_behavior_mirror_to_target
- Likely shared core processing logic

**Likely Purpose:** Core AI state processing shared by multiple systems
**Proposed Name:** `ai_state_processor_core` or `ai_behavior_update_common`

---

### sub_3F3A8 (256 bytes) - AI HELPER FUNCTION

**Characteristics:**
- 256 bytes (medium)
- Called by 5 functions (widely used helper)
- Calls 11 functions
- Accesses: `word_3B830`
- Array/memory iteration

**Likely Purpose:** Common AI calculation or state update helper
**Proposed Name:** `ai_state_calculate_helper` or `ai_behavior_calc_step`

---

### sub_49997 (130 bytes) - VECTOR ACCUMULATOR

**Characteristics:**
- 130 bytes
- Called by 2 functions
- Calls only 1 function: `fixed_vec3_accumulate_a` ✓ (already documented!)
- Accesses: `word_6B586`, `word_6B588`, `word_499DE`
- Array/memory iteration

**Pattern Recognition:**
- Calls fixed-point 3D vector accumulation
- Likely accumulates movement/position deltas
- Called by ai_context_batch_processor

**Likely Purpose:** Accumulate AI entity movement vectors
**Proposed Name:** `ai_movement_vector_accumulate` or `ai_position_delta_accumulate`

---

### sub_407C0 (131 bytes) - POSITION/TERRAIN HANDLER

**Characteristics:**
- 131 bytes
- Called by 3 functions
- Calls 5 functions including:
  - `terrain_farobj_tile_copy_resolve` ✓ (already documented!)
  - `fixed_matrix_mul` ✓
  - `flag_byte_get` ✓
- Accesses: `word_407BE`

**Pattern Recognition:**
- Calls terrain coordinate conversion
- Calls matrix multiplication (rotation/transform)
- Checks flags

**Likely Purpose:** Update AI entity position relative to terrain
**Proposed Name:** `ai_entity_terrain_position_update` or `ai_position_terrain_sync`

---

### sub_423A9 (178 bytes) - AI TRACKING/BEHAVIOR

**Characteristics:**
- 178 bytes
- Called by 2 functions
- Calls 9 functions
- Accesses: `byte_3D41A`
- Array/memory iteration

**Likely Purpose:** AI tracking or pursuit behavior
**Proposed Name:** `ai_target_pursuit_update` or `ai_tracking_behavior_step`

---

### sub_40884 (99 bytes) - ANGLE/ORIENTATION HELPER

**Characteristics:**
- 99 bytes
- Called by 2 functions
- Calls 4 functions: `sub_407B0`, `sub_40DC5`, `stub_to_24980`, `stub_to_249d8`
- Two stubs suggest angle operations (24980/249d8 are angle functions)

**Likely Purpose:** AI angle/heading calculations
**Proposed Name:** `ai_angle_calculate_helper` or `ai_heading_update_calc`

---

### sub_3EB4E (87 bytes) - STATE MACHINE DISPATCHER

**Characteristics:**
- 87 bytes
- Called by 5 functions (widely used)
- Calls 0 functions (LEAF!)
- 11 comparisons - **STATE MACHINE or DISPATCH**
- Array/memory iteration

**Pattern Recognition:**
- Many comparisons with no callees = dispatch table or state machine
- Likely switches on AI state value and returns result
- Pure computation, no side effects

**Likely Purpose:** AI state value dispatcher or state checker
**Proposed Name:** `ai_state_value_dispatcher` or `ai_state_check_switch`

---

### sub_425A2 (88 bytes) - HUD TRACKING DISPLAY

**Characteristics:**
- 88 bytes
- Called by 4 functions
- Calls 5 HUD functions: ✓
  - `hud_project_gate_draw`
  - `hud_track_gate_draw`
  - `hud_track_distance_draw`
  - `hud_track_marker_draw`
  - `fixed_vec3_accumulate_a`

**Pattern Recognition:**
- ALL callees are HUD drawing functions!
- Clearly draws tracking information on HUD
- Part of HUD system, not AI system!

**Likely Purpose:** Draw AI target tracking on HUD
**Proposed Name:** `hud_ai_target_tracking_draw` or `hud_track_overlay_draw`
**Note:** Should be in HUD system, not AI system!

---

### sub_42503 (80 bytes) - STATE DISPATCHER

**Characteristics:**
- 80 bytes
- Called by 6 functions (frequently used)
- Calls 2 functions: `sub_40CB7`, `stub_to_24988`
- 7 comparisons - **STATE MACHINE or DISPATCH**
- Accesses: `word_55E50`, `word_3B834`, `word_55E4E`

**Likely Purpose:** AI state dispatcher or condition checker
**Proposed Name:** `ai_state_condition_check` or `ai_behavior_gate_check`

---

## Summary Table

| Address | Current Name | Proposed Name | System | Size | Confidence |
|---------|--------------|---------------|--------|------|------------|
| 0x3D37F | sub_3D37F | `ai_entity_update_step` | AI | 1319B | HIGH |
| 0x3CF9D | sub_3CF9D | `ai_state_processor_core` | AI | 886B | HIGH |
| 0x3F3A8 | sub_3F3A8 | `ai_state_calculate_helper` | AI | 256B | MEDIUM |
| 0x49997 | sub_49997 | `ai_movement_vector_accumulate` | AI | 130B | HIGH |
| 0x407C0 | sub_407C0 | `ai_entity_terrain_position_update` | AI | 131B | HIGH |
| 0x423A9 | sub_423A9 | `ai_target_pursuit_update` | AI | 178B | MEDIUM |
| 0x40884 | sub_40884 | `ai_angle_calculate_helper` | AI | 99B | MEDIUM |
| 0x3EB4E | sub_3EB4E | `ai_state_value_dispatcher` | AI | 87B | HIGH |
| 0x425A2 | sub_425A2 | `hud_ai_target_tracking_draw` | HUD | 88B | **VERY HIGH** |
| 0x42503 | sub_42503 | `ai_state_condition_check` | AI | 80B | HIGH |

## Next Steps

1. Add these 10 functions to `registry/functions.yaml`
2. Run IDA synchronization
3. Analyze remaining 73 functions (mostly smaller helpers)
4. Group by calling patterns to identify clusters
5. Continue expanding call graph

## Key Insights

- **Most functions follow SI/DI array iteration pattern** - processing entity records
- **Shared data access patterns** - word_3B830, word_3B832, word_3B834 are central AI state
- **Clear hierarchies** - Large functions call many helpers, small functions are leaves
- **Cross-system integration** - One function (sub_425A2) belongs to HUD, not AI!
- **State machines are common** - Multiple dispatch/switch patterns (3EB4E, 42503)

This validates our understanding of the AI system architecture!
