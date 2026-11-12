# DGROUP:0x4287 - Camera/View State Structure

**Address**: DGROUP base + 0x4287 (17,031 bytes)  
**Usage**: Passed to view_projection via DS:DI  
**Loaded by**: sub_256A3 (view_projection_wrapper)  
**Status**: Partially analyzed, structure layout unknown

---

## Overview

This is THE critical data structure for rendering. Every frame, sub_256A3 loads this address into DS:DI and passes it to view_projection, which uses it to transform the 3D world to 2D screen coordinates.

---

## How It's Used

### Loading Sequence (sub_256A3)

```assembly
sub_256A3:
  push ds                ; Save current DS
  mov di, 7B0Eh          ; DGROUP selector
  mov ds, di             ; Load DGROUP into DS
  mov di, 4287h          ; Load offset 0x4287 into DI
  push cs                ; Prepare for far return
  call 0x20BDB           ; Call view_projection
  pop ds                 ; Restore DS
  retf                   ; Far return
```

**Result**: DS:DI points to DGROUP:0x4287 when view_projection executes.

### Access Pattern

```
game_frame_pipeline_step (frame N)
  ↓
sub_256A3 loads DS:DI = DGROUP:0x4287
  ↓
view_projection receives DS:DI
  ↓
  Reads camera position, rotation, FOV, etc.
  ↓
  Transforms all 3D objects based on this state
  ↓
  Returns
  ↓
Frame N rendering complete
```

**Key insight**: This structure defines "where the camera is looking" for the entire frame.

---

## What We Know

### From Finding 207
- **Offset**: 0x4287 = 17,031 bytes into DGROUP
- **Accessed by**: sub_256A3 (10,222 calls in traces)
- **Purpose**: Camera/view state for rendering

### From sub_256A3 Analysis
- **Loaded via**: DS:DI register pair
- **Passed to**: view_projection (0x20BDB)
- **Scope**: Used throughout rendering pipeline

### From Architecture Understanding
- **Size**: Unknown (likely 16-64 bytes)
- **Type**: Structure (not simple value)
- **Contents**: Camera/view transformation data

---

## Likely Structure Layout (Hypothesis)

### Based on typical 3D camera systems:

```c
struct camera_view_state {
    // Position (6 bytes)
    int16_t world_x;        // +0x00: Camera X position
    int16_t world_y;        // +0x02: Camera Y position  
    int16_t world_z;        // +0x04: Camera Z (altitude)
    
    // Orientation (6 bytes)
    int16_t pitch;          // +0x06: Look up/down angle
    int16_t yaw;            // +0x08: Look left/right angle
    int16_t roll;           // +0x0A: Bank angle
    
    // View Parameters (8 bytes)
    int16_t fov;            // +0x0C: Field of view
    int16_t aspect_ratio;   // +0x0E: Screen aspect
    int16_t near_plane;     // +0x10: Near clipping distance
    int16_t far_plane;      // +0x12: Far clipping distance
    
    // Transformation Matrix (optional, 18 bytes)
    int16_t matrix[3][3];   // +0x14: Rotation matrix
    
    // Total: 20-38 bytes minimum
};
```

### Alternative: Pre-computed Matrix

```c
struct view_matrix {
    // 4x4 transformation matrix
    int16_t m[4][4];        // 32 bytes
    
    // Or 3x3 with translation
    int16_t rotation[3][3]; // 18 bytes
    int16_t translation[3]; // 6 bytes
    
    // View parameters
    int16_t near_plane;     // 2 bytes
    int16_t far_plane;      // 2 bytes
    
    // Total: 28-32 bytes
};
```

---

## Evidence for Structure Size

### Access Pattern Analysis Needed

To determine actual size, we need:

1. **IDA xref analysis** - Find all functions accessing DGROUP:0x4287
2. **Offset detection** - Look for `[di+X]` patterns (X = field offset)
3. **Range analysis** - Find highest offset accessed
4. **Boundary check** - Check what's at 0x4287 + size

### Known Accessors

**Primary**:
- sub_256A3 - Loads base address
- view_projection - Uses for transformation

**Possible**:
- fixed_vec3_transform_es - May read rotation matrix
- Camera update functions - May write position/orientation
- Input handling - May update based on joystick/keyboard

---

## Verification Plan

### Step 1: Find All Xrefs (IDA)
```python
# In IDA Python
dgroup_base = idc.get_segm_start(idc.get_segm_by_name("DGROUP"))
target = dgroup_base + 0x4287
xrefs = list(idautils.XrefsTo(target, 0))
print(f"Found {len(xrefs)} xrefs")
```

### Step 2: Detect Field Accesses
```python
# Look for offset patterns
for xref in xrefs:
    disasm = idc.GetDisasm(xref.frm)
    # Check for [di+offset], [ds:4287+offset], etc.
```

### Step 3: Map Structure Fields
```python
# Build offset map
offsets = {}
for each access:
    extract offset
    determine size (byte/word/dword)
    identify read vs write
```

### Step 4: Document Layout
```c
// Final structure based on evidence
struct camera_view_state {
    type1 field1;  // +0x00: description
    type2 field2;  // +0x04: description
    // ...
};
```

---

## Related Structures

### Nearby DGROUP Offsets

Likely related camera/view data nearby:

- **0x4200-0x4287**: Previous structures (scan for names)
- **0x4287-0x4300**: This structure + padding
- **0x4300+**: Next structures

### Other View-Related Data

May be referenced together:
- View frustum planes
- Projection matrix cache
- Screen dimensions
- Viewport bounds

---

## Importance

### Why This Matters

1. **Rendering Core**: Every frame depends on this
2. **Camera System**: Defines player viewpoint
3. **Transformation**: Basis for all 3D math
4. **Performance**: Hot path (10K+ accesses)

### What We Can Learn

- Camera update frequency
- Coordinate system (left/right handed)
- Fixed-point precision
- Field of view range
- Clipping plane values

---

## Next Steps

### Immediate (Blocked by IDA automation issues)
1. ⬜ Run IDA xref analysis
2. ⬜ Detect field offsets
3. ⬜ Determine structure size
4. ⬜ Map all fields

### Alternative Approaches
1. **Runtime tracing**: Capture memory at DGROUP:0x4287 during gameplay
2. **Disassembly**: Manual inspection of view_projection code
3. **Pattern matching**: Look for similar structures in other games
4. **Reverse from math**: Work backward from transformation equations

### Workaround for IDA Issues
1. Use simpler IDA scripts (single-purpose, quick exit)
2. Extract data incrementally
3. Manual verification in IDA GUI
4. Document findings as they come

---

## Current Status

**Known**:
- ✅ Location: DGROUP:0x4287
- ✅ Purpose: Camera/view state
- ✅ Loaded by: sub_256A3
- ✅ Used by: view_projection
- ✅ Critical for rendering

**Unknown**:
- ❌ Structure size
- ❌ Field layout
- ❌ Field types (int16/int32)
- ❌ Coordinate system
- ❌ Update frequency

**Next**: Manual IDA inspection or runtime tracing to fill gaps.

---

## Files
- dgroup_4287_analysis.json - Old Finding 207 data
- sub_256A3_manual_analysis.md - Wrapper function analysis  
- this file - Structure specification (in progress)

---

**Status**: Structure location and purpose identified. Layout analysis blocked by IDA automation issues. Manual verification needed.
