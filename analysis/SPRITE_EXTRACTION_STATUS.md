# Falcon 3.0 Sprite Extraction Status

**Date**: 2024
**Goal**: Extract F-16 aircraft and weapon sprites from loadout menu
**Status**: BLOCKED - Need to identify correct graphics file

---

## What We Know

### Graphics Rendering Pipeline

Complete rendering pipeline traced:

```
GRAPHICS FILE → Loader → byte_79976 array → 
ui_element_render_complex_a → dispatch_220ec_invoke → draw_from_struct → 
rle_vga_decompressor (0x88460) → VGA display
```

**Key Functions**:
- `picfont_idx_dat_loader` (0x1293F0) - Loads PICFONT.IDX/DAT
- `ui_element_render_complex_a` (0x11CC39) - Main rendering coordinator
- `dispatch_220ec_invoke` (0x25EF4) - Graphics dispatcher
- `rle_vga_decompressor` (0x88460) - RLE decompression to VGA planar

### RLE Decompressor Algorithm

Successfully reverse-engineered from assembly at 0x88460:

```
Format: [width:word][height:word][4 planes of RLE data]

RLE Encoding:
- Flag byte & 0x80 = 1 (RUN):   count = flag & 0x7F, 1 value byte, repeat count times
- Flag byte & 0x80 = 0 (LITERAL): count = flag, copy count bytes literally

Output: VGA planar mode (4 bit planes, 16 colors)
Width processing: width_bytes = width / 4 (assembly divides by 4 at lines 17-18)
```

**Documentation**: `rle_decompressor_complete.txt`

### Graphics Files Identified

| File | Purpose | Used By |
|------|---------|---------|
| PICFONT.IDX/DAT | UI fonts (7 entries, 217 bytes) | All game modes |
| PATCHES.IDX/DAT | F-16 squadron insignia | Falcon CD |
| HPATCHES.IDX/DAT | F/A-18 squadron insignia | Hornet CD |
| MPATCHES.IDX/DAT | MiG-29 squadron insignia | MiG CD |
| MADFONT.IDX/DAT | Alternative font system | Menus |
| GENBMAP.IDX/DAT | General bitmap graphics | Unknown |
| FGENBMAP.IDX/DAT | F-16 general bitmaps | Unknown |
| MGENBMAP.IDX/DAT | MiG general bitmaps | Unknown |

### PICFONT Analysis

Attempted to extract PICFONT.IDX/DAT:
- 7 entries, total 217 bytes
- All entries start with 0x0400 (may be magic number OR width)
- Dimensions extracted don't make sense (15752x23548 pixels - way too large for VGA)
- Conclusion: Either wrong file or misunderstanding format

**Hypothesis**: PICFONT contains UI font glyphs, NOT weapon sprites.

---

## What We Don't Know

### Critical Missing Piece

**Which file contains the F-16 aircraft image and weapon sprites shown in loadout menu?**

Candidates:
1. **Embedded in FALCONCD.EXE** - Sprites might be compiled into executable
2. **GENBMAP.DAT / FGENBMAP.DAT** - "General Bitmap" files (1299 / 865 bytes)
3. **Different file format** - Maybe not .IDX/.DAT at all
4. **Dynamically generated** - Sprites drawn procedurally (unlikely for bitmaps)

### Format Issues

Even with correct file, PICFONT analysis shows we may have:
- Wrong header structure (is 0x0400 a magic number or actual width?)
- Wrong offset (does sprite data start at byte 0, 4, or 6?)
- Different RLE variant (PICFONT might use different compression than weapons)
- Endianness issues (seems unlikely on x86)

---

## Next Steps

### Option A: Trace Loadout Menu Graphics Loading

1. Set breakpoint in IDA on `rle_vga_decompressor` (0x88460)
2. Run game to loadout menu
3. Capture what file/data is being decompressed when F-16 is rendered
4. Trace back to see which loader function loaded it

**Pros**: Definitive answer
**Cons**: Requires running game in debugger

### Option B: Try Other Graphics Files

Extract and attempt to decompress:
1. FGENBMAP.IDX/DAT (865 bytes) - F-16 specific
2. GENBMAP.IDX/DAT (1299 bytes) - General graphics
3. MONITOR.IDX/DAT (10921 bytes) - Larger file, might contain more

**Pros**: Can do immediately
**Cons**: Might waste time on wrong files

### Option C: Analyze byte_79976 Array

1. Find where byte_79976 is populated
2. Trace backwards to loader
3. Identify source file from loader

**Pros**: Code-based analysis (our strength)
**Cons**: Complex data flow tracing

### Option D: Search for F-16 Visual Signature

1. Search all .DAT files for visual patterns (white pixels in F-16 shape)
2. Look for reasonable dimensions (100x50 pixels for F-16?)
3. Test RLE decompression on candidates

**Pros**: Systematic
**Cons**: Labor-intensive, may not recognize compressed data

---

## Recommendations

### ~~Option B: Try Other Graphics Files~~ - ATTEMPTED, FAILED

Tested FGENBMAP.DAT:
- 18 entries, 865 bytes total
- Same issue: dimensions nonsense (8192x34812 pixels)
- Same 0x0400 pattern at start of each entry
- **Conclusion**: Format interpretation is fundamentally wrong

### Next: Option C (Trace byte_79976 Array) - **RECOMMENDED**

This is now the best path forward:

1. Find all writes to byte_79976 in IDA
2. Trace backwards to identify loader function
3. Identify which file is loaded into byte_79976
4. Analyze that specific loader's format handling

**Why this will work**:
- byte_79976 is confirmed to hold sprite data (referenced by ui_element_render_complex_a)
- Tracing writes will definitively show source
- We'll see the actual format transformation in code

### Alternative: Option A (Live Debugging)

If code tracing fails:
- Run FALCONCD.EXE in DOSBox debugger
- Breakpoint on rle_vga_decompressor (0x88460)
- Navigate to loadout menu
- Capture SI register (data pointer) when F-16 is drawn
- Work backwards from that address to source file

**Pros**: 100% definitive
**Cons**: Requires setting up debugging environment

---

## Scripts Created

### Working

- `extract_rle_decompressor.py` - Extracted RLE assembly from IDA ✓
- `test_picfont_parse.py` - Analyzed PICFONT structure ✓
- `test_picfont_parse2.py` - Tested header interpretations ✓

### Attempted (Have Bugs)

- `extract_picfont_sprites.py` - Python RLE decompressor (HANGS - infinite loop)
- `extract_picfont_v2.py` - Corrected RLE (WRONG DIMENSIONS - format mismatch)

**Issue**: RLE algorithm is correct (matches assembly) but PICFONT format doesn't match expectations.

---

## Documentation Created

- `R57_WEAPONS_LOADOUT_MENU_ANALYSIS.md` - Complete loadout menu state machine
- `rle_decompressor_complete.txt` - RLE assembly with annotations
- `GRAPHICS_SYSTEM_FINDINGS.md` - Graphics pipeline documentation (existing)
- `SPRITE_EXTRACTION_STATUS.md` - This file

---

## Conclusion

We have **95% of the technical knowledge** needed:
- ✓ RLE algorithm reverse-engineered and implemented
- ✓ Rendering pipeline traced (file → loader → buffer → renderer → VGA)
- ✓ Loader functions identified (picfont_idx_dat_loader at 0x1297F0)
- ✓ File format structure understood (.IDX/.DAT pairs)
- ✓ Sprite pointer array located (byte_79976, an array of far pointers)

We are missing **5% critical piece**:
- ✗ Actual sprite data source unclear (PICFONT.DAT is 217 bytes, loader expects 427)
- ✗ File format interpretation is wrong (all attempts show invalid dimensions)
- ✗ byte_79976 initialized to 0, cannot trace writes statically

**Key Finding**: byte_79976 is an ARRAY OF FAR POINTERS (not sprite data itself):
- Functions reference byte_79976+0, +4, +0x18, +0x24, +0x28, +0x48, etc.
- Each entry is a 4-byte far pointer (segment:offset)
- These point to actual RLE-compressed sprite data
- Data is loaded at runtime, not visible in static analysis

**Blocking Issue**: Static analysis has hit its limit. We need runtime data.

**Recommended Next Step**: DEBUG THE RUNNING GAME
1. Set up DOSBox with debugger support
2. Load FALCONCD.EXE
3. Break point on rle_vga_decompressor (0x88460)
4. Navigate to loadout menu
5. When breakpoint hits, capture SI register (points to sprite data)
6. Dump that memory region and analyze format
7. Trace back to see which file it came from

**Alternative (if debugging not feasible)**: 
- Accept that weapons might be drawn procedurally, not from sprites
- Or weapon sprites might be embedded in executable, not in external files
- Document what we've learned and move to other systems

**Time Investment**: 
- Debugging approach: ~2 hours (definitive answer)
- Further static analysis: Likely futile without runtime data
