# Tactical Map Object Rendering - Falcon 3.0

**Created**: 2026-11-15  
**Status**: Research Phase - 25% Complete  
**Goal**: Understand how different object types (aircraft, waypoints, threats) are rendered on the tactical map

---

## Executive Summary

The Falcon 3.0 tactical map renders multiple object types using a shared 3D projection system (`fixed_vec3_accumulate_a`) followed by specialized rendering for each object type. Waypoints are confirmed to use 3D→2D projection followed by text rendering for labels.

**Key Finding**: The tactical map is NOT a simple 2D overlay - it uses the same 3D perspective projection as the HUD and external view, projecting 3D world coordinates to screen space.

---

## Object Types on Tactical Map

### Confirmed Object Types:
1. **Waypoints** - Navigation points with labels (INVESTIGATED ✓)
2. **Aircraft** - Player and AI flight positions (NOT YET FOUND)
3. **Threats** - SAM sites, AAA positions (NOT YET FOUND)
4. **Targets** - Ground targets, objectives (NOT YET FOUND)
5. **Bullseye** - Reference point (NOT YET FOUND)
6. **Flight Paths** - Lines connecting waypoints (PARTIALLY UNDERSTOOD)

---

## Waypoint Rendering Pipeline (DECODED)

### Function Call Chain:
```
overlay_r57_processor_2 (0x1A0E10)
  └─> waypoint_display_helper (0x1A163A) - 1383 bytes
       ├─> farobj_vec3_accum_b_ret (0x022C89) - 3D projection
       │    └─> fixed_vec3_accumulate_a (0x022C91) - Core 3D math
       └─> ui_text_render_engine (0x128598) - Text labels
```

### Waypoint Display Process:

1. **Data Preparation** (waypoint_coordinate_processor - 0x1A2441)
   - Reads 21-byte waypoint records from 0x4FC2:0x168
   - Processes waypoint markers, coordinates, flags
   - Outputs 6-byte display records

2. **3D Projection** (waypoint_display_helper - 0x1A163A)
   - Calls `farobj_vec3_accum_b_ret` **6 times** per waypoint
   - Projects 3D world coordinates to 2D screen coordinates
   - Uses custom 15-bit fixed-point format
   - Camera/view matrix applied during projection
   
3. **Text Rendering** (ui_text_render_engine - 0x128598)
   - Draws waypoint labels/numbers
   - Called via `loc_68716+1` and `loc_686FC+3`
   - Both resolve to `ui_loadout_menu_enter` (0x683C1)
   - Likely shared text rendering subsystem

### Waypoint Structure (21 bytes):
```c
struct Waypoint {
    uint8_t  marker;        // +0x00: Always 0x01
    int16_t  x_coord;       // +0x01: World X coordinate
    int16_t  y_coord;       // +0x03: World Y coordinate
    int16_t  altitude;      // +0x05: Z coordinate (altitude)
    uint8_t  flags[15];     // +0x07: Type, action, etc.
};
```

**Array Location**: Segment 0x4FC2, offset 0x168

---

## Graphics Primitives Used

### Core Drawing Functions:

1. **graphics_line_draw_bresenham** (0x028B08) - 409 bytes
   - Standard Bresenham line drawing algorithm
   - Draws flight path connections
   - Called by `pos_diff_norm` (0x28874)
   - **Only 1 static xref found** (dynamic dispatch likely)

2. **draw_from_struct** (0x02245A) - 104 bytes
   - Main drawing dispatcher
   - Takes drawing parameters from structure
   - **Only 4 static xrefs found**:
     - `explosion_visual_effect_update` (0x32393) - 2 calls
     - `mode_axis_state_select` (0x34C31) - 1 call
     - `r29_draw_from_struct_far_wrapper` (0x13DA52) - 1 call
   - Likely called via function pointer (dynamic dispatch)

3. **ui_text_render_engine** (0x128598) - 1282 bytes
   - Comprehensive text rendering system
   - Handles fonts, positioning, colors
   - Used for waypoint labels
   - Also used by menus and UI elements

### Drawing Observation:
The low number of static xrefs (4 for draw_from_struct, 1 for line_draw) suggests:
- **Dynamic dispatch via function pointers**
- **Drawing table-driven** (array of draw commands)
- Most calls happen via vtable or command buffer

---

## 3D Projection System (SHARED WITH ALL RENDERING)

### Core Function: fixed_vec3_accumulate_a (0x022C91)

**Usage Statistics**:
- **Size**: 68 bytes
- **Calls per frame**: 51,000+ (confirmed via instrumentation)
- **Used by**: HUD, cockpit, tactical map, external view, ALL 3D rendering

**Algorithm**:
```
Result = (X×ScaleX % DivisorX) + (Y×ScaleY % DivisorY) + (Z×ScaleZ % DivisorZ)
```

**Fixed-Point Format**:
- Custom 15-bit format with per-axis corrections
- Divisors: X=32771, Y=32779, Z=32783 (prime numbers)
- Uses remainder (modulo), not quotient
- Provides sub-pixel precision and variation

**State Variables** (cs segment):
```assembly
cs:0x22C71/73/75 - vec3_x/y/z_component
cs:0x22C7D/7F/81 - matrix_scale_x/y/z  
cs:0x22C83/85/87 - fixedpoint_divisor_x/y/z
```

**See**: `docs/3D_PROJECTION_MATH_DECODED.md` for complete analysis

---

## Rendering Coordinator Functions

### tactical_screen_coordinator (0x12DB6A) - 1024 bytes
- **Purpose**: Main UI coordinator for tactical screen
- **Segment**: R29 overlay
- **Functions**:
  - Polls keyboard input (`input_poll_handler`)
  - Manages graphics mode switching
  - Coordinates UI text rendering
  - Dispatches to `r29_tactical_screen_coordinator` (0x12DF6A)

### r29_tactical_screen_coordinator (0x12DF6A) - 6799 bytes
- **Purpose**: R29 overlay tactical planning/mission editor coordinator
- **Size**: 6799 bytes (large coordinator)
- **Status**: Not yet analyzed

---

## Object Type Functions Found

### From IDA Search Results:

#### Flight-Related (48 functions):
- `flight_entity_simulation_frame_step` (0x3A3D6)
- `flight_aircraft_slot_cycle_update` (0x49546)
- `flight_aircraft_slot_physics_step` (0x496D3)
- **Note**: These are physics/simulation, not rendering

#### Waypoint-Related (3 functions):
- `waypoint_display_helper` (0x1A163A) ✓ ANALYZED
- `waypoint_coordinate_processor` (0x1A2441) ✓ ANALYZED
- `ai_waypoint_behavior_execute` (0x3F287) - AI navigation

#### Target-Related (7 functions):
- `ai_target_priority_evaluator` (0x3E96F)
- `hud_ai_target_tracking_draw` (0x425A2) - HUD tracking display
- `farobj_slot_target_bind` (0x445A6)
- `target_cycle_scan` (0x48B05)
- **Status**: AI targeting, not map display

#### Map-Related (27 functions):
- `map_view_project_pipeline` (0x3A88D) ⭐ NEEDS INVESTIGATION
- `map_view_entity_project` (0x47871) ⭐ NEEDS INVESTIGATION
- `hud_map_overlay_frame` (0x3A6B1) ⭐ NEEDS INVESTIGATION
- `map_overlay_clip_frame` (0x3A5D2) ⭐ NEEDS INVESTIGATION
- `slot2_map_window_refresh` (0x12895)
- `slot2_map_window_load` (0x12BEA)
- Many others - terrain, EMS, tiles

#### Symbol/Icon-Related:
- **No functions found with "symbol" or "icon" keywords**
- Suggests symbols might be:
  - Drawn as text characters (ASCII art)
  - Stored in bitmap tables
  - Drawn via generic primitives

---

## Next Investigation Priorities

### HIGH PRIORITY:
1. ⭐ **map_view_project_pipeline** (0x3A88D) - 36 bytes
   - Name suggests main map projection entry point
   - Small size = likely dispatcher

2. ⭐ **map_view_entity_project** (0x47871) - 198 bytes
   - Projects entities (aircraft?) to map view
   - Larger size = contains logic

3. ⭐ **hud_map_overlay_frame** (0x3A6B1) - 192 bytes
   - HUD map overlay rendering
   - Might show how objects are drawn

4. ⭐ **map_overlay_clip_frame** (0x3A5D2) - 223 bytes
   - Clipping for map overlay
   - Related to above

### MEDIUM PRIORITY:
5. **r29_tactical_screen_coordinator** (0x12DF6A) - 6799 bytes
   - Complete tactical screen logic
   - Very large, needs careful analysis

6. **farobj_render_draw_1f712** (0x26CD8) - 551 bytes
   - Far object rendering
   - Might handle distant aircraft

7. **object_scale_gather_draw** (0x268DD) - 338 bytes
   - Object scaling for distance
   - Could apply to all map objects

### LOW PRIORITY:
8. Icon/symbol bitmap tables search
9. Aircraft symbol character codes
10. Threat symbol definitions

---

## Key Insights

### 1. Shared 3D Pipeline
The tactical map uses the SAME 3D projection system as:
- HUD targeting display
- Cockpit instrument rendering  
- External view camera
- All 3D objects

This means map objects are true 3D entities projected to screen space, not simple 2D overlays.

### 2. Dynamic Dispatch Pattern
Low static xref counts suggest:
- Function pointer tables for rendering
- Command buffer-based drawing
- Type-specific renderers registered in tables

### 3. Text-Based Symbols?
No dedicated symbol/icon functions suggest:
- Waypoint numbers drawn as text ✓ CONFIRMED
- Aircraft might be letters (F, E, N for Friend/Enemy/Neutral)
- SAM sites might be characters (S, A, @, *)
- Uses font rendering, not sprite system

### 4. Overlay Architecture
Key functions in R29 and R57 overlays:
- Tactical planning in R29
- Flight/loadout display in R57
- Map rendering split across overlays

---

## Open Questions

1. **Where are aircraft positions rendered?**
   - Not in waypoint_display_helper
   - Likely in map_view_entity_project?
   - Or farobj_render_draw_1f712?

2. **How are threat symbols drawn?**
   - SAM sites, AAA positions
   - As text characters?
   - As line primitives?

3. **What draws flight path lines?**
   - graphics_line_draw_bresenham involved
   - But how is it called? (only 1 static xref)

4. **Is there a symbol table?**
   - Character codes for each object type?
   - Color assignments?

5. **How does zoom work?**
   - Matrix scale values in vec3_accumulate?
   - Separate zoom variable?

---

## Investigation Strategy

### Phase 1: Map Projection Functions (NEXT)
1. Export and analyze `map_view_project_pipeline`
2. Export and analyze `map_view_entity_project`
3. Understand relationship between these functions
4. Identify entity types handled

### Phase 2: Overlay Rendering (AFTER PHASE 1)
1. Analyze `hud_map_overlay_frame`
2. Analyze `map_overlay_clip_frame`
3. Understand frame composition

### Phase 3: Symbol System (TBD)
1. Search for character/color tables
2. Find symbol-to-character mappings
3. Locate object type enumeration

### Phase 4: Runtime Debugging (USER TASK)
1. Capture map state during gameplay
2. Record entity positions and types
3. Verify projection math with live data

---

## Related Documentation

- `docs/3D_PROJECTION_MATH_DECODED.md` - Complete 3D projection analysis
- `docs/TACTICAL_MAP_DISPLAY_RESEARCH.md` - Initial waypoint research
- `docs/TACTICAL_MAP_BREAKTHROUGH.md` - 3D discovery document
- `docs/architecture/rendering.md` - Overall rendering architecture
- `docs/SESSION_TACTICAL_MAP_PROGRESS.md` - Progress tracking

---

## Completion Status

### What We Know (25%):
- ✅ Waypoint rendering pipeline (data → 3D → text)
- ✅ 3D projection system (fixed_vec3_accumulate_a)
- ✅ Text rendering for labels
- ✅ Graphics primitives (line, draw_from_struct)
- ✅ Core coordinators identified

### What We Don't Know (75%):
- ❌ Aircraft position rendering
- ❌ Threat symbol rendering
- ❌ Flight path line drawing dispatch
- ❌ Symbol table/character mappings
- ❌ Object type enumeration
- ❌ Zoom mechanism
- ❌ Map entity data structures
- ❌ Color assignment system
- ❌ Clipping and culling logic

---

## Scripts Created

1. `analysis/ida_scripts/find_map_object_renderers.py`
   - Found draw_from_struct callers
   
2. `analysis/ida_scripts/find_line_draw_callers.py`
   - Found line drawing callers
   
3. `analysis/ida_scripts/investigate_drawing_calls.py`
   - Analyzed drawing functions
   
4. `analysis/ida_scripts/search_map_object_types.py`
   - Searched for object type functions
   - Generated keyword matches
   - Found 27 map-related functions

**Outputs**:
- `analysis/ida_scripts/map_object_renderers.json`
- `analysis/ida_scripts/line_draw_callers.json`
- `analysis/ida_scripts/drawing_functions_analysis.json`
- `analysis/ida_scripts/map_object_types.json`

---

## Next Steps

1. **Export map_view_project_pipeline** (0x3A88D)
   - Understand main projection entry point
   
2. **Export map_view_entity_project** (0x47871)
   - Understand entity rendering
   
3. **Analyze map overlay functions** (hud_map_overlay_frame, etc.)
   - Complete frame rendering pipeline
   
4. **Search for symbol tables**
   - Character codes, colors, object types
   
5. **User runtime debugging** (deferred)
   - Capture live map state
   - Verify analysis with real data

---

**Last Updated**: 2026-11-15  
**Estimated Completion**: Need 3-4 more investigation sessions for 80%+ understanding
