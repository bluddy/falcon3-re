# view_projection Analysis

**Function:** view_projection (sub_20BDB)  
**Location:** seg020:151B (linear 0x20BDB)  
**Size:** 1,076 bytes  
**Type:** Far call, resident (not overlay)

## Overview

`view_projection` is a significant graphics function that appears to handle 3D-to-2D projection or view transformations. Called by at least 3 functions, it accesses multiple DGROUP data locations and calls into math/graphics helper functions.

## Basic Properties

```
Linear Address: 0x20BDB
Segment:Offset: seg020:151B
Size: 1,076 bytes (0x434)
Far call: Yes
Overlay: No (resident in seg020)
```

## Call Graph

### Callers (3 known)

1. **sub_256A3** (seg020:5FE3, 0x256A3)
   - Accesses DGROUP:0x4287 before calling
   - 15 bytes, very small wrapper
   - Calls view_projection at offset +0x0A

2. **sub_27079** (seg020:79B9, 0x27079)  
   - 103 bytes
   - Calls view_projection at offset +0x53
   - Similar prologue to sub_270E0

3. **sub_270E0** (seg020:7A20, 0x270E0)
   - 93 bytes
   - Calls view_projection at offset +0x4F
   - Nearly identical first 32 bytes to sub_27079

**Pattern:** sub_27079 and sub_270E0 have very similar code (likely variants or wrappers)

### Callees (16 internal calls)

view_projection makes 16 calls to other functions:

**seg015 calls (6):**
- seg015:0C65 (0x1CC57)
- seg015:0C7A (0x1CC6C)
- seg015:0CDB (0x1CCCD)
- seg015:0CF0 (0x1CCE2)
- seg015:0D51 (0x1CD43)
- seg015:0D66 (0x1CD58)

**seg017 calls (3):**
- seg017:021C (0x1D8B2)
- seg017:01E3 (0x1D879)
- seg017:01FE (0x1D894)

**seg020 calls (1):**
- seg020:1A2F (0x210EF)

**Implication:** seg015 and seg017 likely contain math libraries (trigonometry, fixed-point arithmetic, matrix operations)

## Data Access Patterns

### DGROUP Accesses (15 identified)

CS-segment overrides accessing data:
```
+0x0000: [0x005C] - Store at start
+0x0005: [0x005E] - Store 
+0x000B: [0x0026] - Load
+0x0095: [0x0032] - Store
+0x010B: [0x002E] - Store
+0x0181: [0x0030] - Store
... (9 more)
```

**Note:** These may include:
- Input parameters (viewpoint, angles)
- Output buffers (projected coordinates)
- Transformation matrices
- Graphics state

### Connection to DGROUP:0x4287

**Known:** sub_256A3 accesses DGROUP:0x4287 before calling view_projection.

**Bytecode of sub_256A3:**
```
1E BF 0E 7B 8E DF BF 87 42 0E E8 2B B5 1F CB
```

Disassembly likely:
```assembly
push ds              ; 1E
mov  di, 0x7B0E      ; BF 0E 7B
mov  ds, di          ; 8E DF (or setup DGROUP)
mov  di, 0x4287      ; BF 87 42  ← ACCESS TO 0x4287!
push cs              ; 0E
call view_projection ; E8 2B B5  (rel -19157)
retf                 ; 1F CB
```

**Hypothesis:** DGROUP:0x4287 is a pointer or structure passed to view_projection as a parameter (via DI register).

## Function Structure Analysis

### First 64 bytes

```
0000: 2E 8C 06 5C 00  - CS: mov [005C], es (save ES)
0005: 2E 89 1E 5E 00  - CS: mov [005E], bx (save BX)
000A: 06              - push es
000B: 2E 8B 0E 26 00  - CS: mov cx, [0026] (load parameter?)
0010: 8B 75 20        - mov si, [di+20h]  ← ACCESS [DI+0x20]
0013: F7 45 24 80 00  - test word [di+24h], 0080h
0018: 74 03           - jz short +3
001A: E9 6C 01        - jmp +0x16C
001D: 0B F6           - or si, si
001F: 78 03           - js short +3  
0021: E9 65 01        - jmp +0x165
0024: F7 DE           - neg si
0026: 8B 05           - mov ax, [di]      ← ACCESS [DI+0]
0028: 8B 55 02        - mov dx, [di+2]    ← ACCESS [DI+2]
002B: 26 2B 07        - ES: sub ax, [bx]
002E: 26 1B 57 02     - ES: sbb dx, [bx+2]
0032: D1 E0           - shl ax, 1
0034: D1 D2           - rcl dx, 1
... (multiply/shift operations)
```

### Structure Access Pattern

**DI register appears to point to a structure:**
```c
struct ViewData {
    int16 field_00;      // [di+0]  - X coordinate?
    int16 field_02;      // [di+2]  - Y coordinate? 
    ...
    int16 field_20;      // [di+20h] - loaded into SI
    uint16 flags_24;     // [di+24h] - tested for 0x0080
    ...
};
```

**If DGROUP:0x4287 is passed via DI**, then it's accessing a structure at that offset.

## Likely Purpose

Based on evidence:

1. **Name suggests:** View/projection transformation
2. **Structure access:** Reads coordinates at [di+0], [di+2], etc.
3. **Math calls:** Calls into seg015/seg017 (likely trig/math)
4. **Size:** 1,076 bytes suggests complex transformation logic
5. **Multiple code paths:** Tests flags ([di+24h]) and branches

**Hypothesis:** This function performs 3D-to-2D projection transformation:
- Input: 3D point structure (passed via DI from DGROUP:0x4287)
- Operations: Coordinate transformation, rotation, perspective division
- Output: 2D screen coordinates (stored back or returned)
- Uses: Flight rendering, cockpit graphics, terrain display

## Naming Suggestions

Current: `view_projection`  
Consider:
- `transform_3d_to_screen` - More specific
- `project_world_to_view` - Standard graphics terminology
- `render_point_transform` - Indicates rendering context

Current name is reasonable; no change recommended without IDA context.

## Next Steps

### 1. Disassemble in IDA ✓ (Manual step)
Navigate to seg020:151B and review full disassembly.

### 2. Analyze DGROUP:0x4287 Structure
```powershell
# Check if DGROUP:0x4287 is defined in IDA
# Look for structure definitions
# Check xrefs to nearby addresses (0x4287±32)
```

### 3. Trace Parameter Flow
- How does data get into DGROUP:0x4287?
- Is it a global structure or per-frame buffer?
- What other functions access it?

### 4. Identify Called Math Functions
Map the seg015/seg017 functions:
- Are they sin/cos?
- Fixed-point multiply/divide?
- Matrix operations?

### 5. Check Callers' Context
Analyze what sub_27079 and sub_270E0 do:
- Are they rendering different object types?
- Do they set up different parameters?

## Related Findings

- **Finding 206:** Overlay analysis confirmed 97% hot-path coverage
- **Finding 207:** RESOLVED - sub_256A3 calls view_projection (not missing function)
- **Session 56:** Discovered 57% of functions use multi-entry architecture

## Files

- `analysis/s4/analyze_view_projection.py` - Bytecode analysis script
- `analysis/s4/view_projection_analysis.md` - This document
- `analysis/s4/segment_map.json` - Address mappings

---

**Status:** Initial analysis complete  
**Priority:** HIGH - Central graphics function with 3+ callers  
**Blockers:** None - can proceed with IDA disassembly review  
**Date:** 2026-11-12
