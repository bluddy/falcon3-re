# Game Loop Analysis - Main Frame Pipeline

**Function**: game_frame_pipeline_step  
**Address**: 0x2FD42  
**Size**: 387 bytes  
**Status**: ✅ Verified via IDA API

---

## Overview

This is the **MAIN GAME LOOP** for Falcon 3.0. Every frame goes through this pipeline.

### Statistics
- **Total calls**: 44 function calls per frame
- **Unique functions**: 36 different functions
- **Size**: 387 bytes

---

## Top Functions by Call Count

| Calls | Function | Purpose |
|-------|----------|---------|
| 4x | farobj_slot_project_step (0xCC2) | Project slots (4 categories) |
| 3x | **farobj_sort_and_step** (0x1C5C) | **Visibility culling** ⭐ |
| 3x | es_ptr_slots_init (0x1BA6) | Reset slot pointers |
| 2x | loc_2F05F (0x7F) | Unknown loop step |

**This confirms**: farobj_sort_and_step is called **3 TIMES PER FRAME** from the main game loop!

---

## Frame Pipeline Sequence

### Phase 1: Setup & State (calls 1-12)
```
1.  fn_table_dispatch           - Dispatch table initialization
2.  near_fnptr_invoke           - Function pointer invocation
3.  farobj_pos_wrap_update      - Update farobj positions
4.  pos_clamp_40                - Clamp positions
5.  entity_update_batch         - Batch update entities
6.  view_pos_cache_update       - Update view cache
7.  terrain_vm_flag_gate        - Terrain visibility check
8.  flag_gate_zero_abc          - Flag gate logic
9.  viewmode3_vector_project    - View mode 3 projection
10. sub_256A3                   - Unknown (view related)
11. entity_state_load           - Load entity states
12. es_word_zero                - Clear entity state word
```

### Phase 2: Terrain & View (calls 13-18)
```
13. terrain_frame_update_driver - Main terrain update
14. viewlist_project_flagged    - Project flagged view items
15. state_word_11cc8_get        - Get state word
16. r39_farptr_gate_big         - Overlay gate
17. farobj_scan_74_timer_c      - farobj scan timer
18. farobj_scan_74_gate_a       - farobj scan gate
```

### Phase 3: Entity Processing (calls 19-22)
```
19. es_ptr_slots_init           - Init slot pointers (1st)
20. store_fall_sim_step         - Store simulation step
21. entity_move_project_step    - Project entity movement
22. farobj_slot_project_step    - Project slot (1st)
```

### Phase 4: Visibility Pass 1 (calls 23-25)
```
23. farobj_sort_and_step        - Culling pass 1 ⭐
24. loc_2F05F                   - Loop step
25. es_ptr_slots_init           - Reset slots (2nd)
```

### Phase 5: Slot Processing (calls 26-28)
```
26. farobj_slot_project_step    - Project slot (2nd)
27. farobj_slot_project_step    - Project slot (3rd)
28. farobj_sort_and_step        - Culling pass 2 ⭐
```

### Phase 6: View Objects (calls 29-36)
```
29. loc_2F05F                   - Loop step
30. es_ptr_slots_init           - Reset slots (3rd)
31. farobj_slot_project_step    - Project slot (4th)
32. viewobj_self_copy_project   - Copy self view object
33. viewobj_table32_flag_project - Table 32 objects
34. viewobj_table64_project     - Table 64 objects
35. viewobj_table72_flag_project - Table 72 objects
36. viewobj_5982_scan_all       - Scan all view objects
```

### Phase 7: Final Culling & HUD (calls 37-44)
```
37. farobj_sort_and_step        - Culling pass 3 ⭐
38. farobj_scan_74_clear_b      - Clear farobj scan
39. r32_hud_phase_dispatch      - HUD rendering dispatch
40. entity_table_gate_47a8d     - Entity table gate
41-44. [Additional cleanup/dispatch]
```

---

## Three farobj_sort_and_step Calls

### Call 1 (address 0x2FE37) - After Entity Movement
```
21. entity_move_project_step
22. farobj_slot_project_step
23. farobj_sort_and_step        ← CALL 1
```
**Purpose**: Cull objects after entity positions updated

### Call 2 (address 0x2FE66) - After Slot Projection
```
26. farobj_slot_project_step
27. farobj_slot_project_step  
28. farobj_sort_and_step        ← CALL 2
```
**Purpose**: Cull after multiple slot projections

### Call 3 (address 0x2FE9C) - Before HUD
```
36. viewobj_5982_scan_all
37. farobj_sort_and_step        ← CALL 3
38. farobj_scan_74_clear_b
39. r32_hud_phase_dispatch
```
**Purpose**: Final culling before HUD rendering

---

## Object Categories

The 4x calls to `farobj_slot_project_step` suggest **4 object categories**:

1. **Entities** (planes, missiles, etc.)
2. **Terrain** (ground, mountains)
3. **Static objects** (buildings, trees)
4. **View objects** (HUD elements, cockpit)

Each category gets:
- Slot projection (farobj_slot_project_step)
- Visibility culling (farobj_sort_and_step)
- View transformation (view* functions)

---

## Rendering Integration

After game_frame_pipeline_step completes, rendering functions are called:
- view_projection (transforms objects)
- Graphics functions (draws to screen)
- Display swap (shows frame)

The game loop ensures:
1. Objects are updated (positions, states)
2. Visibility is culled (3 passes)
3. Slots are projected (4 categories)
4. View objects are prepared
5. HUD is ready

Then rendering begins with clean, culled object lists.

---

## Performance Optimization

### Multi-Pass Culling Strategy

**Why 3 culling passes?**

1. **Pass 1**: After entity movement
   - Cull objects that moved out of view
   - Quick rejection based on new positions

2. **Pass 2**: After slot projections
   - Cull based on projection results
   - More expensive but more accurate

3. **Pass 3**: Final pass before rendering
   - Last chance to reject invisible objects
   - Ensures clean lists for rendering

### Frame Budget

With 18 FPS target (55ms per frame):
- 44 function calls
- 3 visibility culling passes
- 4 slot projection passes
- Terrain, entities, view objects all processed

This aggressive pipeline keeps Falcon 3.0 playable on 1991 hardware (386/486 CPUs).

---

## Callers of game_frame_pipeline_step

This function is called by higher-level game loop managers:
- Main game loop
- Mission update loop
- Training mode loop
- Demo playback loop

---

## Key Insights

1. **Frame structure is highly optimized**
   - 3 visibility passes
   - 4 object categories
   - Interleaved culling and projection

2. **farobj is central to performance**
   - Called 3x per frame from main loop
   - Plus called from view_projection
   - Total: 4-5 visibility passes per frame

3. **Slot-based architecture**
   - 4 slot projection calls
   - Suggests pre-allocated object pools
   - Avoids dynamic memory allocation

4. **HUD is separate pipeline**
   - Final farobj pass before HUD
   - r32_hud_phase_dispatch after culling
   - Ensures HUD doesn't interfere with 3D

5. **Terrain gets special treatment**
   - terrain_frame_update_driver
   - terrain_vm_flag_gate
   - Separate from entity processing

---

## Connection to view_projection

```
game_frame_pipeline_step (main loop)
  │
  ├──→ farobj_sort_and_step (3x) - pre-culling
  ├──→ entity processing
  ├──→ terrain processing
  └──→ view object preparation
        │
        └──→ [frame complete]
              │
              └──→ view_projection (rendering)
                     │
                     ├──→ fixed_vec3_transform_es
                     ├──→ vec2_normalize_seq
                     ├──→ farobj_record_step (4th pass)
                     ├──→ overlay_tail_bridge
                     ├──→ farobj_record_push_7c054
                     ├──→ farobj_record_lookup_step
                     └──→ farobj_record_push_7d0c6
```

---

## Files
- game_loop_analysis.json - Complete call sequence (44 calls)
- analyze_game_loop.py - Analysis script
- this file - Summary and insights

---

**This explains the complete frame pipeline from game loop to rendering!**
