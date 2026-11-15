# PEOPLE.DAT Investigation Status

**Date**: 2026-11-11  
**Status**: ❌ Format not yet decoded - extractions unsuccessful  
**Priority**: Need code analysis to understand format  

---

## What We Know

### File Structure
- **40 pilot face images** stored in PEOPLE.DAT
- **Index file** (PEOPLE.IDX) with standard format: (offset, size) pairs
- **File sizes**: 481-696 bytes per face
- **Three coordinate groups**:
  - (78, 160) / 0x4E, 0xA0: 8 faces
  - (78, 168) / 0x4E, 0xA8: 26 faces  
  - (58, 176) / 0x3A, 0xB0: 6 faces

### Header Format (6 bytes)
```
0x0000: Magic = 0x0400 (2 bytes)
0x0002: X coordinate = screen position (2 bytes)
0x0004: Y coordinate = screen position (2 bytes)
```

Coordinates are screen positions where faces should be drawn, NOT image dimensions.

---

## What We Tried

### ❌ Attempt 1: Uncompressed VGA
- Assumed faces were raw pixel data
- **Result**: Pixellated messes with random colors
- **Why it failed**: Data is NOT uncompressed

### ❌ Attempt 2: VGA Planar Format
- Tried 4-bitplane interleaved format
- **Result**: Still pixellated messes
- **Why it failed**: Wrong interpretation or dimensions

### ❌ Attempt 3: RLE Decompression
- Applied the RLE decompressor at 0x88460
- **Result**: Produces almost no data (0-122 bytes)
- **Why it failed**: Either wrong decompressor or data isn't RLE

---

## Data Analysis

### Statistical Evidence

**Byte distribution analysis** of Face 0 pixel data (660 bytes):
- **Adjacent identical bytes**: 0.6% (extremely low)
- **Unique values**: 232 out of 660 bytes (35%)
- **Most common byte**: Appears only 9 times (1.4%)
- **Distribution**: Almost uniform/random

**This suggests**:
- Data is **heavily compressed** or encoded
- NOT simple uncompressed pixels (would have 5-20% adjacent matches)
- NOT RLE (wrong decompression results)
- Possibly **bit-packed, delta-encoded, or custom format**

### Common Prefixes

Faces within same coordinate group share common data:
- Group (78,160): **60-byte common prefix**
- Group (78,168): **116-byte common prefix**
- Group (58,176): **17-byte common prefix**

This common data might be:
- Palette data
- Base template image
- Decompression metadata
- Background/frame

---

## Next Steps

### Required: Find Display Code

To properly extract these faces, we MUST find the game code that:
1. **Loads PEOPLE.DAT** - Find file I/O calls
2. **Decodes the data** - Find the decompression/decoding routine
3. **Renders to screen** - Find VGA blit at coordinates (78,160) etc.

### Where to Look

**Squadron/Roster Screens**:
- `squad_campaign_file_loader` (0x06a651) - 46 references
- Squadron management UI functions
- Pilot roster display code

**File Loading**:
- `idx_dat_loader` (0x1297F0) - Generic .IDX/.DAT loader
- Operation dispatch system (ops 6, 8, 0xA)
- File I/O wrappers

**Screen Rendering**:
- Search for constants 0x4E, 0xA0, 0xA8 (screen coordinates)
- VGA blit functions at specific positions
- Face/portrait rendering routines

---

## Hypotheses

### Hypothesis 1: Custom Compression
- Faces use proprietary compression optimized for photos
- Not RLE (doesn't work well for photos anyway)
- Possibly: Delta encoding, LZ-variant, or bit-packing

### Hypothesis 2: Palette + Indices
- Common prefix = shared palette (60-116 bytes for ~15-30 colors)
- Remaining data = palette indices for pixels
- Would explain high "unique value" count

### Hypothesis 3: Planar + Metadata
- Data is VGA planar but with additional encoding
- Common prefix = rendering metadata
- Need to understand exact unpacking routine

---

## Tools Needed

1. **IDA script** to find PEOPLE.DAT file opens
2. **Trace execution** when viewing pilot roster
3. **Identify decompression** routine (not the RLE one)
4. **Extract rendering** logic to understand format

---

## Comparison: What DOES Work

For reference, we successfully extracted:
- ✅ **Full-screen VGA images** (320×200, uncompressed, 4-byte header)
- ✅ **Button graphics** (67 buttons, uncompressed, size table header)

Both of these were **uncompressed** and had **clear dimension indicators**.

PEOPLE.DAT is fundamentally different - it's **compressed/encoded** and requires code analysis to decode.

---

## Recommendation

**Defer PEOPLE.DAT extraction** until we:
1. Complete other graphics extraction (buttons ✓, fonts pending)
2. Build better code tracing tools
3. Have time for deep dive into squadron screen rendering

The buttons are perfect and ready to use. Fonts and menu graphics are the next logical target since they use the RLE decompressor we already found.

---

**Status**: Investigation paused - need code analysis  
**Confidence**: LOW (all extraction attempts failed)  
**Files**: Multiple test extractions in `graphics/faces*/` - all incorrect

