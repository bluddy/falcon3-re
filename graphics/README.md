# Falcon 3.0 Graphics Extraction

## Summary

Successfully extracted:
- **7 full-screen VGA images** (320×200 pixels, uncompressed)
- **67 button UI elements** (various sizes, uncompressed)

## Format Discovered

### Full-Screen Images (Uncompressed VGA)

Used for victory/defeat screens and other full-screen displays.

- **Header**: 4 bytes (width as word, height as word, little-endian)
- **Data**: width × height bytes (raw palette indices 0-255)
- **Total size**: 64,004 bytes for 320×200 images

Example header: `40 01 C8 00` = `0x0140` (320) and `0x00C8` (200)

### Button Files (Uncompressed VGA)

Used for UI buttons and controls (BUTTON1, BUTTON2, BUTTON3).

**File Structure:**
```
Header:
  Byte 0:       count (number of records)
  Byte 1:       padding (always 0x00)
  Bytes 2-N:    size table (2 bytes per record, little-endian)

Records:
  Bytes 0-1:    width (word, little-endian)
  Bytes 2-3:    height (word, little-endian)
  Bytes 4-N:    pixel data (width × height bytes)
```

All button graphics are **uncompressed** - the shape and structure are clearly visible.

## Extracted Images

### `/fullscreen/` - Victory/Defeat/Stalemate Screens (7 images)

Full-screen 320×200 VGA images, uncompressed with 4-byte header.

| File | Description | Size | Palette Range |
|------|-------------|------|---------------|
| LOSETEXT_320x200.png | Loss screen (F-16) | 320×200 | 0-254 |
| LOSETEXM_320x200.png | Loss screen (MiG-29) | 320×200 | 0-252 |
| DRAWTEXT_320x200.png | Stalemate screen | 320×200 | 0-255 |
| VICTEXT_320x200.png | Victory screen (F-16) | 320×200 | 0-254 |
| VICTEXM_320x200.png | Victory screen (MiG-29) | 320×200 | 0-220 |
| HTLINFBK.BIN_320x200.png | Unknown (Hornet?) | 320×200 | 4-255 |
| HTLINKGB.BIN_320x200.png | Unknown (Hornet?) | 320×200 | 0-254 |

### `/buttons/` - UI Button Graphics (67 images)

Button UI elements, uncompressed. Each BUTTON file contains multiple records with different sizes.

**BUTTON1** (34 records):
- Sizes: 112×16, 54×16, 56×16, 16×16, 120×22, 50×10, 16×10, etc.
- Purpose: Large menu buttons, navigation elements

**BUTTON2** (20 records):
- Sizes: 88×16, 112×16, 50×18, 24×24
- Purpose: Medium buttons, UI controls

**BUTTON3** (13 records):
- Sizes: 112×3, 112×4, 13×13, 3×16, 96×3, etc.
- Purpose: Small UI elements, dividers, icons

## Palette

**Original extraction**: Used standard VGA palette approximation (incorrect - shows blue)  
**Corrected extraction**: Grey-based menu palette (colors 16-31 mapped to grey ramp)

The armament/menu screens use **grey tones**, not the colorful VGA palette. Corrected versions are in `button*_grey/` subdirectories.

**Status**: ✅ Grey palette much better - text and buttons clearly visible

## What We Learned

1. **VGA full-screen graphics are uncompressed** - as expected for 1991 game technology
2. **Simple header format** - just width and height, no compression needed
3. **RLE compression exists but not for full images** - the RLE decompressor at 0x88460 is for small assets (fonts, sprites, UI elements)
4. **Theater-specific files** (*.ISR, *.BOS, etc.) are for in-sim graphics, not menus

## Still Unknown

The following need further investigation:
- **Fonts** (PICFONT, MADFONT) - use RLE compression, need proper decompression
- **Menu graphics** (SYSMENU.IDX/.DAT, etc.) - RLE compressed UI elements
- **Actual game palette** - current extraction uses VGA palette approximation
- **RLE .IDX/.DAT format** - header values don't match expected pixel counts, may represent VGA coordinates or metadata rather than dimensions

## Tools

- `analysis/extract_raw_vga.py` - Extracts uncompressed 320×200 VGA images
- `analysis/extract_buttons.py` - Extracts all button graphics from BUTTON1/2/3
- RLE decompressor at 0x88460 exists but .IDX/.DAT format not yet fully understood

## Next Steps

To extract remaining graphics:
1. Find the actual VGA palette used by the menu system (not theater-specific ALTPAL files)
2. Understand RLE .IDX/.DAT header values - they may represent VGA coordinates or metadata rather than pixel dimensions
3. Implement RLE decompression for fonts and menu UI elements
4. Test extraction on SYSMENU.IDX/.DAT and MADFONT files
