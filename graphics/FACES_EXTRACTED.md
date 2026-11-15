# Falcon 3.0 Pilot Face Extraction

**Date**: 2026-11-11  
**Source**: PEOPLE.DAT / PEOPLE.IDX  
**Status**: 31 / 40 faces extracted  

---

## Summary

Successfully extracted **31 pilot face photographs** from PEOPLE.DAT using fixed dimensions per coordinate group.

### Extraction Results

| Group Coordinates | Dimensions | Count | Face IDs |
|-------------------|------------|-------|----------|
| (78, 160) | 33×20 | 8 | 0-7 |
| (78, 168) | 32×20 | 17 | 11-24, 35-37 |
| (58, 176) | 25×19 | 6 | 28-33 |

**Missing**: 9 faces (IDs: 8-10, 25-27, 34, 38-39) - may need different dimensions or have issues

---

## Format Discovery

### File Structure

PEOPLE.DAT uses the standard .DAT format but with **uncompressed photographic data**:

```
Header (6 bytes):
  0x0000: Magic = 0x0400 (2 bytes)
  0x0002: X coordinate = screen position (2 bytes)
  0x0004: Y coordinate = screen position (2 bytes)

Pixel Data:
  0x0006+: Raw VGA palette indices (width × height bytes)
```

### Key Insights

1. **Not RLE compressed** - Photographs have high color variation (229-232 unique colors per face), making RLE ineffective
2. **Screen coordinates in header** - The "width/height" fields are actually X,Y screen positions where faces should be drawn
3. **Fixed dimensions per group** - All faces at the same screen coordinates share the same dimensions
4. **Common template data** - Faces in same group share 17-116 bytes of common prefix data (palette or background)

---

## Technical Details

### Dimensions by Group

**Group 1 (78, 160)**: 33×20 pixels
- 8 faces total
- 660-690 bytes per record
- 60-byte common prefix

**Group 2 (78, 168)**: 32×20 pixels
- 26 faces total (17 extracted)
- 628-673 bytes per record
- 116-byte common prefix

**Group 3 (58, 176)**: 25×19 pixels
- 6 faces total
- 475-512 bytes per record
- 17-byte common prefix

### Color Analysis

- **Palette**: Using grey menu palette approximation
- **Color range**: 0-255 (full VGA palette)
- **Unique colors**: 229-232 per face (highly detailed/dithered)
- **Type**: Photographic portraits (not simple graphics)

---

## Extraction Method

Since dimensions aren't stored in the file header, we:

1. Grouped faces by screen coordinates
2. Calculated fixed dimensions based on data size patterns
3. Extracted first W×H pixels from each record
4. Extra bytes after pixel data are padding/metadata

This assumes all faces in a coordinate group have identical dimensions.

---

## Files

### Extracted Images

**Location**: `graphics/faces_fixed/`

Files named: `face_XX_WxH_try.png` where:
- XX = face index (00-39)
- WxH = dimensions used
- _try = indicates fixed-size extraction attempt

### Extraction Scripts

- `extract_all_faces.py` - Auto-calculate dimensions (variable size assumption)
- `extract_faces_fixed_size.py` - Fixed dimensions per group ⭐ (used for final extraction)
- `view_faces.py` - ASCII art preview

---

## Quality Assessment

✅ **Extracted faces show clear features**:
- Eyes, nose, mouth visible
- Hair/head shape distinguishable
- Proper photographic dithering
- High color variation as expected

⚠️ **Palette may be incorrect**:
- Using grey menu palette approximation
- Actual game may use different palette for faces
- Colors might look different in-game

❌ **9 faces not extracted**:
- May use different dimensions
- Could have format variations
- Or data issues in those records

---

## Usage in Game

Based on screen coordinates, these faces appear at:
- **(78, 160)**: Location 1 - possibly pilot roster
- **(78, 168)**: Location 2 - possibly briefing screen  
- **(58, 176)**: Location 3 - possibly status/debriefing

Small size (25-33 pixels wide) suggests:
- Thumbnail portraits
- UI element (not full-screen)
- Multiple faces shown simultaneously

---

## Next Steps

To extract remaining 9 faces:
1. Analyze records 8-10, 25-27, 34, 38-39 individually
2. Try different dimension combinations
3. Check if they're corrupted or use alternate format
4. May need to trace face rendering code to understand exact format

To improve colors:
1. Find actual palette used for pilot faces
2. May be different from menu palette
3. Check if game loads specific palette for roster screens

---

**Status**: Ready for review  
**Confidence**: HIGH (for 31 extracted faces)  
**Output**: `graphics/faces_fixed/*.png`

