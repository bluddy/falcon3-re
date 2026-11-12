# Function Discovery Report

**Date**: 2026-11-11  
**Source**: IDA Pro automated function discovery  
**Total Functions**: 4,170

---

## Discovery Summary

Automated name-based categorization of all 4,170 functions in Falcon 3.0 executable.

### Categorization Results

| Category | Functions | Notes |
|----------|-----------|-------|
| **Uncategorized** | 3,810 (91%) | Generic names (sub_XXXXX) or unknown purpose |
| **Rendering** | 104 (2.5%) | Contains "render", "view", "projection", "transform", "camera" |
| **Overlay** | 90 (2.2%) | Contains "overlay", "hud_draw", "draw_line", etc. |
| **Terrain** | 49 (1.2%) | Contains "terrain", "ground", "elevation", "height" |
| **Targeting** | 43 (1.0%) | Contains "radar", "target", "lock", "track", "rwr" |
| **Input** | 36 (0.9%) | Contains "input", "keyboard", "mouse", "joystick" |
| **HUD** | 34 (0.8%) | Contains "hud_", "airspeed", "altitude", "heading" |
| **Audio** | 3 (0.07%) | Contains "audio", "sound", "speaker", "beep" |
| **Physics** | 1 (0.02%) | Contains "physics", "aero", "flight" (very few matched) |

### Key Findings

1. **Name-Based Discovery Limited**: Only ~9% of functions have descriptive names
2. **Most Functions Generic**: 91% have generated names (sub_XXXXX, dispatch_XXXXX, wrapper functions)
3. **Input System Well-Named**: 36 mouse/joystick functions with clear names ✅
4. **HUD System is 2D Rendering**: 34 hud_* functions are the actual 2D overlay rendering (not "overlay_*")
5. **"Overlay" = Code Overlay Management**: 90 overlay_* functions manage DOS code overlays (EMS, segment swapping), NOT 2D graphics
6. **Terrain Well-Named**: 49 functions including known hot path
7. **Physics/AI/Weapons Poorly Named**: These major systems didn't match patterns

**IMPORTANT CORRECTION**: Our documentation used "overlay system" to mean 2D HUD rendering. The actual naming convention is:
- **"overlay_*" functions** = DOS code overlay management (EMS, segment loading)
- **"hud_*" functions** = 2D HUD rendering (the system we meant)

---

## Sample Function Names by Category

### Input System (36 functions) - BEST NAMED ✅

**Mouse Functions:**
```
mouse_delta_scale_far_entry (16 bytes, 1 call)
mouse_delta_scale_stub (26 bytes, 1 call)
mouse_driver_init (72 bytes, 2 calls)
mouse_reset_if_10000 (13 bytes, 0 calls)
mouse_gate_far_entry (6 bytes, 1 call)
mouse_buttons_get_2 (56 bytes, 2 calls)
mouse_buttons_get (35 bytes, 1 call)
mouse_int33_dispatch (120 bytes, 0 calls) - INT 33h mouse driver interface
```

**Joystick Functions:**
```
int15_joystick_detect (28 bytes, 0 calls) - INT 15h BIOS joystick detection
int15_joystick_read (135 bytes, 0 calls) - INT 15h BIOS joystick read
joystick_poll (...)
```

**Analysis**: Input system functions have excellent descriptive names. Hardware-specific interfaces (INT 15h, INT 33h) clearly identified. Clean separation of mouse vs. joystick. Perfect entry points for deep analysis.

### Overlay System (90 functions) - WELL NAMED ✅

**Overlay Management (NOT 2D rendering as expected!):**
```
overlay_seg_word_set2_if3 (33 bytes, 2 calls)
overlay_seg_word_read (13 bytes, 0 calls)
overlay_seg_word_write (15 bytes, 0 calls)
overlay_slot_mode_enter (26 bytes, 2 calls)
overlay_segment_load (605 bytes, 12 calls) - Core overlay loader
overlay_file_open (276 bytes, 3 calls)
tail_bridge_overlay_load (131 bytes, 3 calls) - The bridge function we analyzed!
overlay_patch_verify (70 bytes, 4 calls)
overlay_ems_stack_segment_load (103 bytes, 2 calls) - EMS memory management
startup_overlay_init (213 bytes, 4 calls)
```

**IMPORTANT DISCOVERY**: These "overlay" functions are actually **CODE OVERLAY MANAGEMENT** (swapping code segments), NOT the 2D HUD overlay rendering system! This is DOS overlay technology for managing large executables in limited memory.

The 2D HUD rendering is likely in a different category (possibly "hud_" functions or uncategorized).

### HUD System (34 functions) - WELL NAMED ✅

**HUD Drawing Functions (actual 2D rendering!):**
```
tail_bridge_to_display_palette_hud_refresh_step (8 bytes, 1 call)
hud_data_panel_draw (273 bytes, 16 calls)
hud_metric_rows_draw (232 bytes, 17 calls)
hud_entity_search_select (337 bytes, 23 calls)
hud_readout_render (908 bytes, 23 calls) - Large, complex HUD rendering
hud_field0c_value_draw (253 bytes, 6 calls)
hud_field14_value_draw (193 bytes, 7 calls)
hud_value_format_draw (216 bytes, 7 calls)
hud_heading_tape_draw (254 bytes, 5 calls) - Heading tape rendering!
hud_panel_rect_compute (325 bytes, 23 calls)
```

**Analysis**: These are the actual 2D HUD overlay rendering functions! `hud_heading_tape_draw` confirms this. `hud_readout_render` at 908 bytes with 23 calls is a major function.

### Terrain System (49 functions) - WELL NAMED ✅

**Terrain Functions:**
```
terrain_height_lookup_11cc8 (142 bytes, 0 calls)
terrain_advance_gated (444 bytes, 1 call) - Large terrain processing
terrain_dot_advance_11cf8 (121 bytes, 1 call)
terrain_matrix_advance_11d04 (188 bytes, 1 call)
terrain_attr_default_60 (10 bytes, 1 call)
terrain_attr_lookup_3840 (157 bytes, 0 calls)
terrain_attr_walk_13110 (82 bytes, 1 call) - The hot path we analyzed!
terrain_lookup_gated_b (21 bytes, 2 calls) - The gatekeeper!
terrain_attr_lookup_3840_b (42 bytes, 0 calls)
terrain_attr_unpack_11c2c (129 bytes, 1 call)
```

**Analysis**: Includes the known hot path functions. `terrain_advance_gated` (444 bytes) is substantial. Many lookup and attribute functions.

### Rendering System (104 functions) - WELL NAMED ✅

**View/Rendering Functions:**
```
viewobj_project_select (20 bytes, 2 calls)
view_scroll_rotate_apply (111 bytes, 4 calls)
view_scroll_clamp_1f702 (28 bytes, 0 calls)
view_extent_get_quad (17 bytes, 0 calls)
view_extent_compute_1f6da (34 bytes, 0 calls)
view_scroll_quad_update (183 bytes, 4 calls)
view_extent_shadow_save_far (4 bytes, 1 call)
view_extent_shadow_save (66 bytes, 1 call)
view_extent_shadow_restore_far (4 bytes, 1 call)
view_extent_shadow_restore (76 bytes, 1 call)
```

**Analysis**: Many view transformation and projection functions. "Extent" likely refers to screen viewport. "Shadow save/restore" for state management.

### Targeting System (43 functions) - MIXED NAMING ⚠️

**Terrain Block Scanning (misclassified?):**
```
terrain_attr_block_scan_inc (157 bytes, 1 call)
terrain_attr_block_scan_axdec (157 bytes, 1 call)
terrain_attr_block_scan_dec (156 bytes, 1 call)
terrain_attr_block_scan (156 bytes, 1 call)
```

**State Management:**
```
state_block_77720_slot_clamp (52 bytes, 1 call)
state_block_77720_commit_12 (29 bytes, 1 call)
state_block_77720_slot_select (76 bytes, 1 call)
state_block_77720_commit (30 bytes, 1 call)
state_block_77720_commit_19 (30 bytes, 1 call)
```

**Analysis**: "Targeting" category caught terrain scanning functions (contains "target" substring but actually terrain). Real targeting functions likely uncategorized.

### Audio System (3 functions) - MINIMAL ⚠️

**Sound Functions:**
```
sound_device_init_far (13 bytes, 1 call)
sound_device_init (69 bytes, 4 calls) - Sound hardware initialization
mode_audio_state_step (121 bytes, 2 calls) - Audio state machine
```

**Analysis**: Only 3 functions matched. Expected 25+ audio functions. Most likely have generic names or embedded in uncategorized.

---

## Implications

### For Further Analysis

1. **Use Call Graph Analysis**: Since names don't reveal much, trace from known entry points
2. **Focus on Named Systems First**: Input, overlay, terrain have good names
3. **Use Data Flow**: Follow data structures to find related functions
4. **Manual Naming**: As functions are understood, rename in IDA for future analysis

### Systems Needing Manual Discovery

- **Physics**: 48 functions expected, only 1 matched
- **Weapons**: ~100 functions expected, 0 matched (likely in targeting or uncategorized)
- **AI**: ~100 functions expected, 0 matched (likely in uncategorized)
- **Audio**: 25 functions expected, only 3 matched

### Well-Documented Systems

- **Input**: 36/74 functions matched (49%) - good coverage
- **Overlay**: 90/96 functions matched (94%) - excellent
- **Terrain**: 49 functions found (expected ~15, so likely includes related functions)
- **Rendering**: 104 functions found (expected ~6 core, so includes many helpers)

---

## Next Steps

### Immediate Actions

1. **Extract Sample Names**: Read full JSON to show representative function names per category
2. **Analyze Call Graphs**: From known functions (view_projection, terrain_frame_update_driver), trace callees
3. **Cross-Reference with Estimates**: Compare found functions to expected counts from documentation
4. **Manual Categorization**: Use IDA to manually categorize important uncategorized functions

### Deep Dive Priorities

1. **Input System** (36 functions, well-named) - Complete analysis
2. **Overlay System** (90 functions, well-named) - Map drawing primitives
3. **Terrain System** (49 functions) - Understand beyond hot path
4. **Rendering** (104 functions) - Separate core from utilities

### Discovery Strategies for Poorly-Named Systems

**Physics System**:
- Start from control input consumption
- Trace aircraft state updates
- Look for trig functions (sin, cos, atan2)
- Find lookup table accesses

**Weapons/AI**:
- Start from weapon fire triggers
- Trace missile state updates
- Look for AI decision points
- Find targeting data accesses

**Audio**:
- Look for INT 33h (Sound Blaster)
- Port 0x61 access (PC Speaker)
- Port 0x388 (AdLib)
- DMA setup functions

---

## Function Discovery Tools

### Created Scripts

- `discover_all_functions.py` - IDA script to extract and categorize all functions
- `all_functions_categorized.json` - Complete function database (4,170 functions)

### Analysis Method

```python
# Pattern matching on function names
if 'mouse' in name or 'joystick' in name:
    category = 'input'
elif 'overlay' in name or 'draw' in name:
    category = 'overlay'
# ... etc
```

**Limitations**: Only catches functions with descriptive names. Misses:
- Generic names (sub_12345)
- Abbreviated names
- Domain-specific terminology we didn't predict

---

## Conclusion

Automated name-based discovery successfully categorized **360 functions (9%)** across 9 systems. The remaining **3,810 functions (91%)** require:
- Call graph analysis
- Data flow tracing
- Manual inspection and naming
- Cross-referencing with known entry points

**Best Coverage**: Input (49%), Overlay (94%)  
**Worst Coverage**: Physics (2%), AI (0%), Weapons (0%), Audio (12%)

The well-named systems (input, overlay, terrain) provide excellent starting points for deeper analysis. The poorly-named systems (physics, AI, weapons) will require tracing from known entry points and data structures.

---

**Status**: Initial discovery complete, detailed extraction in progress  
**Next**: Extract sample function names for each category, begin call graph analysis from known entry points
