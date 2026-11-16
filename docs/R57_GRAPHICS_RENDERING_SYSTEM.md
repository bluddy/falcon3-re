# R57 Loadout Menu - Graphics Rendering System

## Overview

Complete analysis of how the R57 loadout menu displays the F-16 aircraft image and weapon sprites (bombs, missiles) on hardpoints. This document traces the complete rendering pipeline from image file loading through display.

**Key Discovery**: The F-16 aircraft and weapon graphics are loaded from PICFONT.IDX/DAT files and rendered using a multi-layer UI element system that overlays weapon sprites onto hardpoint positions.

---

## Graphics File System

### PICFONT.IDX / PICFONT.DAT

**Format**: .IDX/.DAT pair (index + data)
- **PICFONT.IDX**: Index file containing offsets and sizes
- **PICFONT.DAT**: Data file containing actual image data

**Loader Function**: `picfont_idx_dat_loader` (0x1293F0) → calls → `sub_1297F0`

**Contents** (hypothesis based on menu usage):
- F-16 aircraft silhouette/diagram (top-down or side view)
- Weapon sprites: bombs, missiles, fuel tanks
- UI elements: buttons, borders, text backgrounds
- Menu graphics: selection indicators, cursors

**Structure** (.IDX/.DAT format already decoded in FILE_IO_ANALYSIS.md):
```
.IDX File (index):
  Entry 0: offset=0x0000, size=XXXX  ; F-16 base image?
  Entry 1: offset=XXXX, size=YYYY   ; Bomb sprite type 1?
  Entry 2: offset=YYYY, size=ZZZZ   ; Missile sprite type 1?
  ... (multiple weapon variants)

.DAT File (data):
  [offset 0x0000]: Image data (RLE compressed?)
  [offset XXXX]:   Image data
  [offset YYYY]:   Image data
  ...
```

**Loading Process**:
1. Open .IDX file
2. Read index entries (offset, size pairs)
3. Open .DAT file
4. For each image needed:
   - Seek to offset from index
   - Read 'size' bytes
   - Decompress if RLE encoded
   - Store in memory buffer

---

## Rendering Pipeline

### High-Level Flow

```
Game Start
    ↓
Load PICFONT.IDX/DAT (sub_1297F0)
    ↓
Store image data in memory (segment 7894h or 4FC2h)
    ↓
Enter R57 Menu (r57_menu_state_machine)
    ↓
State Machine Calls Display Handlers
    ├─ menu_r57_flight_display_handler (0x1A6AA6)
    └─ menu_r57_loadout_flight_display (0x1A86C6)
        ↓
Display Handlers Call UI Rendering
    └─ ui_element_render_complex_a (0x11CC39)
        ↓
UI Renderer Dispatches to Draw System
    ├─ dispatch_220ec_invoke (0x25EF4) - Called 2x
    ├─ sub_13DE82 (text rendering)
    └─ sub_13DE3A (text rendering)
        ↓
Draw System Renders to VGA Buffer
    └─ draw_from_struct (0x022455)
        ↓
VGA Display
```

### Display Handler Analysis

#### menu_r57_flight_display_handler (0x1A6AA6, 850B)

**Purpose**: Displays flight selection list

**Called by**: r57_menu_state_machine (State 0, 7 times)

**Key calls**:
- 4x `int_to_string_converter` - Convert flight numbers to text
- 4x `string_concatenate` - Build display strings
- 1x `ui_element_render_complex_a` - **Render UI element**

**Flow**:
1. Format flight data (pilot name, aircraft type, etc.)
2. Call ui_element_render_complex_a to display formatted list
3. Possibly highlights selected flight

#### menu_r57_loadout_flight_display (0x1A86C6, 572B)

**Purpose**: Displays loadout details for selected flight

**Called by**: r57_loadout_display_handler (7 times)

**Key calls**: Same pattern as flight_display_handler
- 4x `int_to_string_converter`
- 4x `string_concatenate`
- 1x `ui_element_render_complex_a`

**Flow**:
1. Format loadout data (weapon counts, types, fuel, weight)
2. Call ui_element_render_complex_a to display formatted details
3. **Likely coordinates with weapon sprite rendering**

---

## UI Element Rendering

### ui_element_render_complex_a (0x11CC39, 133B)

**Purpose**: Complex UI element renderer - likely renders images and text together

**Parameters** (from disassembly):
- `[bp+arg_0]`: Element index (multiplied by 16, +0x13)
- `[bp+arg_2]`: String/text pointer (passed to sub_13DE82)
- `[bp+arg_4]`: Additional parameter (possibly color/attribute)

**Disassembly Analysis**:

```assembly
; Load element index and compute offset
mov     ax, [bp+arg_0]
shl     ax, 4              ; Multiply by 16
add     ax, 13h            ; Add 19 (0x13)
mov     di, ax             ; DI = element offset

; Load base coordinates
mov     si, 0CCh           ; SI = 204 (Y coordinate?)

; First UI element draw (image?)
mov     ax, 7894h
mov     es, ax
push    word ptr es:byte_79976+1Ah    ; Parameter from global array
push    word ptr es:byte_79976+18h    ; Parameter from global array
push    di                             ; Element offset
push    si                             ; Y coordinate
call    dispatch_220ec_invoke          ; DRAW CALL 1

; Adjust coordinates
add     si, 38h            ; SI += 56 (move down?)

; Second UI element draw (another image?)
push    word ptr es:byte_79976+26h    ; Different parameters
push    word ptr es:byte_79976+24h
push    di
push    si
call    dispatch_220ec_invoke          ; DRAW CALL 2

; Restore coordinates
sub     si, 38h            ; SI -= 56 (back to original)
add     di, 6              ; DI += 6 (move right?)

; Text rendering
push    3
push    [bp+arg_4]
push    [bp+arg_2]         ; String pointer
call    sub_13DE82         ; Compute text width

; Center text
mov     si, ax
mov     bx, 2
cwd
idiv    bx                 ; width / 2
mov     si, ax
mov     ax, 104h           ; 260
sub     ax, si             ; 260 - (width/2)
mov     si, ax             ; SI = centered X position

; Draw text
push    3
push    [bp+arg_4]
push    [bp+arg_2]         ; String pointer
push    di                 ; X position
push    si                 ; Y position (centered)
call    sub_13DE3A         ; DRAW TEXT
```

**Interpretation**:
1. **DRAW CALL 1**: Draws first image element (F-16 base? Background?)
   - Uses parameters from `byte_79976+18h, +1Ah` (global array)
   - Positioned at (DI, SI) = (element_index*16+19, 204)

2. **DRAW CALL 2**: Draws second image element (weapon sprite?)
   - Uses parameters from `byte_79976+24h, +26h` (different global array entry)
   - Positioned 56 pixels lower

3. **TEXT**: Renders centered text label
   - Computes text width
   - Centers at X = 260 - (width/2)
   - Positioned 6 pixels right of images

**Global Array at byte_79976**:
- **+0x18-0x1B** (dwords): Image parameters for element 1
- **+0x24-0x27** (dwords): Image parameters for element 2
- Likely contains:
  - Image index into PICFONT.DAT
  - Rendering attributes (color, palette, transparency)

---

## Weapon Sprite Positioning

### Hardpoint Overlay System

**Hypothesis**: The R57 menu uses a **layered rendering approach**:

1. **Layer 0**: Background UI elements (borders, title, etc.)
2. **Layer 1**: F-16 aircraft base image (silhouette from PICFONT.DAT)
3. **Layer 2**: Weapon sprites overlaid at hardpoint positions
4. **Layer 3**: Text labels (weapon names, quantities)

**Hardpoint Positions**:

Based on F-16 hardpoint layout (9 hardpoints):
```
     [1]  [2]     [3]     [4]  [5]
      \\   |       |       |   //
       \\  |       |       |  //
        ━━━━━━━━━━━━━━━━━━━━━
            └─[6]─────[7]─┘
                  [8]
                 (fuselage)
                  [9]
              (centerline)
```

**Coordinate Mapping** (speculation):
- State 1 navigates through `sub_field_count` (flight_record.byte_4)
- This count likely = number of hardpoints with weapons (1-9)
- Each sub-field corresponds to a hardpoint position
- When sub-field changes, weapon sprite is rendered at that hardpoint

**Data Flow**:
```
User navigates to sub-field N (State 1)
    ↓
menu_flight_record_sum = computed global index
    ↓
State 4 loads 23-byte loadout structure
    loadout_array[menu_flight_record_sum]
    ↓
23-byte structure contains:
    - Weapon type per hardpoint (9 bytes)
    - Quantity per weapon type (7 words = 14 bytes)
    ↓
Display handler reads loadout structure
    ↓
For each hardpoint with weapon:
    - Look up weapon sprite index in PICFONT
    - Get hardpoint X,Y coordinates
    - Call ui_element_render_complex_a with:
        * arg_0 = hardpoint index
        * weapon sprite parameters in byte_79976 array
    ↓
ui_element_render_complex_a:
    - Draws F-16 base image (if first element)
    - Overlays weapon sprite at hardpoint position
    - Draws weapon name/quantity text
```

---

## 23-Byte Loadout Structure (Revised)

From State 4 analysis, we identified a 23-byte structure. Based on rendering needs:

```c
struct loadout_config {
    byte hardpoint_weapon_type[9];  // 9 bytes: weapon type per hardpoint
                                    // 0 = empty
                                    // 1 = AIM-9 Sidewinder
                                    // 2 = AIM-7 Sparrow
                                    // 3 = AIM-120 AMRAAM
                                    // 4 = MK-82 bomb
                                    // 5 = MK-84 bomb
                                    // 6 = AGM-65 Maverick
                                    // 7 = Fuel tank
                                    // etc...
    
    word weapon_quantity[7];        // 14 bytes: quantity per weapon type
                                    // [0] = AIM-9 count
                                    // [1] = AIM-7 count
                                    // [2] = AIM-120 count
                                    // [3] = MK-82 count
                                    // etc...
};  // Total: 23 bytes
```

**Mapping to PICFONT Sprites**:
- `hardpoint_weapon_type[i]` → maps to PICFONT.DAT entry index
- E.g., type 4 (MK-82) → PICFONT entry #15 (bomb sprite)
- Renderer looks up sprite, draws at hardpoint[i] position

---

## Dispatch System

### dispatch_220ec_invoke (0x25EF4)

**Purpose**: Generic graphics dispatch function

**Called by**: ui_element_render_complex_a (2x per element)

**Parameters** (from calls):
- Stack +0: SI (Y coordinate)
- Stack +2: DI (X coordinate)  
- Stack +4: Parameter from byte_79976 array (low word)
- Stack +6: Parameter from byte_79976 array (high word)

**Function**: Likely dispatches to lower-level drawing primitives based on parameters:
- Blit image from memory to VGA buffer
- Handle clipping
- Apply palette/color transformations

**Calls** (from registry):
- `draw_from_struct` (0x022455) - Main drawing coordinator

### draw_from_struct (0x022455, 104B)

**Purpose**: Coordinates drawing from structure

**Description** (from registry): "coordinates+attribute into draw callbacks"

**Called by**: 649 callers (very common!)

**Function**:
- Takes drawing structure with coordinates, image data, attributes
- Dispatches to appropriate rendering function
- Handles VGA memory writes

---

## Memory Layout

### Global Arrays (Segment 7894h)

**byte_79976 Array**: UI element image parameters
- Multiple dword entries
- +0x18-0x1B: Image 1 parameters
- +0x24-0x27: Image 2 parameters
- Likely pattern:
  ```c
  struct ui_image_params {
      word picfont_index;    // Index into PICFONT.DAT
      word attributes;       // Color, palette, flags
  };
  ui_image_params byte_79976[N];
  ```

### Image Data Buffers

**Loaded from PICFONT.DAT**:
- Segment 4FC2h or 7894h contains loaded image data
- Each image indexed by PICFONT.IDX entry
- Stored decompressed in memory for fast blitting

---

## Rendering Sequence (Complete)

### Menu Entry (State 0)

```
1. r57_menu_state_machine initializes
   └─ Sets up pointers (dword_79E68, dword_79E2C, dword_79BEC)
   
2. State 0: Flight selection
   └─ Calls menu_r57_flight_display_handler
       └─ Formats flight list strings
       └─ For each flight:
           └─ ui_element_render_complex_a(flight_index, flight_string, attrs)
               └─ dispatch_220ec_invoke × 2 (draw list item background/highlight)
               └─ sub_13DE3A (draw flight text)
```

### Loadout Display (States 1-4)

```
1. State 1: Select sub-field (hardpoint)
   └─ User presses keys to navigate
   └─ menu_temp_accumulator = current sub-field (0..8)
   └─ Recomputes menu_flight_record_sum (global loadout index)

2. State 2: Modify loadout (update offsets)
   └─ Adjusts dword_79E50 structure (animation offsets?)
   └─ Validates changes

3. State 3: Refresh display
   └─ 20-iteration UI loop
   └─ Calls r57_loadout_display_handler
       └─ Calls menu_r57_loadout_flight_display × 7 (once per state)
           └─ For each hardpoint with weapon:
               └─ ui_element_render_complex_a(hardpoint_index, weapon_name, attrs)
                   └─ dispatch_220ec_invoke #1: Draw F-16 base (first call) or blank
                   └─ dispatch_220ec_invoke #2: Draw weapon sprite at hardpoint position
                   └─ sub_13DE3A: Draw weapon name/quantity text

4. State 4: Save loadout
   └─ Copies 23-byte loadout structure
   └─ Updates menu_flight_record_sum
```

### Visual Result

```
┌─────────────────────────────────────────┐
│  LOADOUT - FLIGHT 1                     │  ← Title (State 0 display)
├─────────────────────────────────────────┤
│                                         │
│         [AIM-9]   [AIM-7]  [AIM-9]     │  ← Weapon sprites (layer 2)
│            \\       |       //          │
│             \\      |      //           │
│              ━━━━━━━━━━━━━━             │  ← F-16 image (layer 1)
│                  └──[MK-82]─┘           │
│                   [MK-82]               │
│                 (Fuel Tank)             │
│                                         │
│  AIM-9 Sidewinder x 2                  │  ← Text labels (layer 3)
│  AIM-7 Sparrow x 1                     │
│  MK-82 Bomb x 2                        │
│  External Fuel x 1                     │
│                                         │
│  Total Weight: 42,850 lbs              │  ← Calculated stats
│  [SELECT] [MODIFY] [DONE]              │  ← UI buttons
└─────────────────────────────────────────┘
```

---

## Outstanding Questions

1. **What is byte_79976 array size?** Need to find full structure
2. **PICFONT.DAT entry count?** How many sprites total?
3. **Weapon type → sprite index mapping?** Need lookup table
4. **Hardpoint coordinate table?** Where are X,Y positions stored?
5. **What is dword_79E50 structure really?** Animation state? Scroll offsets?
6. **RLE decompression?** Is image data compressed in PICFONT.DAT?
7. **Palette system?** VGA 256-color mode? 16-color EGA?

---

## Next Steps

### To Complete Graphics Understanding:

1. **Extract PICFONT.IDX/DAT from game files**
   - Parse .IDX to get entry count and offsets
   - Extract sprites from .DAT
   - Identify F-16 base image and weapon sprites

2. **Analyze picfont_idx_dat_loader (0x1293F0)**
   - Trace complete loading sequence
   - Find where images are stored in memory
   - Document RLE decompression (if present)

3. **Analyze dispatch_220ec_invoke (0x25EF4)**
   - Understand parameter encoding
   - Trace to VGA memory writes
   - Document blitting algorithm

4. **Find hardpoint coordinate table**
   - Search for 9-element array of coordinate pairs
   - Likely in segment 4FC2h or 7894h
   - Used by ui_element_render_complex_a

5. **Map byte_79976 array**
   - Find array bounds
   - Document structure of each entry
   - Trace how picfont_index is determined

6. **Create visual extraction tool**
   - Parse PICFONT.DAT
   - Export sprites as .PNG
   - Create reference guide showing weapon types

---

## References

- **FILE_IO_ANALYSIS.md**: PICFONT loader (sub_1297F0)
- **R57_STATE_MACHINE_COMPLETE.md**: State machine flow
- **R57_STATE_4_ANALYSIS.md**: 23-byte loadout structure
- **R57_STATES_1_2_3_ANALYSIS.md**: Sub-field navigation
- **registry/functions.yaml**: ui_element_render_complex_a, dispatch_220ec_invoke, draw_from_struct

---

*Analysis based on IDA extraction and R57 state machine analysis*  
*Graphics pipeline: PICFONT.DAT → picfont_loader → byte_79976 array → ui_element_render → dispatch → VGA*  
*Next: Extract actual PICFONT.DAT file and decode sprites*
