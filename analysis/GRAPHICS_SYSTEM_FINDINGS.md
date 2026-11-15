# Falcon 3.0 Graphics System Analysis

## Summary

Analysis of the Falcon 3.0 graphics and menu system, focusing on rendering pipeline, file formats, and overlay architecture.

## File Formats Discovered

### .IDX/.DAT File Format

**Index File (.IDX)**:
- Array of uint16 pairs: `[offset, size]`
- Each pair defines one record in the corresponding .DAT file
- Example: `0x029A, 0x02A5` = record starts at offset 666, size 677 bytes

**Data File (.DAT) - Per Record**:
```
Header (6 bytes):
  [0-1] Magic number: 0x0400
  [2-3] X coordinate (uint16) - screen position for blitting
  [4-5] Y coordinate (uint16) - screen position for blitting

Data (variable):
  Compressed graphics data (format depends on file type)
```

### Known Graphics Files

| File | Records | Description | Status |
|------|---------|-------------|--------|
| BUTTON1 | 34 | UI widgets (handles, screws, zoom labels) | ✅ Extracted |
| BUTTON2 | 20 | Armament screen buttons | ✅ Extracted |
| BUTTON3 | 13 | Frame components with rounded corners | ✅ Extracted |
| PEOPLE.DAT | 40 | Pilot face portraits | ❌ Compressed, format unknown |
| MONITOR.DAT | 12 | Setup screen graphics | ❌ Compressed |
| SYSMENU.DAT | 89 | System menu elements | ❌ Compressed |
| MADFONT.DAT | 91 | Font glyphs | ❌ Compressed |

### BUTTON Files Format (Uncompressed)

```
File structure:
  Byte 0: count (number of button graphics)
  Byte 1: padding (0x00)
  Bytes 2-N: size table (uint16_t per record)

Each Record:
  Bytes 0-1: width (uint16_t)
  Bytes 2-3: height (uint16_t)
  Bytes 4-N: pixel data (width × height bytes, uncompressed VGA)
```

Successfully extracted with grey palette (colors 16-31 mapped to grey ramp).

## Rendering Pipeline

### Key Functions

#### Graphics Loading
- **`madfont_idx_dat_loader`** (0x139909)
  - Generic .IDX/.DAT file loader
  - Reads index, loads data records
  - Calls graphics_record_processor with callbacks

- **`idx_record_callback_1`** (0x1396E6)
  - Processes .IDX record headers
  - Prepares data for decompression

- **`graphics_record_processor`** (0x2BFC3)
  - Stub function that loads overlay
  - Jumps to `r02_farptr_pair_call_entry` (0x100D01)
  - Real processing happens in overlay code

#### Menu Rendering
- **`ui_menu_panel_renderer`** (0x133ADC)
  - Main menu panel renderer
  - Builds filenames using `menu_field_offset_calculate`
  - Loads graphics from .DAT files

- **`menu_panel_background_draw`** (0x127ED2)
  - Draws menu panel backgrounds
  - Calls `view_limits_load`

- **`ui_text_render_engine`** (0x128598)
  - Text rendering for UI
  - 1282 bytes, handles text layout in menus

- **`ui_menu_transition_renderer`** (0x12A9F7)
  - Animated menu transitions
  - 1402 bytes, handles UI state updates

#### Graphics Processing
- **`rle_vga_decompressor`** (0x88460)
  - VGA planar mode RLE decompressor
  - 114 bytes
  - Input: SI=data ptr, DI=Y coord, BX=X coord/4
  - Data format: [width:word][height:word][rle_compressed_planes]
  - RLE: flag byte - bit7=1: run (count+value), bit7=0: literal (count+data)
  - Outputs to VGA mode 13h planar format (4 bit planes)
  - **Note**: May not be used for all graphics types

#### File I/O
- **`op_dispatch_far_entry`** (0x225A8)
  - Operation dispatcher for file I/O
  - Op 0x04 = Open file
  - Op 0x08 = Close file
  - Op 0x0C = Read file
  - Uses DOS int 21h calls

### Call Graph (Menu System)

Starting from 5 menu functions, discovered 80 unique callees:
- 23 common infrastructure functions
- 4 rendering pipeline functions
- Multiple UI/menu coordination functions

## Overlay Architecture

### Segments

Total: 135+ segments identified, including:
- **Base segments** (seg000-seg022): Core game code
- **R-series overlays** (R01-R69): Runtime-loaded code modules
- **VGRAPH segment** (0x85AE0-0x889C5): Graphics routines

### Key Overlays

| Overlay | Address | Size | Purpose |
|---------|---------|------|---------|
| R01_1CF6 | 0x2CF60 | 1424 | Unknown |
| R02_1CF6s | 0x100000 | 4512 | Graphics processing (called by graphics_record_processor) |
| R05_1F64 | 0x2F640 | 46416 | Large overlay - likely main game code |
| R30_569F | 0x669F0 | 25508 | Unknown |
| R69_606E | 0x706E0 | 84359 | Largest overlay |
| VGRAPH | 0x85AE0 | 12005 | VGA graphics routines |

### Overlay Loading Mechanism

- **16 overlay loader functions** identified
- Functions use far jumps (`jmp far ptr`) to transfer control to overlays
- Example: `tail_bridge_overlay_load` → loads overlay → jumps to overlay code
- **graphics_record_processor** is a tail-call bridge to overlay R02

## Graphics Compression Issue

### Problem
PEOPLE.DAT and other .DAT files contain compressed data that hasn't been successfully decompressed:
- Data has very high Shannon entropy (7.6 bits/byte)
- RLE decoder produces incorrect output
- Uncompressed interpretation shows noise

### Possible Causes
1. Wrong decompressor - may not use RLE at 0x88460
2. Dimensions not in data stream - passed externally or fixed
3. Overlay-specific code - real decompressor is in overlay R02
4. Different compression algorithm (LZW, Huffman, custom)

### What's Known
- Data is definitely compressed (entropy analysis confirms)
- Format includes 6-byte position header
- After header: 660 bytes of high-entropy data
- No clear width/height dimensions at start of compressed stream

## Next Steps

1. **Analyze overlay R02** (0x100000-0x1011A0)
   - Extract and disassemble overlay code
   - Find the actual graphics decompressor
   
2. **Trace graphics loading in debugger**
   - Break on PEOPLE.DAT file access
   - Follow code execution through decompression
   
3. **Examine VGRAPH segment** (0x85AE0-0x889C5)
   - May contain additional graphics routines
   - 12KB of VGA-specific code

4. **Expand menu system analysis**
   - Trace menu state machine
   - Document UI flow
   - Map menu data structures

## Files Created

### Extracted Graphics
- `graphics/fullscreen/` - 7 full-screen VGA images (320×200)
- `graphics/buttons/button1_grey/` - 34 button images
- `graphics/buttons/button2_grey/` - 20 armament screen buttons
- `graphics/buttons/button3_grey/` - 13 frame components

### Analysis Scripts
- `extract_buttons.py` - Extract BUTTON files
- `recolor_buttons.py` - Apply grey palette
- `extract_raw_vga.py` - Extract full-screen images
- `rle_decompress.py` - RLE implementation (unsuccessful for faces)

### IDA Scripts
- `expand_menu_system.py` - Menu call graph expansion
- `analyze_panel_renderer.py` - Rendering function analysis
- `disasm_graphics_loader.py` - Graphics loader disassembly
- `disasm_idx_dat_loader.py` - IDX/DAT loader disassembly
- `disasm_decompressor.py` - RLE decompressor disassembly
- `find_decompress_funcs.py` - Search for decompression candidates
- `analyze_overlays.py` - Overlay structure analysis
- `expand_from_rendering.py` - Rendering call graph expansion
- `sync_all_comments.py` - Sync function names and comments to IDA

### Documentation
- `graphics/README.md` - Graphics extraction documentation
- `analysis/MENU_SYSTEM_CODE_STRUCTURE.md` - Menu system structure
- `analysis/PEOPLE_DAT_STATUS.md` - Face extraction attempts log

## IDA Database Status

✅ Function names synchronized:
- All graphics/rendering functions named
- Menu system functions named
- File I/O dispatcher named
- RLE decompressor documented

✅ Comments added:
- Detailed comments on graphics functions
- File format documentation
- RLE algorithm documentation
- Overlay jump targets documented

## Statistics

- **Functions analyzed**: 11+ rendering/menu functions
- **Call graph nodes**: 80+ unique functions discovered
- **Overlay segments**: 135+ segments identified
- **Graphics extracted**: 67 button images + 7 full-screen images
- **File formats documented**: 2 (.IDX/.DAT, BUTTON)
- **Decompressors found**: 1 (RLE VGA planar at 0x88460)
- **IDA scripts created**: 12
- **Python analysis scripts**: 10+

---

*Last updated: Analysis session focusing on graphics extraction and rendering pipeline*
