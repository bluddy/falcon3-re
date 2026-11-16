# R57 State Machine - Complete Analysis

## Overview

Complete documentation of all 7 states in the r57_menu_state_machine function (3083 bytes, 952 instructions). Extracted from IDA with full disassembly.

**Function**: `r57_menu_state_machine` at 0x1A57F0  
**State Variable**: `current_view_index` (word_79F16, segment 7894h)  
**States**: 0-6 (7 total)  
**Jump Table**: jpt_1A5A25 at line 161

---

## State Case Locations

| State | Line | Address | Label | Size (lines) | Purpose |
|-------|------|---------|-------|--------------|---------|
| 0 | 162 | 0x1A5A2A | Initial state | 114 | Flight selection, navigation |
| 1 | 276 | 0x1A5B90 | Secondary state | 90 | (TBD from analysis) |
| 2 | 366 | 0x1A5CA4 | Third state | 61 | (TBD from analysis) |
| 3 | 427 | 0x1A5D72 | Fourth state | 22 | (TBD from analysis) |
| 4 | 449 | 0x1A5DBA | Fifth state | 155 | (TBD from analysis) |
| 5 | 604 | 0x1A5FB3 | Sixth state | 4 | Jump to 0x1A59B4 (ESC handler) |
| 6 | 608 | 0x1A5FC0 | Final/exit state | 334 | Complex exit/mouse handling |
| Default | - | - | def_1A5A25 | - | Render and loop |

---

## State 0: Flight Selection (Lines 162-275)

**Purpose**: Initial state - display flight list, handle navigation

**Entry**: 0x1A5A2A  
**Size**: ~114 lines

### Flow

```
1. Animate transition (loc_67CA5+1)
2. Call sub_12805C (update)
3. Call menu_cursor_position_set (wait for input)
4. Check input:
   - If word_79B6C == '6': Previous flight (lines 171-203)
   - Else: Next flight (lines 204-228)
5. Validate flight record (byte at record+0x15 must be != 0)
6. Loop until valid flight found
7. Compute word_79F34 sum from flight records (lines 231-256)
8. Check byte_7A302 and byte_7A30E flags (lines 259-264)
9. Call overlay bridges and display handlers
10. Fall through or jump to next processing
```

### Navigation Logic

**Previous Flight** (key '6', lines 171-203):
```assembly
; word_79B62 = menu_current_flight_index
; word_79EEC = menu_total_flights_count

mov ax, es:word_79EEC        ; Get total flights
dec ax                       ; total - 1
add es:word_79B62, ax        ; current += (total - 1)
                            ; This is: current = current - 1 (with wrap)

; Modulo operation
mov ax, es:word_79B62
cwd
idiv word ptr es:15ACh       ; current %= divisor
mov es:word_79B62, dx        ; Store remainder

; Compute flight record pointer
mov ax, es:word_79B62        ; Load index
mov dx, 82h                  ; 130 bytes per record
imul dx                      ; offset = index * 130
les bx, es:dword_79BEC       ; Load base pointer
add bx, ax                   ; ES:BX = base + offset

; Validate flight
cmp byte ptr es:[bx+15h], 0  ; Check record+0x15
jz .loop_again               ; If 0, invalid, try again
```

**Next Flight** (default, lines 204-228):
```assembly
; Same as previous but increment instead of decrement
inc es:word_79B62            ; current++
; Then same modulo and validation
```

### Record Sum Computation (lines 231-256)

```assembly
; Initialize sum
mov es:word_79E88, 0         ; Clear word_79E88
mov es:word_79F34, ax        ; Copy to word_79F34

; Loop from 0 to current_flight_index
mov [bp+var_4], 0
.loop:
  ; Get record[var_4] byte at offset +4
  mov ax, [bp+var_4]
  mov dx, 82h
  imul dx                    ; offset = var_4 * 130
  les bx, es:dword_79BEC
  add bx, ax
  mov al, es:[bx+4]          ; Load byte at record+4
  cbw                        ; Sign extend to word
  add es:word_79F34, ax      ; Sum += record[i].byte_4
  
  inc [bp+var_4]
  cmp ax, [bp+var_4]
  jg .loop                   ; while var_4 < current_index
```

**Purpose**: Accumulates a sum from byte field at offset +4 in each flight record from 0 to current index.

### Display Calls (lines 265-275)

```assembly
call far ptr loc_68006               ; Overlay call
call sub_2C8FB                       ; Unknown
call overlay_bridge_to_68338         ; Overlay bridge
call overlay_bridge_to_68b4a         ; Overlay bridge
call overlay_bridge_to_68d32         ; Overlay bridge
call menu_r57_flight_display_handler ; Display flight list
call ui_menu_transition_animate      ; Animate transition
```

---

## State 1: Secondary State (Lines 276-365)

**Entry**: 0x1A5B90  
**Size**: ~90 lines

### Structure (similar to State 0)

```
1. Animate transition
2. Call sub_12805C
3. Call menu_cursor_position_set
4. Similar navigation logic with validation
5. Different overlay calls
6. Calls menu_r57_flight_display_handler
```

**Difference from State 0**: Likely different input handling or different validation logic. Needs detailed analysis to understand state transition conditions.

---

## State 2: Third State (Lines 366-426)

**Entry**: 0x1A5CA4  
**Size**: ~61 lines

### Structure

```
1. Animate transition
2. Call sub_12805C
3. Call menu_cursor_position_set
4. Navigation with validation
5. Overlay bridges
6. Call menu_r57_flight_display_handler
```

**Pattern**: Each state follows similar structure - animate, update, wait for input, navigate, validate, display.

---

## State 3: Fourth State (Lines 427-448)

**Entry**: 0x1A5D72  
**Size**: ~22 lines (shortest state)

### Structure

```
1. Animate transition
2. Call sub_12805C
3. Call menu_cursor_position_set
4. Call far ptr tail_bridge_to_slot_record_init_b
5. Jump to loc_1A5FA1
```

**Note**: Much shorter than other states. Possibly a transition state or initialization state.

---

## State 4: Fifth State (Lines 449-603)

**Entry**: 0x1A5DBA  
**Size**: ~155 lines (largest state)

### Notable Features

- Contains a large loop (lines 523-603)
- Initializes loop variable to 0 (line 524)
- Loop condition at line 525
- Uses 82h (130 byte) stride
- Multiple overlay bridge calls
- Sets word_79E9C to 4 (line 521)

**Complexity**: This appears to be the most complex state, possibly handling loadout configuration or detailed display.

---

## State 5: Sixth State (Lines 604-607)

**Entry**: 0x1A5FB3  
**Size**: 4 lines (shortest - just a jump)

```assembly
mov ax, 7894h
mov es, ax
push es:current_view_index
jmp loc_1A59B4
```

**Purpose**: Jumps to loc_1A59B4, which is in the ESC key handler (line 126). This is likely the "back" or "cancel" state.

---

## State 6: Final/Exit State (Lines 608-942)

**Entry**: 0x1A5FC0  
**Size**: ~334 lines (complex exit logic)

### Structure

```
1. Animate transition
2. Call sub_12805C
3. Call menu_cursor_position_set
4. Check word_79B6C == 0 (line 619)
5. Complex coordinate checking (word_79E7E, word_79E80)
6. Multiple nested if/else branches
7. Mouse/cursor position handling
8. Field selection logic (word_79EA0 array indexing)
9. Exit cleanup
```

### Coordinate Checks

The state checks multiple coordinate ranges:
- word_79E7E compared with 0x86, 0x76, 0xB6, 0x9E
- word_79E80 compared with 0x58, 0x18

**Interpretation**: These are likely mouse/cursor coordinates or UI region boundaries. The state is handling click regions or cursor navigation within the UI.

### Field Selection (lines 736-740, 791-795)

```assembly
mov bx, es:word_79EA0        ; Load field index
shl bx, 1                    ; Multiply by 2 (word array)
mov ax, 4FC2h
mov es, ax
; Then array access at es:[bx+...
```

**Purpose**: Selecting between multiple UI fields/buttons based on word_79EA0 index.

---

## Default Case: Render Loop

**Label**: def_1A5A25  
**Multiple entry points**: Lines 102, 144, 159, 522, 603, 621, 725, 735, 790, 830, 840, 942

### Structure

From lines 100-144:
```assembly
mov es:word_79E9C, 4
call ui_text_render_setup
call far ptr unk_67609              ; Default case entry
push [bp+var_2]
call far ptr sub_2C8E7
pop cx
call sub_12805C
call sub_12DB63
; ... input handling ...
; ... then render finalization ...
push es:word_13E012
call ui_font_config_apply
push es:word_13E012
call far ptr menu_finalize_render
pop cx
call sub_11D274
jmp def_1A5A25                      ; Loop back
```

**Purpose**: Main rendering loop. Setups UI, processes input, renders frame, loops. This is where the state machine returns after processing state-specific logic.

---

## State Transition Logic

### How States Change

The `current_view_index` (word_79F16) is modified by:

1. **Direct assignment** in input handlers:
   - Line 124: `mov es:current_view_index, 6` (exit to state 6)
   
2. **Unknown mechanisms**: The disassembly shows states being checked but doesn't show explicit transitions between 0→1→2→3→4→5. The transitions likely happen via:
   - Input handlers not yet traced
   - Functions called that modify current_view_index
   - Conditions checked that trigger state changes

### Linear vs Branching

From the structure:
- States 0-4: Similar patterns, suggest linear progression?
- State 5: Jump to ESC handler (back/cancel)
- State 6: Complex exit with coordinate checking

**Hypothesis**: States 0-4 may be linear progression through menu steps, State 5 is cancel, State 6 is final confirmation/exit.

---

## Flight Record Structure (130 bytes, 0x82)

From State 0 analysis:

| Offset | Type | Name | Purpose |
|--------|------|------|---------|
| +0x04 | byte | field_4 | Summed in State 0 loop (accumulator) |
| +0x15 | byte | valid_flag | Must be != 0 for valid record |
| ... | ... | ... | (Other fields not yet analyzed) |

**Base Pointer**: `dword_79BEC` (menu_flight_records_ptr)  
**Stride**: 130 bytes (0x82)  
**Access Pattern**: `base + (index * 130)`

---

## Key Variables

| Variable | Segment:Offset | Purpose | States Used |
|----------|----------------|---------|-------------|
| current_view_index | 7894:15AC | Current state 0-6 | All (state selector) |
| word_79B62 | 7894:1968 | menu_current_flight_index | 0,1,2 (navigation) |
| word_79EEC | 7894:1CF8 | menu_total_flights_count | 0,1,2 (modulo) |
| word_79B6C | 7894:1972 | Input/command byte | 0 (key '6'), 6 (coord check) |
| dword_79BEC | 7894:19F2 | menu_flight_records_ptr | 0,1,2,4 (record access) |
| word_79E88 | 7894:1C8E | Temp/sum variable | 0 (accumulator) |
| word_79F34 | 7894:2140 | Computed sum | 0 (result) |
| word_79EA0 | 7894:1CA6 | Field/button index | 6 (UI selection) |
| word_79E9C | 7894:1CA2 | UI mode/config | Default (set to 4) |
| word_79E7E | 7894:1C8A | Coordinate Y? | 6 (region checks) |
| word_79E80 | 7894:1C86 | Coordinate X? / ui_screen_width_pixels | 6 (region checks) |
| byte_7A302 | 7894:2108 | Flag | 0 (checked) |
| byte_7A30E | 7894:2114 | Flag | 0 (checked) |
| word[7894:15AC] | 7894:15AC | Modulo divisor | 0,1,2 (navigation) |

**Note**: word[7894:15AC] is at the same address as current_view_index. This is likely an error in IDA's disassembly comment, or there's segment overlap. Need to verify.

---

## Function Calls by State

### State 0
- loc_67CA5+1 (animate)
- sub_12805C (update)
- menu_cursor_position_set (input)
- loc_68006 (overlay)
- sub_2C8FB
- overlay_bridge_to_68338
- overlay_bridge_to_68b4a
- overlay_bridge_to_68d32
- menu_r57_flight_display_handler ← **Display**
- ui_menu_transition_animate

### States 1-4
- Similar pattern with menu_r57_flight_display_handler
- State 3 adds: tail_bridge_to_slot_record_init_b

### State 5
- Just jumps to ESC handler (no direct calls)

### State 6
- loc_67CA5+1 (animate)
- sub_12805C (update)
- menu_cursor_position_set (input)
- Multiple conditional branches (no display handler visible)

### Default Case
- ui_text_render_setup
- unk_67609
- sub_2C8E7
- sub_12805C
- sub_12DB63
- ui_font_config_apply
- menu_finalize_render
- sub_11D274

---

## Outstanding Questions

1. **What triggers transitions between states 0→1→2→3→4?**
   - Not visible in extracted disassembly
   - Likely in called functions or input handlers

2. **What is word[7894:15AC] really?**
   - Used as divisor in modulo
   - Same address as current_view_index (suspicious)
   - Need to verify segment mapping

3. **What are the coordinate ranges in State 6?**
   - word_79E7E: 0x86, 0x76, 0xB6, 0x9E
   - word_79E80: 0x58, 0x18
   - Are these pixels? Tiles? UI regions?

4. **What is the byte at flight_record+0x15?**
   - Used as valid flag
   - What makes a flight valid/invalid?

5. **What is the byte at flight_record+0x04?**
   - Accumulated in State 0
   - Result stored in word_79F34
   - Purpose of this sum?

6. **How does r57_loadout_display_handler integrate?**
   - Separate entry point (not called from state machine)
   - When is it invoked?

7. **What are byte_7A302 and byte_7A30E?**
   - Checked in State 0 before proceeding
   - Flags for some condition?

8. **What does word_79E9C control?**
   - Set to 4 in default case and State 4
   - UI mode or rendering config?

---

## Recommendations

1. **Trace input handlers** - The scan code/input processing likely modifies current_view_index
2. **Analyze called functions** - sub_12805C, sub_2C8FB, etc. may change state
3. **Verify address mappings** - word[7894:15AC] collision needs resolution
4. **Extract State 4 logic** - Largest state, needs detailed analysis
5. **Extract State 6 logic** - Complex coordinate checking needs mapping
6. **Trace display handlers** - When is r57_loadout_display_handler vs menu_r57_flight_display_handler?
7. **Document record structure** - Need all 130 bytes mapped

---

## Next Steps

1. ✅ Extract complete disassembly (952 instructions) - DONE
2. ✅ Identify all 7 state case locations - DONE
3. ✅ Document State 0 in detail - DONE
4. ⏳ Document State 4 in detail (complex loop)
5. ⏳ Document State 6 in detail (coordinate handling)
6. ⏳ Trace input→state transition logic
7. ⏳ Analyze display handler integration
8. ⏳ Map complete flight record structure

---

*Generated from: r57_state_machine_full_disasm.txt (952 instructions, 3083 bytes)*  
*Last updated: [Current session]*
