# 3D Objects System - Initial Findings

## Object Model Files Identified

| File | Size | Vertices | Lines | Aircraft |
|------|------|----------|-------|----------|
| FALCOBJ.BIN | 7,502 bytes | 202 | 140 | F-16 Fighting Falcon |
| HORNOBJ.BIN | 9,906 bytes | 228 | 166 | F/A-18 Hornet |
| FULCOBJ.BIN | 7,888 bytes | 216 | 154 | MiG-29 Fulcrum |
| FSXOBJ.BIN | 8,510 bytes | ? | ? | ? |
| JFULCOBJ.BIN | 8,096 bytes | ? | ? | Japanese MiG-29? |

Additional object databases:
- `OBJECTS` (163KB) - Main object database
- `SOBJECTS` (96KB) - Secondary objects (ground units?)

## File Format Structure

### Header (first 32 bytes)

```
Offset  Size   Field               Example (F-16)
------  -----  ------------------  --------------
0x00    word   file_size - 10      7492 (file is 7502 bytes)
0x02    word   vertex_count        202
0x04    word   line_count          140
0x06    word   unknown             0
0x08    word   large_offset        0x1AAA (6826)
0x0A    word   version?            2
0x0C    word   feature_count       250 (polygons?)
0x0E    word   unknown             0
0x10    word   unknown             22
0x12    word   unknown             28
0x14    word   constant            10000 (0x2710) - scale factor?
0x16    word   constant            -32768 (0x8000) - flag?
0x18    word   constant            153 (0x99)
0x1A    word   unknown             0
0x1C    word   terminator          -1 (0xFFFF)
0x1E    word   constant            16384 (0x4000)
```

**Observations**:
- word[0] = filesize - 10 (verified for all 3 files)
- word[1] = vertex count (202, 228, 216 for F-16, F/A-18, MiG-29)
- word[2] = line/edge count (140, 166, 154)
- word[6] = possible polygon or surface count (250, 550, 250)
- Consistent constants suggest format version markers

### Data Sections

Based on size analysis:

1. **Header** (0x00-0x20): 32 bytes, counts and metadata
2. **Feature descriptors** (~0x20-0x9C): Variable-length records
3. **Aircraft name** (~0x91-0x99): ASCII string (e.g. "F16    ", "F/A-18 ", "MIG29  ")
4. **Vertex data** (location TBD): vertex_count × 6 bytes (int16 X, Y, Z triplets)
5. **Line data** (after vertices): line_count × 4 bytes (word pairs: v1_index, v2_index)
6. **Polygon/surface data** (remaining): Feature descriptors, possibly texture coords

### Coordinate System

From sample data at offset 0x160+ (likely vertices):

```
F-16 samples:
  V0: X=     0, Y=  -200, Z=     0
  V1: X=     0, Y=     0, Z=   200
  V2: X=     0, Y=   200, Z=     0
```

Coordinates appear to be **signed 16-bit integers** in aircraft-local space:
- Range: approximately -10,000 to +10,000 units
- Scale: word[0x14] = 10,000 suggests this is the reference scale
- Axes: Standard aircraft convention (X=right, Y=up, Z=forward? TBD)

### Model Complexity

| Aircraft | Vertices | Lines | Complexity |
|----------|----------|-------|------------|
| F-16 | 202 | 140 | Medium |
| F/A-18 | 228 | 166 | Higher (twin-engine, larger) |
| MiG-29 | 216 | 154 | Medium-high |

**Rendering**: Wireframe only, NO textures (1991 technology, 386 CPU).

Lines-to-vertices ratio:
- F-16: 140/202 = 0.69
- F/A-18: 166/228 = 0.73
- MiG-29: 154/216 = 0.71

This is consistent with **wireframe mesh**: each edge connects two vertices, typical mesh has ~0.7-0.8 edges per vertex.

## Rendering Functions (From Prior Analysis)

| Address | Name | Description |
|---------|------|-------------|
| 0x13CB0 | farobj_batch_build_project | Batch object projection/rendering |
| 0x20BDB | view_projection | Core 3D→2D projection (282K calls/session) |
| 0x2703F | farptr_table_get | Load FarObj from slot table |
| 0x26B2E | object_proj_draw_dispatch | Object rendering dispatcher |
| 0x165D4 | object_quad_proj_draw | Quad projection |

## Next Steps

1. **Locate vertex data precisely**: Determine exact offset where vertices start
2. **Parse line list**: Verify edge indices reference valid vertices
3. **Understand polygon data**: If any filled polygons exist (doubtful)
4. **Analyze FarObj structure**: Complete the ≥210-byte entity structure
5. **Trace rendering pipeline**: From FarObj → model load → projection → screen
6. **LOD system**: How does distance affect model detail?
7. **Animation**: Control surfaces (flaps, gear, etc.)

## Architecture Notes

### Memory Model

**Likely approach**:
1. Model files (`*OBJ.BIN`) loaded into memory at startup or on-demand
2. Parsed into vertex arrays and edge lists
3. FarObj structure contains:
   - Pointer to model data
   - Current position/orientation (int32 X, Y, Z, angles)
   - Rendering flags (visible, LOD level, etc.)
4. Each frame:
   - Iterate FarObjs in view frustum
   - Project vertices: world → view → screen
   - Draw edges as lines via `line_draw_441e` (same as terrain!)

### Performance Budget

From terrain analysis, we have ~13,680 cycles remaining (23% of 60K frame budget).

**Estimated object rendering cost**:
- 10 visible aircraft @ 200 vertices each = 2,000 points
- Projection: ~3 cycles/vertex = 6,000 cycles
- Line drawing: ~20 cycles/line × 1,400 lines = ~28,000 cycles

**PROBLEM**: 28K cycles exceeds budget!

**Solution**:
- **LOD system**: Distant objects have fewer lines
- **Culling**: Backface culling, view frustum culling
- **Simplified models**: Probably <100 lines for distant objects
- **Sprites**: Very distant objects might be 2D sprites, not 3D

### Comparison to Terrain

| System | Vertices/Frame | Lines/Frame | Rendering Method |
|--------|----------------|-------------|------------------|
| Terrain | ~250 points | ~250 lines | Coastline/river vectors |
| Objects | ~2,000 points (est) | ~1,400 lines (est) | Aircraft/vehicle wireframes |

Objects are **8× more vertices** but same line-drawing code (`line_draw_441e`).

## Status

**3D Objects: 15% understood**

✅ File format identified (header structure)  
✅ Vertex and line counts extracted  
✅ Model files located  
✅ Rendering functions known from prior work  
⚠️ Vertex data location TBD  
⚠️ Exact format of lines/edges TBD  
❌ FarObj structure incomplete  
❌ Rendering pipeline not traced  
❌ LOD system unknown  
❌ Animation system unknown  

**Next session**: Pin down exact binary format, then trace rendering pipeline.
