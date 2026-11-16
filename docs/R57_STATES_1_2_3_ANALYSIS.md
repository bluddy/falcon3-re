# R57 State Machine - States 1, 2, 3 Analysis

## Overview

Analysis of States 1, 2, and 3 from the r57_menu_state_machine function. These states handle sub-field navigation within the currently selected flight's loadout.

**Function**: `r57_menu_state_machine` at 0x1A57F0  
**States Covered**: 1, 2, 3 (Second, Third, Fourth states - 0-indexed)

---

## State 1: Loadout Sub-Field Navigation (Lines 276-365)

**Entry**: Line 276, Address 0x1A5B90  
**Size**: 90 lines  
**Purpose**: Navigate through loadout sub-fields (weapons, quantities, etc.)

### Flow Overview

```
1. Animate transition
2. Call display update
3. Wait for input
4. Check input (key '6' vs other)
   - '6': Decrement sub-field index (with wrap)
   - Other: Increment sub-field index (with wrap)
5. Clamp sub-field index to valid range [0, flight_record.byte_4-1]
6. Compute and update menu_flight_record_sum
7. Check flags and display or exit
```

### Entry and Input Check (Lines 276-286)

```assembly
; Standard entry
mov ax, 7894h
mov es, ax
push es:current_view_index    ; Push state 1
call far ptr loc_67CA5+1      ; Animate transition
pop cx

call sub_12805C               ; Display update
call menu_cursor_position_set ; Wait for input

; Check input
mov ax, 7894h
mov es, ax
cmp es:word_79B6C, 36h        ; Check menu_input_command_byte == '6'
jnz short loc_1A5BF6          ; Not '6', go to increment path
```

**Branch**: Input '6' = previous sub-field, else = next sub-field

### Path A: Previous Sub-Field (Key '6', Lines 287-308)

```assembly
; Decrement menu_temp_accumulator
mov ax, 7894h
mov es, ax
dec es:word_79E88             ; menu_temp_accumulator--
mov es, ax
cmp es:word_79E88, 0          ; Check if < 0
jge short loc_1A5C37          ; If >= 0, skip wrap

; Wrap to maximum: Get flight_record[current].byte_4 - 1
mov ax, 7894h
mov es, ax
mov ax, es:word_79B62         ; Load menu_current_flight_index
mov dx, 82h                   ; 130 bytes per flight record
imul dx
mov dx, 7894h
mov es, dx
les bx, es:dword_79BEC        ; Load menu_flight_records_ptr
add bx, ax                    ; BX = base + offset

mov al, es:[bx+4]             ; Load flight_record.byte_4
cbw                           ; Sign-extend to word
dec ax                        ; max_value = byte_4 - 1
mov dx, 7894h
mov es, dx
mov es:word_79E88, ax         ; menu_temp_accumulator = max

jmp short loc_1A5C37          ; Continue to sum calculation
```

**Logic**: 
- Decrements `menu_temp_accumulator`
- If goes negative, wraps to `flight_record[current].byte_4 - 1`
- This is the **maximum sub-field index** for this flight

**Key Discovery**: `flight_record.byte_4` stores the **count of sub-fields** (weapons, quantities, etc.) for that flight.

### Path B: Next Sub-Field (Default, Lines 309-329)

```assembly
; Increment menu_temp_accumulator
mov ax, 7894h
mov es, ax
inc es:word_79E88             ; menu_temp_accumulator++

; Get maximum value from flight record
mov ax, 7894h
mov es, ax
mov ax, es:word_79B62         ; Load menu_current_flight_index
mov dx, 82h
imul dx
mov dx, 7894h
mov es, dx
les bx, es:dword_79BEC        ; Load menu_flight_records_ptr
add bx, ax

mov al, es:[bx+4]             ; Load flight_record.byte_4
cbw
mov dx, 7894h
mov es, dx
cmp ax, es:word_79E88         ; Compare byte_4 with menu_temp_accumulator
jg short loc_1A5C37           ; If byte_4 > accumulator, OK

; Wrap to 0
mov ax, 7894h
mov es, ax
mov es:word_79E88, 0          ; menu_temp_accumulator = 0
```

**Logic**:
- Increments `menu_temp_accumulator`
- If exceeds `flight_record.byte_4`, wraps to 0
- Implements circular navigation through sub-fields

### Sum Calculation (Lines 330-355)

```assembly
; Copy menu_temp_accumulator to menu_flight_record_sum
mov ax, 7894h
mov es, ax
mov ax, es:word_79E88         ; Load menu_temp_accumulator
mov dx, 7894h
mov es, dx
mov es:word_79F34, ax         ; menu_flight_record_sum = accumulator

; Accumulate sum from flight records [0..current_flight_index)
mov [bp+var_4], 0             ; Loop counter = 0
jmp short .loop_check

.loop_body:
  mov ax, [bp+var_4]
  mov dx, 82h                 ; 130 bytes per record
  imul dx
  mov dx, 7894h
  mov es, dx
  les bx, es:dword_79BEC      ; Load base pointer
  add bx, ax
  
  mov al, es:[bx+4]           ; Load flight_record[i].byte_4
  cbw
  mov dx, 7894h
  mov es, dx
  add es:word_79F34, ax       ; sum += byte_4
  
  inc [bp+var_4]

.loop_check:
  mov ax, 7894h
  mov es, ax
  mov ax, es:word_79B62       ; Load current_flight_index
  cmp ax, [bp+var_4]
  jg short .loop_body         ; Loop while i < current_flight_index
```

**Result**: `menu_flight_record_sum = menu_temp_accumulator + sum(flight_record[0..current-1].byte_4)`

**Same pattern as State 0!** This is computing the **global index** into the loadout array.

### Exit Logic (Lines 356-365)

```assembly
mov ax, 7894h
mov es, ax
cmp es:byte_7A302, 0          ; Check menu_flag_byte_7a302
jz short loc_1A5CA1           ; If 0, exit

mov ax, 7894h
mov es, ax
cmp es:byte_7A30E, 0          ; Check menu_flag_byte_7a30e
jz short loc_1A5CA1           ; If 0, exit

jmp loc_1A5B60                ; Both flags set, continue to display

; Exit paths
loc_1A5CA1:
  jmp loc_1A5FA1              ; Exit
```

**Condition**: Both flags must be set to proceed to display. If either is 0, exits.

---

## State 2: Data Modification (Lines 366-426)

**Entry**: Line 366, Address 0x1A5CA4  
**Size**: 61 lines  
**Purpose**: Modifies data structure and checks validation

### Flow Overview

```
1. Animate transition
2. Call display update
3. Wait for input
4. Loop 20 times: UI frame + overlay calls
5. Modify dword_79E50 structure (add offsets to fields)
6. Check flags and validation
7. Conditional additional offset
8. Exit
```

### Entry and UI Loop (Lines 366-385)

```assembly
; Standard entry
mov ax, 7894h
mov es, ax
push es:current_view_index    ; Push state 2
call far ptr loc_67CA5+1      ; Animate
pop cx

call sub_12805C               ; Update
call menu_cursor_position_set ; Wait for input

; Loop 20 times (0x14)
mov [bp+var_4], 0
jmp short .loop_check

.loop_body:
  push [bp+var_4]
  call far ptr tail_bridge_to_ui_menu_frame_enter
  pop cx
  
  push [bp+var_4]
  call far ptr overlay_bridge_to_68019
  pop cx
  or ax, ax
  jg short .loop_body         ; If ax > 0, retry
  
  inc [bp+var_4]

.loop_check:
  cmp [bp+var_4], 14h         ; Loop 20 times
  jl short .loop_body
```

**Same 20-iteration pattern as State 4!** Likely processing 20 UI elements or data entries.

### Data Structure Modification (Lines 386-396)

```assembly
; Load pointer dword_79E50
mov ax, 7894h
mov es, ax
les bx, es:dword_79E50        ; Load far pointer

; Add 0x1E (30 decimal) to field at offset +0x24
add word ptr es:[bx+24h], 1Eh

; Add 0x1E to field at offset +0x26
mov es, ax
les bx, es:dword_79E50
add word ptr es:[bx+26h], 1Eh

; Add 0x203 (515 decimal) to dword at offset +0x00
mov es, ax
les bx, es:dword_79E50
add word ptr es:[bx], 203h    ; Low word
adc word ptr es:[bx+2], 0     ; High word with carry
```

**Data Structure at dword_79E50**:
- `+0x00` (dword): Incremented by 515 (0x203)
- `+0x24` (word): Incremented by 30 (0x1E)
- `+0x26` (word): Incremented by 30 (0x1E)

**Hypothesis**: These are coordinates or offsets being advanced. 515 pixels? 30-degree rotation?

### Validation and Conditional Addition (Lines 397-425)

```assembly
; Check flags
mov ax, 7894h
mov es, ax
cmp es:byte_7A302, 0          ; Check flag 1
jz short loc_1A5D6F           ; If 0, exit

mov ax, 7894h
mov es, ax
cmp es:byte_7A30E, 0          ; Check flag 2
jz short loc_1A5D6F           ; If 0, exit

; Both flags set, check additional condition
mov ax, 7894h
mov dx, 7894h
mov es, dx
mov dl, es:byte_7A30F         ; Load byte_7a30f
mov dh, 0                     ; Extend to word
mov es, ax
cmp es:word_79F34, dx         ; Compare menu_flight_record_sum < byte_7a30f
jge short loc_1A5D6F          ; If >= , skip additional offset

; Check array at segment 602Eh
mov es, ax
mov bx, es:word_79F34         ; Load sum
shl bx, 2                     ; Multiply by 4 (dword array)
mov ax, 602Eh
mov es, ax
cmp byte ptr es:[bx+1], 3     ; Check array[sum].byte_1 == 3
jnz short loc_1A5D6F          ; If != 3, skip

; Add additional offset
mov ax, 7894h
mov es, ax
les bx, es:dword_79E50
add word ptr es:[bx], 3Fh     ; Add 0x3F (63) to low word
adc word ptr es:[bx+2], 0     ; Carry to high word

jmp loc_1A5FA1                ; Exit
```

**Complex Validation**:
1. Both flags (byte_7A302, byte_7A30E) must be set
2. `menu_flight_record_sum` < `byte_7A30F` (some limit)
3. Array at `602Eh:[menu_flight_record_sum * 4 + 1]` == 3

**If all conditions met**: Add additional 63 (0x3F) to dword_79E50[0]

**Hypothesis**: Conditional offset based on weapon type or loadout configuration. Array at 602Eh likely stores weapon/item properties.

---

## State 3: Simple UI Loop (Lines 427-448)

**Entry**: Line 427, Address 0x1A5D72  
**Size**: 22 lines (shortest state)  
**Purpose**: Simple UI frame processing loop

### Complete Code (Lines 427-448)

```assembly
; Standard entry
mov ax, 7894h
mov es, ax
push es:current_view_index    ; Push state 3
call far ptr loc_67CA5+1      ; Animate
pop cx

call sub_12805C               ; Update
call menu_cursor_position_set ; Wait for input

; Loop 20 times
mov [bp+var_4], 0
jmp short .loop_check

.loop_body:
  push [bp+var_4]
  call far ptr tail_bridge_to_ui_menu_frame_enter
  pop cx
  
  push [bp+var_4]
  call far ptr overlay_bridge_to_68019
  pop cx
  or ax, ax
  jg short .loop_body         ; If ax > 0, retry
  
  inc [bp+var_4]

.loop_check:
  cmp [bp+var_4], 14h         ; Loop 20 times
  jl short .loop_body

; Call slot record init and exit
call far ptr tail_bridge_to_slot_record_init_b
jmp loc_1A5FA1                ; Exit
```

**Structure**: Nearly identical to State 2's loop, but without data modification. Just processes 20 UI frames and exits.

**Hypothesis**: State 3 is a **refresh/redraw** state that updates the display without modifying data.

---

## Comparison: States 1, 2, 3

### Common Patterns

All three states:
1. Animate transition (loc_67CA5+1)
2. Call sub_12805C (display update)
3. Call menu_cursor_position_set (wait for input)
4. Process data or UI
5. Exit to loc_1A5FA1 or continue to display

### Differences

| Aspect | State 1 | State 2 | State 3 |
|--------|---------|---------|---------|
| **Size** | 90 lines | 61 lines | 22 lines |
| **Input Handling** | Yes (key '6') | No | No |
| **Data Modification** | menu_temp_accumulator | dword_79E50 fields | None |
| **Validation** | 2 flags | 3 conditions + array | None |
| **Loop** | Sum calculation | 20 UI frames | 20 UI frames |
| **Purpose** | Sub-field navigation | Data/offset update | UI refresh |

### State Progression Hypothesis

Based on the patterns, a likely flow:

```
State 0: Select flight
    ↓
State 1: Select sub-field (weapon, quantity, etc.) within flight
    ↓
State 2: Modify selected sub-field (adjust values, update offsets)
    ↓
State 3: Refresh display
    ↓
State 4: Copy/save loadout data
    ↓
State 5: Cancel/back (jump to ESC handler)
    ↓
State 6: Exit with validation
```

---

## Key Variables

### State 1
- **menu_temp_accumulator** (word_79E88): Current sub-field index (0 to byte_4-1)
- **menu_flight_record_sum** (word_79F34): Global loadout array index
- **flight_record.byte_4**: Count of sub-fields for this flight
- **menu_flag_byte_7a302**, **menu_flag_byte_7a30e**: Display enable flags

### State 2
- **dword_79E50**: Data structure pointer
  - `+0x00` (dword): Incremented by 515, conditionally by 63
  - `+0x24` (word): Incremented by 30
  - `+0x26` (word): Incremented by 30
- **byte_7A30F**: Validation threshold
- **Array at 602Eh**: 4-byte stride, byte at +1 checked for == 3

### State 3
- No unique variables (uses standard UI loop)

---

## Data Structures

### Flight Record (130 bytes, 0x82)

From State 1 analysis:

| Offset | Type | Name | Purpose |
|--------|------|------|---------|
| +0x04 | byte | sub_field_count | Number of sub-fields (weapons, quantities, etc.) for this flight |
| +0x15 | byte | valid_flag | Must be != 0 for valid record (from State 0) |
| ... | ... | ... | (Other 128 bytes) |

**Key Discovery**: byte_4 is not just an accumulator value, it's a **count** of sub-elements!

### Structure at dword_79E50

From State 2 analysis:

| Offset | Type | Name | Purpose |
|--------|------|------|---------|
| +0x00 | dword | field_0 | Value incremented by 515 (+63 conditional) |
| +0x24 | word | field_24 | Value incremented by 30 |
| +0x26 | word | field_26 | Value incremented by 30 |
| ... | ... | ... | (Other fields unknown) |

**Hypothesis**: Coordinate or offset structure for UI positioning or 3D rendering.

### Array at Segment 602Eh

From State 2 validation:
- **Stride**: 4 bytes (dword)
- **Indexed by**: menu_flight_record_sum
- **Field checked**: Byte at offset +1
- **Value checked**: == 3 (triggers conditional offset)

**Hypothesis**: Weapon or loadout item property array. Byte +1 might be weapon type or category.

---

## Outstanding Questions

1. **What is dword_79E50?** Need to identify in globals. Structure with offsets being modified.

2. **What are the 515, 30, 63 values?** Pixels? Degrees? Game units?

3. **What is the array at 602Eh?** What do the 4 bytes represent?

4. **What is byte_7A30F?** Threshold value for validation.

5. **What triggers state transitions?** How does menu progress from State 1 → 2 → 3?

6. **Why 20 iterations?** Consistent across States 2, 3, 4. 20 weapons? 20 UI elements?

7. **What does overlay_bridge_to_68019 return?** Checked in retry loops.

8. **What is tail_bridge_to_slot_record_init_b?** Called at end of State 3.

---

## Hypotheses

### Hypothesis 1: Hierarchical Navigation
**Evidence**:
- State 0: Select flight (top level)
- State 1: Select sub-field within flight (second level)
- States 2-3: Modify and refresh display

**Interpretation**: Menu has hierarchical navigation: Flight → Weapon/Field → Value

### Hypothesis 2: Sub-Field = Weapons/Quantities
**Evidence**:
- byte_4 stores count of sub-fields per flight
- State 1 navigates through these sub-fields
- 20-iteration loops (20 = max weapons?)

**Interpretation**: Sub-fields are individual weapon slots or quantity values for the selected flight.

### Hypothesis 3: Offset Updates = Animation
**Evidence**:
- State 2 adds fixed values (515, 30, 30) to structure fields
- Values could be animation deltas or position offsets

**Interpretation**: State 2 advances an animation or scrolls display content.

---

## Next Steps

1. ⏳ Identify dword_79E50 in disassembly and add to globals
2. ⏳ Identify array at 602Eh structure
3. ⏳ Analyze overlay_bridge_to_68019 function
4. ⏳ Trace state transition triggers
5. ⏳ Determine purpose of 20-iteration loops
6. ⏳ Map complete flight record structure (128 bytes remaining)

---

*Extracted from: r57_state_machine_full_disasm.txt*  
*State 1: Lines 276-365 (90 lines)*  
*State 2: Lines 366-426 (61 lines)*  
*State 3: Lines 427-448 (22 lines)*
