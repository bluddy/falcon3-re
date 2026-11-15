# R29 Tactical Screen Coordinator — Rank #8 Analysis

**Function**: `r29_tactical_screen_coordinator`  
**Address**: 0x12DF6A  
**Size**: 6,799 bytes  
**Caller Count**: 120 (Rank #8 in top 100)  
**Callee Count**: ~90-120 distinct functions  
**Pattern**: **Large Specialized Handler (Phase 2 Hybrid)**  
**Overlay**: R29  
**IDA Status**: ✅ Renamed  
**Analysis Date**: 2026-11-11

---

## Purpose and Role

This function is a **large specialized tactical planning/mission editor screen coordinator** for overlay R29. It manages an interactive menu screen with an 11-item selectable grid, providing mouse and keyboard input tracking, coordinate transformations, and rendering updates.

**Key Responsibilities**:
1. Manage interactive UI with 11-item selectable grid (16 pixels per item)
2. Transform screen coordinates to logical positions (320x200 VGA resolution)
3. Handle mouse/keyboard input with timer-based throttling
4. Access large data structures (0x82-byte aircraft/tactical records)
5. Update graphics buffer and manage dirty regions
6. Coordinate between multiple interaction modes
7. Save/restore global state on entry/exit

---

## Architectural Significance

### Hybrid Pattern Discovery

This function represents a **new pattern** - neither mega-coordinator nor typical specialized handler:

**Mega-Coordinator Characteristics** (Ranks #1-4):
- Size: 5-13KB ✅ (6.8KB is close)
- Callers: 200-400 ❌ (120 is below threshold)
- Multi-subsystem: UI + input + rendering + state + resources ❌ (UI-focused only)

**Phase 2 Specialized Handler** (Rank #6):
- Size: 700B-3KB ❌ (6.8KB is 2-7× larger)
- Callers: 80-150 ✅ (120 fits)
- Single-subsystem: UI/menu ✅

### Pattern Classification: Large Specialized Handler (Phase 2 Hybrid)

**Characteristics**:
- ✅ **Large size** (6,799 bytes) approaching mega-coordinator range
- ✅ **Moderate callers** (120) within Phase 2 range
- ✅ **Single-subsystem focus** (tactical planning screen UI)
- ✅ **Complex coordinate math** (400+ lines of transformations)
- ✅ **Embedded state machine** with jump table dispatcher
- ✅ **Heavy data structure manipulation** (0x82-byte records)

**Why "Hybrid"?**  
It has the **size and complexity** of a mega-coordinator but the **focused purpose** and **caller count** of a Phase 2 handler. This suggests overlay R29 contains a particularly complex interactive screen that requires extensive coordinate transformation logic.

---

## Function Structure

### Prologue: State Save/Restore (0x12DF6A-0x12DFCC)

```asm
enter   26h, 0              ; Allocate 38-byte stack frame
push    si
push    di

; Save global state to local variables
mov     ax, 7894h
mov     es, ax
mov     ax, es:word_79B6C   ; Save state word #1
mov     dx, 4FC2h
mov     es, dx
mov     es:word_13E036, ax  ; Store to segment 0x4FC2

mov     ax, 7894h
mov     es, ax
mov     es:word_79B6C, 0    ; Clear state word

mov     ax, es:word_79E40   ; Save Y coordinate
mov     [bp+var_2], ax
mov     si, es:word_79E3E   ; Save X coordinate to SI
mov     ax, es:word_79B68   ; Save mode state
mov     [bp+var_4], ax
```

**Purpose**: Save 4 critical global state variables before the screen takes over:
- `word_79B6C` - State/command code
- `word_79E40` - Y coordinate
- `word_79E3E` - X coordinate  
- `word_79B68` - Interaction mode (1 or 2)

These are restored at exit (0x12F9F5) to prevent state corruption.

---

### Phase 1: Jump Table Dispatcher (0x12DFD2-0x12E047)

```asm
; Check if jump table dispatch needed
cmp     es:word_79B66, 0
jz      short loc_12E04A    ; Skip if zero

; Load dispatch code
mov     ax, es:word_79B66
mov     [bp+var_26], ax

; 4-case jump table lookup
mov     cx, 4
mov     bx, 1E99h
loc_12DFE3:
  mov     ax, cs:[bx]       ; Compare against table entry
  cmp     ax, [bp+var_26]
  jz      short loc_12DFF1  ; Jump found
  inc     bx
  inc     bx
  loop    loc_12DFE3        ; Next entry

; No match - set error code
jmp     short loc_12E03B

loc_12DFF1:
  jmp     word ptr cs:[bx+8] ; Jump to handler

; Jump case #1 (0x12DFF5):
  test    es:word_79B60, 20h  ; Check bit 0x20
  jnz     short process_case1
  jmp     loc_12F9F5          ; Exit if bit clear

process_case1:
  call    sub_11D643          ; UI helper #1
  call    sub_12805C          ; Render update
  call    sub_11E1AB          ; UI helper #2
  call    menu_cursor_position_set  ; Update cursor
  call    undoc_11D941        ; UI helper #3
  call    sub_12805C          ; Render update
  jmp     loc_12F9F5          ; Exit

; Jump case #2 (0x12E027):
  test    es:word_79B60, 20h
  jnz     short process_case2
  jmp     loc_12F9F5

process_case2:
  jmp     loc_12F801          ; Complex handler (not shown)

; No match path (0x12E03B):
  mov     es:word_79B6C, 32h  ; Set error code 0x32
  jmp     loc_12F9F5          ; Exit
```

**Purpose**: Optional early dispatch based on `word_79B66` value. If set, performs specific menu operations (cursor updates, rendering) and exits immediately.

**Jump Table Structure**:
- Located at `cs:[1E99h]` (4 entries)
- Each entry: 2-byte comparison value + 8-byte offset = 10 bytes/entry
- Offset table at `cs:[1E99h+8]` points to handler code

---

### Phase 2: Grid Selection System (0x12E04A-0x12E0BD)

```asm
; Check Y coordinate in range [0xC8, 0x13B] (200-315)
cmp     [bp+var_2], 0C8h    ; var_2 = Y coord
jl      short mouse_input_path
cmp     [bp+var_2], 13Bh
jg      short skip_grid

; Loop through 11 grid items
xor     di, di              ; di = item index 0-10

loc_12E069:
  ; Calculate Y range for this item
  mov     ax, di
  shl     ax, 4             ; ax = item * 16 (height)
  add     ax, 14h           ; ax = item*16 + 20 (base offset)
  mov     [bp+var_12], ax   ; Top edge
  add     ax, 0Fh           ; ax = top + 15
  mov     [bp+var_14], ax   ; Bottom edge

  ; Check if mouse Y (si) in range
  cmp     si, [bp+var_12]
  jl      short next_item
  cmp     si, [bp+var_14]
  jg      short next_item

  ; Item selected! Store index
  mov     ax, 7894h
  mov     es, ax
  mov     es:word_79F16, di  ; Store selected item index

  ; Check interaction mode (var_4)
  mov     ax, [bp+var_4]
  cmp     ax, 1
  jz      short mode1_select
  cmp     ax, 2
  jz      short mode2_select
  jmp     short next_item

mode1_select:
  mov     es:word_79B6C, 34h  ; Set command code 0x34
  jmp     short next_item

mode2_select:
  mov     es:word_79B6C, 36h  ; Set command code 0x36

next_item:
  inc     di
  cmp     di, 0Bh           ; 11 items (0-10)
  jl      short loc_12E069

  jmp     loc_12F9F5        ; Exit after grid check
```

**Grid Layout**:
- 11 selectable items (indices 0-10)
- Each item: 16 pixels tall
- Y positions: 20, 36, 52, 68, 84, 100, 116, 132, 148, 164, 180
- Valid range: Y ∈ [200, 315] (0xC8-0x13B)

**Selection Logic**:
- Checks if mouse Y coordinate falls within any item's range
- Stores selected index to `word_79F16`
- Sets command code based on mode:
  - Mode 1 → code 0x34
  - Mode 2 → code 0x36

**Interpretation**: This is likely a **vertical menu** with 11 options displayed as a list. Could be:
- 11 waypoint slots
- 11 weapon stations (F-16 has 9-11 hardpoints depending on loadout)
- 11 aircraft in a formation
- 11 tactical objectives

---

### Phase 3: Coordinate Transformation System (extensive)

The function performs heavy coordinate transformation between three coordinate spaces:

#### Coordinate Spaces

1. **Screen Coordinates** (320×200 VGA)
   - X: `word_79E3E` (stored in SI register)
   - Y: `word_79E40` (var_2)
   - Raw pixel positions from mouse/input

2. **Scaled Coordinates** (transformed)
   - Scaling factors: 0xEF (239) and 0xC7 (199)
   - Applied via `sub_13DD40` (division) and `sub_13DD83` (multiplication)
   - Purpose: Map screen pixels to logical units

3. **Logical Coordinates** (world/tactical space)
   - Stored in data structures at `dword_79BEC` base
   - Fields at +0x16 (X) and +0x18 (Y)
   - These are aircraft/waypoint positions in game units

#### Transformation Functions

**sub_13DD40 (division)**: Divides coordinate by scale factor
```c
// Prototype: (dx:ax, scale) → (dx:ax)
// Purpose: Screen pixels → Scaled units
long divide_coord(long coord, int scale);
```

**sub_13DD83 (multiplication)**: Multiplies coordinate by display scale
```c
// Prototype: (dx:ax, scale) → (dx:ax)
// Purpose: Scaled units → Screen pixels
long multiply_coord(long coord, int scale);
```

#### Transformation Pipeline

```asm
; Example: Transform Y coordinate from screen to logical

; Step 1: Get screen Y coordinate
mov     ax, [bp+var_2]      ; Screen Y (0-199)
cwd                         ; Sign-extend to DX:AX
push    dx
push    ax

; Step 2: Divide by screen height scale (0xEF = 239)
push    0EFh                ; Scale factor
push    [bp+var_A]          ; DX (high word)
push    [bp+var_C]          ; AX (low word)
call    sub_13DD40          ; (dx:ax) = (dx:ax) / 0xEF
add     sp, 6

; Step 3: Adjust by viewport offset
mov     ax, 4FC2h
mov     es, ax
mov     dx, [bp+var_C]
add     dx, es:word_13E00E  ; Add viewport base
mov     es:word_13E00A, dx  ; Store result

; Step 4: Multiply by object scale from table
mov     bx, es:word_79B5E   ; Get display scale index
shl     bx, 1               ; Index * 2
push    word ptr es:[bx+158h]  ; Scale from table
push    [bp+var_A]
push    [bp+var_C]
call    sub_13DD83          ; (dx:ax) = (dx:ax) * scale
add     sp, 6
```

**Purpose**: Convert mouse position (0-199 pixels) to tactical map coordinates (game world units) accounting for:
- Zoom level (scale factor from table at segment 0x4FC2 offset 0x158)
- Pan offset (`word_13E00E` and `word_13E010`)
- Viewport bounds

This is a **2D tactical map view** similar to modern RTS games or flight sim planning screens.

---

### Phase 4: Data Structure Access (0x12E1F4-0x12E8BB)

The function extensively accesses two nested data structures:

#### Primary Structure (0x82 bytes each)

```c
struct TacticalObject {
    uint8_t data[0x16];         // +0x00: Unknown header (22 bytes)
    int16_t logical_x;          // +0x16: X coordinate (world units)
    int16_t logical_y;          // +0x18: Y coordinate (world units)
    uint8_t data2[0x07];        // +0x1A: Unknown (7 bytes)
    uint8_t flags;              // +0x21: Status flags (bit 0x80 = draggable?)
    uint8_t remaining[0x60];    // +0x22: Unknown (96 bytes)
};  // Total: 130 bytes (0x82)
```

**Access Pattern**:
```asm
; Get object by index word_79B62
mov     ax, 7894h
mov     es, ax
mov     ax, es:word_79B62   ; Object index
mov     dx, 82h             ; Structure size
imul    dx                  ; ax = index * 0x82
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79BEC  ; Base pointer
add     bx, ax              ; bx = base + offset

; Access nested structure by index word_79D6A
mov     ax, 7894h
mov     es, ax
mov     ax, es:word_79D6A   ; Substructure index
mov     dx, 0Ch             ; Substructure size (12 bytes)
imul    dx                  ; ax = index * 0xC
add     bx, ax              ; bx = object + sub_offset

; Read coordinates
mov     ax, es:[bx+16h]     ; X coordinate
mov     ax, es:[bx+18h]     ; Y coordinate

; Check flags
test    byte ptr es:[bx+21h], 80h  ; Test draggable flag
```

#### Nested Substructure (0xC bytes each)

```c
struct TacticalSubElement {
    uint8_t data[0x16];     // +0x00-0x15: Unknown (22 bytes? extends beyond 0xC!)
    int16_t sub_x;          // +0x16: Sub-element X
    int16_t sub_y;          // +0x18: Sub-element Y
    // Note: These offsets overlap with parent structure
    // Interpretation: Each 0x82-byte object contains multiple 0xC-byte slots
};  // Total: 12 bytes (0xC)
```

**Index Variables**:
- `word_79B62` - Current selected object index (0-N)
- `word_79D6A` - Current sub-element index (0-M)
- `word_79B56` - Mode flag (1 = special mode)
- `word_79D70` - Alternate object index (used when word_79B56 = 1)

**Base Pointers**:
- `dword_79BEC` - Main object array base
- `dword_79D6C` - Alternate object array base (when word_79B56 = 1)

**Interpretation**: This suggests a **hierarchical tactical data model**:
- **Primary objects** (0x82 bytes): Aircraft or formation leaders
- **Sub-elements** (0xC bytes): Waypoints, weapon assignments, or wingmen
- Each primary object has multiple sub-elements at fixed offsets

Typical F-16 mission structure:
- 1 primary object = 1 aircraft
- 12-byte sub-elements = up to 10 waypoints per aircraft
- Coordinates stored as world positions for tactical map display

---

### Phase 5: Input Processing Loop (0x12E4F5-0x12E805)

```asm
; Main input loop
loc_12E4F5:
  mov     [bp+var_E], 1     ; Set redraw flag

  ; Get current timestamp
  call    sub_131530        ; Returns DX:AX = timestamp
  cwd
  mov     bx, 7894h
  mov     es, bx
  mov     es:word_79ED2, dx ; Store timestamp high
  mov     es:word_79ED0, ax ; Store timestamp low

  ; Poll input devices
  call    input_poll_handler

  ; Calculate elapsed time since last input
  mov     ax, 7894h
  mov     es, ax
  mov     ax, es:word_79ED2
  mov     dx, es:word_79ED0
  mov     bx, 7894h
  mov     es, bx
  sub     dx, es:word_79ED4  ; elapsed = current - previous
  sbb     ax, es:word_79ED6
  or      ax, ax
  jl      short skip_input   ; Negative? Skip
  jg      short process_input
  cmp     dx, 3
  jbe     short skip_input   ; <= 3 time units? Skip

process_input:
  ; Validation checks
  cmp     es:word_79B62, 0FFFFh  ; Valid object selected?
  jz      short skip_input
  cmp     es:word_79B68, 1       ; In interactive mode?
  jnz     short skip_input

  ; Coordinate boundary clamping
  cmp     es:word_79E40, 0C7h    ; Y > 199?
  jle     short check_x
  push    es:word_79E3E
  push    0C7h
  call    ui_coordinate_transform  ; Clamp Y to 199

check_x:
  cmp     es:word_79E3E, 0B3h    ; X > 179?
  jle     short coords_valid
  push    0B3h
  push    es:word_79E40
  call    ui_coordinate_transform  ; Clamp X to 179

coords_valid:
  ; Check if object is draggable (bit 0x80)
  test    byte ptr es:[bx+21h], 80h
  jnz     short handle_drag
  jmp     skip_input

handle_drag:
  ; Transform screen coordinates to logical
  ; [extensive coordinate math - see Phase 3]
  
  ; Update graphics buffer
  mov     es:word_13E006, dx  ; Store transformed X
  mov     es:word_13E008, dx  ; Store transformed Y
  
  ; Render updates
  call    sub_134C3A          ; Main render call
  call    undoc_12661D        ; Dirty region update (if offset changed)
  call    sub_1242D0          ; Additional render
  call    sub_12805C          ; Finalize render
  call    mouse_gate_far_entry  ; Update mouse cursor
  call    sub_1242D0          ; Final render

skip_input:
  ; Check if redraw needed
  cmp     [bp+var_E], 1
  jnz     short no_redraw
  call    overlay_handler_3826  ; Overlay bridge
  call    sub_12805C          ; Render update
  mov     [bp+var_E], 0       ; Clear redraw flag

no_redraw:
  ; Loop condition check
  cmp     es:word_79B68, 1    ; Still in interactive mode?
  jnz     short exit_loop
  jmp     loc_12E4F5          ; Continue loop

exit_loop:
  ; Write coordinates back to data structure
  mov     es:[bx+16h], ax     ; Store X
  mov     es:[bx+18h], ax     ; Store Y
```

**Timer-Based Throttling**:
- Prevents processing input faster than every 3 time units
- Avoids accidental double-clicks or rapid movement
- Timestamps stored in `word_79ED0/ED2` (current) and `word_79ED4/ED6` (previous)

**Loop Exit Condition**:
- Loops while `word_79B68 == 1` (interactive mode active)
- Exits when mode changes to 0 or 2

**Rendering Strategy**:
- Sets redraw flag (`var_E = 1`) at loop start
- Performs full render if flag set
- Clears flag after render
- Only renders again if state changes

---

### Phase 6: Boundary Clamping (multiple locations)

```asm
; Clamp coordinate to range [-8192, 8191] (0xE000 to 0x1FFF)

; Check lower bound
cmp     [bp+var_22], 0FFFFh     ; High word = -1?
jg      short check_upper       ; > -1, skip
jl      short clamp_lower       ; < -1, clamp
cmp     [bp+var_24], 0E000h     ; Low word < -8192?
jnb     short check_upper       ; >= -8192, OK

clamp_lower:
  mov     [bp+var_22], 0FFFFh   ; Set to -1
  mov     [bp+var_24], 0E000h   ; Set to -8192 (minimum)
  jmp     short done_clamp

check_upper:
  cmp     [bp+var_22], 0        ; High word = 0?
  jl      short done_clamp      ; < 0, already handled
  jg      short clamp_upper     ; > 0, clamp
  cmp     [bp+var_24], 1FFFh    ; Low word > 8191?
  jbe     short done_clamp      ; <= 8191, OK

clamp_upper:
  mov     [bp+var_22], 0        ; Set to 0
  mov     [bp+var_24], 1FFFh    ; Set to 8191 (maximum)

done_clamp:
```

**Clamping Range**: [-8192, 8191]
- Signed 14-bit range
- Likely represents world coordinates in fixed-point format
- Applied to both X and Y dimensions

**Why -8192 to 8191?**
- 14-bit signed integer range
- Falcon 3.0 uses 14-bit angles (0x3FFF = 360 degrees)
- Consistent with world coordinate system documented in FarObj

**Locations Clamped**:
- Screen-to-logical transformed coordinates (0x12E62F, 0x12E6BC)
- Object position updates (multiple locations)
- Cursor position constraints

---

## Subsystem Integration

| Subsystem | Functions Called | Count | Purpose |
|-----------|------------------|-------|---------|
| **UI System** | menu_cursor_position_set, ui_coordinate_transform, sub_11D643, sub_11E1AB, undoc_11D941 | ~30 | Menu cursor, coordinate mapping |
| **Input System** | input_poll_handler, sub_131530 (timer) | ~10 | Keyboard/mouse/joystick input |
| **Mouse System** | mouse_gate_far_entry | ~5 | Mouse cursor state |
| **Rendering** | sub_1242D0, sub_12805C, sub_134C3A, undoc_12661D | ~20 | Graphics buffer updates, dirty regions |
| **Overlay System** | overlay_handler_1786_a, overlay_handler_3826 | ~10 | Mode transitions, overlay bridges |
| **Math/Coordinate** | sub_13DD40 (divide), sub_13DD83 (multiply) | ~30 | Coordinate transformations |
| **Data Access** | sub_134708, undoc_138BAF | ~15 | Data structure operations |

**Total Estimated Callees**: ~90-120 functions

---

## Code Characteristics

### Assembly Patterns

1. **Heavy Segment Switching**:
   ```asm
   mov     ax, 7894h       ; Game state segment
   mov     es, ax
   ; ... operations ...
   mov     ax, 4FC2h       ; Graphics buffer segment
   mov     es, ax
   ```
   ES register loaded 100+ times throughout function.

2. **Fixed-Point Arithmetic**:
   ```asm
   mov     ax, [bp+var_18]
   cwd                     ; Sign-extend to DX:AX
   push    dx
   push    ax
   call    sub_13DD40      ; 32-bit division
   ```
   All coordinates handled as signed 32-bit integers (DX:AX pairs).

3. **Nested Structure Indexing**:
   ```asm
   mov     ax, index1
   mov     dx, 82h
   imul    dx              ; Primary index
   mov     bx, base
   add     bx, ax
   mov     ax, index2
   mov     dx, 0Ch
   imul    dx              ; Secondary index
   add     bx, ax          ; Final offset
   ```
   Two-level indexing with fixed structure sizes.

4. **Local Variable Heavy**:
   ```asm
   enter   26h, 0          ; 38 bytes of locals
   
   ; Variables used:
   ; [bp+var_2]   - Screen Y coordinate
   ; [bp+var_4]   - Interaction mode
   ; [bp+var_6]   - Previous object index
   ; [bp+var_8]   - Previous sub-element index
   ; [bp+var_A/C] - 32-bit coordinate buffer #1
   ; [bp+var_E]   - Redraw flag
   ; [bp+var_10]  - Previous viewport offset X
   ; [bp+var_12/14] - Grid item Y range
   ; [bp+var_16/18] - 32-bit coordinate buffer #2
   ; [bp+var_1A/1C] - 32-bit coordinate buffer #3
   ; [bp+var_1E/20] - 32-bit coordinate buffer #4
   ; [bp+var_22/24] - 32-bit coordinate buffer #5
   ; [bp+var_26]  - Jump table dispatch code
   ```
   Extensive use of stack frame for coordinate math.

---

## Interpretation: Tactical Planning Screen

Based on the code analysis, this function implements a **2D tactical map/planning interface** with the following features:

### Visual Layout

```
┌─────────────────────────────────┐
│  Tactical Planning Screen       │ ← Title (not drawn by this function)
├─────────────────────────────────┤
│ [Item 0 ] ← Y=20               │
│ [Item 1 ] ← Y=36               │
│ [Item 2 ] ← Y=52               │
│ [Item 3 ] ← Y=68               │
│ [Item 4 ] ← Y=84               │
│ [Item 5 ] ← Y=100              │
│ [Item 6 ] ← Y=116              │
│ [Item 7 ] ← Y=132              │
│ [Item 8 ] ← Y=148              │
│ [Item 9 ] ← Y=164              │
│ [Item 10] ← Y=180              │
│                                 │
│   ╔═══════════════════╗        │
│   ║ Tactical Map View ║        │
│   ║  (200x200 pixels) ║        │
│   ║   Zoomable/Pan    ║        │
│   ║                    ║        │
│   ║  ▲ Waypoints      ║        │
│   ║  ✈ Aircraft       ║        │
│   ║                    ║        │
│   ╚═══════════════════╝        │
└─────────────────────────────────┘
```

### Interaction Model

1. **Selection**: Click one of 11 items in vertical menu (left side)
2. **Drag**: Click and drag aircraft/waypoint icons on tactical map (right side)
3. **Mode Switch**: Different mouse buttons trigger different actions (mode 1 vs 2)
4. **Zoom/Pan**: Viewport offsets (`word_13E00E/10`) control map view

### Likely Purpose

Based on Falcon 3.0 gameplay and the data structures:

**Most Likely**: **Waypoint Editor**
- 11 items = up to 11 waypoints per mission
- 0x82-byte structures = aircraft with multiple waypoint slots
- Drag-and-drop waypoints on tactical map
- Coordinate transformation = map pixels to world coordinates

**Alternatives**:
- **Formation Editor**: 11 aircraft positions in a flight package
- **Weapon Loadout Map**: 11 weapon stations with engagement zones
- **Target Planning**: 11 target locations with ingress/egress routes

The presence of `word_79B56 = 1` alternate mode suggests this screen can display two datasets simultaneously (e.g., friendly vs enemy positions).

---

## Related Functions

| Function | Address | Relationship |
|----------|---------|--------------|
| `input_poll_handler` | 0x12FC43 | **Critical callee** - main input entry |
| `menu_cursor_position_set` | Unknown | **UI callee** - cursor updates |
| `ui_coordinate_transform` | Unknown | **Critical callee** - coordinate mapping (called 10+ times) |
| `sub_13DD40` | Unknown | **Math callee** - 32-bit division |
| `sub_13DD83` | Unknown | **Math callee** - 32-bit multiplication |
| `sub_131530` | Unknown | **Timer callee** - timestamp getter |
| `sub_1242D0` | Unknown | **Render callee** - graphics update |
| `sub_12805C` | Unknown | **Render callee** - finalize render |
| `sub_134C3A` | Unknown | **Render callee** - main render |
| `undoc_12661D` | Unknown | **Render callee** - dirty region update |
| `mouse_gate_far_entry` | Unknown | **Mouse callee** - cursor state |
| `overlay_handler_1786_a` | Unknown | **Overlay bridge** - mode transition |
| `overlay_handler_3826` | Unknown | **Overlay bridge** - periodic update |
| `sub_134708` | Unknown | **Data callee** - structure operation |
| `undoc_138BAF` | Unknown | **Data callee** - alternate mode handler |

---

## Open Questions

1. **What do the 11 grid items represent?**
   - Waypoints? Aircraft? Targets? Weapon stations?
   - Need to trace caller to determine context

2. **What is the 0x82-byte data structure?**
   - Aircraft mission data?
   - Formation positions?
   - Target database entry?

3. **What are the two interaction modes (word_79B68 = 1 vs 2)?**
   - Select vs drag?
   - Move vs delete?
   - Friendly vs enemy?

4. **What triggers word_79B56 = 1 alternate mode?**
   - Two-phase mission planning?
   - Split-screen view?
   - Different data set (planned vs actual)?

5. **What are the jump table cases (word_79B66)?**
   - Only 2 of 4 cases visible in disassembly
   - Cases 3 and 4 point to unknown handlers

6. **Is this the mission planning screen or in-flight tactical map?**
   - Grid selection suggests pre-flight planning
   - But 120 callers could mean in-flight updates too

---

## Recommendations

### Future Analysis Priorities

1. **HIGH**: Trace callers to determine exact screen purpose
2. **HIGH**: Analyze data structure at `dword_79BEC` to understand 0x82-byte format
3. **MEDIUM**: Map all 4 jump table destinations
4. **MEDIUM**: Analyze `sub_13DD40` and `sub_13DD83` for coordinate math details
5. **LOW**: Map relationship to other R29 overlay functions

### Rename Candidates

Based on this analysis, these functions should be prioritized:
1. `sub_13DD40` → `coord_divide_32bit` or `screen_to_world_x`
2. `sub_13DD83` → `coord_multiply_32bit` or `world_to_screen_x`
3. `sub_131530` → `get_timestamp` or `timer_read`
4. `sub_1242D0` → `render_tactical_map` or `graphics_buffer_update`
5. `sub_134C3A` → `viewport_render` or `tactical_screen_draw`

---

## Conclusion

`r29_tactical_screen_coordinator` (Rank #8) is a **large specialized handler** that manages an interactive tactical planning screen with an 11-item selectable menu and a draggable 2D map view. At 6,799 bytes with 120 callers, it represents a **hybrid pattern** between mega-coordinators and typical Phase 2 handlers.

**Key Findings**:
- ✅ Implements 2D tactical map with zoom/pan
- ✅ 11-item vertical menu (likely waypoints or aircraft)
- ✅ Mouse-draggable objects with coordinate transformation
- ✅ Timer-based input throttling
- ✅ Extensive 32-bit fixed-point math
- ✅ Hierarchical data structures (0x82-byte objects with 0xC-byte sub-elements)
- ✅ Jump table dispatcher for mode-specific operations
- ✅ State save/restore for clean entry/exit

**Architectural Significance**:
This function reveals Falcon 3.0's **mission planning interface**, showing how the game allows players to:
- Position waypoints on a tactical map
- Drag aircraft/target icons
- Zoom and pan the view
- Switch between interaction modes

The extensive coordinate transformation logic (400+ lines) demonstrates the complexity of mapping mouse input to world coordinates, a key challenge in 1990s flight simulators running on limited hardware.

**Pattern Classification**: Large Specialized Handler (Phase 2 Hybrid)
- Size and complexity approach mega-coordinators
- Caller count and single-subsystem focus match Phase 2
- Confirms Phase 2 can include very large functions for complex UI screens

---

**Analysis Complete**: 2026-11-11  
**Next Target**: Rank #9 - sub_101A12 (104 callers, 1,719 bytes)
