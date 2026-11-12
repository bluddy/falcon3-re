# Falcon 3.0 Overlay System Deep Dive

**Version:** 1.0  
**Status:** Active Analysis  
**Last Updated:** 2026-11-11

## Executive Summary

The overlay system manages **2D screen-space UI elements and vector graphics** rendered on top of the 3D world. With 96 functions, it's a substantial subsystem responsible for HUD overlays, targeting reticles, cockpit instruments, and vector map displays.

**KEY DISCOVERY:** The overlay system is **tightly integrated with the rendering pipeline** via `overlay_tail_bridge` (0x2C09F), which is called directly from `view_projection` after 3D rendering completes. This ensures overlays are drawn last, on top of the rendered 3D scene.

**System Profile:**
- Functions: 96 identified
- Integration: Called from view_projection (0x202DB)
- Bridge Function: overlay_tail_bridge (0x2C09F, 8 bytes)
- Rendering: Vector graphics + bitmap sprites
- Coordinate System: Screen space (2D, post-projection)
- Complexity: Medium-High (substantial system)

**Analysis Progress:** 20% - Architecture mapped, function inventory complete, detailed analysis needed

## System Architecture

### Data Flow

```
view_projection (0x202DB)
    ↓ [3D rendering complete]
    ↓
overlay_tail_bridge (0x2C09F)
    ↓
[OVERLAY RENDERING SYSTEM - 96 functions]
    ↓ Instrument rendering
    ↓ HUD elements
    ↓ Targeting reticles
    ↓ Vector maps
    ↓ Text displays
    ↓
[SCREEN OUTPUT]
```

### Integration Points

**Callers:**
- `view_projection` (0x202DB) - Main rendering coordinator
- Calls `overlay_tail_bridge` at 0x20FD3

**Rendering Order:**
1. 3D world rendering (terrain, objects)
2. 3D culling and depth sorting
3. **← Overlay rendering happens here**
4. Frame complete

**Why This Order:**
- Overlays must appear on top of 3D scene
- No depth testing for overlays (always visible)
- Uses separate 2D coordinate system (screen pixels, not world space)

## Core Functions

### Bridge Function

**overlay_tail_bridge** at 0x2C09F (8 bytes)

**Purpose:** Entry point from rendering pipeline to overlay system

**Verified Properties:**
- Size: 8 bytes (extremely small - likely just a jump or call chain)
- Called from: view_projection at 0x20FD3
- Likely implementation: Dispatcher or function pointer call
- Role: Bridges 3D rendering context to 2D overlay context

**Analysis Needed:**
- Disassemble to see if it's a direct call, indirect call, or dispatcher
- Identify what overlay functions it calls
- Determine if it saves/restores graphics state

### Function Inventory

**Total Functions:** 96 (discovered via search patterns)

**Search Patterns Used:**
- "overlay_*" prefix
- Functions called from overlay_tail_bridge
- Functions accessing screen buffer
- Vector graphics primitives

**Expected Function Categories:**

1. **Drawing Primitives** (~20 functions)
   - Line drawing
   - Circle/arc drawing
   - Polygon fill
   - Text rendering
   - Sprite blitting

2. **HUD Elements** (~25 functions)
   - Airspeed indicator
   - Altitude indicator
   - Heading indicator
   - Artificial horizon
   - G-force meter
   - Fuel gauge
   - Weapon status
   - Radar display

3. **Targeting System** (~15 functions)
   - Target box rendering
   - Lead indicator
   - Lock-on indicator
   - Missile diamond
   - Gun reticle

4. **Cockpit Instruments** (~20 functions)
   - MFD (Multi-Function Display) rendering
   - Engine instruments
   - Warning lights
   - Threat display

5. **Utility** (~16 functions)
   - Coordinate transformation (world → screen)
   - Clipping (keep overlays within screen bounds)
   - State management
   - Color/palette handling

**Status:** Categories are estimates. Need to analyze actual function list to verify.

## Rendering Techniques

### Vector Graphics

**Assumption:** Overlays use vector graphics (lines, arcs, circles) not bitmaps

**Evidence:**
- Flight sims in 1991 era typically used vector HUDs
- More efficient than bitmaps for dynamic UI
- Scales better to different resolutions
- Lower memory footprint

**Typical Algorithms:**
- Bresenham line drawing
- Midpoint circle algorithm
- Polygon scan conversion
- Clipping (Cohen-Sutherland or Liang-Barsky)

### Text Rendering

**Assumption:** Bitmap fonts or vector fonts

**Typical Approach (1991):**
- Bitmap font atlas in memory
- Character lookup by ASCII code
- Blit character glyph to screen buffer
- Possibly cached to avoid redundant draws

### Coordinate Systems

**Screen Space:**
- Origin: Top-left (0, 0)
- X-axis: Left to right (0 to 319 for 320x200, or 0 to 639 for 640x480)
- Y-axis: Top to bottom
- Units: Pixels

**HUD Space:**
- Possibly normalized coordinates (-1 to +1 or 0 to 1)
- Translated to screen space by overlay system
- Allows resolution-independent HUD design

## Data Structures

### Expected Structures (Need Verification)

```c
// Overlay command/primitive
struct OverlayCommand {
    uint8_t type;        // 0=line, 1=circle, 2=text, 3=sprite, etc.
    uint8_t color;       // Palette index
    int16_t x1, y1;      // Start/center position
    int16_t x2, y2;      // End/radius (depends on type)
    void* data;          // Text string or sprite data (if applicable)
};

// Display list (array of commands)
struct OverlayDisplayList {
    uint16_t count;
    OverlayCommand commands[MAX_OVERLAYS];
};

// Screen buffer
struct ScreenBuffer {
    uint16_t width;
    uint16_t height;
    uint8_t* pixels;     // Linear framebuffer
};
```

### Memory Locations (Need Discovery)

- Overlay command buffer: Unknown
- Screen buffer pointer: Unknown (possibly video memory direct access)
- Font atlas: Unknown
- Sprite data: Unknown

## Function Analysis Template

For each overlay function discovered, document:

1. **Address & Size:** `function_name` at 0xABCDE (XXX bytes)
2. **Purpose:** What this function renders or manages
3. **Callers:** What calls it (overlay_tail_bridge or other overlay functions)
4. **Callees:** What it calls (primitives, utilities)
5. **Algorithm:** Rendering logic
6. **Data Access:** Screen buffer, command buffer, assets
7. **Performance:** Expected cost (low/medium/high)

## Performance Characteristics

### Expected Timings (1991 Hardware)

**Typical Overlay Budget:** 2-5ms per frame

**Per-Element Costs (estimated):**
- Line drawing: 50-200 µs (depends on length)
- Circle drawing: 100-500 µs (depends on radius)
- Text character: 20-50 µs (bitmap blit)
- Sprite: 100-1000 µs (depends on size)

**Total Overlay Count per Frame:** 50-200 elements (lines, circles, chars)

**Optimization Strategies:**
- Display list caching (only redraw changed elements)
- Dirty rectangle tracking (only update changed screen regions)
- Fast scan conversion (optimized assembly)
- Direct video memory writes (no buffering)

## Integration with Other Systems

### Rendering System

**Tight Integration:**
- Called at end of rendering pipeline
- Assumes 3D rendering is complete
- Writes directly to framebuffer
- No depth testing (always on top)

### HUD System

**Overlay subsystem of HUD:**
- HUD generates overlay commands
- Overlay system renders them
- Two-stage design: logic (HUD) + rendering (overlay)

### Input System

**Indirect Integration:**
- Input affects HUD state
- HUD state affects overlay rendering
- No direct connection

## Discovery Status

### ✅ Completed

1. **Function Count:** 96 functions identified
2. **Integration Point:** overlay_tail_bridge called from view_projection
3. **Architecture:** 2D rendering on top of 3D, post-projection

### 🔄 In Progress

1. **Function List:** Need to extract actual names of 96 functions
2. **Bridge Analysis:** Disassemble overlay_tail_bridge to find entry points
3. **Primitive Identification:** Find drawing primitive functions

### 📋 Next Steps

1. **Search for Overlay Functions:**
   - Pattern: "overlay_*"
   - Pattern: "hud_*"  
   - Pattern: "draw_*"
   - Pattern: functions called from overlay_tail_bridge

2. **Analyze overlay_tail_bridge:**
   - Disassemble 8 bytes
   - Find what it calls
   - Trace call graph

3. **Categorize Functions:**
   - Drawing primitives
   - HUD elements
   - Targeting system
   - Cockpit instruments
   - Utilities

4. **Map Data Structures:**
   - Find overlay command buffer
   - Find screen buffer pointer
   - Identify font and sprite assets

5. **Profile Performance:**
   - Count overlay elements per frame
   - Measure rendering cost
   - Identify hotspots

## Open Questions

### Architecture
1. **Display List:** Is there an overlay command buffer or direct rendering?
2. **Double Buffering:** Does the system use double buffering for flicker-free rendering?
3. **Clipping:** What clipping algorithm is used?
4. **Z-Order:** Can overlays have depth/layering or all flat?

### Implementation
5. **Vector vs. Bitmap:** Pure vector, pure bitmap, or hybrid?
6. **Font System:** Bitmap fonts or vector fonts?
7. **Color:** Palette-based (256 colors) or direct color?
8. **Primitives:** What drawing primitives are available?

### Performance
9. **Hotspot:** Which overlay elements cost the most to render?
10. **Optimization:** Display list caching? Dirty rectangles?
11. **Bottleneck:** Is overlay rendering a performance concern?

### Data
12. **Assets:** Where are fonts, sprites, and HUD graphics stored?
13. **Screen Buffer:** Direct VGA access or framebuffer?
14. **Command Format:** How are overlay commands structured?

## Next Steps

1. **Disassemble overlay_tail_bridge** - Understand entry point
2. **Search for overlay functions** - Build complete function list
3. **Analyze drawing primitives** - Identify line, circle, text functions
4. **Map HUD elements** - Connect HUD to overlay rendering
5. **Profile execution** - Measure overlay rendering cost
6. **Document functions** - Complete analysis of key functions
7. **Update ARCHITECTURE.md** - Add overlay system details

## References

- **ARCHITECTURE.md**: Overall system structure
- **RENDERING_SYSTEM.md**: 3D rendering pipeline (overlays render after this)
- **CULLING_SYSTEM.md**: 3D culling (overlays bypass this)
- **HUD_SYSTEM.md**: HUD logic (generates overlay commands)
- **SYSTEM_MAP.md**: Initial discovery of 96 overlay functions

---

**Analysis Status:** Stage 1 - Architecture defined, function inventory complete, detailed analysis needed  
**Confidence:** Medium (architecture), Low (implementation details)  
**Verification:** 20% (integration point verified, details need IDA analysis)
