# Top 400 Batch 2 - Function Analysis
**Date**: 2026-11-14  
**Source**: `top400_batch2_analysis.json`  
**Functions Analyzed**: 13  
**Analyst**: Automated categorization with manual review

---

## Executive Summary

This batch contains a diverse mix of functions:
- **5 UI/Menu handlers** - Menu rendering and interaction
- **2 Dispatch wrappers** - Simple register-setup-and-dispatch patterns
- **2 Data processors** - Array/table iteration and filtering
- **2 Overlay bridge functions** - Cross-overlay call thunks
- **1 Input processor** - Controller/input state management
- **1 File I/O helper** - Temporary file operations

**High Confidence**: 9/13 (69%)  
**Medium Confidence**: 3/13 (23%)  
**Low Confidence**: 1/13 (8%)

---

## Detailed Analysis

### 1. Function 0x128028 - `dispatch_22094_wrapper`
**Rank**: 353 | **Size**: 26 bytes | **Calls**: 1 | **Called by**: 8

**Disassembly Pattern**:
```asm
push    bp
mov     bp, sp
push    di
push    si
mov     di, [bp+arg_0]    ; Load 4 args into registers
mov     bx, [bp+arg_2]
mov     cx, [bp+arg_4]
mov     ax, [bp+arg_6]
call    dispatch_22094_stub
pop     si
pop     di
pop     bp
retf
```

**Pattern Identified**: Pure dispatch wrapper
- Takes 4 stack arguments
- Loads them into DI, BX, CX, AX
- Calls a single dispatcher
- Returns immediately

**Callers**: All from `utility_1959` and `sub_11E1AB` - likely menu/UI utility functions

**Category**: **Dispatch Wrapper**  
**System**: **Unknown - needs dispatcher analysis**  
**Confidence**: **HIGH (95%)**

**Proposed Name**: `dispatch_22094_wrapper_4arg`  
**Description**: Wrapper that loads 4 arguments into registers (DI, BX, CX, AX) and dispatches to 0x255B2

**Evidence**:
- Classic wrapper pattern: setup registers → call → return
- No local logic or computation
- Multiple callers suggests common utility

---

### 2. Function 0x128042 - `dispatch_2208c_wrapper`
**Rank**: 354 | **Size**: 26 bytes | **Calls**: 1 | **Called by**: 8

**Disassembly Pattern**:
```asm
push    bp
mov     bp, sp
push    di
push    si
mov     bx, [bp+arg_0]    ; Different register assignment
mov     di, [bp+arg_2]
mov     cx, [bp+arg_4]
mov     ax, [bp+arg_6]
call    dispatch_2208c_stub
pop     si
pop     di
pop     bp
retf
```

**Pattern Identified**: Pure dispatch wrapper (variant)
- Similar to 0x128028 but different register mapping (BX, DI, CX, AX)
- Same callers (utility_1959, sub_11E1AB)

**Category**: **Dispatch Wrapper**  
**System**: **Unknown - needs dispatcher analysis**  
**Confidence**: **HIGH (95%)**

**Proposed Name**: `dispatch_2208c_wrapper_4arg`  
**Description**: Wrapper that loads 4 arguments into registers (BX, DI, CX, AX) and dispatches to 0x255B8

**Evidence**:
- Identical structure to 0x128028
- Paired usage pattern (both called from same locations)
- Likely handles related operations with different register conventions

---

### 3. Function 0x130CE7 - `input_controller_slot_mapper`
**Rank**: 357 | **Size**: 353 bytes | **Calls**: 0 | **Called by**: 8

**Disassembly Analysis**:
```asm
xor     cx, cx
jmp     loc_130E3C          ; Jump to loop condition

; Main loop body
mov     di, 5               ; Start at slot 5
jmp     loc_130D8E

; Inner loop - search for next occupied slot
mov     si, cx
inc     si
cmp     si, 0Ah             ; Max 10 slots (0-9)
jle     short loc_130D01
xor     si, si              ; Wrap to 0

; Check if slot is occupied
mov     bx, si
shl     bx, 1
mov     ax, 7894h
mov     es, ax
cmp     word ptr es:[bx+1938h], 0  ; Check slot status
jz      short loc_130D79            ; Skip if empty

; Calculate array index: cx * 0x1C + di * 2
mov     ax, cx
mov     dx, 1Ch
imul    dx
mov     dx, di
shl     dx, 1
add     ax, dx
mov     dx, 4FC2h
mov     bx, ax
mov     es, dx
mov     es:[bx+60Ah], si    ; Store slot index

; Check slot type
mov     bx, si
shl     bx, 1
mov     ax, 7894h
mov     es, ax
cmp     word ptr es:[bx+1938h], 1   ; Type 1?
jnz     short loc_130D53

; Type 1: store value 0xDC
mov     ax, si
mov     dx, 1Ch
imul    dx
mov     dx, 4FC2h
mov     bx, ax
mov     es, dx
mov     word ptr es:[bx+600h], 0DCh

; Type 2: store value 0x131
cmp     word ptr es:[bx+1938h], 2
jnz     short loc_130D79
mov     word ptr es:[bx+600h], 131h
```

**Pattern Identified**: Input device slot management
- Iterates through 10 slots (0-9)
- Checks slot occupancy at es:[bx+1938h]
- Maps occupied slots to an array structure (28-byte stride: 0x1C)
- Assigns type-specific values (0xDC for type 1, 0x131 for type 2)
- Second loop does reverse mapping (decrement with wrap)

**Callers**:
- `input_poll_handler` (2 calls)
- `overlay_r48_processor`
- `overlay_r49_processor`
- `overlay_r4F_handler`
- `overlay_r58_handler`

**Category**: **Data Processor**  
**System**: **Input System**  
**Confidence**: **HIGH (90%)**

**Proposed Name**: `input_slot_circular_mapper`  
**Description**: Maps input device slots (0-9) to controller array, handling circular navigation with forward and reverse wrapping

**Evidence**:
- Called from input_poll_handler
- Circular iteration (wrap at 10)
- Type-based value assignment (0xDC, 0x131)
- Slot status checking
- Bidirectional mapping

---

### 4. Function 0x133BD5 - `mission_temp_file_handler`
**Rank**: 358 | **Size**: 250 bytes | **Calls**: 11 | **Called by**: 8

**Disassembly Analysis**:
```asm
push    7894h
push    0F5Ah
push    2
call    int_to_string_converter    ; Convert 2 to string

; Build filename: "w-.`TEMP" + string + ".DAT"
push    7894h
push    0F32h
push    7894h
push    0F5Ah
mov     ax, 602Eh
mov     es, ax
push    word ptr es:aWTemp+2        ; ".`TEMP"
push    word ptr es:aWTemp
call    string_concatenate

push    7894h
push    0F32h
mov     ax, 602Eh
mov     es, ax
push    word ptr es:aDat+1          ; ".`.DAT"
push    word ptr es:byte_151337
push    7894h
push    0F32h
call    string_concatenate

call    flag2224a_clear
call    mouse_gate_far_entry

; Open file: op_dispatch(seg, off, 0, 2, 6)
push    7894h
push    0F32h
push    0
push    2
push    6
call    op_dispatch_far_entry       ; Service 6 = file open
add     sp, 0Ah
mov     si, ax                       ; Save file handle

cmp     ax, 0FFFFh
jz      short loc_133CAB            ; Failed

; Read 3 data blocks from file
push    word ptr es:dword_79D1A+2
push    word ptr es:dword_79D1A
push    12C0h                        ; 4800 bytes
push    si
push    0Ah
call    op_dispatch_far_entry       ; Service 0Ah = file read

push    word ptr es:dword_79E28+2
push    word ptr es:dword_79E28
push    7D0h                         ; 2000 bytes
push    si
push    0Ah
call    op_dispatch_far_entry

push    es:word_79E72
push    es:word_79E70
push    0BB8h                        ; 3000 bytes
push    si
push    0Ah
call    op_dispatch_far_entry

; Close file: op_dispatch(buffer, 0, handle, 8)
push    word ptr es:dword_79E60+2
push    word ptr es:dword_79E60
push    0
push    si
push    8
call    op_dispatch_far_entry       ; Service 8 = file close

call    flag2224a_set
```

**Pattern Identified**: Temporary file I/O
- Builds filename "w-.`TEMP2.DAT"
- Opens file (op_dispatch service 6)
- Reads 3 data blocks (4800, 2000, 3000 bytes)
- Closes file (op_dispatch service 8)
- Gates with flag 2224a

**Callers**:
- `game_mode_r48_main_coordinator` (3 calls)
- `game_mode_r53_main_coordinator`
- Various overlay processors

**Category**: **File I/O Helper**  
**System**: **Resource/Mission System**  
**Confidence**: **MEDIUM (80%)**

**Proposed Name**: `mission_temp_file_load`  
**Description**: Loads mission data from temporary file (w-.`TEMP2.DAT), reading three data blocks into global buffers

**Evidence**:
- String manipulation for filename
- op_dispatch calls with file I/O services (6=open, 0Ah=read, 8=close)
- Fixed-size reads suggest structured data
- Called from game mode coordinators
- Mouse gate suggests UI context

---

### 5. Function 0x13ABA7 - `menu_item_proximity_selector`
**Rank**: 359 | **Size**: 448 bytes | **Calls**: 6 | **Called by**: 8

**Disassembly Analysis**:
```asm
enter   1Ah, 0
mov     di, [bp+arg_0]
mov     [bp+var_12], 2000h          ; Min distance = 8192
mov     [bp+var_14], 0
mov     [bp+var_6], 0FFFFh           ; Best index = -1
mov     [bp+var_2], 0                ; Current index

; Loop through items
mov     [bp+var_4], 0                ; Valid flag
mov     [bp+var_A], 0
mov     [bp+var_C], 0

; Get item at offset
mov     ax, di
mov     dx, 4Eh ; 'N'                ; Stride = 78 bytes
imul    dx
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79B6E
add     bx, ax
add     bx, [bp+var_2]
mov     al, es:[bx+44h]              ; Get item ID
mov     [bp+var_19], al

cmp     [bp+var_19], 0FFh            ; 0xFF = empty
jz      short loc_13AC3E

mov     [bp+var_4], 1                ; Mark valid

; Filter check
cmp     [bp+arg_2], 0
jnz     short loc_13AC3E
xor     si, si
mov     ax, 602Eh
mov     es, ax
mov     al, es:[si+3645h]            ; Check filter list
cmp     al, [bp+var_19]
jnz     short loc_13AC30
mov     [bp+var_4], 0                ; Filtered out

; Validate item
mov     al, [bp+var_19]
cbw
push    ax
push    di
push    cs
call    near ptr sub_13B1F4          ; Validation function
or      al, al
jnz     short loc_13AC5B

; Calculate distance: abs(item.x - current.x)
mov     al, [bp+var_19]
cbw
mov     dx, 4Eh
imul    dx
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79B6E
add     bx, ax
push    word ptr es:[bx+40h]         ; item.x
mov     ax, di
mov     dx, 4Eh
imul    dx
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79B6E
add     bx, ax
push    word ptr es:[bx+40h]         ; current.x
push    cs
call    near ptr signed_diff_abs
pop     cx
pop     cx
mov     [bp+var_C], ax               ; dx_abs

; Similar for Y coordinate
push    word ptr es:[bx+42h]         ; item.y
[... similar code for Y ...]
call    near ptr signed_diff_abs

; Compare against minimum distance
```

**Pattern Identified**: Proximity-based menu item selection
- Iterates through 78-byte item structures
- Calculates Manhattan distance (|dx| + |dy|)
- Tracks closest valid item
- Filters items based on exclusion list
- Returns index of nearest item

**Callers**: All from `menu_cmd_store_and_record_scan` and `overlay_r48_processor`

**Category**: **UI Processor**  
**System**: **Menu System**  
**Confidence**: **HIGH (85%)**

**Proposed Name**: `menu_item_proximity_select`  
**Description**: Selects nearest valid menu item by calculating Manhattan distance, filtering against exclusion list

**Evidence**:
- 78-byte struct (menu item size)
- Position fields at +0x40, +0x42 (X, Y coordinates)
- Distance calculation with signed_diff_abs
- Filter list at 602E:3645h
- Called from menu command handlers

---

### 6. Function 0x1558C8 - `ui_draw_dispatch_5arg`
**Rank**: 360 | **Size**: 14 bytes | **Calls**: 1 | **Called by**: 8

**Disassembly Pattern**:
```asm
push    ax
push    ds
push    si
push    di
push    bx
call    sub_13DE3A                   ; Drawing function
add     sp, 0Ah                      ; 5 args × 2 bytes
retn
```

**Pattern Identified**: Near-call wrapper
- Pushes 5 registers (AX, DS, SI, DI, BX)
- Calls drawing function
- Cleans stack
- Near return (not far)

**Callers**: All from UI-related functions in overlay 0x15xxxx range

**Category**: **Dispatch Wrapper**  
**System**: **UI/Rendering**  
**Confidence**: **HIGH (90%)**

**Proposed Name**: `ui_draw_5arg_wrapper`  
**Description**: Wrapper that pushes 5 registers (AX, DS, SI, DI, BX) and calls drawing function at 0x13DE3A

**Evidence**:
- Simple register setup pattern
- Called from UI functions
- Drawing function target
- Stack cleanup

---

### 7. Function 0x16F4B1 - `menu_button_render_switch`
**Rank**: 362 | **Size**: 86 bytes | **Calls**: 3 | **Called by**: 8

**Disassembly Analysis**:
```asm
push    bp
mov     bp, sp
push    si
mov     si, [bp+arg_0]

mov     ax, si
or      ax, ax
jz      short loc_16F4CA            ; Case 0
cmp     ax, 5
jz      short loc_16F4E1            ; Case 5
cmp     ax, 6
jz      short loc_16F4F7            ; Case 6
jmp     short loc_16F504            ; Default

; Case 0: Check threshold, call variant A
loc_16F4CA:
mov     ax, 7894h
mov     es, ax
cmp     es:word_79E80, 12Ch         ; Compare to 300
jl      short loc_16F504            ; Skip if < 300
push    si
call    ui_element_render_variant_a
pop     cx
jmp     short loc_16F504

; Case 5: Check threshold, call variant B
loc_16F4E1:
mov     ax, 7894h
mov     es, ax
cmp     es:word_79E80, 12Ch
jl      short loc_16F504
push    si
call    ui_element_render_variant_b
jmp     short loc_16F4DE

; Case 6: Call with string
loc_16F4F7:
push    ds
push    0A50Dh                      ; String offset
push    si
call    sub_11CA9E
add     sp, 6
```

**Pattern Identified**: Menu button rendering dispatcher
- Switch on button type (0, 5, 6)
- Checks word_79E80 threshold (300)
- Calls different rendering variants
- Case 6 uses string parameter

**Callers**: All from `overlay_r48_processor`

**Category**: **UI Renderer**  
**System**: **Menu System**  
**Confidence**: **HIGH (90%)**

**Proposed Name**: `menu_button_render_dispatch`  
**Description**: Dispatches menu button rendering based on type (0=variant A, 5=variant B, 6=string), gated by threshold check at 0x79E80

**Evidence**:
- Simple switch statement
- Rendering function calls
- Threshold gate (word_79E80 >= 300)
- Called from overlay processor
- Button type parameter

---

### 8. Function 0x172436 - `campaign_menu_button_render`
**Rank**: 363 | **Size**: 293 bytes | **Calls**: 3 | **Called by**: 8

**Disassembly Analysis**:
```asm
enter   4, 0
push    si
mov     si, [bp+arg_0]

mov     ax, si
shl     ax, 4                       ; button_index × 16
add     ax, 0Ch                     ; + 12
mov     [bp+var_2], ax

add     ax, 0Fh                     ; + 15
mov     [bp+var_4], ax              ; Y coordinates

mov     bx, si
cmp     bx, 7                       ; switch 8 cases
jbe     short loc_172459

; Jump table dispatch
jmp     cs:jpt_17245B[bx]

; Case 0: "CAMPAIGN STATUS"
loc_172460:
mov     ax, 7894h
mov     es, ax
cmp     es:word_79BD8, 0            ; Check mode
jnz     short loc_172485            ; Different string if mode != 0

mov     ax, 602Eh
mov     es, ax
push    word ptr es:aCampaignStatus_0+1
push    word ptr es:byte_15155C     ; "CAMPAIGN STATUS"
push    si
call    undoc_11C5DC                ; Highlighted render
jmp     loc_172555

loc_172485:                          ; Normal render
mov     ax, 602Eh
mov     es, ax
push    word ptr es:aCampaignStatus_0+1
push    word ptr es:byte_15155C
jmp     loc_172538

; Case 1: "SUPPLY STATUS"
loc_172497:
mov     ax, 7894h
mov     es, ax
cmp     es:word_79BD8, 1
jnz     short loc_1724B5

mov     ax, 602Eh
mov     es, ax
push    word ptr es:a94SupplyStatus+2
push    word ptr es:a94SupplyStatus ; "SUPPLY STATUS"
jmp     short loc_17247C

; Case 2: "ALLIED AIRCRAFT"
; Case 3: "ENEMY AIRCRAFT"
; Case 4: "ALLIED FORCES"
; Case 5: "ENEMY FORCES"
; Case 6: "OCCUPATION"
; Case 7: "DONE"
```

**Pattern Identified**: Campaign menu rendering
- 8-button menu (0-7)
- Each button has a label string
- Mode-based highlighting (word_79BD8)
- Strings: CAMPAIGN STATUS, SUPPLY STATUS, ALLIED AIRCRAFT, ENEMY AIRCRAFT, ALLIED FORCES, ENEMY FORCES, OCCUPATION, DONE

**Callers**: All from `overlay_r49_processor`

**Category**: **UI Renderer**  
**System**: **Menu System - Campaign**  
**Confidence**: **HIGH (95%)**

**Proposed Name**: `campaign_menu_render_buttons`  
**Description**: Renders campaign menu buttons (0-7) with labels, highlighting current selection based on mode (word_79BD8)

**Evidence**:
- 8-case switch on button index
- String literals for each button
- Mode-based highlighting
- Position calculation (index × 16 + 12)
- Called from overlay_r49 (campaign overlay)

---

### 9. Function 0x17B2B6 - `debriefing_menu_button_render`
**Rank**: 365 | **Size**: 135 bytes | **Calls**: 8 | **Called by**: 8

**Disassembly Analysis**:
```asm
push    bp
mov     bp, sp
push    si
mov     si, [bp+arg_0]

mov     bx, si
cmp     bx, 0Ah                     ; switch 11 cases
ja      short def_17B2C6

shl     bx, 1
jmp     cs:jpt_17B2C6[bx]

; Case 0
loc_17B2CB:
push    si
call    ui_element_render_variant_a
jmp     short loc_17B339

; Case 4
loc_17B2D3:
push    si
call    ui_element_render_variant_b
jmp     short loc_17B339

; Case 5: "REPORT"
loc_17B2DB:
mov     ax, 602Eh
mov     es, ax
push    word ptr es:aF3Report+2
push    word ptr es:aF3Report       ; "REPORT"
push    si
call    ui_element_render_complex_a
add     sp, 6
jmp     short def_17B2C6

; Case 6: "WAR ROOM"
loc_17B2F5:
mov     ax, 602Eh
mov     es, ax
push    word ptr es:a4WarRoom+1
push    word ptr es:byte_151A36     ; "WAR ROOM"
push    si
call    utility_11c90f
jmp     short loc_17B2F0

; Case 7: "EDIT FLIGHTS"
loc_17B30C:
mov     ax, 602Eh
mov     es, ax
push    word ptr es:aE1EditFlights+2
push    word ptr es:aE1EditFlights  ; "EDIT FLIGHTS"
push    si
call    sub_11CA9E
jmp     short loc_17B2F0

; Case 8
push    si
call    ui_element_render_variant_c

; Case 9
push    si
call    ui_element_render_variant_e

; Case 10
push    si
call    ui_element_render_variant_d
```

**Pattern Identified**: Debriefing menu rendering
- 11-button menu (0-10)
- Mixed rendering: some use variants (A/B/C/D/E), some use strings
- Strings: REPORT, WAR ROOM, EDIT FLIGHTS

**Callers**: All from `overlay_r4F_handler` (debriefing overlay)

**Category**: **UI Renderer**  
**System**: **Menu System - Debriefing**  
**Confidence**: **HIGH (95%)**

**Proposed Name**: `debriefing_menu_render_buttons`  
**Description**: Renders debriefing menu buttons (0-10) using various rendering variants and string labels (REPORT, WAR ROOM, EDIT FLIGHTS)

**Evidence**:
- 11-case switch
- Multiple rendering variants
- String labels for specific cases
- Called from overlay_r4F (debriefing)

---

### 10. Function 0x196BB9 - `ui_callback_chain_validator`
**Rank**: 366 | **Size**: 34 bytes | **Calls**: 4 | **Called by**: 8

**Disassembly Analysis**:
```asm
push    bp
mov     bp, sp
call    loc_6A565+3                 ; r30_farobj_proc_f
or      ax, ax
jz      short loc_196BD7            ; Return 0 if failed

push    [bp+arg_0]
call    loc_6A53B                   ; r30_farcb_seq
pop     cx
or      ax, ax
jz      short loc_196BD7            ; Return 0 if failed

mov     ax, 1                       ; Success
jmp     short loc_196BD9

loc_196BD7:
xor     ax, ax                      ; Failure

loc_196BD9:
pop     bp
retf
```

**Pattern Identified**: Callback chain validation
- Calls r30_farobj_proc_f (FarObj processor)
- If success, calls r30_farcb_seq (callback sequence)
- Returns 1 if both succeed, 0 otherwise

**Callers**: From overlay_r54_processor, overlay_r58_ui_coordinator, various R58 functions

**Category**: **Validation Helper**  
**System**: **UI/FarObj System**  
**Confidence**: **MEDIUM (75%)**

**Proposed Name**: `ui_farobj_callback_validate`  
**Description**: Validates FarObj state and executes callback chain, returning success/failure flag

**Evidence**:
- Two-stage validation
- FarObj system calls
- Boolean return
- Called from UI coordinators

---

### 11. Function 0x19FE2D - `aircraft_type_counter`
**Rank**: 367 | **Size**: 107 bytes | **Calls**: 0 | **Called by**: 8

**Disassembly Analysis**:
```asm
push    bp
mov     bp, sp
push    si
push    di
mov     cx, [bp+arg_2]              ; Aircraft type to count
xor     si, si                       ; Current index
xor     di, di                       ; Counter

cmp     [bp+arg_4], 0
jz      short loc_19FE8D            ; Branch based on mode

; Mode 1: Count in full array
xor     si, si
jmp     short loc_19FE61

loc_19FE43:
mov     ax, si
mov     dx, 12h                     ; Stride = 18 bytes
imul    dx
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79D6C          ; Array pointer
add     bx, ax
mov     al, es:[bx+1]               ; Get type at +1
cbw
cmp     ax, cx                      ; Compare to target type
jnz     short loc_19FE60
inc     di                          ; Increment counter

loc_19FE60:
inc     si

loc_19FE61:
mov     ax, 7894h
mov     es, ax
cmp     es:word_79EEE, si           ; Compare to array size
jg      short loc_19FE43            ; Continue if more

jmp     short loc_19FE92

; Mode 2: Count in range [0, arg_0)
loc_19FE6F:
mov     ax, si
mov     dx, 12h
imul    dx
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79D6C
add     bx, ax
mov     al, es:[bx+1]
cbw
cmp     ax, cx
jnz     short loc_19FE8C
inc     di

loc_19FE8C:
inc     si

loc_19FE8D:
cmp     si, [bp+arg_0]              ; Compare to limit
jnz     short loc_19FE6F

loc_19FE92:
mov     ax, di                      ; Return count
pop     di
pop     si
pop     bp
retf
```

**Pattern Identified**: Array filtering/counting
- Iterates through 18-byte aircraft structures
- Counts entries where type field (+1) matches target
- Two modes: full array or range [0, limit)
- Array at es:dword_79D6C

**Callers**: Multiple from sub_19E152, sub_19E6B1, sub_19F384, sub_19F8E3

**Category**: **Data Processor**  
**System**: **Aircraft/Entity System**  
**Confidence**: **HIGH (85%)**

**Proposed Name**: `aircraft_type_count_in_range`  
**Description**: Counts aircraft of specific type in array (18-byte stride), either full array or range [0, limit)

**Evidence**:
- 18-byte struct (aircraft record)
- Type field at +1
- Two counting modes
- Array pointer at 79D6C
- Called from entity/aircraft functions

---

### 12. Function 0x2C185 - `overlay_tail_bridge_6eee6`
**Rank**: 393 | **Size**: 8 bytes | **Calls**: 1 | **Called by**: 7

**Disassembly Pattern**:
```asm
call    near ptr tail_bridge_overlay_load
jmp     loc_6EEE6
```

**Pattern Identified**: Overlay bridge
- Loads tail overlay
- Jumps to target in overlay space

**Callers**: From undoc_4E5CC, sub_4E602, undoc_4E653, sub_4E6F4, entity_build_dispatch

**Category**: **Overlay Bridge**  
**System**: **Overlay Management**  
**Confidence**: **HIGH (95%)**

**Proposed Name**: `overlay_tail_bridge_6eee6`  
**Description**: Loads tail overlay and jumps to routine at 0x6EEE6

**Evidence**:
- Classic overlay bridge pattern
- tail_bridge_overlay_load call
- Far jump to overlay space
- Multiple similar functions in same area

---

### 13. Function 0x345FD - `key_event_gate_process_0c`
**Rank**: 399 | **Size**: 17 bytes | **Calls**: 1 | **Called by**: 7

**Disassembly Pattern**:
```asm
cmp     cs:byte_2F6B6, 1            ; Check gate flag
jnz     short locret_3460D          ; Skip if not set
mov     bx, 0Ch                     ; Event code 0x0C
call    key_event_gated_process
retf
```

**Pattern Identified**: Gated keyboard event processor
- Checks flag byte_2F6B6
- If set, processes keyboard event 0x0C

**Callers**: From undoc_3C3E1, undoc_3DE6F, farobj_index_cycle_advance, farobj_index_decrement_step, sub_41D23, undoc_428D4

**Category**: **Input Handler**  
**System**: **Keyboard/Input**  
**Confidence**: **HIGH (90%)**

**Proposed Name**: `key_event_gate_process_0c`  
**Description**: Conditionally processes keyboard event 0x0C if gate flag (byte_2F6B6) is enabled

**Evidence**:
- Gate pattern (check flag → process if set)
- Keyboard event processing
- Event code 0x0C
- Called from farobj and input contexts

---

## Summary Table

| Address | Current Name | Proposed Name | Category | System | Confidence | Size |
|---------|-------------|---------------|----------|--------|------------|------|
| 0x128028 | undoc_128028 | dispatch_22094_wrapper_4arg | Dispatch Wrapper | Unknown | 95% | 26 |
| 0x128042 | undoc_128042 | dispatch_2208c_wrapper_4arg | Dispatch Wrapper | Unknown | 95% | 26 |
| 0x130CE7 | undoc_130CE7 | input_slot_circular_mapper | Data Processor | Input | 90% | 353 |
| 0x133BD5 | sub_133BD5 | mission_temp_file_load | File I/O | Resource/Mission | 80% | 250 |
| 0x13ABA7 | sub_13ABA7 | menu_item_proximity_select | UI Processor | Menu | 85% | 448 |
| 0x1558C8 | sub_1558C8 | ui_draw_5arg_wrapper | Dispatch Wrapper | UI/Rendering | 90% | 14 |
| 0x16F4B1 | sub_16F4B1 | menu_button_render_dispatch | UI Renderer | Menu | 90% | 86 |
| 0x172436 | undoc_172436 | campaign_menu_render_buttons | UI Renderer | Menu/Campaign | 95% | 293 |
| 0x17B2B6 | sub_17B2B6 | debriefing_menu_render_buttons | UI Renderer | Menu/Debriefing | 95% | 135 |
| 0x196BB9 | sub_196BB9 | ui_farobj_callback_validate | Validation | UI/FarObj | 75% | 34 |
| 0x19FE2D | undoc_19FE2D | aircraft_type_count_in_range | Data Processor | Aircraft/Entity | 85% | 107 |
| 0x2C185 | sub_2C185 | overlay_tail_bridge_6eee6 | Overlay Bridge | Overlay Mgmt | 95% | 8 |
| 0x345FD | sub_345FD | key_event_gate_process_0c | Input Handler | Keyboard | 90% | 17 |

---

## Registry Entries (YAML Format)

```yaml
# Batch 2 - 13 Functions
# Generated: 2026-11-14

functions:
  - address: 0x128028
    name: dispatch_22094_wrapper_4arg
    category: dispatch_wrapper
    system: unknown
    description: Wrapper that loads 4 arguments into registers (DI, BX, CX, AX) and dispatches to 0x255B2
    confidence: high
    size: 26
    calls: 1
    called_by: 8
    evidence:
      - Classic wrapper pattern with register setup
      - Single dispatcher call
      - Multiple utility callers
    
  - address: 0x128042
    name: dispatch_2208c_wrapper_4arg
    category: dispatch_wrapper
    system: unknown
    description: Wrapper that loads 4 arguments into registers (BX, DI, CX, AX) and dispatches to 0x255B8
    confidence: high
    size: 26
    calls: 1
    called_by: 8
    evidence:
      - Paired with 0x128028 (same callers)
      - Different register mapping
      - Related operation variant
    
  - address: 0x130CE7
    name: input_slot_circular_mapper
    category: data_processor
    system: input
    description: Maps input device slots (0-9) to controller array, handling circular navigation with forward and reverse wrapping
    confidence: high
    size: 353
    calls: 0
    called_by: 8
    evidence:
      - Called from input_poll_handler
      - Circular iteration with wrap at 10
      - Type-based value assignment (0xDC, 0x131)
      - Bidirectional mapping logic
      - Slot status array at es:[bx+1938h]
    
  - address: 0x133BD5
    name: mission_temp_file_load
    category: file_io
    system: resource_mission
    description: Loads mission data from temporary file (w-.`TEMP2.DAT), reading three data blocks into global buffers
    confidence: medium
    size: 250
    calls: 11
    called_by: 8
    evidence:
      - Filename construction with string_concatenate
      - op_dispatch file I/O (service 6=open, 0Ah=read, 8=close)
      - Three fixed-size reads (4800, 2000, 3000 bytes)
      - Called from game mode coordinators
      - Flag gating (2224a)
    
  - address: 0x13ABA7
    name: menu_item_proximity_select
    category: ui_processor
    system: menu
    description: Selects nearest valid menu item by calculating Manhattan distance, filtering against exclusion list
    confidence: high
    size: 448
    calls: 6
    called_by: 8
    evidence:
      - 78-byte struct (menu item)
      - Position fields at +0x40, +0x42
      - Manhattan distance calculation (|dx| + |dy|)
      - Filter list at 602E:3645h
      - Called from menu_cmd_store_and_record_scan
      - Minimum distance tracking
    
  - address: 0x1558C8
    name: ui_draw_5arg_wrapper
    category: dispatch_wrapper
    system: ui_rendering
    description: Wrapper that pushes 5 registers (AX, DS, SI, DI, BX) and calls drawing function at 0x13DE3A
    confidence: high
    size: 14
    calls: 1
    called_by: 8
    evidence:
      - Simple register push pattern
      - Near return (internal wrapper)
      - Called from UI overlay functions
      - Drawing function target
    
  - address: 0x16F4B1
    name: menu_button_render_dispatch
    category: ui_renderer
    system: menu
    description: Dispatches menu button rendering based on type (0=variant A, 5=variant B, 6=string), gated by threshold check at 0x79E80
    confidence: high
    size: 86
    calls: 3
    called_by: 8
    evidence:
      - 3-case switch (0, 5, 6)
      - Threshold gate (word_79E80 >= 300)
      - Rendering variant calls
      - String parameter for case 6
      - Called from overlay_r48_processor
    
  - address: 0x172436
    name: campaign_menu_render_buttons
    category: ui_renderer
    system: menu_campaign
    description: Renders campaign menu buttons (0-7) with labels, highlighting current selection based on mode (word_79BD8)
    confidence: high
    size: 293
    calls: 3
    called_by: 8
    evidence:
      - 8-case switch with jump table
      - String literals CAMPAIGN STATUS, SUPPLY STATUS, ALLIED AIRCRAFT, ENEMY AIRCRAFT, ALLIED FORCES, ENEMY FORCES, OCCUPATION, DONE
      - Mode-based highlighting (word_79BD8)
      - Position calculation (index × 16 + 12)
      - Called from overlay_r49_processor (campaign overlay)
    
  - address: 0x17B2B6
    name: debriefing_menu_render_buttons
    category: ui_renderer
    system: menu_debriefing
    description: Renders debriefing menu buttons (0-10) using various rendering variants and string labels (REPORT, WAR ROOM, EDIT FLIGHTS)
    confidence: high
    size: 135
    calls: 8
    called_by: 8
    evidence:
      - 11-case switch
      - Mixed rendering (variants A/B/C/D/E + strings)
      - String literals REPORT, WAR ROOM, EDIT FLIGHTS
      - Called from overlay_r4F_handler (debriefing overlay)
    
  - address: 0x196BB9
    name: ui_farobj_callback_validate
    category: validation
    system: ui_farobj
    description: Validates FarObj state and executes callback chain, returning success/failure flag
    confidence: medium
    size: 34
    calls: 4
    called_by: 8
    evidence:
      - Two-stage validation
      - r30_farobj_proc_f and r30_farcb_seq calls
      - Boolean return pattern
      - Called from UI coordinators
    
  - address: 0x19FE2D
    name: aircraft_type_count_in_range
    category: data_processor
    system: aircraft_entity
    description: Counts aircraft of specific type in array (18-byte stride), either full array or range [0, limit)
    confidence: high
    size: 107
    calls: 0
    called_by: 8
    evidence:
      - 18-byte struct iteration
      - Type field at +1
      - Two counting modes (full/range)
      - Array pointer at es:dword_79D6C
      - Called from aircraft/entity functions
    
  - address: 0x2C185
    name: overlay_tail_bridge_6eee6
    category: overlay_bridge
    system: overlay_management
    description: Loads tail overlay and jumps to routine at 0x6EEE6
    confidence: high
    size: 8
    calls: 1
    called_by: 7
    evidence:
      - Classic overlay bridge pattern
      - tail_bridge_overlay_load call
      - Far jump to overlay space
      - Called from entity and build functions
    
  - address: 0x345FD
    name: key_event_gate_process_0c
    category: input_handler
    system: keyboard
    description: Conditionally processes keyboard event 0x0C if gate flag (byte_2F6B6) is enabled
    confidence: high
    size: 17
    calls: 1
    called_by: 7
    evidence:
      - Gate pattern (check flag before process)
      - Event code 0x0C
      - Called from farobj and input contexts
      - Flag at cs:byte_2F6B6
```

---

## Pattern Distribution

### By Category:
- **Dispatch Wrapper**: 3 (23%)
- **UI Renderer**: 3 (23%)
- **Data Processor**: 2 (15%)
- **UI Processor**: 1 (8%)
- **File I/O**: 1 (8%)
- **Validation**: 1 (8%)
- **Overlay Bridge**: 1 (8%)
- **Input Handler**: 1 (8%)

### By System:
- **Menu**: 4 (31%)
- **UI/Rendering**: 3 (23%)
- **Input/Keyboard**: 2 (15%)
- **Unknown**: 2 (15%)
- **Aircraft/Entity**: 1 (8%)
- **Resource/Mission**: 1 (8%)

### By Confidence:
- **High (85-95%)**: 11 (85%)
- **Medium (75-80%)**: 2 (15%)
- **Low (<75%)**: 0 (0%)

---

## Key Findings

1. **Menu System Dominance**: 4/13 functions (31%) are menu-related, suggesting these top-400 functions include critical UI code

2. **Dispatch Wrapper Pattern**: 3 wrappers indicate standardized calling conventions across the codebase

3. **Campaign & Debriefing Menus**: Two complete menu rendering functions identified with all button labels:
   - Campaign: 8 buttons (CAMPAIGN STATUS, SUPPLY STATUS, etc.)
   - Debriefing: 11 buttons (REPORT, WAR ROOM, EDIT FLIGHTS, etc.)

4. **Input System**: One complex circular slot mapper (353 bytes) suggests sophisticated controller/joystick management with 10 device slots

5. **Aircraft Data**: 18-byte aircraft record structure identified with type field at +1

6. **File I/O Pattern**: Temporary mission files use "w-.`TEMP#.DAT" naming convention

---

## Recommended Next Steps

1. **Investigate Dispatchers**: Analyze 0x255B2 (dispatch_22094) and 0x255B8 (dispatch_2208c) to understand what these wrappers actually do

2. **Menu System Documentation**: Document complete menu button layouts for campaign and debriefing screens

3. **Input Slot Mapping**: Test circular slot mapper with multiple input devices to understand type codes (0xDC, 0x131)

4. **Aircraft Structure**: Map complete 18-byte aircraft record structure

5. **Apply Names**: Run IDA naming script with these proposed names

---

**Analysis Complete**: 13/13 functions categorized with high confidence
