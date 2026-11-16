# R57 State Machine - State 4 Detailed Analysis

## Overview

State 4 is the largest and most complex state in the R57 menu state machine (155 lines, 449-603). It appears to handle loadout configuration with data copying and initialization.

**Function**: `r57_menu_state_machine` at 0x1A57F0  
**State**: 4 (Fifth state - 0-indexed)  
**Entry**: Line 449, Address 0x1A5DBA  
**Exit**: Line 603 (jump to loc_1A5FA1)  
**Size**: 155 lines of disassembly

---

## High-Level Flow

State 4 has two distinct paths based on `menu_temp_accumulator` (word_79E88):

### Path A: menu_temp_accumulator == 0 (Lines 449-522)
**Initialization/Setup Path**
1. Animate transition
2. Call display update
3. Wait for input
4. Initialize UI fields
5. Call overlay bridges
6. Initialize 11 records (28 bytes each)
7. Set up data pointers
8. Transform coordinates
9. Set UI mode to 4
10. Jump to default render case

### Path B: menu_temp_accumulator != 0 (Lines 523-603)
**Data Processing Path**
1. Compute sum from flight records
2. Calculate source and destination pointers based on sum
3. Loop through 20 (0x14) iterations calling UI frame handlers
4. Copy 23 bytes (0x17) from source to destination
5. Call utility function
6. Check flag and continue or exit

---

## Detailed Analysis

### Entry and Branching (Lines 449-461)

```assembly
; Entry point
mov ax, 7894h
mov es, ax
push es:current_view_index    ; Push state 4
call far ptr loc_67CA5+1      ; Animate transition
pop cx

call sub_12805C               ; Display update
call menu_cursor_position_set ; Wait for input

; Branch decision
mov ax, 7894h
mov es, ax
cmp es:word_79E88, 0          ; Check menu_temp_accumulator
jz short loc_1A5DE4           ; If 0, go to Path A (init)
jmp loc_1A5EC8                ; If != 0, go to Path B (processing)
```

**Key Decision**: `menu_temp_accumulator` (word_79E88) determines which path to take.

---

## Path A: Initialization (Lines 461-522)

### Step 1: Prepare UI (Lines 461-477)

```assembly
call far ptr sub_2C72F        ; Unknown prep function
call sub_2C8FB                ; Unknown

; Get field index and push to overlay
mov ax, 7894h
mov es, ax
mov bx, es:word_79EA0         ; Load menu_ui_field_index
shl bx, 1                     ; Multiply by 2 (word array)
mov ax, 4FC2h
mov es, ax
push word ptr es:[bx+30Ah]    ; Push array[field_index] from 4FC2:030A

call overlay_bridge_to_68f9e  ; Pass to overlay

; Call overlay bridges
call overlay_bridge_to_68338
call overlay_bridge_to_68b4a
call overlay_bridge_to_68d32

push 6
call far ptr sub_2C351        ; Unknown with param 6
```

**Purpose**: Sets up UI state, calls overlay bridges with field index parameter.

### Step 2: Initialize 11 Records (Lines 478-497)

```assembly
; Loop: for (var_4 = 0; var_4 < 0xB; var_4++)
mov [bp+var_4], 0
jmp short .loop_check

.loop_body:
  ; Compute record offset: var_4 * 0x1C (28 bytes)
  mov ax, [bp+var_4]
  mov dx, 1Ch
  imul dx
  
  ; Set far pointer: record[var_4].ptr = 4FC2:0A68
  mov dx, 4FC2h
  mov bx, ax
  mov es, dx
  mov word ptr es:[bx+606h], 4FC2h    ; Segment
  mov word ptr es:[bx+604h], 0A68h    ; Offset
  
  ; Set field: record[var_4].word+8 = 6
  mov ax, [bp+var_4]
  mov dx, 1Ch
  imul dx
  mov dx, 4FC2h
  mov bx, ax
  mov es, dx
  mov word ptr es:[bx+608h], 6        ; record+8 = 6
  
  inc [bp+var_4]

.loop_check:
  cmp [bp+var_4], 0Bh         ; Loop while < 11
  jl short .loop_body
```

**Data Structure**: Array of 11 records at segment 4FC2:0604+
- Base: 4FC2:0604h
- Stride: 28 bytes (0x1C)
- Fields initialized:
  - `+0x00` (dword): Far pointer = 4FC2:0A68
  - `+0x04` (word): Value = 6

**Same pattern as State 0 initialization!** This suggests a reset or re-initialization.

### Step 3: Set Data Pointers (Lines 498-509)

```assembly
; Set up pointer 1
mov ax, 4FC2h
mov es, ax
mov es:word_13E94E, 4FC2h     ; Segment
mov es:word_13E94C, 868h      ; Offset
; Pointer 1 = 4FC2:0868h

; Set up pointer 2 (dword_79E68)
mov ax, 7894h
mov es, ax
mov word ptr es:dword_79E68+2, 4FC2h  ; Segment
mov word ptr es:dword_79E68, 600h     ; Offset
; dword_79E68 = 4FC2:0600h

; Set up pointer 3 (dword_79E2C)
mov ax, 7894h
mov es, ax
mov word ptr es:dword_79E2C+2, 4FC2h  ; Segment
mov word ptr es:dword_79E2C, 6A8h     ; Offset
; dword_79E2C = 4FC2:06A8h
```

**Three Pointers**:
1. 4FC2:13E94C/E = 4FC2:0868h
2. 7894:dword_79E68 = 4FC2:0600h
3. 7894:dword_79E2C = 4FC2:06A8h

### Step 4: Transform Coordinates (Lines 510-518)

```assembly
mov es, ax
les bx, es:dword_79E2C        ; Load pointer 3 (4FC2:06A8h)
push word ptr es:[bx+2]       ; Push word at offset +2
mov es, ax
les bx, es:dword_79E2C
push word ptr es:[bx]         ; Push word at offset +0
call ui_coordinate_transform  ; Transform (X, Y) coordinates
pop cx
pop cx
```

**Purpose**: Transforms a 2D coordinate pair from dword_79E2C[0] and dword_79E2C[2].

### Step 5: Set UI Mode and Exit (Lines 519-522)

```assembly
mov ax, 7894h
mov es, ax
mov es:word_79E9C, 4          ; Set menu_ui_mode_config = 4
jmp def_1A5A25                ; Jump to default render loop
```

**Exit**: Jumps to default case (render loop), which will display the initialized UI.

---

## Path B: Data Processing (Lines 523-603)

### Step 1: Compute Flight Record Sum (Lines 523-541)

```assembly
xor di, di                    ; DI = sum = 0
mov [bp+var_4], 0             ; Loop counter = 0
jmp short .loop_check

.loop_body:
  ; Compute flight record offset: var_4 * 0x82 (130 bytes)
  mov ax, [bp+var_4]
  mov dx, 82h
  imul dx
  
  ; Load flight record base pointer
  mov dx, 7894h
  mov es, dx
  les bx, es:dword_79BEC      ; Load menu_flight_records_ptr
  add bx, ax                  ; BX = base + offset
  
  ; Load byte at record+4 and add to sum
  mov al, es:[bx+4]           ; Load flight_record[var_4].byte_4
  cbw                         ; Sign-extend to word
  add di, ax                  ; sum += byte_4
  
  inc [bp+var_4]

.loop_check:
  mov ax, 7894h
  mov es, ax
  mov ax, es:word_79B62       ; Load menu_current_flight_index
  cmp ax, [bp+var_4]
  jg short .loop_body         ; Loop while var_4 < current_flight_index
```

**Result**: DI contains sum of `flight_record[i].byte_4` for i from 0 to current_flight_index-1.

**Same calculation as State 0!** But instead of storing in word_79F34, it uses DI for immediate calculation.

### Step 2: Calculate Source Pointer (Lines 542-551)

```assembly
; Source = dword_79E6C + (DI * 23)
mov ax, di                    ; Load sum
mov dx, 17h                   ; 23 decimal (0x17)
imul dx                       ; offset = sum * 23

mov dx, 7894h
mov es, dx
mov dx, word ptr es:dword_79E6C+2   ; Load segment
mov bx, word ptr es:dword_79E6C     ; Load offset
add bx, ax                    ; offset += sum * 23

; Save to local var: [bp+var_8] = far pointer
mov word ptr [bp+var_8+2], dx      ; Segment
mov word ptr [bp+var_8], bx        ; Offset
```

**Source Pointer**: `dword_79E6C + (sum * 23)`  
**Stride**: 23 bytes (0x17) - indexed by the computed sum

### Step 3: Calculate Destination Pointer (Lines 552-563)

```assembly
; Destination = dword_79E6C + (menu_flight_record_sum * 23)
mov ax, 7894h
mov es, ax
mov ax, es:word_79F34         ; Load menu_flight_record_sum (from State 0)
mov dx, 17h                   ; 23 decimal
imul dx                       ; offset = menu_flight_record_sum * 23

mov dx, 7894h
mov es, dx
mov dx, word ptr es:dword_79E6C+2   ; Load segment
mov bx, word ptr es:dword_79E6C     ; Load offset
add bx, ax                    ; offset += menu_flight_record_sum * 23

; Save to local var: [bp+var_C] = far pointer
mov word ptr [bp+var_C+2], dx      ; Segment
mov word ptr [bp+var_C], bx        ; Offset
```

**Destination Pointer**: `dword_79E6C + (menu_flight_record_sum * 23)`  
**Same array, different index**: Uses the sum computed in State 0

### Step 4: UI Frame Loop (Lines 564-576)

```assembly
xor si, si                    ; SI = counter = 0
jmp short .loop_check

.loop_body:
  push si
  call far ptr tail_bridge_to_ui_menu_frame_enter  ; Enter menu frame
  pop cx
  
.retry:
  push si
  call far ptr overlay_bridge_to_68019  ; Process overlay
  pop cx
  or ax, ax                   ; Check return value
  jnz short .retry            ; If != 0, retry
  
  inc si

.loop_check:
  cmp si, 14h                 ; Loop while SI < 20 (0x14)
  jl short .loop_body
```

**Purpose**: Calls UI frame enter and overlay bridge 20 times. The overlay bridge is retried until it returns 0.

**Iteration Count**: 20 (0x14) iterations - possibly 20 UI elements or animation frames?

### Step 5: Copy 23 Bytes (Lines 577-585)

```assembly
xor si, si                    ; SI = byte offset = 0
jmp short .loop_check

.loop_body:
  les bx, [bp+var_8]          ; Load source pointer
  mov al, es:[bx+si]          ; Load source[si]
  
  les bx, [bp+var_C]          ; Load destination pointer
  mov es:[bx+si], al          ; destination[si] = source[si]
  
  inc si

.loop_check:
  cmp si, 17h                 ; Loop while SI < 23 (0x17)
  jl short .loop_body
```

**Purpose**: Copies 23 bytes from source to destination.

**Data Flow**: `dword_79E6C[computed_sum * 23 .. +23]` → `dword_79E6C[menu_flight_record_sum * 23 .. +23]`

### Step 6: Utility Call and Exit (Lines 586-603)

```assembly
mov ax, 7894h
mov es, ax
push es:word_79F34            ; Push menu_flight_record_sum
call utility_large_2971       ; Unknown utility function
pop cx

; Check exit condition
mov ax, 7894h
mov es, ax
cmp es:byte_7A302, 0          ; Check menu_flag_byte_7a302
jz short loc_1A5FA1           ; If 0, exit to loc_1A5FA1
; Otherwise continue (lines 595-603 not shown in excerpt)
```

**Exit Condition**: If `menu_flag_byte_7a302` is 0, jumps to loc_1A5FA1. Otherwise continues (likely loops back).

---

## Data Structures

### Record Array at 4FC2:0604+ (28 bytes each, 11 records)

| Offset | Type | Name | Value (Init) | Purpose |
|--------|------|------|--------------|---------|
| +0x00 | dword | far_ptr | 4FC2:0A68 | Far pointer to data |
| +0x04 | word | field_4 | 6 | Unknown field |
| +0x06-0x1B | ? | ... | ? | Unknown (22 bytes) |

**Total Size**: 11 records × 28 bytes = 308 bytes (0x134)

### Array at dword_79E6C (23-byte stride)

**Base**: dword_79E6C (segment 7894h)  
**Stride**: 23 bytes (0x17)  
**Indexing**: By sum of flight_record[].byte_4 values

**Purpose**: Appears to be loadout data indexed by a computed sum. State 4 copies one 23-byte entry to another based on flight selection.

**Hypothesis**: This array stores loadout configurations, and State 4 is copying the loadout for the computed flight to the loadout for the previously selected flight.

---

## Control Flow

```
State 4 Entry
    ↓
Animate + Update + Wait for Input
    ↓
Check menu_temp_accumulator (word_79E88)
    ↓
    ├─ == 0 ─→ Path A: Initialize UI
    │           ├─ Prepare UI fields
    │           ├─ Initialize 11 records (28B each)
    │           ├─ Set 3 data pointers
    │           ├─ Transform coordinates
    │           ├─ Set UI mode = 4
    │           └─ Jump to default render
    │
    └─ != 0 ─→ Path B: Process Data
                ├─ Compute sum from flight records (DI)
                ├─ Calculate source ptr: dword_79E6C + (DI * 23)
                ├─ Calculate dest ptr: dword_79E6C + (word_79F34 * 23)
                ├─ Loop 20 times: UI frame + overlay calls
                ├─ Copy 23 bytes: source → destination
                ├─ Call utility_large_2971(word_79F34)
                └─ Check flag and exit or continue
```

---

## Key Variables

| Variable | Type | Purpose in State 4 |
|----------|------|-------------------|
| current_view_index | word | State selector (= 4) |
| menu_temp_accumulator (word_79E88) | word | Path selector (0=init, !=0=process) |
| menu_ui_field_index (word_79EA0) | word | UI field index for overlay call |
| menu_current_flight_index (word_79B62) | word | Loop limit for sum calculation |
| menu_flight_records_ptr (dword_79BEC) | dword | Base pointer for flight records |
| menu_flight_record_sum (word_79F34) | word | Destination index (from State 0) |
| dword_79E6C | dword | Base pointer for 23-byte loadout array |
| dword_79E68 | dword | Data pointer 2 (set to 4FC2:0600) |
| dword_79E2C | dword | Data pointer 3 (set to 4FC2:06A8, coordinates) |
| menu_flag_byte_7a302 (byte_7A302) | byte | Exit condition flag |
| [bp+var_4] | word | Local loop counter |
| [bp+var_8] | dword | Local source pointer |
| [bp+var_C] | dword | Local destination pointer |
| DI | word | Computed sum accumulator |
| SI | word | Loop counter / byte offset |

---

## Outstanding Questions

1. **What sets menu_temp_accumulator?** How does the menu determine whether to take Path A or B?

2. **What is the 23-byte structure?** Stride is 23 bytes, indexed by flight record sum - likely loadout config.

3. **What is utility_large_2971?** Called with menu_flight_record_sum parameter. Utility function name suggests large/complex operation.

4. **What are the 11 records for?** Initialized in both State 0 and State 4 Path A - UI elements? Menu slots?

5. **Why 20 iterations?** UI frame loop runs 20 times - 20 weapons? 20 UI elements? 20 animation frames?

6. **What is overlay_bridge_to_68019?** Called in retry loop until returns 0.

7. **What is dword_79E6C?** Base pointer for loadout array. Need to identify in globals.

8. **What happens after line 595?** If menu_flag_byte_7a302 != 0, what path is taken?

---

## Hypotheses

### Hypothesis 1: Loadout Copy Operation
**Evidence**:
- Computes sum from flight records (index into loadout array)
- Copies 23 bytes from computed index to stored index
- Uses menu_flight_record_sum from State 0 as destination
- Called after flight selection in menu flow

**Interpretation**: State 4 copies the selected flight's loadout configuration to the active/editing slot.

### Hypothesis 2: Two-Phase State
**Evidence**:
- Branch on menu_temp_accumulator
- Path A initializes UI (first entry into state)
- Path B processes data (subsequent entries)

**Interpretation**: State 4 is entered multiple times. First entry initializes (menu_temp_accumulator=0), subsequent entries process changes (menu_temp_accumulator!=0).

### Hypothesis 3: 23-Byte Loadout Structure
**Evidence**:
- Stride is 23 bytes
- Indexed by computed sum (not simple index)
- Copied as a unit

**Possible Structure** (speculation):
```
struct loadout_config {
    byte weapon_types[9];      // 9 hardpoints, 1 byte each = 9B
    word quantities[7];        // 7 weapon quantities = 14B
    // Total: 23 bytes
}
```

---

## Next Steps

1. ⏳ Find dword_79E6C in disassembly and add to globals registry
2. ⏳ Analyze utility_large_2971 function
3. ⏳ Trace what sets menu_temp_accumulator
4. ⏳ Analyze overlay_bridge_to_68019 function
5. ⏳ Determine the 23-byte loadout structure
6. ⏳ Understand the 11 record array purpose
7. ⏳ Document complete Path B exit logic (lines 595-603)

---

*Extracted from: r57_state_machine_full_disasm.txt*  
*State 4: Lines 449-603 (155 lines)*
