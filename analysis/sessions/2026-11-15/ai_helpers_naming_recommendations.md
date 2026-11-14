# AI Helper Functions - Naming Recommendations
**Date:** 2026-11-15  
**Source:** Batch analysis of 19 remaining AI helper functions

## High Priority - Widely Used Leaf Functions (Pure Calculations)

These are fundamental helpers called by many functions. No callees = pure computation.

### sub_428A1 (32B) - **21 CALLERS!** 
**Pattern:** 3 comparisons, no calls, 32 bytes  
**Callers:** Widely used across AI system  
**Proposed Name:** `ai_state_value_get` or `ai_field_value_calc`  
**Confidence:** HIGH  
**Rationale:** Most widely used leaf function. Likely gets/calculates a core AI state value.

---

### sub_40DB5 (16B) - **17 CALLERS**
**Pattern:** No comparisons, no calls, tiny (16B)  
**Callers:** Used across AI system  
**Proposed Name:** `ai_field_offset_calc` or `ai_record_field_get`  
**Confidence:** MEDIUM  
**Rationale:** Very small, no comparisons = simple field accessor or offset calculator.

---

### sub_428C1 (19B) - **17 CALLERS**
**Pattern:** 1 comparison, no calls, tiny (19B)  
**Callers:** Used across AI system  
**Proposed Name:** `ai_field_check_flag` or `ai_state_flag_test`  
**Confidence:** MEDIUM  
**Rationale:** One comparison suggests flag/condition check.

---

### sub_407B0 (14B) - **13 CALLERS**
**Pattern:** No comparisons, no calls, tiny (14B)  
**Callers:** Used across AI and other systems  
**Proposed Name:** `ai_record_field_read` or `ai_offset_get`  
**Confidence:** MEDIUM  
**Rationale:** Very small accessor, likely reads a specific field.

---

### sub_3E1C2 (52B) - **7 CALLERS**
**Pattern:** 6 comparisons, no calls, array iteration (SI/DI)  
**Callers:** farobj_index_resolve_step, ai_state_processor_core, ai_state_calculate_helper, etc.  
**Proposed Name:** `ai_state_range_check` or `ai_value_validate`  
**Confidence:** HIGH  
**Rationale:** 6 comparisons = range checking or validation logic.

---

### sub_3F603 (35B) - **5 CALLERS**
**Pattern:** 2 comparisons, no calls, array iteration  
**Callers:** farobj_index_decrement_step, ai_state_processor_core, ai_entity_update_step  
**Proposed Name:** `ai_index_bounds_check` or `ai_array_validate`  
**Confidence:** MEDIUM  
**Rationale:** Called by index functions with 2 comparisons = bounds checking.

---

## High Confidence - Function Call Patterns

### sub_3F6D6 (42B) ✓ **HIGH CONFIDENCE**
**Calls:** `angle_xy_far`, `angle_aux_far` (both angle functions!)  
**Callers:** 11 functions including ai_state_processor_core, ai_entity_update_step  
**Proposed Name:** `ai_angle_calculate`  
**Confidence:** **VERY HIGH**  
**Rationale:** Clearly calculates angles by calling two angle helper functions.

---

### sub_40E38 (14B) ✓ **HIGH CONFIDENCE**  
**Calls:** `fixed_vec3_accumulate_a` (3D vector accumulation!)  
**Callers:** 39 functions (EXTREMELY widely used!)  
**Proposed Name:** `ai_vector_accumulate`  
**Confidence:** **VERY HIGH**  
**Rationale:** Wrapper for 3D vector accumulation, used everywhere.

---

### sub_40E46 (14B) ✓ **HIGH CONFIDENCE**
**Calls:** `fixed_vec3_accumulate_a` (same as 40E38!)  
**Callers:** 12 functions including ai_state_processor_core, ai_state_calculate_helper  
**Proposed Name:** `ai_vector_accumulate_alt` or `ai_position_accumulate`  
**Confidence:** **VERY HIGH**  
**Rationale:** Parallel to 40E38, likely accumulates different vector (position vs velocity?).

---

### sub_3E8C5 (13B) - **MEDIUM CONFIDENCE**
**Calls:** `farobj_flag_gate_check` (flag checking!)  
**Callers:** 4 functions  
**Proposed Name:** `ai_farobj_flag_check`  
**Confidence:** MEDIUM  
**Rationale:** Wrapper for farobj flag gate check, tiny helper.

---

## Medium Priority - Dispatchers and State Machines

### sub_3DED9 (69B)
**Calls:** `sub_40CB7`  
**Callers:** farobj_index_resolve_step, ai_state_processor_core, ai_entity_update_step  
**Pattern:** 6 comparisons, array iteration  
**Proposed Name:** `ai_state_dispatch_helper`  
**Confidence:** LOW  
**Rationale:** Multiple comparisons suggest dispatch logic.

---

## Summary Table

| Address | Current Name | Proposed Name | Callers | Size | Confidence |
|---------|--------------|---------------|---------|------|------------|
| 0x428A1 | sub_428A1 | `ai_state_value_get` | 21 | 32B | HIGH |
| 0x40DB5 | sub_40DB5 | `ai_field_offset_calc` | 17 | 16B | MEDIUM |
| 0x428C1 | sub_428C1 | `ai_field_check_flag` | 17 | 19B | MEDIUM |
| 0x407B0 | sub_407B0 | `ai_record_field_read` | 13 | 14B | MEDIUM |
| 0x3F6D6 | sub_3F6D6 | `ai_angle_calculate` | 11 | 42B | **VERY HIGH** |
| 0x40E38 | sub_40E38 | `ai_vector_accumulate` | 39 | 14B | **VERY HIGH** |
| 0x40E46 | sub_40E46 | `ai_vector_accumulate_alt` | 12 | 14B | **VERY HIGH** |
| 0x3E1C2 | sub_3E1C2 | `ai_state_range_check` | 7 | 52B | HIGH |
| 0x3F603 | sub_3F603 | `ai_index_bounds_check` | 5 | 35B | MEDIUM |
| 0x3E8C5 | sub_3E8C5 | `ai_farobj_flag_check` | 4 | 13B | MEDIUM |

## Recommendations

**Immediate Action - Add These 10 Functions:**

The 10 functions above are well-understood and ready to add to registry:
- 3 VERY HIGH confidence (clear call patterns)
- 2 HIGH confidence (leaf functions with clear patterns)
- 5 MEDIUM confidence (widely used, clear categories)

**Next Steps:**

Remaining 9 functions have low confidence and need deeper analysis:
- Most are called "ai_helper_*" with generic names
- Need to trace their data accesses
- May need to examine calling context in more detail

**Total Progress:**
- Started with 83 new AI functions
- Already named 10 (previous session)
- Recommending 10 more (this session)
- **20/83 = 24% coverage** so far
- With 1,912 total functions in registry (1,902 + 10 more)

## Key Insights

1. **Leaf functions are fundamental** - The most widely used functions have no callees
2. **Call patterns reveal purpose** - Functions calling angle/vector functions are obvious
3. **Caller count indicates importance** - 21 callers = core utility
4. **Size correlates with complexity** - <20 bytes = simple accessors, 30-50 bytes = calculations
5. **Comparison count = branching** - More comparisons = validation/dispatch logic

This batch analysis technique is working well for helper functions!
