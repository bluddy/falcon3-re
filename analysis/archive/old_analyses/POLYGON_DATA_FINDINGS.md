# Polygon/Surface Data Analysis - Initial Findings

## Summary

The 5-7KB section after lines in *OBJ.BIN files contains **multiple data types**, not just polygon definitions.

## File Layout (F-16 Example)

```
Offset       Size      Content
-----------  --------  ----------------------------------
0x0000       32 bytes  Header
0x0020       ~128      Metadata / feature descriptors
0x00A0       1,212     Vertex data (202 vertices × 6 bytes)
0x055C       560       Line data (140 lines × 4 bytes)
0x078C       546       SECTION 1: Vertex index lists
0x09AE       ~5,000    SECTION 2: Unknown coordinate-like data
0x1AAA       ???       SECTION 3: large_offset points here
```

## Section 1: Vertex Index Lists (0x078C - 0x09AE, 546 bytes)

### Structure

**Format**: Variable-length records of vertex indices, terminated by 0xFFFF

**Sample Data**:
```
5E 00  1E 00  0C 00  28 00  1E 00  0C 00  00 00  22 00 ...
  94     30     12     40     30     12      0     34  ...
```

### Characteristics

- **Length**: 273 words (546 bytes)
- **Valid indices**: 211 out of 272 (78%)
- **Contains**: Both absolute and negative (wrap-from-end) indices
- **Invalid indices**: 61 (22%) - might be flags or other data interleaved

### Example Indices (first 20)

| Index | Raw Value | Resolved | Valid? |
|-------|-----------|----------|--------|
| 0 | 94 | V94 | ✓ |
| 1 | 30 | V30 | ✓ |
| 2 | 12 | V12 | ✓ |
| 3 | 40 | V40 | ✓ |
| 4 | 30 | V30 | ✓ |
| 8 | 30 | V30 | ✓ |
| 11 | -34 (0xDE) | V168 | ✓ |
| 15 | -30 (0xE2) | V172 | ✓ |
| 20 | -23 (0xE9) | V179 | ✓ |

### Interpretation

**Likely purpose**: 
1. **Surface/polygon definitions**: Lists of vertices that form surfaces
2. **Visibility groups**: Groups of geometry for LOD or culling
3. **Rendering batches**: Vertices grouped for efficient rendering

**Questions**:
- Why 22% invalid indices?
- Is there structure within the 546 bytes?
- Are there multiple sub-records?

## Section 2: Coordinate-Like Data (0x09AE - 0x1AAA, ~5,000 bytes)

### Structure

After the vertex index section, the data changes to values in the 4,500-5,800 range.

**Sample Data** (as int16 triplets):
```
Offset   X      Y      Z      Possible Meaning
------   -----  -----  -----  ----------------
0x09AE:  4950   5786   4892   Normal vector? Precomputed coord?
0x09B4:  5298   5512   5688   Normal vector? Precomputed coord?
0x09BA:  5608   5576   5392   Normal vector? Precomputed coord?
0x09C0:  5528   5098   5408   Normal vector? Precomputed coord?
```

### Characteristics

- **Range**: Values 4,000 - 6,000 (much larger than vertex coords which are -5,000 to +5,000)
- **Quantity**: ~2,500 words = ~833 triplets
- **Not vertex indices**: Values far exceed vertex_count (202)
- **Structured**: Appears as consistent triplets

### Hypotheses

1. **Surface Normals**: Precomputed normal vectors for shading
   - Why? Wireframe doesn't need normals... unless for backface culling!
   - Range matches typical fixed-point normal encoding

2. **LOD Coordinates**: Simplified vertex positions for distant rendering
   - Different coordinate space (offset or scaled)
   - Would explain why values don't match main vertices

3. **Bounding Volumes**: Precomputed bounding boxes or spheres
   - Used for collision detection or culling
   - Organized by surface or component

4. **Transformed Coordinates**: Pre-projected or pre-rotated positions
   - For specific viewing angles (rare in 1991)
   - Unlikely but possible

## Section 3: Data at large_offset (0x1AAA)

### Header Field

```c
struct ObjectHeader {
    ...
    uint16 large_offset;  // = 0x1AAA for F-16
    ...
};
```

### Data at 0x1AAA

```
Offset   Hex Data                                      Interpretation
-------  --------------------------------------------  ----------------
0x1AAA:  40 00 60 00 70 00 50 00 FF FF 02 00 B0 04   Indices? + 0xFFFF
         64    96   112    80   -1     2   1200

0x1ABA:  B8 1A 04 00 FF FF 00 40 29 00              More indices?
         6840   4    -1   16384  41

0x1ACA:  00 00 88 FF 00 00 F1 FF 88 FF 00 00       Coordinates?
         0    -120    0    -15   -120    0

0x1ADA:  0A 00 FB FF F1 FF 64 00 05 00 F1 FF       Coordinates?
         10    -5    -15   100    5     -15
```

### Characteristics

- **Starts with valid indices**: 64, 96, 112, 80 (all < 202)
- **Has 0xFFFF terminators**: Suggests record boundaries
- **Mixed data**: Indices, coordinates, flags
- **Pointed to by header**: Must be important!

### Interpretation

**Likely purpose**: 
1. **Key feature descriptors**: Important surfaces (cockpit, wings, control surfaces)
2. **Animation metadata**: Hinges, pivot points for flaps/gear
3. **Special geometry**: High-priority surfaces that always render
4. **LOD transition table**: Which features visible at each distance

## Comparison Across Aircraft

| Aircraft | Vertices | Lines | Feature Count | Section 1 | Section 2 | large_offset |
|----------|----------|-------|---------------|-----------|-----------|--------------|
| **F-16** | 202 | 140 | 250 | 546 bytes | ~5,000 | 0x1AAA (6826) |
| **F/A-18** | 228 | 166 | 550 | ? | ~7,700 | 0x23FE (9214) |
| **MiG-29** | 216 | 154 | 250 | ? | ~5,800 | 0x1C2A (7210) |

### Observations

- **F/A-18** has 2× feature_count (550 vs 250)
- **large_offset** scales with file size (~90% through polygon section)
- **Section 2 size** correlates with complexity (F/A-18 largest)

## Most Common Word Values

### F-16 Polygon Section

| Value | Count | Possible Meaning |
|-------|-------|------------------|
| 0x0000 (0) | 130 | Null/padding |
| 0x0004 (4) | 95 | Common vertex V4 or flag |
| 0xFFFF (-1) | 57 | Record terminator |
| 0x0001 (1) | 31 | Common vertex V1 |
| 0x0003 (3) | 28 | Common vertex V3 |
| 0x01A0 (416) | 24 | Coordinate or offset? |
| 0x15B8 (5560) | 21 | Section 2 coordinate |
| 0x15A8 (5544) | 21 | Section 2 coordinate |

### Key Insights

1. **0xFFFF appears 57 times**: Suggests ~57 records or sub-structures
2. **Vertices 0, 1, 3, 4 very common**: Center or reference vertices?
3. **Value 416 (0x01A0) repeats**: Possible offset into data?

## Next Steps

### 1. Parse Section 1 Properly
- Treat as 0xFFFF-terminated records
- Count how many records
- Analyze size distribution
- Look for patterns (triangles = 3 indices, quads = 4, etc.)

### 2. Identify Section 2 Data Type
- If normals: Should be unit vectors (magnitude ~1.0 in fixed-point)
- If coordinates: Should relate to main vertex positions
- If LOD: Should be simpler/fewer than main vertices

### 3. Decode large_offset Section
- Parse mixed data (indices + coordinates + flags)
- Understand record structure
- Link back to main geometry

### 4. Find LOD System in Code
- Search for functions that access large_offset
- Trace how feature_count is used
- Find distance-based rendering code

## Questions Remaining

1. **What are the 61 invalid indices in Section 1?**
   - Interleaved flags?
   - Different record type markers?
   - Actual errors in our parsing?

2. **Why does feature_count (250/550) not match Section 1 structure?**
   - Is it counting something else?
   - Does it include Section 2 data?
   - Is it a capacity, not actual count?

3. **What is the range 4,000-6,000 in Section 2?**
   - Normals in fixed-point?
   - Offset coordinate space?
   - Precomputed values (projections, distances)?

4. **How is large_offset used in rendering?**
   - Special geometry?
   - LOD table?
   - Animation metadata?

## Status Update

**3D Objects: 85% → 88% COMPLETE**

Before:
- ❌ Polygon data (unknown, 10%)

After:
- ⚠️ Polygon data (partially understood, 7%)
  - ✓ Section 1: Vertex index lists (identified)
  - ⚠️ Section 2: Coordinate-like data (identified, not decoded)
  - ⚠️ Section 3: large_offset data (identified, not decoded)

**Remaining work**: 12% (decode sections 2 & 3, find LOD system in code)

## Tools Created

1. **analysis/decode_polygon_data.py**: Initial exploration
2. **analysis/analyze_polygon_structure.py**: Record parsing attempt
3. Manual hex dump analysis

**Next**: 
- Write proper parser for 0xFFFF-terminated records
- Test normal vector hypothesis for Section 2
- Trace large_offset usage in disassembly

---

**Analysis Date**: 2026-11-11  
**Files Analyzed**: FALCOBJ.BIN, HORNOBJ.BIN, FULCOBJ.BIN  
**Key Finding**: Polygon section has 3 distinct sub-sections, not uniform data  
**Impact**: Closer to understanding complete 3D format

