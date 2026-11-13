# Ready for 3D Objects System

## Terrain: COMPLETE ✅

All questions answered:

### ✅ Rivers and Roads Rendering
**Answer**: Identical to coastlines. Same Bresenham line rendering code.

**Two-pass system**:
- Pass 1 @ 0x14B60: Uses `word_11C16` (coastline grid)
- Pass 2 @ 0x14B8D: Uses `word_11C18` (river/road grid)

Both passes call the same functions:
- `pos_diff_norm` @ 0x28874 (compute delta from player)
- `line_draw_441e` @ 0x28B08 (Bresenham line drawing)

**Visual distinction**: Palette color and rendering order, NOT different algorithms.

### ✅ Architecture Documentation
- `docs/architecture/terrain.md`: Completely rewritten with ISLDAT+MAPOBJ details
- `docs/architecture/index.md`: Updated with terrain completion status
- `analysis/RIVERS_ROADS_RENDERING.md`: Detailed explanation of two-pass system

## Systems Complete (100%)

1. ✅ **HUD Rendering** - 40+ functions, text, sprites, cockpit instruments
2. ✅ **Input System** - 47 functions, dual-path joystick, demo recording, 550 cycles/frame
3. ✅ **Terrain System** - Heightmap + vectors (ISLDAT+MAPOBJ), 37,770 cycles/frame
   - Heightmap: 31×31 grid, bilinear sampling, LOD system
   - Coastlines: Spatial index (grids → pointers → coords), Bresenham lines
   - Rivers/Roads: Same algorithm, second grid (`word_11C18`)

## Next System: 3D Objects

### What We Know (From Prior Analysis)

From `docs/architecture/farobj.md`:
- **FarObj struct**: ≥210 bytes per object
- **Type system**: Entity class codes, descriptors
- **Main table**: R05_400C:0x34 - slot array
- **Batch renderer**: `farobj_batch_build_project` @ 0x13CB0

From `docs/architecture/rendering.md`:
- **3D pipeline**: `view_projection` @ 0x20BDB (282K calls/session)
- **Projection**: World → screen coordinates
- **Rendering**: Wireframe? Filled? Sprites?

### Key Questions for 3D Objects

1. **Mesh Format**:
   - How are aircraft/tank models stored?
   - Vertex arrays? Edge lists? Polygon meshes?
   - Where are model files? (*.3DO? *.MDL?)

2. **Rendering Method**:
   - Wireframe only?
   - Filled polygons?
   - Sprites for distant objects?
   - LOD system?

3. **Animation**:
   - Control surfaces (flaps, rudder, ailerons)
   - Landing gear
   - Weapon bay doors
   - How are animations encoded?

4. **Visibility & Culling**:
   - View frustum culling?
   - Backface culling?
   - Occlusion?

5. **Object Types**:
   - Player aircraft
   - Enemy aircraft
   - Ground units (tanks, SAMs, trucks)
   - Buildings
   - Weapons (missiles, bombs)
   - Effects (explosions, smoke)

### Functions to Analyze

From function list and traces:

| Address | Name | Description |
|---------|------|-------------|
| 0x13CB0 | farobj_batch_build_project | Batch object renderer (346B) |
| 0x20BDB | view_projection | 3D→2D core (1076B, 282K calls) |
| 0x2703F | farptr_table_get | Load FarObj from table (78 callers) |
| 0x26B2E | object_proj_draw_dispatch | Object projection dispatch (244B) |
| 0x165D4 | object_quad_proj_draw | Quad projection (91B) |
| 0x165F9 | object_init_flag_draw | Object init flags (52B) |

### Data Files to Find

Likely model file patterns:
- `*.3DO` - 3D object files?
- `*.MDL` - Model files?
- `OBJECTS.*` - Object database?
- Theater-specific: `MAPOBJ.XXX` (already found, contains terrain vectors)

### Approach

1. **Find model files**: Search game directory for 3D object data
2. **Analyze FarObj structure**: Complete the ≥210-byte struct
3. **Trace rendering pipeline**: From FarObj → screen pixels
4. **Decode mesh format**: Vertices, edges, faces
5. **Understand animation**: Control surface articulation
6. **Document performance**: Object rendering cycle budget

## Current Performance Budget

| System | Cycles/Frame | % of 60K | Status |
|--------|--------------|----------|--------|
| Terrain | 37,770 | 63% | ✅ Complete |
| Input | 550 | <1% | ✅ Complete |
| HUD | ~8,000 | 13% | ✅ Complete |
| **Subtotal** | **46,320** | **77%** | |
| **Remaining** | **13,680** | **23%** | For 3D objects, AI, physics |

3D object rendering must fit in remaining ~13,680 cycles, likely split:
- Object projection/transform: ~5,000 cycles (8%)
- Rasterization/drawing: ~8,000 cycles (13%)
- AI/physics: ~680 cycles (1%) - very tight!

Let's find out how they do it.

## Session Statistics

- **Terrain Start**: 88% (honest admission)
- **Terrain End**: 100% (verified with binary data)
- **Breakthroughs**: 3 (ISLDAT format, MAPOBJ discovery, rivers/roads)
- **Documents Created**: 10 markdown files
- **Python Tools**: 2 (decode_isldat_structure.py, decode_mapobj.py)
- **Architecture Files Updated**: 2 (terrain.md, index.md)
- **Time**: Extended single session
- **User Feedback**: "keep going with terrain. we're not done until we're done" ✅

**Mission accomplished. Moving to 3D objects.**
