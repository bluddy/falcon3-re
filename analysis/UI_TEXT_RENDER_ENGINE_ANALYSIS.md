# Deep-Dive Analysis: ui_text_render_engine

**Date**: 2026-11-11  
**Function Address**: 0x128518 (1213848 decimal, linear)  
**Size**: 1282 bytes, 452 instructions  
**Purpose**: Core UI text rendering engine for menu system

---

## Executive Summary

`ui_text_render_engine` is the **primary text rendering function** for Falcon 3.0's menu system. With **70 callers** across the entire UI, this function handles:
- Text layout and positioning
- Font rendering
- Text attributes (color, style)
- Special character handling ('=' character at 0x3D has special logic)
- Coordinate calculation
- Multiple rendering modes

This is one of the most critical UI functions in the codebase.

---

## Function Statistics

| Metric | Value |
|--------|-------|
| **Size** | 1,282 bytes |
| **Instructions** | 452 |
| **Callers** | 70 (widespread usage) |
| **Callees** | 12 |
| **Complexity** | High (multiple branches, modes) |
| **Stack Frame** | 28 bytes (0x1C) |

---

## Function Signature (Preliminary)

Based on the `enter` instruction and observed calls:

```c
void __near ui_text_render_engine(
    uint8_t param_0,          // [bp+arg_0] - compared to '=' (0x3D)
    uint8_t line_or_row,      // [bp+arg_2] - iteration counter from loop
    uint8_t max_count,        // [bp+arg_4] - moved to SI
    void __far *data_ptr,     // [bp+arg_6:arg_8] - far pointer to data
    uint16_t code_segment     // [bp+arg_A] - CS for string literals
);
```

**Calling Convention**: Near call (same segment), likely Pascal (observed stack cleanup in callers)

---

## Major Callers (Top 20 of 70)

| Address | Function | Context | Calls |
|---------|----------|---------|-------|
| 0x683CE-0x68944 | ui_loadout_menu_enter | Weapons loadout screen | 8 |
| 0x6AF5D-0x6B1BB | ui_slot_list_mode_enter | Slot list menu | 4 |
| 0x1295C6 | ui_text_render_loop | Loop wrapper | N× |
| 0x678AB | display_palette_hud_refresh_step | Palette/HUD refresh | 1 |
| 0x6792C | menu_page_draw_step | General menu drawing | 1 |
| 0x683A2 | ui_slot_record_init | Slot initialization | 1 |
| 0x6B69C | undoc_6B669 | Unknown menu function | 1 |
| 0x12950D-0x129577 | undoc_129468 | Unknown utility | 2 |

**Pattern**: Most calls are from high-level menu entry functions and page drawing routines.

---

## Callees Analysis (12 functions)

### Rendering & Layout Functions
1. **utility_900** - Called early, likely initialization or setup
2. **undoc_1290EA** - Unknown purpose
3. **undoc_1298AB** - Unknown purpose
4. **sub_1299AE** - Unknown purpose
5. **sub_129A87** - Unknown purpose
6. **sub_12A114** - Unknown purpose

### Dispatch & Callback Functions
7. **dispatch_220f0_invoke_1arg** - Function dispatcher with 1 argument
8. **far_cb_1** - Far callback #1

### Drawing/Rendering Functions
9. **undoc_12B07D** - Unknown rendering
10. **undoc_12BE93** - Unknown rendering
11. **undoc_12BED1** - Unknown rendering
12. **undoc_12C2F7** - Unknown rendering

**Observation**: Many callees are still unnamed (`undoc_*`), suggesting these are lower-level primitives.

---

## Key Code Patterns Found

### Pattern 1: Special Character Handling

```asm
0x128524:  cmp     [bp+arg_0], 3Dh ; '='
0x128528:  jz      short loc_1285E0
```

**Analysis**: The '=' character (ASCII 0x3D) has **special meaning**, branching to different rendering logic. This could indicate:
- Horizontal line drawing
- Field separator
- Alignment marker
- Special formatting code

### Pattern 2: Segment 0x602E Data Access

```asm
0x12852A:  mov     ax, 602Eh
0x12852D:  mov     es, ax
0x12852F:  mov     al, es:byte_14E76C
0x128533:  push    ax
; ... repeated for byte_14E76D and byte_14E76E
```

**Analysis**: Reads **3 consecutive bytes** from segment `0x602E` (extended menu data):
- `byte_14E76C` - First byte (position? attribute?)
- `byte_14E76D` - Second byte
- `byte_14E76E` - Third byte

These are pushed as parameters to `utility_900`, suggesting they configure rendering.

### Pattern 3: Graphics Mode Check

```asm
0x128540:  mov     ax, 7894h
0x128543:  mov     es, ax
0x128545:  cmp     es:word_78940, 0  ; Graphics mode check
```

**Analysis**: Checks `word_78940` in segment `0x7894` (main game state). This is the **graphics mode flag** we've seen before:
- 0 = Text mode / VGA text
- Non-zero = Graphics mode / VGA 13h

---

## Data Segments Referenced

### Segment 0x602E - Extended Menu Data
- `byte_14E76C` - Rendering config byte 1
- `byte_14E76D` - Rendering config byte 2
- `byte_14E76E` - Rendering config byte 3

**Purpose**: These bytes control how text is rendered (color, position, attributes).

### Segment 0x7894 - Main Game State
- `word_78940` - Graphics mode flag

**Purpose**: Determines rendering mode (text vs. graphics).

---

## Parameters Interpretation

From observed calls, particularly from `ui_text_render_loop`:

```c
ui_text_render_engine(
    CS,             // Code segment for string literals
    0x1F,           // param_0 = 31 (0x1F) - possibly color/attribute
    i,              // Line number (1, 2, 3, ...)
    0x0A,           // max_count = 10
    data_ptr        // Far pointer to structure (e.g., 0x602E:0x1400)
);
```

### Hypothesis: Parameter Meanings

| Parameter | Likely Meaning | Evidence |
|-----------|---------------|----------|
| `param_0` (0x1F) | Text attribute/color | Compared to '=', value 31 is white on black |
| `line_or_row` | Row/line number | Incremented in loop (1, 2, 3...) |
| `max_count` (0x0A) | Max lines/items | Matches structure size (10 bytes) |
| `data_ptr` | Text or data source | Points to menu state or string data |
| `code_segment` | String segment | CS value for near-far pointer conversion |

---

## Stack Frame Layout (28 bytes)

```
[bp+arg_A]  = Code segment (CS)
[bp+arg_8]  = Far pointer segment
[bp+arg_6]  = Far pointer offset
[bp+arg_4]  = Max count (moved to SI)
[bp+arg_2]  = Line/row number
[bp+arg_0]  = First param (compared to '=')
[bp+0]      = Saved BP
[bp-2]      = ?
...
[bp-0x1B]   = Initialized to 0
[bp-0x1C]   = Initialized to 0
```

**Analysis**: Large stack frame (28 bytes) suggests multiple local variables for:
- Position tracking (X, Y coordinates)
- Character buffer
- Rendering state
- Temporary calculations

---

## Control Flow

### Entry Point
1. Save SI, DI (standard)
2. Load `max_count` into SI
3. Initialize two locals to 0 (`[bp-0x1B]`, `[bp-0x1C]`)
4. Check if far pointer is NULL (`arg_6 | arg_8`)
5. If NULL, jump to exit (0x128A96)

### Special Character Branch
1. Check if `param_0` == '=' (0x3D)
2. If yes, jump to special handler (0x1285E0)
3. Otherwise, continue to normal rendering

### Segment 0x602E Configuration
1. Read 3 bytes from `0x602E:0x14E76C-E`
2. Push them as parameters
3. Call `utility_900` (setup function)
4. Check graphics mode at `0x7894:word_78940`

### (Remainder requires full disassembly analysis)

---

## Rendering Pipeline (Hypothesized)

Based on structure and calls:

```
1. Parameter Validation
   └─> Check NULL pointer → exit if NULL

2. Special Character Check
   └─> If char == '=' → special rendering path

3. Configuration Load
   └─> Read 3 bytes from 0x602E
   └─> Call utility_900(byte1, byte2, byte3)

4. Graphics Mode Check
   └─> Check word_78940
   └─> Branch on text vs. graphics mode

5. Text Rendering
   └─> Calculate position (X, Y from line_or_row)
   └─> Load character data from data_ptr
   └─> Render character(s) via drawing functions
   └─> Update position

6. Exit
   └─> Restore SI, DI
   └─> Leave, return
```

---

## Mystery: The '=' Character

The special handling of '=' (0x3D) is intriguing. Possible meanings:

### Hypothesis 1: Horizontal Line
- '=' often represents horizontal separators in TUI
- Could render as ═══ (double line) or ─── (single line)

### Hypothesis 2: Field Assignment
- '=' might indicate "Label = Value" formatting
- Special rendering for key-value pairs in menus

### Hypothesis 3: Box Drawing
- Part of ASCII box-drawing character set
- Used for menu borders and frames

### Hypothesis 4: Format Code
- Not a literal character but a **control code**
- Triggers special formatting (alignment, color change)

**Next Step**: Analyze the code at `loc_1285E0` (the '=' handler) to determine true purpose.

---

## Integration with Menu System

```
ui_loadout_menu_enter
    ├─> ui_text_render_engine (direct call x8)
    │   ├─> utility_900 (setup)
    │   ├─> undoc_1290EA
    │   ├─> ... (text processing)
    │   ├─> undoc_12B07D (draw)
    │   ├─> undoc_12BE93 (draw)
    │   └─> undoc_12BED1 (draw)
    └─> ui_text_render_loop
        └─> ui_text_render_engine (N iterations)

menu_page_draw_step
    └─> ui_text_render_engine (page rendering)

display_palette_hud_refresh_step
    └─> ui_text_render_engine (HUD text)
```

---

## Proposed Sub-Function Analysis Priority

To fully understand `ui_text_render_engine`, analyze these callees in order:

1. **utility_900** - Configuration/setup function (called first)
2. **undoc_12B07D** - Drawing function (likely VGA writes)
3. **undoc_12BE93** - Drawing function
4. **undoc_12BED1** - Drawing function
5. **dispatch_220f0_invoke_1arg** - Function dispatcher
6. **undoc_1290EA** - Unknown early call

---

## Next Steps

### Immediate
1. ✅ **Identified ui_text_render_engine** - Core rendering function found
2. **Extract full disassembly** - Get complete instruction listing for deeper analysis
3. **Analyze '=' handler** - Understand special character rendering at 0x1285E0
4. **Analyze utility_900** - Understand rendering configuration

### Follow-up
5. **Analyze drawing functions** - undoc_12B07D, undoc_12BE93, undoc_12BED1
6. **Map byte_14E76C usage** - Find where these config bytes are set
7. **Trace parameter flow** - Confirm parameter meanings with concrete examples

---

## Code Reconstruction (Partial)

```c
// Stack frame structure
struct text_render_context {
    uint8_t unknown_1B;     // [bp-0x1B]
    uint8_t unknown_1C;     // [bp-0x1C]
    // ... 24 more bytes of locals
};

void __near ui_text_render_engine(
    uint8_t char_or_attr,     // First param, checked against '='
    uint8_t line_number,      // Row/line to render
    uint8_t max_lines,        // Maximum lines
    void __far *data_source,  // Far pointer to text/data
    uint16_t string_segment   // CS for string literals
) {
    struct text_render_context ctx;
    
    // Initialize locals
    ctx.unknown_1B = 0;
    ctx.unknown_1C = 0;
    
    // Validate pointer
    if (data_source == NULL) {
        return;
    }
    
    // Special character handling
    if (char_or_attr == '=') {
        // Special rendering path
        goto special_equals_handler;
    }
    
    // Load rendering configuration
    uint8_t config1 = *(uint8_t __far *)MK_FP(0x602E, 0x14E76C);
    uint8_t config2 = *(uint8_t __far *)MK_FP(0x602E, 0x14E76D);
    uint8_t config3 = *(uint8_t __far *)MK_FP(0x602E, 0x14E76E);
    
    utility_900(config1, config2, config3);
    
    // Check graphics mode
    uint16_t gfx_mode = *(uint16_t __far *)MK_FP(0x7894, 0x78940);
    if (gfx_mode == 0) {
        // Text mode rendering
        // ...
    } else {
        // Graphics mode rendering
        // ...
    }
    
    // ... (452 instructions of text processing and rendering)
    
special_equals_handler:
    // Special handling for '=' character
    // ...
}
```

---

## Statistics Summary

- **Importance**: ★★★★★ Critical (70 callers, core UI function)
- **Complexity**: ★★★★☆ High (452 instructions, multiple modes)
- **Completeness**: ★★☆☆☆ Partial (need full disassembly for complete understanding)
- **Dependencies**: 12 callees (many unanalyzed)

---

## Key Findings

1. **Central UI Function**: 70 callers make this the most-used text rendering function
2. **Multi-Mode Rendering**: Handles both text mode and graphics mode
3. **Special Character Support**: '=' character has distinct rendering path
4. **Configuration-Driven**: Uses 3-byte config from segment 0x602E
5. **Complex Pipeline**: 12 callee functions suggest sophisticated rendering

---

**Analysis Status**: Structural analysis complete, deep instruction-level analysis needed for full understanding.
