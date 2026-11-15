# RLE Decompression Investigation

**Date:** 2026-11-15  
**Status:** IN PROGRESS - Format partially decoded  
**Goal:** Reverse-engineer the RLE compression algorithm used for menu graphics

---

## Summary

Menu graphics in Falcon 3.0 are stored in .DAT files with RLE compression achieving 1-4% compression ratios. We've identified the file format structure but the exact RLE algorithm remains to be fully decoded.

---

## File Format (CONFIRMED ✓)

### Header Structure
```c
struct DataEntry {
    uint8_t  marker[2];     // Always 0x00, 0x04
    uint16_t width;         // Image width pixels (little-endian)
    uint16_t height;        // Image height pixels (little-endian)
    uint8_t  rle_data[];    // RLE compressed pixel data
};
```

### Example: PICFONT.DAT Entry 0
```
Header: 00 04 16 00 EC 01
- Marker: 0x00 0x04
- Width: 0x0016 = 22 pixels
- Height: 0x01EC = 492 pixels
- Uncompressed size: 22 × 492 = 10,824 pixels
- Compressed size: 37 bytes
- Compression ratio: 0.34% (extremely high!)
```

**Compressed data (first 20 bytes):**
```
88 3D FC 5B F0 5F 46 FF 5F FD FB 8F 5D FD 97 F5 AF 05 0B E5
```

---

## RLE Algorithm Investigation

### Hypothesis 1: Simple [count][value] RLE

**Test:** Decode as pairs of [count][value]
```
88 3D → 136 pixels of value 0x3D
FC 5B → 252 pixels of value 0x5B
F0 5F → 240 pixels of value 0x5F
...
```

**Result:** Decoded only 1,474 / 10,824 pixels = **13.6%**  
**Conclusion:** ✗ Simple [count][value] is NOT the format

### Why Simple RLE Fails

The extremely high compression ratio (0.34%) suggests the data is mostly background pixels with sparse foreground. Simple [count][value] RLE would need:
- 10,824 pixels / 255 max count = at least 43 pairs = 86 bytes
- Actual compressed size: 37 bytes

This suggests a more sophisticated algorithm.

### Hypothesis 2: Control Byte Format

Many RLE formats use a control byte to indicate run type:
```c
if (control_byte & 0x80) {
    // High bit set: RLE run
    count = control_byte & 0x7F;
    value = next_byte;
    // Fill 'count' pixels with 'value'
} else {
    // High bit clear: Literal run
    count = control_byte & 0x7F;
    // Copy next 'count' bytes literally
}
```

**Status:** NOT YET TESTED

### Hypothesis 3: Variable-Length Encoding

Could use variable-length count encoding:
- 1-byte counts for runs ≤ 127
- 2-byte counts for runs > 127
- Special escape codes for very long runs

**Status:** NOT YET TESTED

### Hypothesis 4: Bit-Packed or Palette-Indexed

Given the 0.34% ratio, the image might be:
- 1-bit or 2-bit per pixel (monochrome or 4-color)
- Palette-indexed with most pixels being index 0 (background)
- RLE compresses runs of background

**Status:** PLAUSIBLE - needs testing

---

## Code Analysis Results

### VGA Upload Function

**vga_dac_palette_upload** (0x4F271)
- Has only **4 callers** (not 11 as originally documented)
- Callers:
  1. main_game_loop_update (0x2F6D0, 1123B, score 7/10)
  2. terrain_state_reinit (0x31138, 481B, score 5/10)
  3. main_frame_update_loop (0x31319, 257B, score 5/10)
  4. mode_extent_recompute (0x322E5, 174B, score 0/10)

**None showed strong RLE decompression patterns** (no REP STOSB/MOVSB)

### Font Loader Functions

**picfont_idx_dat_loader** (0x1297F0, 187B)
- Loads PICFONT.IDX/.DAT pair
- Template pattern for all .IDX/.DAT loaders

**madfont_idx_dat_loader** (0x1397CE, 1463B)
- Loads madfont.idx/.dat font file pair
- Score: 6/10 (23 byte compares, 38 buffer writes)
- Most promising candidate

### Loader Callees Analysis

Font loaders call these functions (none are decompressors):
- `op_dispatch_far_entry` (0x22598, 30B) - Dispatch
- `pending_task_run` (0x258B2, 26B) - Task management
- `font_file_parser` (0x13142E, 243B) - Font parsing
- Various dispatch and callback functions

**Conclusion:** Decompression may be **inlined** in the loaders or done through dispatch tables

---

## Analysis Tools Created

1. **find_rle_decompressor.py**
   - Traced backward from vga_dac_palette_upload
   - Analyzed callers for RLE patterns (loops, REP STOSB, buffer writes)
   - Found 4 callers, none with strong RLE signatures

2. **trace_font_loader_callees.py**
   - Traced callees of font loaders
   - Analyzed 11 unique callees
   - None scored high for RLE decompression patterns

3. **analyze_rle_format.py**
   - Manual analysis of PICFONT.DAT
   - Tested simple [count][value] RLE hypothesis
   - Result: Only decoded 13.6% of pixels - format is more complex

---

## Key Insights

### Compression Ratio Analysis

| File | Dimensions | Uncompressed | Compressed | Ratio |
|------|-----------|--------------|------------|-------|
| PICFONT Entry 0 | 22×492 | 10,824 pixels | 37 bytes | 0.34% |
| Typical small | 8×56 | 448 pixels | 13 bytes | 2.9% |
| Typical large | 150×88 | 13,200 pixels | 164 bytes | 1.2% |

**Observations:**
1. Extremely high compression (< 4%) indicates:
   - Mostly solid color (background)
   - Sparse foreground pixels
   - Very efficient RLE or specialized format

2. Smaller images have worse compression (2.9%)
   - Less redundancy to compress
   - Overhead from headers/control bytes

3. Larger images compress better (1.2%)
   - More long runs of background
   - Amortized header overhead

### Font Images Characteristics

PICFONT dimensions suggest:
- 22 pixels wide × 492 pixels tall
- 492 / 22 ≈ 22 rows → probably **22 characters** in a single tall strip
- Each character: 22×22 pixels
- Font glyphs are mostly background (transparent/black)

This explains the 0.34% ratio - each character is perhaps 2-10 foreground pixels on a 484-pixel background!

---

## Next Steps

### Immediate

1. **Examine madfont_idx_dat_loader disassembly**
   - Open in IDA: 0x1397CE
   - Look for inline decompression loops
   - Find buffer fill operations
   - Check for bit manipulation

2. **Test control byte hypothesis**
   - Implement decoder with high-bit control
   - Run on PICFONT.DAT entry 0
   - Verify pixel count matches 10,824

3. **Analyze bit-packing**
   - Check if data is 1-bit, 2-bit, or 4-bit per pixel
   - Test palette-indexed decoding
   - Look for bit-shift operations in code

### Alternative Approaches

4. **Search for REP instructions**
   - Global search in IDA for REP STOSB/MOVSB
   - These are fast fill/copy - typical in decompressors
   - May be in a helper function we haven't traced

5. **Trace from file I/O**
   - Find DOS INT 21h file read operations
   - Follow data flow from file → buffer → decompression → VGA
   - May reveal decompressor between read and display

6. **Examine similar games**
   - Check if other MicroProse games use same format
   - F-15 Strike Eagle, F-19 Stealth Fighter, F-117A
   - May have documented RLE algorithms

---

## Documentation References

- **MENU_DATA_FORMAT_SPEC.md** - Complete .IDX/.DAT format specification
- **MENU_ARCHITECTURE_SUMMARY.md** - Menu system architecture
- **FILE_IO_ANALYSIS.md** - File I/O functions (picfont_idx_dat_loader documented)

---

## Investigation Log

### 2026-11-15 Session

**Actions:**
1. ✓ Created find_rle_decompressor.py - traced from VGA upload
2. ✓ Created trace_font_loader_callees.py - analyzed loader callees
3. ✓ Created analyze_rle_format.py - manual format analysis
4. ✓ Tested simple [count][value] RLE - FAILED (only 13.6% decoded)

**Findings:**
- VGA upload has 4 callers, none are obvious decompressors
- Font loaders don't call obvious decompression functions
- RLE format is more complex than simple [count][value]
- Compression ratio (0.34-4%) suggests specialized algorithm

**Conclusion:**
- Decompression likely inlined in loaders or done via dispatch
- Need to examine disassembly directly
- Alternative: implement decoder by trial-and-error with test data

---

## Status

**File Format:** ✓ 100% documented (header structure confirmed)  
**RLE Algorithm:** ⏳ 20% understood (simple RLE ruled out, format TBD)  
**Decompressor Location:** ⏳ 50% (likely in madfont_idx_dat_loader or inlined)  
**Implementation:** ❌ 0% (cannot extract graphics yet)

**Blocking Issues:**
1. Exact RLE algorithm unknown
2. Decompressor function not identified (may be inlined)
3. Need to examine disassembly or implement trial-and-error decoder

**Recommended Next Action:**  
Open IDA at 0x1397CE (madfont_idx_dat_loader) and manually trace the decompression loop to understand the algorithm.

