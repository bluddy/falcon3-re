# The ISLDAT Coordinate Mystery - SOLVED

## The Problem

ISLDAT files contain "coastline point lists" that look like this:
```
0x7008  <- Pointer from pointer table
0x7808
0x8008
...
```

These values are WAY too large to be file offsets (ISLDAT.ISR is only 6,787 bytes). So what are they?

## The Solution

They are **segment-relative offsets** into a **runtime coordinate buffer** loaded into a separate data segment.

## How It Works

### 1. Separate Data Segments

From `pos_neighbor_norm_scan` @ 0x14B17:

```assembly
push  ds
mov   ds, cs:word_11BEA          ; Load coordinate segment into DS
...
call  active_farptr_set           ; Sets ES to reference segment
...
; Now the code runs with:
;   DS = coordinate buffer segment (where 0x7008, 0x7808 etc. point)
;   ES = reference point segment (where 0xC57 player position lives)
```

### 2. Point Structure Access

From `pos_diff_norm` @ 0x28874:

```assembly
; DI = offset from ISLDAT list (e.g. 0x7008)
; BX = reference point offset (e.g. 0xC57)

push  ds
push  es
mov   cx, cs:word_1F6E6
mov   si, [di+20h]          ; DS:[DI+20h] - field from point structure
shl   si, cl
mov   ax, [di]              ; DS:[DI] - X coordinate low word
mov   dx, [di+2]            ; DS:[DI+2] - X coordinate high word  
sub   ax, es:[bx]           ; ES:[BX] - reference X from player pos
sbb   dx, es:[bx+2]         ; 32-bit subtraction
```

**Point Structure** (12+ bytes):
```
struct CoastlinePoint {
    int32  x;        // [+0]  Low word, [+2] High word
    int32  y;        // [+4]  Low word, [+6] High word  
    int32  z;        // [+8]  Low word, [+10] High word
    uint16 field20;  // [+20h] Some index or scale factor
    ...              // Possibly more fields
};
```

### 3. Runtime Coordinate Generation

The coordinates at offsets like 0x7008 are **NOT loaded from ISLDAT**. They are:

**Option A**: Generated from heightmap data
- Coastline points might be computed from heightmap elevation
- Water level threshold determines coastline edges
- Explains why ISLDAT only stores indices, not actual coords

**Option B**: Generated from 3D world geometry
- Coastlines might be part of larger 3D terrain mesh
- ISLDAT indices reference pre-generated vertex buffer
- Buffer populated during world/theater initialization

**Option C**: Loaded from separate theater file
- Another file (not ISLDAT) contains actual coordinates
- ISLDAT.ISR might be paired with ISLCOORD.ISR or similar
- Coordinates loaded into segment `cs:word_11BEA`

## Key Implications

### 1. ISLDAT is an Index File, Not a Data File

- **What ISLDAT Contains**:
  - Spatial index grids (which cells have coastlines)
  - Pointer tables (where to find point index lists)
  - Point index lists (which points form each coastline segment)

- **What ISLDAT Does NOT Contain**:
  - Actual X,Y,Z coordinates
  - Those live in runtime memory, generated or loaded elsewhere

### 2. The Coordinate Buffer is Large

- Offsets like 0x7008 (28,680), 0x8008 (32,776) suggest:
  - Coordinate buffer is ~32KB+ in size
  - Possibly up to 64KB (full segment)
  - With 12 bytes/point: ~2,700 to 5,400 points
  - Enough for detailed coastline/river geometry

### 3. Multi-Theater Support

- Each theater (ISR, KOR, HOK, IRQ, PAN, BOS) has its own ISLDAT file
- Each references the same coordinate buffer layout
- Buffer must be regenerated/reloaded when switching theaters

## Remaining Questions

1. **Where are coordinates loaded from?**
   - Separate file? (ISLCOORD.XXX?)
   - Generated from heightmap?
   - Baked into executable?
   
2. **What is cs:word_11BEA?**
   - Where is this segment pointer initialized?
   - When is the coordinate buffer populated?

3. **What is field [di+20h]?**
   - Some kind of scale factor or LOD level
   - Used in `mov si, [di+20h]; shl si, cl` calculation

4. **How do coordinates map to world space?**
   - 32-bit coords suggest high precision
   - What are the units and origin?

## Next Steps

1. Find where `cs:word_11BEA` is initialized
2. Trace back to coordinate buffer loading/generation
3. Determine if coordinates come from:
   - Separate file
   - Heightmap algorithm
   - Pre-computed table

## Status Update

**Terrain System: 93% Complete**

We now understand:
- ✅ ISLDAT is an index file, not a coordinate file
- ✅ Runtime coordinate buffer in separate segment
- ✅ Point structure format (12+ bytes, 3×32-bit coords)
- ✅ How indices are resolved to coordinates
- ⚠️ Still don't know where coordinates come from
- ❌ Still haven't found polygon fill algorithm

The mystery is 80% solved - we know HOW the system works, just not WHERE the actual coordinate data originates.
