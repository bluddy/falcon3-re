# Top 500 Batch 2 Analysis

## Overview
Analyzing 27 functions from top500_batch2_analysis.json (ranks 429-500)

## Function Categorizations

### 1. sub_1854CF (0x1854cf, 134B, rank 429)
**Pattern:** Menu UI dispatcher with jump table
**System:** Menu/UI
**Evidence:**
- Jump table switch on argument (10 cases)
- Calls `ui_element_render_variant_a`, `ui_element_render_variant_b`
- Memory checks at segment 7894h (menu state)
- String references: "q3.`RERUN", "NEXT MISSION", "SQUADRON RECORDS"
- Called 7 times from `game_mode_r53_main_coordinator`

**Proposed Name:** `menu_r53_button_dispatcher`
**Description:** Dispatches menu button rendering for R53 game mode based on button index (0-9)
**Confidence:** High (95%)

---

### 2. sub_1A6AA6 (0x1a6aa6, 850B, rank 430)
**Pattern:** Complex menu state handler with multiple paths
**System:** Menu/UI
**Evidence:**
- Jump table switch (7 cases)
- Heavy use of `int_to_string_converter`, `string_concatenate`
- Strings: "OF", "FLIGHT #", "FA-18"
- Renders flight selection UI with formatted text
- Called 7 times from `r57_menu_state_machine`
- Checks `word_79EEC`, `word_79B62` (menu state variables)

**Proposed Name:** `menu_r57_flight_display_handler`
**Description:** Handles flight selection menu display with flight number formatting and aircraft type
**Confidence:** High (90%)

---

### 3. sub_1A86C6 (0x1a86c6, 572B, rank 431)
**Pattern:** Menu display handler (similar to sub_1A6AA6)
**System:** Menu/UI
**Evidence:**
- Nearly identical structure to sub_1A6AA6
- Same string patterns: "OF", "FLIGHT #", "F-16"
- Called 7 times from `r57_loadout_display_handler`
- Checks `word_79EA4` instead of `word_79EEC`

**Proposed Name:** `menu_r57_loadout_flight_display`
**Description:** Displays flight information in loadout selection screen
**Confidence:** High (90%)

---

### 4. sub_2978E (0x2978e, 393B, rank 465)
**Pattern:** 3D geometry processor
**System:** 3D rendering
**Evidence:**
- Calls `fixed_vec3_cross`, `vec3_dot`, `fixed_vec3_magnitude_gate`
- Calls `record_span_mask_rebuild`, `line_table_build_dispatch`
- Vector math operations with fixed-point arithmetic
- Checks `state_byte_1f73a`, `state_byte_1f72f` (rendering flags)
- Called from `object_proj_draw_dispatch`, `line_record_flag_dispatch`

**Proposed Name:** `render_3d_polygon_visibility_test`
**Description:** Tests polygon visibility using cross products and builds span records for rendering
**Confidence:** High (85%)

---

### 5. sub_3E01A (0x3e01a, 20B, rank 469)
**Pattern:** Bit field manipulator
**System:** State management
**Evidence:**
- Manipulates bits in `ds:15B4h` (adds 0x1000, 0x4000)
- Multiple bit masks: 0x3000, 0xC000
- Very small function (20 bytes)
- Called from multiple subsystems

**Proposed Name:** `state_flags_increment_field`
**Description:** Increments specific bit fields in state flags register
**Confidence:** Medium (75%)

---

### 6. undoc_3F287 (0x3f287, 289B, rank 470)
**Pattern:** AI waypoint/behavior processor
**System:** AI
**Evidence:**
- Checks `ai_heading_correction_calc` flag
- Manipulates entity offsets (+0Eh, +0Fh, +1Dh, +1Fh, +21h)
- Calls `ai_state_calculate_helper`, `stub_to_24988`
- Jump table for waypoint types (cases 1-4)
- Called from `farobj_view_project_step`, `hud_digit_extract`

**Proposed Name:** `ai_waypoint_behavior_execute`
**Description:** Executes AI waypoint behavior, updating heading, pitch, and altitude targets
**Confidence:** High (85%)

---

### 7. undoc_43842 (0x43842, 101B, rank 475)
**Pattern:** HUD text renderer
**System:** HUD/UI
**Evidence:**
- Calls `int32_to_ascii_short`, `op_dispatch` (multiple times)
- String formatting at offset 0x2615h
- Sets byte values: 'R', 'E', '.'
- Increments `word_43509` (counter)
- Writes to display buffer 0xD829h

**Proposed Name:** `hud_text_render_formatted`
**Description:** Renders formatted text to HUD display buffer with coordinate tracking
**Confidence:** High (80%)

---

### 8. undoc_47B68 (0x47b68, 94B, rank 477)
**Pattern:** Entity flag manager
**System:** Entity management
**Evidence:**
- Accesses segment 0x63FDh (entity data)
- Checks entity flags at offset +76h (bits 0-3)
- Manipulates entity state at offset 0x1940h
- Calls `fixed_vec3_accumulate_b`
- Called from `ai_entity_update_step`, `r05_farptr_dispatch_big`

**Proposed Name:** `entity_flags_update_state`
**Description:** Updates entity state flags and accumulates position vectors
**Confidence:** High (85%)

---

### 9. undoc_4AAA4 (0x4aaa4, 24B, rank 480)
**Pattern:** 3D object angle calculator
**System:** 3D rendering
**Evidence:**
- Calls `sub_4AE27`, `angle_xy_far`
- Loads far pointer from entity structure
- Stores result at offset +30h
- Called from `entity_spawn_from_tile`, `farobj_3d_model_rotate_step`

**Proposed Name:** `farobj_calculate_screen_angle`
**Description:** Calculates screen-space angle for far object rendering
**Confidence:** High (85%)

---

### 10. sub_4AC1E (0x4ac1e, 64B, rank 481)
**Pattern:** Collision detection helper
**System:** Physics/Collision
**Evidence:**
- Checks byte at offset +0Ch (collision flags)
- Tests bits 1, 2 (collision layers)
- Sets flags at offsets +0Ah (bits 5, 6)
- Stores collision targets at +16h, +18h, +1Ah, +1Ch
- Called 6 times from `undoc_4AB06`

**Proposed Name:** `collision_layer_test_and_store`
**Description:** Tests collision between two objects and stores collision data
**Confidence:** High (90%)

---

### 11. sub_4AE66 (0x4ae66, 64B, rank 482)
**Pattern:** Bounding box distance checker
**System:** Physics/Collision
**Evidence:**
- Loop checking 3 axes (cx=2, iterates 3 times with +4)
- Compares distances with threshold (bp)
- Tracks maximum distance (bx)
- Called from `entity_move_project_step`, `mode_record_field_lookup`

**Proposed Name:** `collision_aabb_distance_test`
**Description:** Tests if two AABBs are within threshold distance on all axes
**Confidence:** High (90%)

---

### 12. sub_106B07 (0x106b07, 32B, rank 484)
**Pattern:** Data copier/serializer
**System:** Data management
**Evidence:**
- Segment 0x709Fh data operations
- `rep movsb` for memory copy
- Updates `word_70A4D` (data offset/cursor)
- First byte is length prefix (`cl = [si]`)
- Called from multiple undoc functions in 0x106xxx range

**Proposed Name:** `data_buffer_append_block`
**Description:** Appends length-prefixed data block to buffer and updates cursor
**Confidence:** High (85%)

---

### 13. sub_11D346 (0x11d346, 66B, rank 485)
**Pattern:** UI box renderer (variant 1)
**System:** Menu/UI
**Evidence:**
- Calls `dispatch_220ec_invoke` (drawing)
- Calls `sub_13DE3A` with incremented coordinates (+2)
- Uses palette data from 0x79976 segment
- Push value 1 (likely box style)

**Proposed Name:** `ui_box_render_style1`
**Description:** Renders UI box with style 1 (raised/3D effect with +2 offset)
**Confidence:** High (90%)

---

### 14. sub_11D388 (0x11d388, 66B, rank 486)
**Pattern:** UI box renderer (variant 2)
**System:** Menu/UI
**Evidence:**
- Identical structure to sub_11D346
- Different palette offset (+5Eh vs +5Ah)
- Push value 3 (different box style)

**Proposed Name:** `ui_box_render_style3`
**Description:** Renders UI box with style 3 (different palette/shadow)
**Confidence:** High (90%)

---

### 15. sub_11D3CA (0x11d3ca, 66B, rank 487)
**Pattern:** UI box renderer (variant 3)
**System:** Menu/UI
**Evidence:**
- Same pattern as previous two
- Palette offset +62h
- Push value 3

**Proposed Name:** `ui_box_render_style3_alt`
**Description:** Renders UI box with alternate style 3 palette
**Confidence:** High (90%)

---

### 16. undoc_11FC1B (0x11fc1b, 51B, rank 488)
**Pattern:** Pilot/squadron selector
**System:** Menu/Campaign
**Evidence:**
- Checks `word_79BDA` (selection index)
- Compares with `word_79B72` (total count)
- Calls `undoc_11F99E` with selected pilot index
- Simple bounds checking pattern

**Proposed Name:** `menu_pilot_select_validate`
**Description:** Validates and executes pilot selection from roster
**Confidence:** High (85%)

---

### 17. undoc_127FF6 (0x127ff6, 50B, rank 489)
**Pattern:** Data structure initializer
**System:** Data management
**Evidence:**
- Segment 0x788Dh initialization
- Copies 5 arguments to offsets 0, 2, 4, 6, 8
- Calls `sub_254DC`
- Simple parameter copying pattern

**Proposed Name:** `data_struct_init_5params`
**Description:** Initializes data structure with 5 parameters at segment 788Dh
**Confidence:** Medium (70%)

---

### 18. undoc_1298AB (0x1298ab, 259B, rank 491)
**Pattern:** Screen transition effect
**System:** UI/Graphics
**Evidence:**
- Increments/wraps `byte_14E964` (0-3 counter)
- Sets up coordinate pairs in `word_151ABC`, `word_151ABE`
- Calls `far_cb_1`, `sub_2BFC3`, `far_cb_0` (graphics callbacks)
- Different coordinate modes based on arg_0 (1, 2, other)

**Proposed Name:** `ui_screen_transition_animate`
**Description:** Animates screen transition effect with moving boxes
**Confidence:** High (85%)

---

### 19. sub_1299AE (0x1299ae, 217B, rank 492)
**Pattern:** Grid pattern renderer
**System:** UI/Graphics
**Evidence:**
- Loop with counter (var_2)
- Increments di by 3, si by 3 (grid spacing)
- Wraps at 64h (100 decimal)
- Calls same graphics callbacks as undoc_1298AB

**Proposed Name:** `ui_grid_pattern_render`
**Description:** Renders animated grid pattern for UI backgrounds
**Confidence:** High (85%)

---

### 20. sub_129A87 (0x129a87, 217B, rank 493)
**Pattern:** Grid pattern renderer (variant)
**System:** UI/Graphics
**Evidence:**
- Nearly identical to sub_1299AE
- Different palette offset (+14h vs +10h)
- Same grid spacing and wrap logic

**Proposed Name:** `ui_grid_pattern_render_alt`
**Description:** Renders alternate grid pattern with different palette
**Confidence:** High (85%)

---

### 21. undoc_12BE93 (0x12be93, 62B, rank 494)
**Pattern:** Text buffer flusher
**System:** UI/Text
**Evidence:**
- Segment 0x709Fh buffer operations
- `rep movsb` from 0x2CBh to 0x1D1h
- Calls `undoc_12BBA6` (text rendering)
- Clears counters: `word_70A4F`, `word_70A4D`

**Proposed Name:** `ui_text_buffer_flush`
**Description:** Flushes text buffer to screen and resets cursor
**Confidence:** High (90%)

---

### 22. undoc_12BED1 (0x12bed1, 61B, rank 495)
**Pattern:** Text buffer writer
**System:** UI/Text
**Evidence:**
- Writes 0xFD marker + length
- Writes arg_0 + 20h (palette/style)
- `rep movsb` to copy string
- Calls `sub_12BCED` (text system)

**Proposed Name:** `ui_text_buffer_write_styled`
**Description:** Writes styled text to buffer with palette offset
**Confidence:** High (90%)

---

### 23. sub_12D4E3 (0x12d4e3, 19B, rank 496)
**Pattern:** Interrupt dispatcher (INT 7Ah)
**System:** Hardware/Network
**Evidence:**
- Saves/restores all registers
- `int 7Ah` (Novell NetWare API)
- Sets bx=0 (function code)
- Push/pop all general registers

**Proposed Name:** `netware_api_call_dispatch`
**Description:** Dispatches call to Novell NetWare INT 7Ah with register preservation
**Confidence:** High (95%)

---

### 24. sub_132182 (0x132182, 244B, rank 497)
**Pattern:** Squadron data loader
**System:** Campaign/Save
**Evidence:**
- String concat: ".BIN", "SQUAD"
- Opens file with `op_dispatch_far_entry`
- Reads into `dword_79E64` (4 KB buffer)
- Called from overlay_r45_logic, r53_head_garbage_fragment

**Proposed Name:** `campaign_squadron_data_load`
**Description:** Loads squadron data from SQUAD.BIN file
**Confidence:** High (90%)

---

### 25. sub_13296E (0x13296e, 408B, rank 498)
**Pattern:** Numeric input handler
**System:** UI/Input
**Evidence:**
- Loop calling `flag_table_pop_far_thunk` (keyboard input)
- Checks for '0'-'9', '-' (minus sign)
- Backspace handling (case 8)
- Builds string with underscore cursor
- Converts to integer at end

**Proposed Name:** `ui_numeric_input_handler`
**Description:** Handles numeric text input with sign support and validation
**Confidence:** High (95%)

---

### 26. undoc_13367B (0x13367b, 600B, rank 499)
**Pattern:** Pilot image loader
**System:** UI/Resources
**Evidence:**
- Loads "PILOTBKG.BIN", "PLANE.BIN", "PLAFE.BIN"
- Sets up image buffers at specific offsets (9C44h, 404h, 406h)
- Multiple file operations with `op_dispatch_far_entry`
- Checks `byte_7A302`, `byte_7A30E` (pilot availability flags)

**Proposed Name:** `ui_pilot_images_load_all`
**Description:** Loads all pilot-related images (background, plane, face)
**Confidence:** High (90%)

---

### 27. undoc_136133 (0x136133, 368B, rank 500)
**Pattern:** Save file writer
**System:** Campaign/Save
**Evidence:**
- Creates "TEMP1.DAT" filename
- Writes multiple data blocks to file
- Writes campaign state from various segments (79E60h, 79E5Ch, etc.)
- Calls `flag2224a_clear`, `flag2224a_set` (save system flags)

**Proposed Name:** `campaign_save_temp_file_write`
**Description:** Writes temporary save file with campaign state data
**Confidence:** High (90%)

---

## Pattern Summary

### By System:
- **Menu/UI:** 10 functions (37%)
- **3D Rendering:** 2 functions (7%)
- **AI:** 2 functions (7%)
- **Physics/Collision:** 2 functions (7%)
- **Campaign/Save:** 3 functions (11%)
- **Graphics:** 3 functions (11%)
- **Text System:** 2 functions (7%)
- **Input:** 1 function (4%)
- **Hardware:** 1 function (4%)
- **Entity Management:** 1 function (4%)

### By Pattern:
- **Dispatchers:** 3 functions
- **Renderers:** 8 functions
- **Data Loaders:** 3 functions
- **State Managers:** 4 functions
- **Input Handlers:** 1 function
- **Math/Geometry:** 2 functions
- **Buffer Managers:** 3 functions
- **Hardware Interface:** 1 function
- **Collision Detection:** 2 functions

### Notable Clusters:
1. **UI Box Renderers (0x11D346-0x11D3CA):** Three variants of box rendering with different styles
2. **R57 Menu Handlers (0x1A6AA6, 0x1A86C6):** Paired functions for flight/loadout displays
3. **Grid Renderers (0x1299AE, 0x129A87):** Two variants of animated grid backgrounds
4. **Text Buffer (0x12BE93, 0x12BED1):** Write and flush operations

---

## Proposed Registry Entries (YAML)

```yaml
# Menu/UI System
0x1854cf:
  name: menu_r53_button_dispatcher
  type: dispatcher
  system: menu
  description: Dispatches menu button rendering for R53 game mode
  confidence: 0.95
  calls: [ui_element_render_variant_a, ui_element_render_variant_b, utility_11c90f, sub_11CA9E]
  called_by: [game_mode_r53_main_coordinator]

0x1a6aa6:
  name: menu_r57_flight_display_handler
  type: renderer
  system: menu
  description: Handles flight selection menu with formatted flight numbers
  confidence: 0.90
  calls: [int_to_string_converter, string_concatenate, undoc_11C7CB]
  called_by: [r57_menu_state_machine]

0x1a86c6:
  name: menu_r57_loadout_flight_display
  type: renderer
  system: menu
  description: Displays flight information in loadout screen
  confidence: 0.90
  calls: [int_to_string_converter, string_concatenate, sub_11C707]
  called_by: [r57_loadout_display_handler]

0x11d346:
  name: ui_box_render_style1
  type: renderer
  system: ui
  description: Renders UI box with raised/3D effect
  confidence: 0.90
  calls: [dispatch_220ec_invoke, sub_13DE3A]

0x11d388:
  name: ui_box_render_style3
  type: renderer
  system: ui
  description: Renders UI box with style 3 palette
  confidence: 0.90
  calls: [dispatch_220ec_invoke, sub_13DE3A]

0x11d3ca:
  name: ui_box_render_style3_alt
  type: renderer
  system: ui
  description: Renders UI box with alternate style 3 palette
  confidence: 0.90
  calls: [dispatch_220ec_invoke, sub_13DE3A]

0x11fc1b:
  name: menu_pilot_select_validate
  type: validator
  system: menu
  description: Validates and executes pilot selection
  confidence: 0.85
  calls: [undoc_11F99E]

0x1298ab:
  name: ui_screen_transition_animate
  type: renderer
  system: graphics
  description: Animates screen transition effect
  confidence: 0.85
  calls: [far_cb_1, sub_2BFC3, far_cb_0]

0x1299ae:
  name: ui_grid_pattern_render
  type: renderer
  system: graphics
  description: Renders animated grid pattern for backgrounds
  confidence: 0.85
  calls: [far_cb_1, sub_2BFC3, far_cb_0]

0x129a87:
  name: ui_grid_pattern_render_alt
  type: renderer
  system: graphics
  description: Renders alternate grid pattern
  confidence: 0.85
  calls: [far_cb_1, sub_2BFC3, far_cb_0]

# 3D Rendering System
0x2978e:
  name: render_3d_polygon_visibility_test
  type: processor
  system: render
  description: Tests polygon visibility and builds span records
  confidence: 0.85
  calls: [fixed_vec3_cross, vec3_dot, record_span_mask_rebuild, line_table_build_dispatch]
  called_by: [object_proj_draw_dispatch, line_record_flag_dispatch]

0x4aaa4:
  name: farobj_calculate_screen_angle
  type: calculator
  system: render
  description: Calculates screen-space angle for far objects
  confidence: 0.85
  calls: [sub_4AE27, angle_xy_far]
  called_by: [entity_spawn_from_tile, farobj_3d_model_rotate_step]

# AI System
0x3f287:
  name: ai_waypoint_behavior_execute
  type: processor
  system: ai
  description: Executes AI waypoint behavior updates
  confidence: 0.85
  calls: [ai_state_calculate_helper, stub_to_24988]
  called_by: [farobj_view_project_step, hud_digit_extract]

# Entity Management
0x47b68:
  name: entity_flags_update_state
  type: manager
  system: entity
  description: Updates entity state flags and position vectors
  confidence: 0.85
  calls: [fixed_vec3_accumulate_b]
  called_by: [ai_entity_update_step, r05_farptr_dispatch_big]

# Physics/Collision
0x4ac1e:
  name: collision_layer_test_and_store
  type: detector
  system: physics
  description: Tests collision between layers and stores results
  confidence: 0.90
  called_by: [undoc_4AB06]

0x4ae66:
  name: collision_aabb_distance_test
  type: detector
  system: physics
  description: Tests AABB distance threshold on all axes
  confidence: 0.90
  called_by: [entity_move_project_step, mode_record_field_lookup]

# Text System
0x12be93:
  name: ui_text_buffer_flush
  type: manager
  system: ui_text
  description: Flushes text buffer to screen
  confidence: 0.90
  calls: [undoc_12BBA6]

0x12bed1:
  name: ui_text_buffer_write_styled
  type: writer
  system: ui_text
  description: Writes styled text to buffer
  confidence: 0.90
  calls: [sub_12BCED]

0x43842:
  name: hud_text_render_formatted
  type: renderer
  system: hud
  description: Renders formatted text to HUD buffer
  confidence: 0.80
  calls: [int32_to_ascii_short, op_dispatch]

# Campaign/Save System
0x132182:
  name: campaign_squadron_data_load
  type: loader
  system: campaign
  description: Loads squadron data from SQUAD.BIN
  confidence: 0.90
  calls: [string_concatenate, op_dispatch_far_entry]
  called_by: [overlay_r45_logic, r53_head_garbage_fragment]

0x136133:
  name: campaign_save_temp_file_write
  type: writer
  system: campaign
  description: Writes temporary campaign save file
  confidence: 0.90
  calls: [op_dispatch_far_entry, flag2224a_clear, flag2224a_set]
  called_by: [overlay_r49_processor, game_mode_r48_main_coordinator]

0x13367b:
  name: ui_pilot_images_load_all
  type: loader
  system: resources
  description: Loads pilot background, plane, and face images
  confidence: 0.90
  calls: [string_concatenate, op_dispatch_far_entry]
  called_by: [r52_data_fragment, overlay_r56_handler]

# Input System
0x13296e:
  name: ui_numeric_input_handler
  type: handler
  system: input
  description: Handles numeric text input with validation
  confidence: 0.95
  calls: [flag_table_pop_far_thunk, sub_11C707, sub_12805C]
  called_by: [overlay_r4E_main, slope_far_call_driver]

# Data Management
0x106b07:
  name: data_buffer_append_block
  type: writer
  system: data
  description: Appends length-prefixed block to buffer
  confidence: 0.85

0x127ff6:
  name: data_struct_init_5params
  type: initializer
  system: data
  description: Initializes 5-parameter data structure
  confidence: 0.70
  calls: [sub_254DC]

# State Management
0x3e01a:
  name: state_flags_increment_field
  type: manager
  system: state
  description: Increments bit fields in state register
  confidence: 0.75

# Hardware/Network
0x12d4e3:
  name: netware_api_call_dispatch
  type: dispatcher
  system: hardware
  description: Dispatches Novell NetWare INT 7Ah calls
  confidence: 0.95
```

---

## Analysis Notes

### High-Confidence Identifications (90%+):
1. **sub_1854CF** - Clear menu dispatcher with button strings
2. **sub_11D346/388/3CA** - Trio of UI box renderers with style variants
3. **sub_4AC1E** - Collision detection with clear bit flag logic
4. **sub_4AE66** - AABB distance test with 3-axis loop
5. **sub_13296E** - Numeric input with visible digit/backspace handling
6. **undoc_12BE93/BED1** - Text buffer write/flush pair
7. **sub_12D4E3** - INT 7Ah Novell NetWare call

### Medium-Confidence (70-85%):
1. **sub_2978E** - Complex 3D math, likely visibility culling
2. **undoc_3F287** - AI waypoint system (needs more context)
3. **undoc_47B68** - Entity flags (segment 63FDh unclear)
4. **undoc_1298AB/1299AE/129A87** - Screen effects (callback names generic)

### Cross-References Found:
- R53/R57 menu systems have parallel implementations
- UI box renderers form a style family (1, 3, 3alt)
- Grid renderers share common callback pattern
- Campaign system uses temp files for saving

### Suggested Follow-ups:
1. Examine R53/R57 overlay structure for full menu flow
2. Map all UI box style variants (likely 0-4)
3. Trace campaign save/load cycle through temp files
4. Identify graphics callback chain (far_cb_0/1, sub_2BFC3)
