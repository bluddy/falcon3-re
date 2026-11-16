# R57 Loadout Menu Flow Analysis

## Overview

The R57 loadout menu system allows players to configure flight groups and their weapon loadouts in Falcon 3.0. This document traces the complete flow from menu entry through state management to rendering.

**Status**: In Progress - Core structure identified, detailed state cases pending

---

## Architecture

### Entry Points

All 4 main R57 functions appear to be overlay entry points (no external callers found):

1. **r57_menu_state_machine** (0x1A5823, 3083B, 105 calls)
   - Main state machine handling user input and state transitions
   - 7-state switch based on `current_view_index` (word_79F16)
   
2. **r57_loadout_display_handler** (0x1A7182, 4549B, 96 calls)
   - Rendering/display logic for loadout view
   - Calls `menu_r57_loadout_flight_display` 7 times (one per state?)
   
3. **overlay_r57_logic** (2423B, 31 calls)
   - Overlay-specific logic and coordination
   
4. **overlay_r57_processor_2** (2090B, 54 calls)
   - Additional overlay processing
   - Calls `overlay_r57_simple_helper` (26B) multiple times

### Function Call Hierarchy

```
r57_menu_state_machine (3083B)
├── menu_r57_flight_display_handler (850B, 14 calls)
│   └── Called 7 times from state machine (likely one per state)
├── menu_cursor_position_set (14 calls)
├── ui_menu_transition_animate (7 calls)
└── Various overlay bridges and UI helpers

r57_loadout_display_handler (4549B)
└── menu_r57_loadout_flight_display (572B, 14 calls)
    └── Called 7 times (likely one per state)

overlay_r57_processor_2 (2090B)
└── overlay_r57_simple_helper (26B)
    └── Called 10 times
```

---

## State Machine (r57_menu_state_machine)

### Initialization (0x1A57F0 - 0x1A5A11)

**Stack Frame**: 12 bytes (0Ch)
- `[bp+var_2]`: Local state counter
- `[bp+var_4]`: Loop variable

**Initialization Sequence**:

```assembly
; 1. Initialize global state flags
mov es:word_79B60, 0           ; Unknown flag
mov es:word_79E86, 0           ; Unknown flag  
mov es:word_79E88, 0           ; Unknown flag

; 2. Initialize current flight index
mov es:word_79B62, 0           ; menu_current_flight_index = 0

; 3. Initialize menu field index
mov [bp+var_2], 0              ; Local state counter = 0
mov es:word_79EA0, 0           ; Menu field index = 0

; 4. Initialize 11 records (28 bytes each, 0x1C)
; Loop: for (var_4 = 0; var_4 < 0xB; var_4++)
mov [bp+var_4], 0
.loop:
  ; Set far pointer: record[var_4].ptr = 4FC2:0A68
  mov word ptr es:[bx+606h], 4FC2h
  mov word ptr es:[bx+604h], 0A68h
  
  ; Set field: record[var_4].field+8 = 6
  mov word ptr es:[bx+608h], 6
  
  inc [bp+var_4]
  cmp [bp+var_4], 0Bh
  jl .loop

; 5. Set up data pointers
mov es:dword_79E68, 4FC2:0600h  ; Set data pointer 1
mov es:dword_79E2C, 4FC2:06A8h  ; Set data pointer 2

; 6. Transform coordinates
les bx, es:dword_79E2C
push word ptr es:[bx+2]
push word ptr es:[bx]
call ui_coordinate_transform
```

### Main Switch Statement (0x1A5A11+)

**State Variable**: `current_view_index` (word_79F16, segment 7894h)
**States**: 0-6 (7 total states)

```assembly
; Load state and dispatch
mov ax, 7894h
mov es, ax
mov bx, es:current_view_index   ; Load current state
cmp bx, 6                        ; Check range [0, 6]
jbe loc_1A5A23                   ; Valid state
jmp def_1A5A25                   ; Out of range -> default

loc_1A5A23:
  shl bx, 1                      ; bx *= 2 (word table)
  jmp cs:jpt_1A5A25[bx]          ; Jump to case handler
```

### Input Handling

**Before State Switch** (lines 110-132):

```assembly
; Check if in specific mode (word_79B6C == 0x32 '2')
cmp es:word_79B6C, 32h
jnz loc_1A59F7                   ; Not in mode, skip to state dispatch

; In mode - handle input scan codes
mov ax, es:input_scan_code_queue ; Get scan code

; ESC key (scan code 1)
cmp ax, 1
jz .handle_esc                   ; Animate exit

; Scan code 3 (possibly '2' or F2)
cmp ax, 3
jz .exit_to_view_6               ; Set current_view_index = 6, exit

; Special code 0xFF
cmp ax, 0FFh
jz .handle_special

jmp loc_1A6272                   ; No match, continue

.exit_to_view_6:
  mov es:current_view_index, 6   ; Transition to view 6
  jmp loc_1A63E7                 ; Exit menu

.handle_esc:
  push 5                         ; Param: state 5
  call loc_67CA5+1               ; Animate transition
  call sub_12805C
  call menu_cursor_position_set
  mov [bp+var_2], 1              ; Set local state = 1

.handle_special:
  ; Render finalization path
  push es:word_13E012
  call ui_font_config_apply
  push es:word_13E012
  call menu_finalize_render
  call sub_11D274
  jmp def_1A5A25                 ; Go to default case
```

**Additional Input Checks** (lines 148-153):

```assembly
; Check for command '4' or '6'
cmp es:word_79B6C, 34h ; '4'
jz loc_1A5A11                    ; Go to state dispatch

cmp es:word_79B6C, 36h ; '6'
jz loc_1A5A11                    ; Go to state dispatch

jmp loc_1A5FE2                   ; Neither, continue elsewhere
```

---

## State Case 0: Initial/Flight Selection

**Entry**: 0x1A5A2A (line 162)

**Purpose**: Initial state - displays flight list, waits for input

### Logic Flow

```assembly
; 1. Animate state transition
mov ax, 7894h
mov es, ax
push es:current_view_index       ; Push current state
call loc_67CA5+1                 ; Animate transition

; 2. Update display
call sub_12805C                  ; Update function
call menu_cursor_position_set    ; Set cursor, wait for input

; 3. Check for specific command (key '6')
mov ax, 7894h
mov es, ax
cmp es:word_79B6C, 36h           ; Check if '6' pressed
jnz loc_1A5AA8                   ; Not '6', skip to next

; 4. Navigation: Previous flight (wrapping)
; This implements: current_index = (current_index + total - 1) % total
mov ax, es:word_79EEC            ; Load menu_total_flights_count
dec ax                           ; total - 1
mov es, dx
add es:word_79B62, ax            ; current += (total - 1)

; Modulo operation
mov ax, es:word_79B62            ; Load adjusted index
cwd                              ; Sign extend for division
idiv word ptr es:15ACh           ; Divide by word[7894:15AC] (probably total)
mov es:word_79B62, dx            ; Store remainder (index % total)

; 5. Compute flight record pointer
mov ax, es:word_79B62            ; Load current_flight_index
mov dx, 82h                      ; 130 bytes per record
imul dx                          ; offset = index * 130
mov es, dx
les bx, es:dword_79BEC           ; Load base ptr menu_flight_records_ptr
; ES:BX now points to current flight record (base + offset)
```

### Key Variables

- **word_79B62** (`menu_current_flight_index`): 0-based current flight
- **word_79EEC** (`menu_total_flights_count`): Total number of flights
- **word_79B6C**: Input/command byte (checked for '6', '4', etc.)
- **dword_79BEC** (`menu_flight_records_ptr`): Base pointer to flight records
- **Record stride**: 130 bytes (0x82) per flight
- **word[7894:15AC]**: Divisor for modulo (likely == menu_total_flights_count)

### Navigation Actions

- **Key '6'**: Previous flight (current = (current + total - 1) % total)
- Other keys likely in loc_1A5AA8+ (not yet analyzed)

---

## State Cases 1-6

**Status**: Not yet extracted from disassembly

The JSON disassembly appears to be truncated at ~200 lines, but the function is 3083 bytes total. Need to extract full disassembly from IDA to document:

- State 1: ?
- State 2: ?
- State 3: ?
- State 4: ?
- State 5: ?
- State 6: ? (possibly exit state based on input handler setting current_view_index = 6)

---

## Global Variables

### Menu State (Segment 7894h)

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| 7894:15AC | word_79F16 | word | `current_view_index` - Current state (0-6) |
| 7894:1968 | word_79B62 | word | `menu_current_flight_index` - 0-based flight index |
| 7894:1CF8 | word_79EEC | word | `menu_total_flights_count` - Total flights |
| 7894:1CAA | word_79EA4 | word | `menu_loadout_mode_flag` - Flight vs loadout mode |
| 7894:1C66 | dword_79E60 | dword | `menu_loadout_data_ptr` - Armament data pointer |
| 7894:19F2 | dword_79BEC | dword | `menu_flight_records_ptr` - Flight records base (130B stride) |
| 7894:1CA6 | word_79EA0 | word | Unknown - Menu field index |
| 7894:1966 | word_79B60 | word | Unknown - Initialized to 0 |
| 7894:1C8C | word_79E86 | word | Unknown - Initialized to 0 |
| 7894:1C8E | word_79E88 | word | Unknown - Initialized to 0 |
| 7894:1972 | word_79B6C | word | Input/command byte ('2','4','6', etc.) |
| 7894:0000+1938 | ui_state_word_array | word[10] | 10-slot UI state array |

### Input (Segment 7894h)

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| 7894:199B | input_scan_code_queue | word | Current keyboard scan code |

### UI (Segment 7894h)

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| 7894:1C86 | ui_screen_width_pixels | word | Screen width (VGA check threshold 300) |

### Other Segments

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| 4FC2:13E030 | word_13E030 | word | State parameter for state_byte_25488_set_arg |
| 4FC2:606h | record_array | struct[11] | 11 records, 28 bytes each (0x1C) |
| 602E:14F8BE | word_14F8BE | word | Bit 3 toggled (XOR 8) on entry |

---

## Data Structures

### Flight Record (130 bytes, 0x82)

**Base**: `menu_flight_records_ptr` (dword_79BEC)
**Stride**: 130 bytes per flight
**Access**: `base_ptr + (flight_index * 130)`

Structure not yet documented (need to analyze usage in display handlers).

### Menu Record (28 bytes, 0x1C)

**Array**: 11 records at segment 4FC2:604h+
**Initialization**:
- `+0x00` (dword): Ptr = 4FC2:0A68
- `+0x04` (word): Field = 6

Structure fields not yet documented.

---

## Rendering Pipeline

### Display Handlers

1. **menu_r57_flight_display_handler** (0x1A6AA6, 850B)
   - Called 7 times from state machine
   - Renders flight selection UI
   - 14 internal calls
   - 111 string references (likely UI templates/formatting)

2. **menu_r57_loadout_flight_display** (0x1A86C6, 572B)
   - Called 7 times from r57_loadout_display_handler
   - Renders loadout details
   - 14 internal calls
   - 79 string references

### Rendering Sequence (from input handling)

```assembly
; Before exiting or transitioning
push es:word_13E012              ; Font/UI config parameter
call ui_font_config_apply        ; Apply font configuration

push es:word_13E012
call menu_finalize_render        ; Finalize and render frame

call sub_11D274                  ; Post-render cleanup?
```

---

## Function Call Frequency Analysis

**From State Machine** (r57_menu_state_machine, 105 calls):

| Calls | Function | Purpose |
|-------|----------|---------|
| 14 | menu_cursor_position_set | Cursor positioning/input wait |
| 12 | sub_12805C | Display update |
| 7 | ui_menu_transition_animate | State transition animation |
| 7 | menu_r57_flight_display_handler | Flight list rendering |
| 6 | overlay_bridge_to_68019 | Overlay coordination |
| 5 | overlay_bridge_to_68338 | Overlay coordination |
| 5 | overlay_bridge_to_68b4a | Overlay coordination |
| 5 | overlay_bridge_to_68d32 | Overlay coordination |
| 5 | tail_bridge_to_ui_menu_frame_enter | Menu frame entry |
| 4 | overlay_bridge_to_68f9e | Overlay coordination |
| 4 | dispatch_220ec_invoke | Dispatcher |
| 3 | sub_2C8FB | Unknown |
| 3 | farobj_record_clear_fields | Clear far object fields |
| 3 | undoc_1A6E06 | Undocumented |
| 3 | sub_2C351 | Unknown |
| 2 | ui_coordinate_transform | Coordinate transformation |

---

## Outstanding Questions

1. **What are states 1-6?** Need to extract full disassembly (JSON truncated at 200 lines, function is 3083B)

2. **What triggers state transitions?** Aside from input setting current_view_index directly, how do states progress?

3. **What is word_79B6C?** Used for input checking ('2', '4', '6'), but exact source unclear

4. **Flight record structure?** 130-byte stride, but internal layout unknown

5. **Menu record structure?** 28-byte records initialized in array of 11 - what are they for?

6. **Loadout mode flag usage?** word_79EA4 (menu_loadout_mode_flag) named but not yet seen in extracted code

7. **String references?** 489 strings in r57_loadout_display_handler, 327 in state machine - are these UI templates or just disassembly artifacts?

8. **How does r57_loadout_display_handler integrate?** Separate entry point but seems parallel to state machine

9. **What is word[7894:15AC]?** Used as divisor for modulo in Case 0 navigation - is this the same as menu_total_flights_count or separate?

---

## Next Steps

1. **Extract full r57_menu_state_machine disassembly** from IDA (create script to dump all 3083 bytes)
2. **Document all 7 state cases** with logic and display handler calls
3. **Trace state transition conditions** - what causes state 0 -> 1, etc.?
4. **Analyze r57_loadout_display_handler** entry and integration
5. **Document flight record structure** (130-byte stride)
6. **Map all display handler calls** to their triggering states
7. **Identify menu record purpose** (11x 28-byte structures)
8. **Trace complete user input flow** from keypress to state change to rendering

---

## References

- Function registry: `registry/functions.yaml` (2,858 functions)
- Global registry: `registry/globals.yaml` (80 globals)
- Top 500 analysis: `docs/TOP_500_COMPLETE.md`
- IDA database: `analysis/ida_falconcd/FALCONCD.EXE.i64`
- Extraction scripts: `analysis/extract_r57_loadout_menu.py`, `analysis/analyze_r57_menu_flow.py`
