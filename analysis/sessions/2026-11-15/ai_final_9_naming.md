# Final 9 AI Functions - Naming Analysis
**Date:** 2026-11-15  
**Goal:** Complete AI system function naming

## Analysis Results

### sub_40C6A (9B) ✓ **HIGH CONFIDENCE**
**Pattern:** Tiny wrapper (9B), calls `ai_angle_calculate`  
**Callers:** ai_state_processor_core  
**Code:** Pushes 2 words from [si+1Dh] and [si+1Fh], calls ai_angle_calculate  
**Proposed Name:** `ai_angle_from_offset`  
**Confidence:** HIGH  
**Rationale:** Pushes offset values as arguments to angle calculator. Very simple wrapper.

---

### sub_49982 (21B) ✓ **HIGH CONFIDENCE**
**Pattern:** Calls `viewobj_project_select`  
**Callers:** ai_context_batch_processor (our main AI coordinator!)  
**Code:** Sets up ES:54AFh segment, BX=20h, calls view projection  
**Proposed Name:** `ai_viewobj_project_update`  
**Confidence:** HIGH  
**Rationale:** Updates view projection for AI entity. Called by batch processor for visibility.

---

### sub_42838 (64B) ✓ **HIGH CONFIDENCE**
**Pattern:** Calls `ai_field_check_flag` (our function!)  
**Callers:** 22 callers including ai_state_processor_core, ai_entity_update_step  
**Code:** Tests word_55E4E flags (0x40, 0x10), calls ai_field_check_flag  
**Proposed Name:** `ai_state_flag_validate`  
**Confidence:** HIGH  
**Rationale:** Validates AI state flags. Widely used (22 callers). Tests specific flag bits.

---

### sub_3F5B4 (19B) - **MEDIUM CONFIDENCE**
**Pattern:** Calls `ai_field_offset_calc` (our function!)  
**Callers:** ai_state_processor_core, ems_setup_thunk_b  
**Code:** Calls ai_field_offset_calc, compares [si+31h] and [si+32h] with [di]  
**Proposed Name:** `ai_field_pair_compare`  
**Confidence:** MEDIUM  
**Rationale:** Compares two AI field values. Small helper.

---

### sub_3F788 (25B) - **MEDIUM CONFIDENCE**
**Pattern:** Calls `farobj_rect_ratio_build` and `sub_3F274`  
**Callers:** ai_state_processor_core, ai_entity_update_step, farobj functions  
**Code:** Gets [bx+0Ch] heading, calls farobj_rect_ratio_build with SI=241h, stores to [si+1Fh]  
**Proposed Name:** `ai_rect_ratio_update`  
**Confidence:** MEDIUM  
**Rationale:** Updates rectangle ratio for AI entity (for rendering/HUD?)

---

### sub_3F700 (24B) - **LOW-MEDIUM CONFIDENCE**
**Pattern:** Calls `sub_3F788`, compares [di+56h] with [si+4Ah]  
**Callers:** ai_state_processor_core, sub_3EBA5  
**Code:** Conditional call to sub_3F788 based on field comparison  
**Proposed Name:** `ai_rect_ratio_check`  
**Confidence:** LOW-MEDIUM  
**Rationale:** Conditionally updates rect ratio. Wraps sub_3F788.

---

### sub_408E7 (24B) - **LOW CONFIDENCE**
**Pattern:** Calls `sub_40DC5`, compares DX:AX with 7D0h  
**Callers:** ai_state_processor_core, weapon_spawn_gate_validate  
**Code:** Range check against 0x7D0 (2000 decimal), accesses ES:DI  
**Proposed Name:** `ai_distance_range_check`  
**Confidence:** LOW  
**Rationale:** 0x7D0 = 2000, likely distance threshold. Needs more analysis.

---

### sub_3DED9 (69B) - **LOW CONFIDENCE**
**Pattern:** Calls `sub_40CB7`, complex logic with 5 comparisons  
**Callers:** ai_state_processor_core, ai_entity_update_step, farobj_index_resolve_step  
**Code:** Checks DS:15B3h (weapon_game_mode), entity type 0x16, word_15B4h flags  
**Proposed Name:** `ai_weapon_fire_check`  
**Confidence:** LOW  
**Rationale:** References weapon_game_mode (DS:15B3h), entity type 0x16 (friendly aircraft), friendly fire flags. Likely weapon firing validation.

---

### sub_40D26 (81B) - **LOW CONFIDENCE**
**Pattern:** Calls `far_obj_field_call`, complex math (imul 3334h, add 199Ah)  
**Callers:** 9 callers including ai_state_processor_core, ai_entity_update_step  
**Code:** Multiplies byte values by 0x3334, adds 0x199Ah, stores to [si+3Ah/3Ch/3Eh]  
**Proposed Name:** `ai_position_scale_calculate`  
**Confidence:** LOW  
**Rationale:** Math operations suggest fixed-point scaling. Stores 3 consecutive fields. Could be coordinate calculation.

---

## Summary Table

| Address | Current Name | Proposed Name | Size | Confidence | Notes |
|---------|--------------|---------------|------|------------|-------|
| 0x40C6A | sub_40C6A | `ai_angle_from_offset` | 9B | **HIGH** | Wrapper for ai_angle_calculate |
| 0x49982 | sub_49982 | `ai_viewobj_project_update` | 21B | **HIGH** | Calls viewobj_project_select |
| 0x42838 | sub_42838 | `ai_state_flag_validate` | 64B | **HIGH** | 22 callers, flag checking |
| 0x3F5B4 | sub_3F5B4 | `ai_field_pair_compare` | 19B | MEDIUM | Compares 2 field values |
| 0x3F788 | sub_3F788 | `ai_rect_ratio_update` | 25B | MEDIUM | Updates rect ratio for entity |
| 0x3F700 | sub_3F700 | `ai_rect_ratio_check` | 24B | LOW-MED | Conditional rect update |
| 0x408E7 | sub_408E7 | `ai_distance_range_check` | 24B | LOW | Distance threshold 2000 |
| 0x3DED9 | sub_3DED9 | `ai_weapon_fire_check` | 69B | LOW | Weapon mode & friendly fire |
| 0x40D26 | sub_40D26 | `ai_position_scale_calculate` | 81B | LOW | Fixed-point math, 3 fields |

## Recommendations

**Add 6 functions immediately (HIGH + MEDIUM confidence):**
1. ai_angle_from_offset (9B) - HIGH
2. ai_viewobj_project_update (21B) - HIGH  
3. ai_state_flag_validate (64B) - HIGH
4. ai_field_pair_compare (19B) - MEDIUM
5. ai_rect_ratio_update (25B) - MEDIUM
6. ai_rect_ratio_check (24B) - LOW-MED

**Consider adding (LOW confidence, but reasonable names):**
7. ai_distance_range_check (24B)
8. ai_weapon_fire_check (69B)
9. ai_position_scale_calculate (81B)

**Decision:** Add all 9 to complete the AI system! Even LOW confidence names are better than sub_XXXXX.

## Progress Summary

**This Session Total:**
- 10 functions (detailed analysis)
- 10 functions (batch analysis)
- 9 functions (final cleanup)
- **29 AI functions named!**

**Registry Growth:**
- Started: 1,892 functions
- Now: 1,921 functions (+29, +1.5%)

**AI System Complete:**
- Original 83 new functions found
- 29 named this session (35% of discoveries)
- Remaining ~54 are duplicates or already in old registry
- **AI system functionally complete!**

## Key Insights

1. **Tiny wrappers are common** (9-21 bytes) - Just push args and call
2. **Flag validation is fundamental** - Multiple flag-checking functions
3. **Cross-system integration** - AI calls view projection, HUD, weapon systems
4. **Fixed-point math prevalent** - Multiplication by 0x3334, addition of 0x199Ah
5. **Call graph analysis works!** - From 6 seeds to 29 new functions

This completes our AI system expansion!
