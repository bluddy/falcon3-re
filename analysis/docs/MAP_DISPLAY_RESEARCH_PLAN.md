# Map Display Code Research Plan
*Falcon 3.0 Tactical Display Analysis*

**Date:** 2024  
**Status:** Planning Phase  
**Previous Achievement:** Mission Editor 99% complete

---

## Research Objectives

### Primary Goals

1. **Understand map rendering pipeline**
   - How waypoints are drawn
   - How flights are displayed
   - Coordinate transformation (world → screen)
   - Zoom/pan mechanics

2. **Identify display functions**
   - Map initialization
   - Coordinate conversion
   - Entity rendering (waypoints, flights, targets)
   - UI overlay rendering

3. **Map data structures**
   - Viewport state
   - Camera/view matrix
   - Display lists
   - Tile/terrain data

4. **User interaction**
   - Mouse click handling on map
   - Drag/pan operations
   - Zoom controls
   - Entity selection

---

## What We Already Know

### Related Functions (From Mission Editor Analysis)

| Function | Address | Purpose | Relevance |
|----------|---------|---------|-----------|
| waypoint_display_processor | 0x1A0F10 | Waypoint rendering | ✅ High |
| waypoint_coordinate_processor | 0x1A2441 | Coord conversion | ✅ Very High |
| waypoint_display_helper | 0x1A163A | Display helper | ✅ High |
| tactical_screen_coordinator | 0x12DB6A | Screen coordination | ✅ Very High |

### Data We Can Trace

**From mission editor:**
- Waypoint array @ 0x4FC2:0x168
- FlightRecord array @ dword_79BEC
- Waypoint coordinates (X, Y as uint16_t)
- Flight-waypoint linkage

**Questions to answer:**
- How are coordinates scaled for display?
- What's the screen resolution?
- How is zoom implemented?
- Where is the viewport center stored?

---

## Search Strategy

### Phase 1: String Discovery (1 hour)

**Search for display-related strings:**
```
- "MAP", "TACTICAL", "DISPLAY"
- "ZOOM", "PAN", "VIEW"
- "NORTH", "SOUTH", "EAST", "WEST"
- "SCALE", "GRID", "COORDINATE"
- "CURSOR", "SELECT", "CLICK"
```

**Expected findings:**
- UI menu strings
- Debug messages
- Coordinate system labels

### Phase 2: Graphics Function Discovery (2 hours)

**Look for:**
- VGA/EGA graphics calls (INT 10h)
- Pixel plotting functions
- Line drawing (Bresenham?)
- Circle drawing (waypoint markers)
- Text rendering (labels)

**Pattern search:**
```asm
; Typical pixel plot
mov     ax, 0A000h      ; VGA segment
mov     es, ax
mov     di, offset      ; Screen offset
mov     byte ptr es:[di], color
```

### Phase 3: Coordinate Transformation (2 hours)

**Track data flow:**
```
Waypoint.x_coord (uint16_t, world space)
         ↓
    [Transformation]
         ↓
Screen X pixel (0-319 or 0-639)
```

**Look for:**
- Multiplication/division for scaling
- Addition/subtraction for viewport offset
- Clipping against screen bounds

### Phase 4: Tactical Screen Analysis (3 hours)

**Focus on:** `tactical_screen_coordinator` @ 0x12DB6A

**Analyze:**
- Function calls (what does it coordinate?)
- Screen update frequency
- Entity iteration loops
- Rendering order

---

## Known Overlays to Investigate

### R57 - Likely Contains Map Code

From previous analysis, R57 has waypoint display functions:
- waypoint_display_processor @ 0x1A0F10 (R63 segment)
- waypoint_coordinate_processor @ 0x1A2441 (R63 segment)

**Note:** R63_569Fs segment confirmed

### R29 - Tactical Coordinator

- tactical_screen_coordinator @ 0x12DB6A (R29 segment)

### R54/R55 - Mission Display

From string analysis:
- "ALLIED WAYPOINTS" referenced in overlay_r54_ui_coordinator

---

## Expected Discoveries

### Graphics Primitives

**Likely to find:**
```c
void plot_pixel(int x, int y, uint8_t color);
void draw_line(int x1, int y1, int x2, int y2, uint8_t color);
void draw_circle(int x, int y, int radius, uint8_t color);
void draw_text(int x, int y, const char* text, uint8_t color);
```

### Coordinate Conversion

**Expected algorithm:**
```c
typedef struct {
    int16_t view_center_x;    // World coordinates
    int16_t view_center_y;
    uint16_t zoom_level;      // Scale factor
    uint16_t screen_width;    // Pixels
    uint16_t screen_height;
} Viewport;

void world_to_screen(Viewport* vp, 
                     uint16_t world_x, uint16_t world_y,
                     int* screen_x, int* screen_y) {
    // Translate to viewport center
    int rel_x = world_x - vp->view_center_x;
    int rel_y = world_y - vp->view_center_y;
    
    // Scale by zoom
    rel_x = (rel_x * vp->zoom_level) / 256;
    rel_y = (rel_y * vp->zoom_level) / 256;
    
    // Translate to screen center
    *screen_x = rel_x + vp->screen_width / 2;
    *screen_y = rel_y + vp->screen_height / 2;
}
```

### Entity Rendering Loop

**Expected pattern:**
```c
void render_tactical_map(Mission* mission) {
    // Clear screen or draw background
    clear_screen();
    
    // Draw terrain/grid
    draw_terrain_grid();
    
    // Draw waypoints
    for (int i = 0; i < mission->waypoint_count; i++) {
        Waypoint* wp = &mission->waypoints[i];
        int sx, sy;
        world_to_screen(&viewport, wp->x_coord, wp->y_coord, &sx, &sy);
        
        // Draw waypoint marker
        draw_circle(sx, sy, 3, COLOR_WAYPOINT);
        
        // Draw waypoint number
        char label[4];
        sprintf(label, "%d", i + 1);
        draw_text(sx + 5, sy - 3, label, COLOR_TEXT);
    }
    
    // Draw flights
    for (int i = 0; i < mission->flight_count; i++) {
        FlightRecord* flight = &mission->flights[i];
        // Get waypoint for flight position
        Waypoint* wp = &mission->waypoints[flight->waypoint_index];
        int sx, sy;
        world_to_screen(&viewport, wp->x_coord, wp->y_coord, &sx, &sy);
        
        // Draw flight icon
        draw_flight_icon(sx, sy, flight->aircraft_count);
    }
    
    // Draw connections (waypoint lines)
    // Draw UI overlay (scale, compass, labels)
}
```

---

## IDA Search Plan

### Script 1: Find Graphics Functions

```python
# Search for:
# - INT 10h (BIOS video)
# - 0xA000 segment (VGA memory)
# - Pixel plot patterns
# - Line drawing loops
```

### Script 2: Find Coordinate Math

```python
# Search for:
# - Multiplication by screen dimensions
# - Division for scaling
# - Addition/subtraction for offset
# - Clipping (cmp with screen bounds)
```

### Script 3: Analyze Display Functions

```python
# Disassemble and analyze:
# - waypoint_coordinate_processor (0x1A2441)
# - tactical_screen_coordinator (0x12DB6A)
# - waypoint_display_processor (0x1A0F10)
```

---

## Success Criteria

### Minimum Goals (80% understanding)

- ✅ Identify main rendering loop
- ✅ Find world-to-screen conversion
- ✅ Locate waypoint drawing code
- ✅ Understand coordinate system

### Stretch Goals (100% understanding)

- ✅ Zoom/pan implementation
- ✅ Mouse click handling
- ✅ All graphics primitives
- ✅ Viewport data structure
- ✅ Terrain/background rendering

---

## Estimated Effort

| Phase | Hours | Priority |
|-------|-------|----------|
| String discovery | 1 | High |
| Graphics functions | 2 | High |
| Coordinate transform | 2 | Critical |
| Tactical screen analysis | 3 | High |
| Mouse/input handling | 2 | Medium |
| Documentation | 2 | High |
| **Total** | **12** | |

**Timeline:** 2-3 sessions

---

## Related Research Questions

### How does map relate to 3D view?

**Hypothesis:** Same coordinate system, different projection
- Tactical map: Top-down 2D projection
- 3D view: Perspective projection
- Both use world coordinates from mission data

### How are targets displayed?

**Expected:** Different icon types
- Enemy aircraft (red)
- Allied aircraft (blue)
- Ground targets (special symbols)
- SAM sites (threat rings?)

### How detailed is the map?

**Possibilities:**
1. **Simple:** Just waypoints and flights
2. **Medium:** + terrain features, cities
3. **Complex:** + elevation contours, detailed terrain

---

## Connection to Mission Editor

**The tactical map IS the mission editor display!**

When we found:
- mission_editor_main_loop @ 0x18BC28
- waypoint display functions in R63

We were already looking at map code! The mission editor IS a tactical map with editing capabilities.

**This means:**
- We already know 50% of the map display
- waypoint_coordinate_processor converts coords
- waypoint_display_processor renders them
- Just need to understand the graphics layer beneath

---

## First Steps

### 1. Disassemble waypoint_coordinate_processor (0x1A2441)

This function had **8 waypoint accesses** - it clearly converts world coordinates to screen coordinates.

### 2. Trace coordinate flow

```
Waypoint.x_coord → waypoint_coordinate_processor → ??? → Screen pixel
```

### 3. Find graphics primitives

What does waypoint_display_processor call to actually draw pixels?

### 4. Locate viewport structure

Where is zoom level stored? View center? Screen resolution?

---

## Expected Challenges

### 1. Overlay Complexity

Map code likely spread across multiple overlays (R54, R55, R57, R63)

**Solution:** Focus on one overlay at a time, trace calls

### 2. Graphics Abstraction

May have multiple layers:
- High-level: draw_waypoint()
- Mid-level: draw_circle()
- Low-level: plot_pixel()

**Solution:** Start high, work down

### 3. Coordinate System

Multiple coordinate spaces:
- World (65535 × 65535)
- Screen (320×200 or 640×480)
- Viewport (scrollable)

**Solution:** Document each transformation

---

## Documentation Plan

### Documents to Create

1. **MAP_DISPLAY_ANALYSIS.md** - Main findings
2. **COORDINATE_SYSTEMS.md** - Coordinate spaces and transforms
3. **GRAPHICS_PRIMITIVES.md** - Low-level drawing functions
4. **TACTICAL_DISPLAY_GUIDE.md** - High-level overview

### Updates to Existing Docs

- Add map display section to mission editor docs
- Update function list with graphics functions
- Add viewport structure to structures.yaml

---

## Let's Begin!

**Starting point:** Disassemble `waypoint_coordinate_processor` @ 0x1A2441

This function is KEY because:
- Called 8 times in mission editor
- Clearly does coordinate conversion
- In R63 segment with other display code

**Expected to find:**
- World coordinate input (waypoint X, Y)
- Screen coordinate output
- Scaling/offset math
- Viewport references

Ready to dive in! 🗺️

---

*Map Display Research Plan v1.0*  
*Building on Mission Editor 99% completion*  
*Target: Tactical map display 80-100% understanding*
