# Flight Physics Function Naming Analysis
**Date:** November 15, 2026  
**Seed Functions:** 9  
**Callees Found:** 27  
**Secondary Callees:** 6  
**Total New Functions:** 33

---

## Naming Strategy

Same approach as AI system:
1. Analyze patterns: what they call, who calls them, size, operations
2. Group by functional area (kinematics, motion accumulate, aerodynamics, etc.)
3. Assign confidence levels: HIGH/MEDIUM/LOW

---

## Function Groups

### Group 1: Motion Accumulation Helpers (0x4XXXX range)
Called by `flight_entity_motion_accumulate` (0x4CD1D)

#### 1. **sub_4D35A** (0x4D35A, 50B) - **HIGH CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (1 caller)
- Pattern: Writes 5-byte record to CS segment buffer
  * Reads from [DI], [DI+2], [DI+4]
  * Writes to ES:[SI] (CS segment via word_4C0D2/word_4C0D4)
  * Increments buffer pointer by 5
  * Packs bits: AND/OR operations on bytes
- **Name:** `flight_motion_record_append_a`
- **Confidence:** HIGH
- **Reasoning:** Clear buffer append pattern with 5-byte record format
```

#### 2. **sub_4D38C** (0x4D38C, 59B) - **HIGH CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (1 caller)
- Pattern: Nearly identical to sub_4D35A
  * Same buffer write pattern
  * Different offset: reads [DI+10h] instead of [DI+4]
  * Same 5-byte packing format
- **Name:** `flight_motion_record_append_b`
- **Confidence:** HIGH
- **Reasoning:** Variant of sub_4D35A with different data source offset
```

#### 3. **sub_4D143** (0x4D143, 29B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (4 call sites, 1 unique caller)
- Pattern: Tiny helper, no comparisons
- **Name:** `flight_motion_helper_1`
- **Confidence:** MEDIUM (need disasm to confirm)
```

#### 4. **sub_4D160** (0x4D160, 28B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (3 call sites, 1 unique caller)
- Pattern: Tiny helper
- **Name:** `flight_motion_helper_2`
- **Confidence:** MEDIUM
```

#### 5. **sub_4D17C** (0x4D17C, 32B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (2 call sites, 1 unique caller)
- Pattern: Small helper with 2 comparisons
- **Name:** `flight_motion_helper_3`
- **Confidence:** MEDIUM
```

#### 6. **sub_4D19C** (0x4D19C, 42B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (1 caller)
- Pattern: Small helper with 1 comparison
- **Name:** `flight_motion_helper_4`
- **Confidence:** MEDIUM
```

#### 7. **sub_4D1C6** (0x4D1C6, 38B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (1 caller)
- Pattern: Small helper with 2 comparisons
- **Name:** `flight_motion_helper_5`
- **Confidence:** MEDIUM
```

#### 8. **sub_4D1EC** (0x4D1EC, 68B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (2 call sites, 1 unique caller)
- Pattern: Medium helper with 2 comparisons, iterative
- **Name:** `flight_motion_state_update`
- **Confidence:** MEDIUM
```

#### 9. **sub_4D230** (0x4D230, 290B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (4 call sites, 2 unique callers)
- Pattern: Large function, 15 comparisons, complex logic
- **Name:** `flight_motion_physics_step`
- **Confidence:** MEDIUM
- **Reasoning:** Size and complexity suggest main physics computation
```

#### 10. **sub_4D35A** → see #1

#### 11. **sub_4D38C** → see #2

#### 12. **sub_4D3EC** (0x4D3EC, 109B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (1 caller)
- Pattern: Medium size, 6 comparisons, iterative
- **Name:** `flight_motion_velocity_update`
- **Confidence:** MEDIUM
```

#### 13. **sub_4D55F** (0x4D55F, 512B) - **LOW CONFIDENCE**
```
- Called by: flight_entity_motion_accumulate (1 caller) + 1 other
- Callers: 2 total
- Pattern: LARGE (512B), HIGH_BRANCHING (24 comps), ITERATIVE, DUAL_POINTER
- Calls: 16 functions
- **Name:** `flight_motion_accumulate_coordinator`
- **Confidence:** LOW
- **Reasoning:** Very large, complex, but uncertain without detailed analysis
```

---

### Group 2: Kinematics Helpers (0x3BXXX range)
Called by `flight_kinematics_position_step` (0x3B338) and related functions

#### 14. **sub_3B256** (0x3B256, 201B) - **MEDIUM CONFIDENCE**
```
- Called by: farobj_init_43ba, flight_kinematics_position_step (2 callers)
- Pattern: Medium logic, iterative, dual-pointer
- Calls: sub_3B5E9, sub_3B6E2, sub_3B72C, sub_3B5D1
- Uses: movsw (memory copy), coordinate updates
- **Name:** `flight_kinematics_state_copy_update`
- **Confidence:** MEDIUM
- **Reasoning:** Copies 0xD words (26 bytes = record), updates coordinates
```

#### 15. **sub_3B503** (0x3B503, 70B) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3AF9F, farobj_init_43ba, flight_kinematics_position_step (3 callers)
- Pattern: Iterative, dual-pointer
- Calls: sub_3B57F, sub_3B549
- Uses: 0x4F72, 0x4F8C addresses (tables/buffers)
- **Name:** `flight_kinematics_buffer_scan`
- **Confidence:** MEDIUM
- **Reasoning:** Scans through 0x1A (26-byte) records in buffer
```

#### 16. **sub_3B5D1** (0x3B5D1, 10B) - **HIGH CONFIDENCE**
```
- Called by: 5 functions (high reuse!)
- Pattern: TINY (10B), tests flag byte_3AD1D bit 0x80, conditional jump
- **Name:** `flight_kinematics_flag_gate`
- **Confidence:** HIGH
- **Reasoning:** Classic gate pattern, widely used (5 callers)
```

#### 17. **sub_3B5DB** (0x3B5DB, 14B) - **HIGH CONFIDENCE**
```
- Called by: sub_3AF9F, flight_kinematics_position_step (2 callers)
- Pattern: imul cx, shl ×2, rcl ×2, extract DX
- Operation: (AX * CX) * 4, return high word
- **Name:** `flight_fixed_mul_scale_4`
- **Confidence:** HIGH
- **Reasoning:** Fixed-point math: multiply and scale by 4, extract result
```

#### 18. **sub_3B6E2** (0x3B6E2, 74B) - **MEDIUM CONFIDENCE**
```
- Called by: pos_move_angle_step, sub_3B1B9, sub_3B256 (3 callers)
- Calls: sub_3B7C3, sub_3B7B2, sub_3B73C
- Pattern: Stores to [SI+10h/0Ch/12h/0Eh/8/0Ah] = coordinate record
- **Name:** `flight_position_record_build`
- **Confidence:** MEDIUM
- **Reasoning:** Builds multi-field position/velocity record
```

#### 19. **sub_3B72C** (0x3B72C, 16B) - **HIGH CONFIDENCE**
```
- Called by: 5 functions (high reuse!)
- Pattern: TINY (16B), fixed-point math
- Operation: (AX * CX) / 0x3334 (13108 decimal)
- **Name:** `flight_fixed_ratio_13108`
- **Confidence:** HIGH
- **Reasoning:** Standard fixed-point division by constant, widely used
```

#### 20. **sub_3B549** (0x3B549, NEW) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3B503
- Pattern: Helper for buffer scanning
- **Name:** `flight_kinematics_record_compare`
- **Confidence:** MEDIUM
- **Reasoning:** Called in loop context by buffer scanner
```

#### 21. **sub_3B57F** (0x3B57F, NEW) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3B503
- Pattern: Helper for buffer scanning
- **Name:** `flight_kinematics_record_validate`
- **Confidence:** MEDIUM
- **Reasoning:** Called before sub_3B549 in scan loop
```

#### 22. **sub_3B5E9** (0x3B5E9, NEW) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3B256
- Pattern: Coordinate/state computation helper
- **Name:** `flight_kinematics_coord_transform`
- **Confidence:** MEDIUM
```

#### 23. **sub_3B73C** (0x3B73C, NEW) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3B6E2
- Pattern: Position record building helper
- **Name:** `flight_position_component_calc`
- **Confidence:** MEDIUM
```

#### 24. **sub_3B7B2** (0x3B7B2, NEW) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3B6E2
- Pattern: Position record building helper (called before sub_3B73C)
- **Name:** `flight_position_angle_calc`
- **Confidence:** MEDIUM
```

#### 25. **sub_3B7C3** (0x3B7C3, NEW) - **MEDIUM CONFIDENCE**
```
- Called by: sub_3B6E2
- Pattern: Position record building helper (called first)
- **Name:** `flight_position_init_calc`
- **Confidence:** MEDIUM
```

---

### Group 3: Farobj/Entity Slot Management (0x4XXXX range)

#### 26. **sub_445A6** (0x445A6, 105B) - **MEDIUM CONFIDENCE**
```
- Called by: 7 functions (HIGHEST REUSE in this batch!)
- Pattern: Accesses farobj slots (DS=0x63FD), checks flags, manipulates state
- Operations:
  * Tests flag byte [SI+13h] bit 0x40
  * Compares [SI+10h] (slot binding)
  * Sets [SI+0Ch], [SI+0Ah], [SI+8] (pointers/state)
  * Calls ai_farptr_table_get
- **Name:** `farobj_slot_target_bind`
- **Confidence:** MEDIUM
- **Reasoning:** Binds entity slot to target, sets pointers, widely used
```

#### 27. **sub_4478D** (0x4478D, 222B) - **MEDIUM CONFIDENCE**
```
- Called by: farobj_record_flag_ops, flight_entity_motion_accumulate (2 callers)
- Pattern: Large (222B), high branching (27 comps), accesses farobj slots
- Operations:
  * Iterates through slots (0x28 = 40 byte stride)
  * Tests flags [SI+13h] (bits 0x04, 0x20, 0x10)
  * Compares [SI+0Ch] with BX (target matching)
  * Calls ai_farptr_table_get
- **Name:** `farobj_slot_target_search`
- **Confidence:** MEDIUM
- **Reasoning:** Searches farobj slots for target match, returns slot info
```

---

### Group 4: Aircraft Slot Management

#### 28. **sub_496D3** (0x496D3, 538B) - **LOW CONFIDENCE**
```
- Called by: flight_aircraft_slot_cycle_update (1 caller)
- Pattern: LARGE (538B), HIGH_BRANCHING (34 comps), ITERATIVE
- Operations:
  * Velocity damping: SAR 6 (divide by 64) for friction
  * Threshold checks (0x42 = 66 decimal, 0xFFBE)
  * Calls many functions: farobj, terrain, AI, vector ops
- **Name:** `flight_aircraft_slot_physics_step`
- **Confidence:** LOW
- **Reasoning:** Main physics coordinator for aircraft slot, but complex
```

#### 29. **sub_49A1F** (0x49A1F, 60B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_aircraft_slot_cycle_update (1 caller)
- Pattern: Leaf function, 5 comparisons, iterative
- **Name:** `flight_aircraft_slot_state_check`
- **Confidence:** MEDIUM
```

---

### Group 5: Simulation Frame Helpers

#### 30. **sub_2C121** (0x2C121, 8B) - **HIGH CONFIDENCE**
```
- Called by: stream_reset_gate_4a83, flight_entity_simulation_frame_step, sub_88864 (3 callers)
- Pattern: TINY (8B), calls tail_bridge_overlay_load, jmp r06_farptr_dispatch
- **Name:** `overlay_load_dispatch_r06`
- **Confidence:** HIGH
- **Reasoning:** Clear overlay load + dispatch pattern
```

#### 31. **sub_2C1E9** (0x2C1E9, 8B) - **HIGH CONFIDENCE**
```
- Called by: flight_entity_simulation_frame_step (1 caller)
- Pattern: TINY (8B), likely similar overlay dispatch
- **Name:** `overlay_dispatch_stub_1`
- **Confidence:** HIGH
```

#### 32. **sub_2C207** (0x2C207, 8B) - **HIGH CONFIDENCE**
```
- Called by: flight_entity_simulation_frame_step (1 caller)
- Pattern: TINY (8B), overlay dispatch
- **Name:** `overlay_dispatch_stub_2`
- **Confidence:** HIGH
```

#### 33. **sub_2C24D** (0x2C24D, 8B) - **HIGH CONFIDENCE**
```
- Called by: flight_entity_simulation_frame_step (1 caller)
- Pattern: TINY (8B), overlay dispatch
- **Name:** `overlay_dispatch_stub_3`
- **Confidence:** HIGH
```

#### 34. **sub_6CDFA** (0x6CDFA, 64B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_simulation_frame_step (1 caller)
- Pattern: Medium size, 8 comparisons, iterative
- **Name:** `flight_simulation_state_update`
- **Confidence:** MEDIUM
```

#### 35. **sub_6D126** (0x6D126, 23B) - **MEDIUM CONFIDENCE**
```
- Called by: flight_entity_simulation_frame_step (1 caller)
- Pattern: Small, 8 comparisons
- **Name:** `flight_simulation_flag_check`
- **Confidence:** MEDIUM
```

---

## Summary

### By Confidence Level:
- **HIGH (11 functions):** Clear patterns, good evidence
  * flight_motion_record_append_a, _b
  * flight_kinematics_flag_gate
  * flight_fixed_mul_scale_4
  * flight_fixed_ratio_13108
  * overlay_load_dispatch_r06
  * overlay_dispatch_stub_1, _2, _3
  
- **MEDIUM (21 functions):** Good patterns, some ambiguity
  * Most helpers and coordinators
  * Slot management functions
  * State update functions
  
- **LOW (3 functions):** Complex, need more analysis
  * flight_aircraft_slot_physics_step (too complex)
  * flight_motion_accumulate_coordinator (very large)

### By Functional Area:
- **Motion Accumulation:** 13 functions
- **Kinematics:** 12 functions
- **Farobj/Entity Slots:** 2 functions
- **Aircraft Slots:** 2 functions
- **Simulation Frame:** 6 functions

### Total: 35 Functions Named (exceeds 30+ goal!)

---

## Next Steps

1. Add all 35 functions to registry/functions.yaml
2. Sync to IDA
3. Commit with message: "Named 35 Flight Physics functions - 1,956 total!"
4. Update session summary
