# Expanded Function Analysis - Falcon 3.0

## Overview

Using heuristic scoring (counting calls, comparisons, data references), we discovered **100 complex functions** beyond the initial menu system call graph. This overcame the limitation of overlay-based far calls that blocked traditional call graph expansion.

## Discovery Method

**Scoring Algorithm:**
- Score = (calls × 2) + comparisons + data_refs
- Threshold: score ≥ 50 for "interesting" functions
- Filters out simple helper functions, focuses on complex logic

## Top 30 Functions Discovered

### Category: Overlay Dispatchers & Coordinators

These are high-level control functions that manage overlay loading and coordinate between different game systems.

| Rank | Function | Address | Score | Size | Description |
|------|----------|---------|-------|------|-------------|
| 1 | r53_sbi_stream_dispatch | 0x1820B0 | 1558 | 12693 | Massive dispatcher - 342 calls, 751 data refs |
| 2 | overlay_r48_coordinator | 0x1744B0 | 1309 | 9061 | 360 calls - major coordinator |
| 3 | overlay_r4F_handler | 0x1793C0 | 1011 | 7661 | 262 calls - overlay handler |
| 4 | overlay_handler_large_1 | 0x12DF6A | 738 | 6799 | Large overlay handler |
| 5 | overlay_r55_dispatcher | 0x18F610 | 722 | 4935 | 212 calls - dispatcher |

**Analysis**: These functions are the "brains" of different game modes/screens. Each overlay (R48, R4F, R53, R55, etc.) likely represents a different game state (in-flight, menu, briefing, etc.).

### Category: Menu & UI Functions

| Rank | Function | Address | Score | Callees | Description |
|------|----------|---------|-------|---------|-------------|
| 7 | **ui_loadout_menu_enter** | 0x0683C1 | 536 | 57 | **Loadout/armament menu** - 142 calls |
| 17 | **menu_cmd_store_and_record_scan** | 0x160780 | 394 | 23 | Menu command processing |
| 24 | event_state_machine | 0x01AB34 | 325 | - | Event handling state machine |
| 25 | mode_axis_state_select | 0x034C31 | 322 | - | Mode/axis selection |

#### ui_loadout_menu_enter (0x683C1) - Detailed Analysis

**Size**: 4170 bytes
**Complexity**: 142 calls, 66 comparisons, 186 data references

**Key Functions Called**:
1. `ui_text_render_engine` - Renders text on screen
2. `menu_selection_ptr_get` - Gets current menu selection
3. `undoc_128AA6` - Unknown menu helper
4. `ui_animation_step` - Menu animations
5. `menu_cursor_ptr_get` - Gets cursor position

**Disassembly Pattern**:
```asm
; Setup data segment
mov     ax, 7894h
mov     es, ax

; Load menu selection data
les     bx, es:dword_79B52
push    word ptr es:dword_79B52+2
push    word ptr es:dword_79B52

; Render text
push    3Fh ; '?'
push    0FEh
push    16h
call    ui_text_render_engine

; Get menu selection
push    639Eh
push    8B9h
call    far ptr menu_selection_ptr_get
```

**Purpose**: This is the main entry point for the **weapons loadout screen** where players select missiles, bombs, fuel tanks, etc.

**Data Structures**:
- `dword_79B52` - Current menu state pointer
- Segment 0x7894 - Main game data segment

#### menu_cmd_store_and_record_scan (0x160780) - Detailed Analysis

**Size**: 4477 bytes
**Complexity**: 54 calls, 81 comparisons, 205 data references

**Key Functions Called**:
1. `undoc_13C868` - Unknown initialization
2. `undoc_136357` - Unknown helper
3. `tail_bridge_to_r30_state_init_all_c` - Overlay bridge to R30
4. `tail_bridge_to_terrain_decay` - Terrain system call
5. `sub_2C40F` - Unknown subsystem

**Disassembly Pattern**:
```asm
enter   0Ch, 0      ; Stack frame with 12 bytes local vars
push    si
push    di

; Check menu state flags
mov     ax, 7894h
mov     es, ax
les     bx, es:dword_79B52
mov     ax, es:[bx]
and     ax, 3       ; Check bits 0-1
cmp     ax, 3
jnz     short skip_flag
mov     [bp+var_9], 1   ; Set flag

; Initialize
call    undoc_13C868

; Clear byte flag
mov     ax, 602Eh
mov     es, ax
mov     es:byte_151C49, 0FFh
```

**Purpose**: Scans and stores menu commands, likely processing user input and updating game state.

### Category: Input & Control

| Rank | Function | Address | Score | Description |
|------|----------|---------|-------|-------------|
| 16 | input_poll_handler | 0x12FAC3 | 430 | Input polling - 137 comparisons |
| 22 | utility_2881 | 0x10A814 | 337 | Utility function - 236 data refs |

### Category: Graphics & Rendering

Functions that work with graphics but weren't in initial rendering analysis:

| Function | Address | Callees | Notes |
|----------|---------|---------|-------|
| overlay_r48_coordinator | 0x1744B0 | 360 | Includes rendering calls |
| overlay_r55_dispatcher | 0x18F610 | 212 | UI dispatcher with graphics |

## Call Relationships

### ui_loadout_menu_enter Call Graph

**Calls (top 10)**:
1. ui_text_render_engine (0x128598) - Text rendering
2. menu_selection_ptr_get - Get selection
3. undoc_128AA6 - Unknown
4. ui_animation_step - Animations
5. menu_cursor_ptr_get - Cursor
6. sub_683C5 - Related menu function
7. undoc_133535 - Unknown
8. sub_2C761 - Unknown
9. sub_2C49B - Unknown
10. sub_128518 - Unknown

**Called by**: None found (likely entry point from main game loop or overlay)

### Overlay Interaction Pattern

Many functions use **tail bridges** to call into overlays:
- `tail_bridge_to_r30_state_init_all_c`
- `tail_bridge_to_terrain_decay`
- `tail_bridge_to_hw_config_apply_chain`

**Pattern**:
```
Base function → tail_bridge → overlay code → far return
```

## Data Segment Map

### Segment 0x7894 - Main Game State
- `dword_79B52` - Menu state pointer
- `dword_79E3A` - Graphics state pointer  
- `word_78940` - Graphics mode flag

### Segment 0x602E - Extended Data
- `byte_151C49` - Menu command flag
- `byte_151C3C` - UI state byte
- `word_151AB8` - Graphics word

## Function Categories Summary

| Category | Count | Examples |
|----------|-------|----------|
| Overlay Control | 12 | r53_sbi_stream_dispatch, overlay_r48_coordinator |
| Menu/UI | 4 | ui_loadout_menu_enter, menu_cmd_store_and_record_scan |
| Input | 2 | input_poll_handler, mode_axis_state_select |
| Graphics | 3 | Various overlay coordinators with rendering |
| State Machines | 2 | event_state_machine, etc. |
| Utilities | 7 | Various helpers and processors |

## Key Insights

### 1. Overlay Architecture is Central
Almost all complex functions are overlay dispatchers/coordinators. The game heavily relies on dynamic code loading.

### 2. Menu System is Multi-Layered
- **Entry functions**: ui_loadout_menu_enter
- **Command processing**: menu_cmd_store_and_record_scan  
- **Rendering**: ui_text_render_engine, menu_panel_background_draw
- **State management**: event_state_machine, menu selection/cursor getters

### 3. Data Segment 0x7894 is Critical
Appears in almost every menu/UI function - contains core game state.

### 4. Far Calls Everywhere
Traditional call graph analysis fails because:
- Far calls to overlays (`call far ptr`)
- Tail bridges that jump to overlays
- Function pointers and indirect calls

### 5. Text Rendering is Key
`ui_text_render_engine` (0x128598) is called by most UI functions. It's 1282 bytes and handles:
- Text positioning
- Font rendering
- Color/attribute setting
- Possibly uses MADFONT.DAT

## Next Analysis Steps

### Priority 1: Analyze ui_loadout_menu_enter Completely
- Extract full disassembly (4170 bytes)
- Map all 57 callees
- Understand weapon/loadout data structures
- Document UI flow

### Priority 2: Overlay R53 Analysis  
- r53_sbi_stream_dispatch is the largest function (12KB)
- 342 function calls - huge coordinator
- Likely handles major game mode (combat? flight?)

### Priority 3: Input System
- input_poll_handler connects to UI
- Understand keyboard/joystick → menu command flow

### Priority 4: Complete Menu State Machine
- event_state_machine + menu_cmd_store_and_record_scan
- How do menu commands trigger actions?
- State transitions

## Files Created

- `ui_functions_scored.json` - 100 scored functions
- `top_functions_analysis.json` - Top 30 with call graphs
- `menu_functions_disasm.json` - Disassembly of key menu functions

## Statistics

- **Total functions scored**: 3000+ scanned
- **Complex functions (score ≥ 50)**: 100
- **Menu/UI functions identified**: 4+
- **Overlay coordinators found**: 12+
- **Average function size (top 30)**: ~6000 bytes
- **Largest function**: r53_sbi_stream_dispatch (12,693 bytes)

---

*Analysis completed using heuristic scoring to overcome overlay call graph limitations*
