# Tactical Map Object Rendering - Session Summary

## Session Information

**Date**: 2026-11-15  
**Focus**: Investigation of tactical map object rendering (aircraft, symbols, threats)  
**Starting Point**: 75% complete (waypoint rendering decoded)  
**Ending Point**: 75% complete (object rendering survey complete)  
**Progress**: +0% (survey phase, no new decode)

---

## Session Goals

After decoding waypoint rendering and 3D projection (75% completion), user requested investigation of:
- How aircraft positions are rendered on tactical map
- How ground targets/threats are drawn
- What symbols/icons are used
- How different object types are displayed

---

## Work Completed

### 1. Created IDA Analysis Scripts ✅

**Purpose**: Search for map object rendering functions

#### Scripts Created:
1. **find_map_object_renderers.py**
   - Searched for callers of `draw_from_struct` (0x02245A)
   - Found only 4 static xrefs (suggests dynamic dispatch)
   - Output: `map_object_renderers.json`

2. **find_line_draw_callers.py**
   - Searched for callers of `graphics_line_draw_bresenham` (0x028B08)
   - Found only 1 static xref to `pos_diff_norm` (0x28874)
   - Output: `line_draw_callers.json`

3. **investigate_drawing_calls.py**
   - Analyzed `loc_68716+1` and `loc_686FC+3` from waypoint_helper
   - Both resolved to `ui_loadout_menu_enter` (0x683C1)
   - Confirmed waypoint labels use `ui_text_render_engine` (0x128598)
   - Output: `drawing_functions_analysis.json`

4. **search_map_object_types.py**
   - Comprehensive keyword search for object-related functions
   - Searched 16 keywords: flight, plane, waypoint, map, tactical, threat, etc.
   - Found 27 map-related functions
   - Found 48 flight-related functions (mostly physics, not rendering)
   - Found segment 0x7894 accessors (display data pointers)
   - Output: `map_object_types.json` (large, ~30KB)

### 2. Key Findings ✅

#### Drawing Function Analysis:
- **draw_from_struct**: Only 4 static xrefs
  - `explosion_visual_effect_update` (2 calls)
  - `mode_axis_state_select` (1 call)  
  - `r29_draw_from_struct_far_wrapper` (1 call)
- **graphics_line_draw_bresenham**: Only 1 static xref
  - `pos_diff_norm` (1 call)

**Interpretation**: Low xref counts indicate:
- Function pointer tables / vtables
- Command buffer-based rendering
- Dynamic dispatch at runtime
- Not all calls visible statically

#### Waypoint Label Rendering:
- Waypoint text drawn via `ui_text_render_engine` (0x128598)
- 1282-byte comprehensive text renderer
- Called from waypoint_display_helper
- Renders waypoint numbers/labels as text

#### High-Priority Functions Identified:
1. **map_view_project_pipeline** (0x3A88D) - 36 bytes
   - Name suggests main map projection entry
   
2. **map_view_entity_project** (0x47871) - 198 bytes
   - Projects entities to map view
   - Likely handles aircraft/targets
   
3. **hud_map_overlay_frame** (0x3A6B1) - 192 bytes
   - HUD map overlay rendering
   
4. **map_overlay_clip_frame** (0x3A5D2) - 223 bytes
   - Clipping logic

### 3. Documentation Created ✅

**MAP_OBJECT_RENDERING.md** (470+ lines)

Comprehensive analysis document containing:
- Object types on tactical map (confirmed + suspected)
- Waypoint rendering pipeline (complete)
- Graphics primitives inventory
- 3D projection system summary
- Rendering coordinator functions
- All keyword search results
- Next investigation priorities
- Open questions
- Investigation strategy
- Completion status breakdown

**Content Sections**:
- Executive Summary
- Object Types (6 categories)
- Waypoint Rendering Pipeline (decoded)
- Graphics Primitives (3 core functions)
- 3D Projection System (shared with all rendering)
- Rendering Coordinators (2 functions)
- Object Type Functions (categorized search results)
- Next Investigation Priorities (14 items)
- Key Insights (4 major findings)
- Open Questions (5 categories)
- Investigation Strategy (4 phases)
- Related Documentation (5 docs)
- Completion Status (25% known, 75% unknown)
- Scripts Created (4 scripts + 4 outputs)
- Next Steps (5 actionable items)

---

## Key Insights Discovered

### 1. Text-Based Symbol System Hypothesis
- No functions found with "symbol" or "icon" keywords
- Waypoint labels confirmed as text characters
- **Hypothesis**: Aircraft and threats might be drawn as text characters:
  - F = Friendly aircraft
  - E = Enemy aircraft
  - N = Neutral aircraft
  - S = SAM site
  - A = AAA position
  - @ or * for ground targets
- Uses font rendering, not sprite/bitmap system

### 2. Dynamic Dispatch Pattern
- Only 4 static xrefs to `draw_from_struct`
- Only 1 static xref to `graphics_line_draw_bresenham`
- Suggests:
  - Function pointer tables
  - Command buffer rendering
  - Type-specific renderers in vtable
  - Most calls happen dynamically

### 3. Shared 3D Pipeline
- Tactical map uses same 3D projection as HUD/cockpit/external view
- `fixed_vec3_accumulate_a` (51K+ calls/frame) handles ALL 3D
- Map objects are true 3D entities, not 2D overlays
- Camera matrix transforms world → screen coordinates

### 4. Map Projection Functions Exist
- `map_view_project_pipeline` - main entry point
- `map_view_entity_project` - projects entities (aircraft?)
- `map_overlay_clip_frame` - clipping logic
- These are NEXT investigation targets

---

## What We Know vs. Don't Know

### Known (25%):
✅ Waypoint rendering (data → 3D → text)  
✅ 3D projection math (fixed_vec3_accumulate_a)  
✅ Text rendering system (ui_text_render_engine)  
✅ Graphics primitives (line, draw_from_struct)  
✅ Core coordinators (tactical_screen_coordinator, etc.)  
✅ Display data structures (pointers at segment 0x7894)  

### Unknown (75%):
❌ Aircraft position rendering  
❌ Threat symbol rendering (SAM, AAA)  
❌ Flight path line drawing dispatch  
❌ Symbol table / character mappings  
❌ Object type enumeration  
❌ Zoom mechanism  
❌ Map entity data structures  
❌ Color assignment system  
❌ Clipping and culling logic  

---

## Next Investigation Steps

### Phase 1: Map Projection Functions (HIGH PRIORITY)
1. Export `map_view_project_pipeline` (0x3A88D)
2. Export `map_view_entity_project` (0x47871)
3. Analyze relationship and entity types handled
4. Determine if this handles aircraft rendering

### Phase 2: Overlay Rendering
1. Analyze `hud_map_overlay_frame` (0x3A6B1)
2. Analyze `map_overlay_clip_frame` (0x3A5D2)
3. Understand frame composition

### Phase 3: Symbol System
1. Search for character/color tables
2. Find symbol-to-character mappings
3. Locate object type enumeration

### Phase 4: Runtime Debugging (USER TASK - DEFERRED)
1. Capture map state during gameplay
2. Record entity positions and types
3. Verify projection math with live data

---

## Files Created This Session

### Scripts (analysis/ida_scripts/):
1. `find_map_object_renderers.py` (48 lines)
2. `find_line_draw_callers.py` (52 lines)
3. `investigate_drawing_calls.py` (134 lines)
4. `search_map_object_types.py` (152 lines)

### Outputs (analysis/ida_scripts/):
1. `map_object_renderers.json` (850 bytes)
2. `line_draw_callers.json` (330 bytes)
3. `drawing_functions_analysis.json` (3.8 KB)
4. `map_object_types.json` (30+ KB, comprehensive)

### Documentation (docs/):
1. `MAP_OBJECT_RENDERING.md` (470+ lines, 17 KB)
   - Complete object rendering analysis
   - Search results organized
   - Investigation priorities
   - Open questions

---

## Session Statistics

- **IDA Scripts**: 4 created, all working
- **JSON Outputs**: 4 generated
- **Documentation**: 1 major document (MAP_OBJECT_RENDERING.md)
- **Functions Analyzed**: 27 map-related, 48 flight-related
- **Keywords Searched**: 16 terms
- **Lines of Documentation**: 470+
- **Time Spent**: ~1.5 hours

---

## Why Progress Stayed at 75%

This was a **survey session**, not a decode session:
- No new systems reverse engineered
- No new algorithms decoded
- No new data structures defined

**Instead we**:
- Cataloged potential target functions
- Organized search results
- Identified investigation priorities
- Prepared for next decode phase

**Progress will jump** when we decode:
- map_view_project_pipeline
- map_view_entity_project  
- Symbol table system

Estimated: +15-20% completion from those three

---

## Related Documentation

All previous tactical map work:
- `docs/3D_PROJECTION_MATH_DECODED.md` - 3D projection complete
- `docs/TACTICAL_MAP_DISPLAY_RESEARCH.md` - Initial waypoint research
- `docs/TACTICAL_MAP_BREAKTHROUGH.md` - 3D discovery
- `docs/FIXED_POINT_FORMAT_DECODED.md` - Custom fixed-point
- `docs/SESSION_TACTICAL_MAP_PROGRESS.md` - Waypoint session
- `docs/SESSION_FINAL_SUMMARY.md` - 75% completion summary
- `docs/architecture/rendering.md` - Overall rendering architecture

New this session:
- `docs/MAP_OBJECT_RENDERING.md` - **Object rendering survey** ⭐

---

## Blockers / Open Items

### Blocked (User Action Needed):
- Runtime debugging deferred (user will do later tonight)
- Need live map state captures
- Need active matrix values during gameplay

### Not Blocked (Can Continue):
- Static analysis of map projection functions ✅
- Export and analyze identified functions ✅
- Search for symbol tables ✅
- Analyze overlay rendering ✅

**Recommendation**: Continue with Phase 1 (map projection functions) in next session

---

## Session Conclusion

Successfully completed reconnaissance of map object rendering system. Identified 27 high-value functions for investigation. Created comprehensive documentation organizing all findings. Ready to proceed with targeted analysis of map projection and entity rendering functions.

**User Decision Point**: Continue investigating map_view_project_pipeline and map_view_entity_project, or switch to different aspect of Falcon 3.0?

---

**Session End**: 2026-11-15 03:45 UTC
