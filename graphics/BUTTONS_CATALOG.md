# Falcon 3.0 Button Graphics Catalog

**Status**: ✅ Successfully Extracted  
**Total**: 67 button graphics  
**Format**: Uncompressed VGA with size table header  

---

## Extraction Quality

**Shapes**: ✅ Clearly visible - 3D button effects with borders, shadows, and highlights  
**Palette**: ~OK - Using VGA approximation, colors are reasonable  
**Structure**: ✅ Perfect - All buttons extracted with correct dimensions  

---

## BUTTON1 - Main Menu Buttons (34 records)

Primary large buttons for main menu navigation.

### Large Buttons (112×16)
- Records 0-2: Wide menu buttons with 3D raised effect
- Records 16-19: Additional wide buttons

### Medium Buttons (54×16, 56×16)
- Records 3-5: Medium width buttons (54×16)
- Records 6-11: Slightly wider buttons (56×16)
- All show clear 3D button styling

### Small Icons (16×16)
- Records 12-15: Small square buttons/icons
- Diagonal shading patterns visible

### Special Elements
- Record 20 (120×22): Extra large button with complex content
- Record 21 (120×4): Thin horizontal bar
- Records 22, 33 (4×176): Vertical divider lines
- Records 23-30: Small utility buttons (50×10, 16×10)
- Record 31 (34×20): Small compact button
- Record 32 (58×16): Medium button

**Visual Style**: Clear 3D raised buttons with border, highlight, and shadow

---

## BUTTON2 - Secondary Buttons (20 records)

Medium-sized buttons for secondary menus.

### Medium Buttons (88×16)
- Records 0-5: Six identical-sized medium buttons
- Clean 3D styling similar to BUTTON1

### Large Buttons (112×16)
- Records 6-7: Two large buttons matching BUTTON1 style

### Small Buttons (50×18)
- Records 8-15: Eight small consistent buttons
- Slightly taller than BUTTON1's 50×10 buttons

### Tiny Icons (24×24)
- Records 16-19: Four square icons
- Diagonal patterns for depth effect

**Visual Style**: Consistent with BUTTON1, slightly smaller overall

---

## BUTTON3 - UI Elements (13 records)

Small UI elements, dividers, and micro-buttons.

### Horizontal Bars
- Record 0 (112×3): Thin horizontal divider
- Record 1 (112×4): Slightly thicker bar
- Record 8 (96×3): Medium-width thin bar
- Record 9 (96×4): Medium-width thicker bar

### Small Icons (13×13 to 20×13)
- Record 2 (13×13): Tiny square icon with diagonal pattern
- Record 4 (13×12): Micro button
- Record 5 (20×13): Small rectangular icon
- Record 7 (14×12): Micro button
- Record 10 (18×13): Small icon
- Record 12 (12×12): Smallest icon

### Vertical Elements
- Records 3, 6 (3×16): Very thin vertical dividers/spacers

### Medium Icon
- Record 11 (17×16): Small rectangular button

**Visual Style**: Minimal, utility UI elements. Less 3D effect than larger buttons.

---

## Usage Patterns

Based on user identification:

**BUTTON1**: Widget elements - decorative flourishes (setup screen handles/screws), map zoom labels, LED-style numerical displays, general purpose buttons  
**BUTTON2**: Armament/loadout screen - weapon category selection, load/unload actions, scroll controls, status displays  
**BUTTON3**: Frame components - rounded corners (pink=transparency), horizontal/vertical bezels for assembling UI borders  

---

## Key Insights

### BUTTON1 - Mixed Widgets
- **Records 16, 19**: Machine aesthetic decorations (handles/screws for setup screen)
- **Record 31**: Map zoom level display
- **Record 32**: LED-style 8-digit numerical display element
- Rest: General purpose menu buttons

### BUTTON2 - Armament Screen
Complete weapon loadout interface (see BUTTON2_ANNOTATED.md for full details)

### BUTTON3 - Frame System
**Modular UI borders** - corner pieces and bezels that can be assembled to create frames of any size:
- Pink color = transparency marker
- Rounded corners for professional look
- Tileable bezel strips for edges
- Classic DOS-era memory optimization  

---

## Technical Details

### File Format
```
Header:
  Byte 0:       count (number of button records)
  Byte 1:       padding (0x00)
  Bytes 2-N:    size table (uint16_t per record)

Each Record:
  Bytes 0-1:    width (uint16_t, little-endian)
  Bytes 2-3:    height (uint16_t, little-endian)
  Bytes 4-N:    pixel data (width × height bytes, uncompressed)
```

### Color Palette
Currently using standard VGA palette approximation:
- Colors 0-15: EGA colors
- Colors 16-231: 6×6×6 RGB cube
- Colors 232-255: Grayscale ramp

**Observed color ranges**:
- Most buttons use colors 16-31 (early RGB cube colors)
- Some use 0-29 (includes EGA colors)
- Narrow range = consistent menu color scheme

### Button Rendering Style
Classic early-90s 3D GUI buttons:
- **Border**: Dark outline (1-2 pixels)
- **Highlight**: Light pixels on top/left edges
- **Shadow**: Dark pixels on bottom/right edges
- **Fill**: Mid-tone solid or gradient
- **Result**: Raised 3D appearance

---

## Extraction Script

`analysis/extract_buttons.py` - Extracts all BUTTON files to PNG

Usage:
```bash
cd analysis
python extract_buttons.py
```

Output: `graphics/buttons/button1/`, `button2/`, `button3/`

---

## Viewing

Since this is a CLI environment, use the preview script for ASCII art:

```bash
cd analysis
python view_button.py                           # View samples
python view_button.py button1/record_00_112x16.png  # View specific
```

Or open PNGs with any image viewer.

---

## Next Steps

Buttons are complete! ✅

Remaining graphics to extract:
1. **Fonts** (MADFONT, PICFONT) - RLE compressed
2. **Menu UI** (SYSMENU, COMMMENU) - RLE compressed small elements
3. **Find actual menu palette** - May improve color accuracy

---

**Catalog Date**: 2026-11-11  
**Status**: Complete and verified  
**Confidence**: HIGH - Shapes clearly visible, format fully understood
