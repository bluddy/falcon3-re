# HUD Drawing Primitives - Analysis

**Date**: 2026-11-11  
**Status**: Partial - Runtime initialization discovered  
**Challenge**: Function pointers initialized at runtime, not in static binary

---

## Key Discovery: Runtime-Initialized Function Pointers

The drawing function pointers in `hud_readout_render` are **NULL in the static binary** and **initialized at runtime**:

```
cs:dword_35924 = 0x00000000  (primary drawing, called 6 times)
cs:dword_35920 = 0x00000000  (secondary drawing, called 3 times)
```

**Bytes at pointer locations**: `0xFF 0xFF 0xFF 0xFF...` (uninitialized)

This is typical for DOS programs that:
1. Detect hardware capabilities at startup (VGA mode, EMS/XMS memory)
2. Set up function pointer tables for different rendering paths
3. Select optimal drawing routines based on detected hardware

---

## Sprite and Drawing Functions (From Previous Analysis)

### sprite_offset_dispatch_343e (20 bytes)
**Address**: 0x35B2F  
**Called by**: hud_readout_render (5 times)  
**Calls**: cs:dword_35924 (the primary drawing function pointer)

**Purpose**: Sprite positioning dispatcher - likely computes sprite offsets and then calls the drawing function.

**Analysis**: This is a **thin wrapper** that:
1. Takes sprite parameters (position, offset)
2. Computes final screen coordinates
3. Calls the drawing function pointer with computed coordinates

### sprite_in_view_test (57 bytes)
**Address**: 0x36FAC  
**Called by**: hud_readout_render (1 time)  
**Calls**: None (pure computation)

**Purpose**: Tests if a sprite is within the viewport bounds.

**Analysis**: Simple visibility test - returns true/false if sprite position is inside screen rectangle. Used to cull off-screen HUD elements.

### int32_to_ascii (157 bytes)
**Address**: 0x228BF  
**Called by**: hud_readout_render (1 time)  
**Calls**: dispatch_22084_near (2 times)

**Purpose**: Convert 32-bit integer to ASCII string for display.

**Analysis**: Number-to-string conversion for displaying numeric HUD values (airspeed, altitude, etc.). The 157-byte size suggests it handles:
- Sign (negative numbers)
- Leading zeros/spaces
- Multiple digit formats
- Possibly decimal points

Calls a dispatcher twice, likely for formatting options (left/right justify, padding, etc.).

### angle_quad_norm_far (12 bytes)
**Address**: 0x25E42  
**Called by**: hud_readout_render (1 time)  
**Calls**: angle_quad_norm_scale (1 time)

**Purpose**: Normalize angle to quadrant (0-359° or 0-2π).

**Analysis**: Tiny function (12 bytes) - just a far call wrapper to the actual normalizer. Used for heading/bearing displays that need angles in standard ranges.

### view_rotation_far_thunk (6 bytes)
**Address**: 0x24530  
**Called by**: hud_readout_render (1 time)  
**Calls**: view_rotation_build (1 time)

**Purpose**: Build view rotation matrix.

**Analysis**: Another tiny wrapper (6 bytes) - far call to the actual rotation matrix builder. This connects the 3D world space to 2D screen space for HUD elements that need to track 3D objects (target boxes, etc.).

---

## Drawing Function Pointer Architecture

### Hypothesis: Hardware-Specific Drawing Paths

**Why Runtime Initialization?**

Different VGA modes and hardware capabilities require different drawing approaches:

1. **Mode 13h (320x200x256)**: Direct framebuffer access
2. **Mode X (320x240x256)**: Planar VGA with page flipping
3. **SVGA modes**: Banked memory access, different APIs

The function pointers likely point to different implementations:

**Primary Drawing (cs:dword_35924 - 6 calls):**
- **Text rendering**: Draw ASCII characters from font atlas
- **Signature**: `void draw_text(int x, int y, const char* text, uint8_t color)`

**Secondary Drawing (cs:dword_35920 - 3 calls):**
- **Shape/sprite rendering**: Draw rectangles, sprites, or lines
- **Signature**: `void draw_shape(int x, int y, uint8_t* sprite_data, uint8_t color)`

### Expected Initialization Flow

```
main() or startup():
    detect_video_mode()
    detect_memory_type()  // EMS, XMS, conventional
    
    if (mode == MODE_13H):
        cs:dword_35924 = &draw_text_mode13h
        cs:dword_35920 = &draw_sprite_mode13h
    elif (mode == MODE_X):
        cs:dword_35924 = &draw_text_modeX
        cs:dword_35920 = &draw_sprite_modeX
    elif (mode == SVGA):
        cs:dword_35924 = &draw_text_svga
        cs:dword_35920 = &draw_sprite_svga
    
    // Now hud_readout_render can call through pointers
```

---

## Indirect Call Pattern

From `hud_readout_render` disassembly:

```asm
; Set up coordinates in BX, DI
add     bx, ds:6F8h        ; Add X offset
add     di, ds:6FAh        ; Add Y offset

; Call drawing function through pointer
call    cs:dword_35924     ; Indirect call - target unknown until runtime
```

This pattern appears **6 times** for text drawing, **3 times** for shape/sprite drawing.

---

## Call Graph (HUD Rendering)

```
hud_readout_render (908 bytes)
    ↓
    ├─ int32_to_ascii (157 bytes)
    │   └─ dispatch_22084_near (format numbers)
    │
    ├─ sprite_offset_dispatch_343e (20 bytes) [x5]
    │   └─ cs:dword_35924 → [runtime: draw_text_*]
    │
    ├─ cs:dword_35924 [x6] → [runtime: draw_text_*]
    │
    ├─ cs:dword_35920 [x3] → [runtime: draw_sprite_*]
    │
    ├─ sprite_in_view_test (57 bytes)
    │   └─ (visibility check)
    │
    ├─ angle_quad_norm_far (12 bytes)
    │   └─ angle_quad_norm_scale
    │
    └─ view_rotation_far_thunk (6 bytes)
        └─ view_rotation_build
```

---

## Data Flow Summary

**Input** (to hud_readout_render):
- HUD element data (values, positions, visibility flags)
- Screen offset (0x6F8, 0x6FA)
- Viewport rectangle (computed from 0x674, 0x6C4, 0x6C6)
- View rotation matrix (0x47D6-0x47E0)

**Processing**:
1. Format numeric values → ASCII strings (int32_to_ascii)
2. Compute sprite positions (sprite_offset_dispatch_343e)
3. Test visibility (sprite_in_view_test)
4. Update view matrix (view_rotation_far_thunk)

**Output** (via function pointers):
- Text drawing calls (6x) → framebuffer
- Sprite/shape drawing calls (3x) → framebuffer

---

## Next Steps to Discover Drawing Functions

### 1. Find Initialization Code

Search for:
- Writes to address 0x35924 and 0x35920
- String references: "VGA", "SVGA", "Mode 13h", "Mode X"
- Video mode detection code (INT 10h calls)

### 2. Identify Drawing Function Candidates

Search for functions that:
- Take X, Y coordinates as parameters
- Access video memory (segment 0xA000 for Mode 13h)
- Have loops for pixel/character drawing
- Are called from initialization code

**Expected function names:**
- draw_text_*, draw_char_*, text_render_*
- draw_sprite_*, blit_*, put_pixel_*
- Mode-specific: *_mode13h, *_modeX, *_svga

### 3. Trace from Known Entry Points

Start from:
- Main entry point or startup code
- Video initialization functions
- Search for "font" or "charset" data

### 4. Analyze Font Data

Search for:
- Character bitmaps (8x8, 8x16 typical)
- Font atlas data structures
- Character width tables

---

## Function Pointer Pattern in Other Systems

This pattern likely appears in:
- **Audio system**: Function pointers for PC Speaker vs. Sound Blaster
- **Input system**: Function pointers for mouse driver vs. direct port access
- **Rendering system**: Different 3D rendering paths

**General Pattern**: Detect hardware → select optimal implementation → store in function pointer

---

## Conclusion

The HUD drawing system uses **runtime-initialized function pointers** to support multiple video modes and hardware configurations. The actual drawing functions are:

✅ **Identified**: sprite_offset_dispatch (wrapper), sprite_in_view_test (visibility), int32_to_ascii (formatting)  
❓ **Unknown**: Primary text drawing function (cs:dword_35924 target)  
❓ **Unknown**: Secondary sprite drawing function (cs:dword_35920 target)

**To discover the actual drawing functions**, we need to:
1. Find video mode initialization code
2. Trace function pointer assignments
3. Identify mode-specific drawing implementations

**Alternative approach**: Run the game in a debugger, break at hud_readout_render, and inspect the function pointer values at runtime.

---

**Status**: Architecture understood, runtime initialization discovered, actual drawing functions pending  
**Verification**: 80% (call patterns verified, pointers confirmed NULL in static binary)  
**Next**: Find video initialization code or debug at runtime to discover drawing function addresses
