# BUTTON3 - Frame Components

**Purpose**: UI frame/border elements with rounded corners and bezels  
**Total Records**: 13  
**Color Note**: Pink color = transparency marker  

---

## Purpose

BUTTON3 contains the **building blocks for UI frames** - corner pieces and edge bezels that can be assembled to create bordered panels.

---

## Frame Components

### Rounded Corners
Multiple records contain corner pieces with:
- Rounded edges
- Pink color marking transparent areas
- Various sizes for different frame types

### Bezels (Long Edges)
Horizontal and vertical bezel strips:
- **Records 0-1** (112×3, 112×4): Long horizontal bezels
- **Records 8-9** (96×3, 96×4): Medium horizontal bezels
- **Records 3, 6** (3×16): Thin vertical bezels/spacers

### Corner & Edge Pieces
- **Record 2** (13×13): Corner piece
- **Record 4** (13×12): Corner piece
- **Record 5** (20×13): Edge piece
- **Record 7** (14×12): Corner piece
- **Record 10** (18×13): Edge piece
- **Record 11** (17×16): Edge piece
- **Record 12** (12×12): Small corner

---

## Assembly Pattern

These pieces are designed to be **assembled at runtime** to create frames of various sizes:

```
Corner ─── Horizontal Bezel ─── Corner
  │                                 │
Vertical                        Vertical
Bezel                           Bezel
  │                                 │
Corner ─── Horizontal Bezel ─── Corner
```

This allows the game to:
1. Create frames of any size without storing complete frame images
2. Reuse components across different UI panels
3. Save memory (DOS era optimization)

---

## Transparency

**Pink color** is used as the transparency marker. During rendering:
- Pink pixels = transparent (don't draw)
- Other pixels = frame border/bevel

This allows rounded corners to blend properly with the background.

---

## Usage

These frame components are likely used for:
- Dialog boxes
- Information panels
- Status displays
- Menu borders
- Pop-up windows

Any UI element that needs a decorative border would use these building blocks.

---

## Technical Implementation

The game probably has a **frame rendering function** that:
1. Takes desired width/height
2. Selects appropriate corner and bezel pieces
3. Blits corners to four corners
4. Tiles/stretches bezels along edges
5. Skips pink pixels (transparency)

Classic DOS-era UI construction technique!

---

**Annotated by**: User  
**Date**: 2026-11-11  
**Insight**: "button3 appears to be a frame. there are rounded corners with a pink color (transparency), and long bezels."
