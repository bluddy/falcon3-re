# Top 500 Functions - Batch 1 Analysis

**Date**: 2024-01-XX  
**Source**: top500_batch1_analysis.json  
**Functions Analyzed**: 20  
**Rank Range**: 403-428

---

## Summary

This batch contains functions primarily from:
- **Menu/UI systems** (7 functions) - Text rendering, element display
- **Network/Sound systems** (5 functions) - Serial communications, timing
- **Overlay systems** (3 functions) - Dynamic state management
- **Data processing** (3 functions) - String/font processing
- **Misc utilities** (2 functions) - Math transforms, lookups

---

## Function Analysis

### 1. undoc_3DE6F (0x3DE6F, 106B, Rank 403)

**Pattern**: Conditional state switcher with key event processing  
**System**: Input/Event System  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Saves multiple state bytes to CS segment
mov cl, cs:byte_427B2
mov cs:byte_427B3, cl
mov cx, cs:word_427B6
mov cs:word_427B8, cx

; Calls key event processor
call key_event_gate_process_0c
```

**Analysis**:
- Preserves previous state (427B2→427B3, 427B6→427B8)
- Sets new state values (bl → 427B0+1, 500h → 427B4)
- Calls r05_dgroup_save_reg and key_event_gate_process_0c
- Called by farobj_slot_update_driver and multiple state handlers
- Second half (after 3DED9) checks HUD font glyphs and bit flags

**Proposed Name**: `input_state_switch_with_key_process`  
**Description**: Switches input state context, preserves previous state, and processes key events through gate

**YAML Entry**:
```yaml
- address: 0x3DE6F
  name: input_state_switch_with_key_process
  system: input
  category: state_manager
  size: 106
  confidence: 85
  notes: "Switches input state with preservation, processes keys; used by farobj_slot_update_driver"
```

---

### 2. undoc_4FECC (0x4FECC, 112B, Rank 408)

**Pattern**: 3D vector transformation (rotation/projection)  
**System**: 3D Math/Graphics  
**Confidence**: VERY HIGH (95%)

**Evidence**:
```asm
; Classic 3D rotation matrix multiply
imul word ptr ds:0EF7h    ; Multiply by matrix element
mov cx, ax
mov di, dx
mov ax, bx
neg ax
imul word ptr ds:0EF5h    ; Another matrix element
add ax, cx
adc dx, di
shl ax, 1                 ; Scale result (fixed-point shift)
rcl dx, 1
```

**Analysis**:
- Takes BP (saved AX) and BX as inputs
- Multiplies by 0EF5h and 0EF7h (likely rotation matrix elements)
- Produces BP and BX outputs (likely rotated coordinates)
- Double-precision arithmetic with 32-bit results
- Shift left by 1 suggests fixed-point scaling
- Second half searches array with mask comparison (visibility check?)

**Proposed Name**: `math_3d_rotate_and_project_xy`  
**Description**: Applies 2x2 rotation matrix to XY coordinates, scales result; includes array search for visibility

**YAML Entry**:
```yaml
- address: 0x4FECC
  name: math_3d_rotate_and_project_xy
  system: graphics_3d
  category: math_transform
  size: 112
  confidence: 95
  notes: "3D coordinate rotation with matrix multiply and fixed-point scaling"
```

---

### 3. sub_100ACC (0x100ACC, 118B, Rank 410)

**Pattern**: Bit stream writer (compression/serialization)  
**System**: Data Compression/Serialization  
**Confidence**: VERY HIGH (95%)

**Evidence**:
```asm
; Recursive bit packing
cmp ax, 8
jbe short loc_100AEA
mov ax, 8
call sub_100ACC         ; Recursive - pack 8 bits at a time

; Bit field operations
mov cl, byte ptr [bp+var_2]
shl al, cl              ; Shift data by bit position
or es:[bx+si+1BAAh], al ; OR into buffer
add ax, [bp+var_4]      ; Add bit count
mov es:[bx+4], ax       ; Update bit position

; Buffer overflow check
cmp si, 800h
jb short loc_100B3C
call sub_100C1B         ; Flush buffer
```

**Analysis**:
- Packs variable-width bit fields into byte stream
- Maintains bit position counter (offset +4)
- Buffer at ES:[BX+1BAAh], 2KB size (800h bytes)
- Calls self recursively for >8 bits
- Second function builds frequency table (byte pairs → word counts)

**Proposed Name**: `data_bitstream_writer_recursive`  
**Description**: Writes variable-width bit fields to packed buffer; flushes at 2KB boundary; recursive for multi-byte values

**YAML Entry**:
```yaml
- address: 0x100ACC
  name: data_bitstream_writer_recursive
  system: compression
  category: serializer
  size: 118
  confidence: 95
  notes: "Bit-packing serializer with recursive >8-bit handling and buffer flush"
```

---

### 4. undoc_102932 (0x102932, 326B, Rank 411)

**Pattern**: Overlay state coordinator with multi-dispatch  
**System**: Overlay Management  
**Confidence**: HIGH (80%)

**Evidence**:
```asm
; Load overlay segment data
mov si, 71C1h
mov ds, si
mov si, bx
shl si, 4
add si, 162h            ; Index into overlay table

; Check against mask array
mov di, 0C48h
lodsw
and ax, es:[di]         ; Mask check
jnz short loc_102956    ; Skip if match

; Multiple dispatch calls
call sub_102C2A
call undoc_102C48
call undoc_102C62
call sub_102C9F
```

**Analysis**:
- Loads from overlay segment 71C1h
- Indexes by BX*16 + 162h (overlay descriptor table)
- Tests 8 words against mask array at ES:0C48h
- Calculates positions using direction vectors (0EC9h offsets)
- Sets multiple destination pointers (0EE1h, 0EDDh, 0EC7h)
- Called by overlay_undecoded_body and r07_state_byte_skip_gate

**Proposed Name**: `overlay_state_coordinator_with_dispatch`  
**Description**: Coordinates overlay state by checking masks, calculating positions, and dispatching to multiple handlers

**YAML Entry**:
```yaml
- address: 0x102932
  name: overlay_state_coordinator_with_dispatch
  system: overlay
  category: state_manager
  size: 326
  confidence: 80
  notes: "Complex overlay state manager with mask checking and multi-dispatch"
```

---

### 5. sub_1086C1 (0x1086C1, 43B, Rank 412)

**Pattern**: Loop dispatcher with table-driven calls  
**System**: Dispatch/Controller  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Read count from CS table
mov bp, 2A7h
mov cl, es:[bp+0]       ; Get loop count
sub ch, ch
inc bp

; Loop through table entries
push cx
push bp
mov al, es:[bp+2]       ; Get parameter from entry
mov bp, es:[bp+0]       ; Get target address
call dispatch_220a8_stub ; Dispatch
pop bp
add bp, 3               ; Next entry (3 bytes each)
pop cx
loop loc_1086CE         ; Repeat
```

**Analysis**:
- Reads table at CS:2A7h (count byte + 3-byte entries)
- Each entry: word address + byte parameter
- Dispatches through dispatch_220a8_stub
- Called 7 times by undoc_108E79
- Second function initializes state and runs overlay poll loop

**Proposed Name**: `dispatch_table_loop_executor`  
**Description**: Executes sequence of calls from CS table; each entry contains address and parameter byte

**YAML Entry**:
```yaml
- address: 0x1086C1
  name: dispatch_table_loop_executor
  system: dispatch
  category: controller
  size: 43
  confidence: 85
  notes: "Table-driven dispatcher, 3-byte entries (word+byte), uses dispatch_220a8_stub"
```

---

### 6. sub_11CB23 (0x11CB23, 133B, Rank 413)

**Pattern**: UI element renderer with dual dispatch  
**System**: Menu/UI  
**Confidence**: VERY HIGH (90%)

**Evidence**:
```asm
; Calculate element offset
mov ax, [bp+arg_0]
shl ax, 4               ; Element size = 16 bytes
add ax, 14h             ; Base offset
mov di, ax

; First dispatch - top/left element
push word ptr es:byte_79976+6
push word ptr es:byte_79976+4
push di
push si
call dispatch_220ec_invoke

; Second dispatch - bottom/right element  
add si, 38h
push word ptr es:byte_79976+2Ah
push word ptr es:byte_79976+28h
push di
push si
call dispatch_220ec_invoke

; Calculate centered position
push [bp+arg_4]
push [bp+arg_2]
call sub_13DE82         ; Calculate size?
mov si, ax
mov bx, 2
idiv bx                 ; Divide by 2
mov si, ax
mov ax, 104h
sub ax, si              ; Center = 260 - (size/2)
```

**Analysis**:
- Renders paired UI elements (top+bottom or left+right)
- Uses 16-byte element descriptors
- Calls dispatch_220ec_invoke twice with different offsets
- Centers content at x=260 (104h)
- Called by overlay handlers and menu systems

**Proposed Name**: `ui_element_render_paired_centered`  
**Description**: Renders paired UI elements (top/bottom) with centered positioning; uses dual dispatch

**YAML Entry**:
```yaml
- address: 0x11CB23
  name: ui_element_render_paired_centered
  system: ui
  category: renderer
  size: 133
  confidence: 90
  notes: "Dual-element renderer with centering, 16-byte descriptors, dispatch_220ec_invoke"
```

---

### 7. undoc_11CEAB (0x11CEAB, 48B, Rank 414)

**Pattern**: Simple UI element renderer  
**System**: Menu/UI  
**Confidence**: HIGH (90%)

**Evidence**:
```asm
; Calculate element offset (same as 11CB23)
mov ax, [bp+arg_0]
shl ax, 4               ; Element size = 16 bytes
add ax, 14h
mov di, ax

; Single dispatch
mov ax, 7894h
mov es, ax
push word ptr es:byte_79976+4Ah
push word ptr es:byte_79976+48h
push di
push si
call dispatch_220ec_invoke
```

**Analysis**:
- Simplified version of sub_11CB23 (single dispatch only)
- Same element structure (16-byte, offset +14h)
- Uses different pointer offset (4Ah vs 6/2Ah)
- Called by r45_menu_element_dispatcher and overlay handlers
- Very simple pattern - likely specialized renderer

**Proposed Name**: `ui_element_render_single`  
**Description**: Renders single UI element using dispatch_220ec_invoke; simpler version of paired renderer

**YAML Entry**:
```yaml
- address: 0x11CEAB
  name: ui_element_render_single
  system: ui
  category: renderer
  size: 48
  confidence: 90
  notes: "Single-element renderer, 16-byte descriptors, related to 11CB23"
```

---

### 8. undoc_123FDD (0x123FDD, 152B, Rank 415)

**Pattern**: UI element renderer with clipping  
**System**: Menu/UI  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Range clipping
cmp si, 0C7h            ; Max X = 199
jg short loc_124071     ; Skip if out of range
cmp di, 0B3h            ; Max Y = 179
jg short loc_124071

; Clamp to safe area
cmp si, 3
jge short loc_124009
mov si, 3               ; Min X = 3
cmp si, 0C4h            ; Max safe X = 196
jle short loc_124012
mov si, 0C4h

; Similar Y clamping (3 to 176)
; Then expand bounds and render
mov ax, di
add ax, 3               ; +3 border
push ax
mov ax, di
add ax, 0FFFDh          ; -3 border
push ax
call undoc_127FA7       ; Draw border/frame?
call dispatch_220e4_invoke_farptr ; Render content
```

**Analysis**:
- Clips coordinates to screen bounds (0-199, 0-179)
- Adds 3-pixel safe margins (3-196, 3-176)
- Expands bounds by ±3 for border
- Two-stage render: border then content
- Called by overlay_handler_3826 and overlay_handler_3105

**Proposed Name**: `ui_element_render_with_clipping`  
**Description**: Renders UI element with screen clipping and 3-pixel border margins; validates and clamps coordinates

**YAML Entry**:
```yaml
- address: 0x123FDD
  name: ui_element_render_with_clipping
  system: ui
  category: renderer
  size: 152
  confidence: 85
  notes: "Clips to screen bounds (199x179), adds 3px borders, dual-phase rendering"
```

---

### 9. sub_12A114 (0x12A114, 550B, Rank 416)

**Pattern**: Font/text renderer with state machine  
**System**: UI/Text Rendering  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Load render config
mov ax, 602Eh
mov es, ax
mov al, es:render_config_byte_2
mov [bp+var_E], al
mov al, es:render_config_byte_1
mov [bp+var_F], al

; Initialize render state
mov ax, 7894h
mov es, ax
mov es:byte_7A304, 1    ; Enable flag
mov es:byte_7A305+2, 0FFh ; Init state
mov es:byte_7A305, 0FFh
mov es:byte_7A305+3, 0FFh

; Main render loop
mov [bp+var_2], 0
jmp loc_12A308          ; Loop 3 iterations (0,1,2)

; Load font/text data
call network_stuff       ; Get character code?
call sub_12A908         ; Load glyph data
call sub_12A981         ; Validate/process glyph
```

**Analysis**:
- Manages text rendering state machine
- Loads configuration from segment 602Eh
- Three-pass rendering loop
- Calls utility_900 multiple times (likely for palette/color)
- Processes glyph data through multi-stage pipeline
- Called by ui_text_render_engine and ui_text_render_simple

**Proposed Name**: `ui_text_render_state_machine`  
**Description**: Multi-pass text renderer with glyph loading, validation, and state management; 3-iteration loop

**YAML Entry**:
```yaml
- address: 0x12A114
  name: ui_text_render_state_machine
  system: ui
  category: text_renderer
  size: 550
  confidence: 85
  notes: "Complex text renderer with 3-pass state machine, glyph processing pipeline"
```

---

### 10. sub_12A908 (0x12A908, 121B, Rank 417)

**Pattern**: Font glyph loader/validator  
**System**: UI/Font System  
**Confidence**: VERY HIGH (95%)

**Evidence**:
```asm
; Check for valid font data structure
les bx, es:dword_14F98C  ; Font data pointer
cmp word ptr es:[bx], 27h ; Magic number check
jnz short loc_12A97C      ; Invalid

; Load glyph metadata
mov ax, es:[bx+6]         ; Segment
mov [bp+var_8], ax
mov ax, es:[bx+8]         ; Offset
mov [bp+var_6], ax
mov word ptr [bp+var_4+2], ax
mov word ptr [bp+var_4], dx

; Copy glyph data
les bx, [bp+var_4]
mov al, es:[bx+4]         ; Glyph size
les bx, [bp+arg_0]
mov es:[bx], al           ; Store size
cmp byte ptr es:[bx], 0C8h ; Max size check (200)
ja short loc_12A97C

; Copy glyph bytes
xor si, si
les bx, [bp+var_4]
mov al, es:[bx+si]
les bx, [bp+arg_4]
mov es:[bx+si], al
inc si
loop                      ; Copy loop
```

**Analysis**:
- Validates font data with magic number 27h
- Loads glyph from far pointer structure
- Maximum glyph size 200 bytes (C8h)
- Copies glyph data byte-by-byte
- Returns success/failure flag
- Called by sub_12A114 (text renderer)

**Proposed Name**: `font_glyph_load_and_validate`  
**Description**: Loads font glyph from data structure, validates magic number and size, copies glyph bytes

**YAML Entry**:
```yaml
- address: 0x12A908
  name: font_glyph_load_and_validate
  system: ui
  category: font_loader
  size: 121
  confidence: 95
  notes: "Validates font data (magic 27h), loads glyph, max size 200 bytes"
```

---

### 11. sub_12BC4F (0x12BC4F, 21B, Rank 418)

**Pattern**: Serial/UART transmitter  
**System**: Hardware I/O (Serial Communications)  
**Confidence**: VERY HIGH (98%)

**Evidence**:
```asm
; Read UART Line Status Register
mov dx, ds:7Ch          ; UART base address
add dx, 5               ; LSR offset (base+5)
in al, dx
test al, 20h            ; Test THR empty bit
jz short loc_12BC56     ; Wait if not ready

; Write data byte
mov dx, ds:7Ch          ; UART base address
lodsb                   ; Load byte from DS:SI
out dx, al              ; Write to THR
loop loc_12BC53         ; Repeat for CX bytes
```

**Analysis**:
- Standard UART transmission loop
- Polls Line Status Register bit 5 (THR empty)
- Writes bytes to Transmit Holding Register
- Uses variable at DS:7Ch for port base address
- Called by interrupt_dma and sound-related functions
- Classic serial port busy-wait pattern

**Proposed Name**: `serial_uart_transmit_polled`  
**Description**: Transmits CX bytes from DS:SI to UART; polls LSR for THR empty before each byte

**YAML Entry**:
```yaml
- address: 0x12BC4F
  name: serial_uart_transmit_polled
  system: hardware_io
  category: serial_comm
  size: 21
  confidence: 98
  notes: "Standard UART TX loop, polls LSR bit 5, port at DS:7Ch"
```

---

### 12. sub_12BC64 (0x12BC64, 31B, Rank 419)

**Pattern**: Timing delay using BIOS timer  
**System**: Hardware I/O (Timing)  
**Confidence**: VERY HIGH (99%)

**Evidence**:
```asm
; Wait for timer tick
xor ax, ax
mov es, ax              ; ES = 0 (BIOS data area)
mov ax, es:46Ch         ; Read timer tick counter
cmp ax, es:46Ch         ; Wait for change
jz short loc_12BC6D     ; Loop until tick

; Double-tick wait for stability
mov ax, es:46Ch         ; Read again
cmp ax, es:46Ch         ; Wait for another tick
jz short loc_12BC78
loop loc_12BC74         ; Repeat CX times
```

**Analysis**:
- Reads BIOS timer at 0:046Ch (updates ~18.2 times/second)
- Waits for tick change (stable timing)
- Double-tick ensures clean sample
- Loops CX times for longer delays
- Called by interrupt handlers and timing-sensitive code
- Standard DOS/BIOS timing pattern

**Proposed Name**: `bios_timer_delay_ticks`  
**Description**: Delays for CX timer ticks using BIOS counter at 0:046Ch; double-samples for stability

**YAML Entry**:
```yaml
- address: 0x12BC64
  name: bios_timer_delay_ticks
  system: hardware_io
  category: timing
  size: 31
  confidence: 99
  notes: "BIOS timer delay, reads 0:046Ch, double-tick sampling, ~55ms per tick"
```

---

### 13. sub_12BC83 (0x12BC83, 4B, Rank 420)

**Pattern**: Wrapper for timer delay  
**System**: Hardware I/O (Timing)  
**Confidence**: VERY HIGH (99%)

**Evidence**:
```asm
call sub_12BC64         ; Call timer delay
retf                    ; Far return
```

**Analysis**:
- Trivial wrapper around sub_12BC64
- Converts near call to far call interface
- No parameter modification
- Called by sound system and DMA functions
- Likely for overlay or segment crossing

**Proposed Name**: `bios_timer_delay_ticks_far`  
**Description**: Far wrapper for bios_timer_delay_ticks; enables cross-segment calls

**YAML Entry**:
```yaml
- address: 0x12BC83
  name: bios_timer_delay_ticks_far
  system: hardware_io
  category: timing
  size: 4
  confidence: 99
  notes: "Far wrapper for 12BC64, no logic"
```

---

### 14. sub_12D4F6 (0x12D4F6, 12B, Rank 421)

**Pattern**: Interrupt vector call (INT 7Ah wrapper)  
**System**: Hardware I/O (Interrupt)  
**Confidence**: HIGH (90%)

**Evidence**:
```asm
push ds
push es
pusha                   ; Save all registers
mov bx, 1               ; Function code
int 7Ah                 ; Call handler
popa                    ; Restore registers
pop es
pop ds
retn
```

**Analysis**:
- Calls INT 7Ah (Novell NetWare or custom handler)
- Function code in BX (value = 1)
- Preserves all registers
- Multiple similar functions with different BX values (2, 3, etc.)
- Could be network protocol, sound driver, or custom hardware
- Called by network/sound-related code

**Proposed Name**: `int7a_call_function_01`  
**Description**: Calls INT 7Ah with function code 1; preserves all registers; likely network or hardware driver

**YAML Entry**:
```yaml
- address: 0x12D4F6
  name: int7a_call_function_01
  system: hardware_io
  category: interrupt_wrapper
  size: 12
  confidence: 90
  notes: "INT 7Ah function 1, register preservation, NetWare or custom driver"
```

---

### 15. sub_12D525 (0x12D525, 22B, Rank 422)

**Pattern**: Interrupt vector call (INT 7Ah wrapper, function 4)  
**System**: Hardware I/O (Interrupt)  
**Confidence**: HIGH (90%)

**Evidence**:
```asm
push ds
push es
push si
push di
push bx
push cx
push dx
push bp
mov bx, 4               ; Function code 4
int 7Ah
pop bp
pop dx
pop cx
pop bx
pop di
pop si
pop es
pop ds
retn
```

**Analysis**:
- Similar to sub_12D4F6 but function code = 4
- Selective register preservation (no AX - return value?)
- More callers (7) suggests more important function
- Called by network and data processing code
- Likely data transfer or status query function

**Proposed Name**: `int7a_call_function_04`  
**Description**: Calls INT 7Ah with function code 4; preserves most registers; returns value in AX

**YAML Entry**:
```yaml
- address: 0x12D525
  name: int7a_call_function_04
  system: hardware_io
  category: interrupt_wrapper
  size: 22
  confidence: 90
  notes: "INT 7Ah function 4, returns AX, heavily used (7 calls)"
```

---

### 16. undoc_139169 (0x139169, 187B, Rank 423)

**Pattern**: String resource loader/processor  
**System**: Resource Management / Localization  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Open string file
push word ptr es:aSqdnamesStr  ; ".`sqdnames.str"
push es:word_14F8C0
push 0
push 0
push 6                          ; File operation code
call op_dispatch_far_entry

; Seek to string offset
push 0
mov ax, [bp+arg_0]
shl ax, 1                       ; Index * 2 (word offset)
cwd
push dx
push ax
push si                         ; File handle
push 0Eh                        ; Seek operation
call op_dispatch_far_wide

; Read string length
push ss
lea ax, [bp+var_2]
push ax
push 2                          ; Read 2 bytes (word)
push si
push 0Ah                        ; Read operation
call op_dispatch_far_entry

; Read string data
push word ptr [bp+arg_2+2]
push word ptr [bp+arg_2]
push 1Eh                        ; String max length
push si
push 0Ah
call op_dispatch_far_entry

; Lowercase conversion (if flag set)
cmp es:word_79E9C, 0
jz short loc_139221
cmp byte ptr es:[bx+si], 61h    ; 'a'
jl short loc_139217
cmp byte ptr es:[bx+si], 7Ah    ; 'z'
jg short loc_139217
add al, 0E0h                    ; Convert case
mov es:[bx+si], al
```

**Analysis**:
- Opens ".`sqdnames.str" resource file
- Seeks to indexed string (arg_0 * 2)
- Reads string length then data
- Optional lowercase conversion (internationalization?)
- File operations through op_dispatch_far_entry
- Called by menu and UI systems

**Proposed Name**: `resource_string_load_indexed`  
**Description**: Loads indexed string from sqdnames.str resource file; supports case conversion for localization

**YAML Entry**:
```yaml
- address: 0x139169
  name: resource_string_load_indexed
  system: resource
  category: string_loader
  size: 187
  confidence: 85
  notes: "Loads strings from sqdnames.str by index, optional lowercase conversion"
```

---

### 17. undoc_13D744 (0x13D744, 56B, Rank 425)

**Pattern**: Multi-condition boolean gate  
**System**: Game State / Campaign  
**Confidence**: HIGH (80%)

**Evidence**:
```asm
; Check condition 1: some data available
mov ax, 7A32h
mov es, ax
mov al, es:0AD4Bh
mov ah, 0
or ax, ax
jnz short loc_13D758
jmp short loc_13D778        ; Return false

; Check condition 2: not in special mode
mov ax, 7894h
mov es, ax
cmp es:word_79B56, 1
jnz short loc_13D767
jmp short loc_13D778        ; Return false

; Check condition 3: feature enabled
mov ax, 602Eh
mov es, ax
cmp es:byte_14EC29, 0
jz short loc_13D778         ; Return false

; All conditions met
mov al, 1                   ; Return true
jmp short loc_13D77A
mov al, 0                   ; Return false
```

**Analysis**:
- Three-condition AND gate
- Checks: data availability, mode flag, feature flag
- Returns boolean in AL
- Called by HUD/menu rendering code
- Second function builds mission filename string
- Likely determines if mission data should be displayed

**Proposed Name**: `campaign_mission_display_enabled`  
**Description**: Returns true if mission display conditions met: data available, not in special mode, feature enabled

**YAML Entry**:
```yaml
- address: 0x13D744
  name: campaign_mission_display_enabled
  system: campaign
  category: state_query
  size: 56
  confidence: 80
  notes: "Three-way AND gate for mission display; checks data/mode/feature flags"
```

---

### 18. undoc_163CCD (0x163CCD, 102B, Rank 426)

**Pattern**: Loadout state updater  
**System**: UI / Loadout Menu  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Set global loadout state
mov ax, 602Eh
mov es, ax
mov es:word_151C15, 12h     ; Set mode to 18

; Update aircraft loadout structure
mov ax, 7894h
mov es, ax
mov ax, es:word_79BDA        ; Current aircraft index
mov dx, 4Eh                  ; Structure size = 78 bytes
imul dx
mov dx, 7894h
mov es, dx
les bx, es:dword_79B6E      ; Loadout array pointer
add bx, ax
mov byte ptr es:[bx+4], 12h ; Set aircraft mode

; Calculate weapon offset
mov ax, [bp+arg_6]
mov dx, 27Ah                ; Weapon structure size = 634 bytes
imul dx
add ax, 68Fh                ; Base weapon offset

; Update loadout data
push 602Eh
push ax                     ; Weapon data offset
mov al, [bp+arg_4]
push ax                     ; Hardpoint
mov al, [bp+arg_2]
push ax                     ; Weapon type
call menu_loadout_data_engine
```

**Analysis**:
- Updates aircraft loadout state (mode 12h)
- 78-byte aircraft structures
- 634-byte weapon structures
- Updates global state and aircraft array
- Called by loadout menu handlers
- Manages hardpoint/weapon assignments

**Proposed Name**: `ui_loadout_state_update_weapon`  
**Description**: Updates loadout state for weapon assignment; modifies aircraft structure and global mode

**YAML Entry**:
```yaml
- address: 0x163CCD
  name: ui_loadout_state_update_weapon
  system: ui
  category: loadout_manager
  size: 102
  confidence: 85
  notes: "Updates loadout state, 78B aircraft + 634B weapon structures"
```

---

### 19. undoc_17DF4D (0x17DF4D, 49B, Rank 427)

**Pattern**: Score accumulator  
**System**: Game State / Campaign  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Initialize accumulator
xor di, di                  ; Sum = 0
xor si, si                  ; Index = 0

; Loop through 4 items
mov ax, si
mov dx, 82h                 ; Structure size = 130 bytes
imul dx
mov dx, 7894h
mov es, dx
les bx, es:dword_79BEC      ; Array pointer
add bx, ax
mov al, es:[bx+4]           ; Load value at offset +4
cbw                         ; Sign-extend
add di, ax                  ; Add to sum
inc si
cmp si, 4
jl short loc_17DF58         ; Loop 4 times

; Return total
mov ax, di
```

**Analysis**:
- Sums byte values from 4 array entries
- 130-byte structure size
- Offset +4 in each structure
- Array at ES:dword_79BEC
- Called by overlay coordinator functions
- Second function searches for zero entry (find slot)

**Proposed Name**: `campaign_score_total_get`  
**Description**: Sums byte values at offset +4 across 4 campaign entries; 130-byte structures

**YAML Entry**:
```yaml
- address: 0x17DF4D
  name: campaign_score_total_get
  system: campaign
  category: data_aggregator
  size: 49
  confidence: 85
  notes: "Sums 4 bytes from 130B structures at dword_79BEC+4"
```

---

### 20. undoc_1852E5 (0x1852E5, 153B, Rank 428)

**Pattern**: Debriefing screen setup  
**System**: UI / Mission Debriefing  
**Confidence**: HIGH (85%)

**Evidence**:
```asm
; Load debriefing UI
push word ptr es:aJ0Debriefing+2  ; ".`DEBRIEFING"
push word ptr es:aJ0Debriefing
call undoc_11C450                  ; Load UI definition
call far ptr loc_69EA9             ; Setup page

; Branch based on mode
cmp [bp+arg_0], 0
jnz short loc_18533A

; Mode 0: Mission complete
push word ptr es:a0Continue+2      ; ".`CONTINUE..."
push word ptr es:a0Continue
push 7
call undoc_11C5DC                  ; Render element 7

push word ptr es:a2NextMission+1   ; ".`NEXT MISSION"
push word ptr es:byte_15183A
push 8
call sub_11CB23                    ; Render element 8

; Mode 1: Mission failed
push word ptr es:a0Continue+2
push word ptr es:a0Continue
push 7
call undoc_11C504                  ; Different renderer

push word ptr es:a2NextMission+1
push word ptr es:byte_15183A
push 8
call sub_11CA0D                    ; Different renderer
```

**Analysis**:
- Loads debriefing screen resources
- Two rendering paths based on arg_0 (success/failure?)
- Renders "CONTINUE..." and "NEXT MISSION" buttons
- Uses different renderers for each mode
- Called by game mode coordinator (r53)
- Multiple UI element renderers

**Proposed Name**: `ui_debriefing_screen_setup`  
**Description**: Sets up mission debriefing screen; different rendering based on success/failure mode

**YAML Entry**:
```yaml
- address: 0x1852E5
  name: ui_debriefing_screen_setup
  system: ui
  category: screen_controller
  size: 153
  confidence: 85
  notes: "Debriefing screen setup, dual mode (success/fail), element rendering"
```

---

## Category Summary

### By System:
- **UI/Menu**: 8 functions (11CB23, 11CEAB, 123FDD, 12A114, 12A908, 163CCD, 1852E5, 17DF4D*)
- **Hardware I/O**: 4 functions (12BC4F, 12BC64, 12BC83, 12D4F6, 12D525)
- **Overlay/State**: 2 functions (102932, 1086C1)
- **Graphics/3D**: 1 function (4FECC)
- **Input/Events**: 1 function (3DE6F)
- **Data Processing**: 2 functions (100ACC, 139169)
- **Campaign**: 2 functions (13D744, 17DF4D)

### By Pattern:
- **Renderers**: 5 functions
- **State Managers**: 3 functions
- **Data Loaders**: 2 functions
- **Hardware Wrappers**: 5 functions
- **Dispatchers**: 2 functions
- **Math/Transform**: 1 function
- **Validators**: 2 functions

### Confidence Distribution:
- **Very High (90-99%)**: 9 functions
- **High (80-89%)**: 11 functions
- **Medium (70-79%)**: 0 functions

---

## Recommended Registry Entries

```yaml
# IDA Naming Script Additions
functions:
  # Input System
  - address: 0x3DE6F
    name: input_state_switch_with_key_process
    system: input
    category: state_manager
    size: 106
    
  # 3D Graphics Math
  - address: 0x4FECC
    name: math_3d_rotate_and_project_xy
    system: graphics_3d
    category: math_transform
    size: 112
    
  # Data Compression
  - address: 0x100ACC
    name: data_bitstream_writer_recursive
    system: compression
    category: serializer
    size: 118
    
  # Overlay Management
  - address: 0x102932
    name: overlay_state_coordinator_with_dispatch
    system: overlay
    category: state_manager
    size: 326
    
  - address: 0x1086C1
    name: dispatch_table_loop_executor
    system: dispatch
    category: controller
    size: 43
    
  # UI Rendering
  - address: 0x11CB23
    name: ui_element_render_paired_centered
    system: ui
    category: renderer
    size: 133
    
  - address: 0x11CEAB
    name: ui_element_render_single
    system: ui
    category: renderer
    size: 48
    
  - address: 0x123FDD
    name: ui_element_render_with_clipping
    system: ui
    category: renderer
    size: 152
    
  - address: 0x12A114
    name: ui_text_render_state_machine
    system: ui
    category: text_renderer
    size: 550
    
  - address: 0x12A908
    name: font_glyph_load_and_validate
    system: ui
    category: font_loader
    size: 121
    
  - address: 0x163CCD
    name: ui_loadout_state_update_weapon
    system: ui
    category: loadout_manager
    size: 102
    
  - address: 0x1852E5
    name: ui_debriefing_screen_setup
    system: ui
    category: screen_controller
    size: 153
    
  # Hardware I/O
  - address: 0x12BC4F
    name: serial_uart_transmit_polled
    system: hardware_io
    category: serial_comm
    size: 21
    
  - address: 0x12BC64
    name: bios_timer_delay_ticks
    system: hardware_io
    category: timing
    size: 31
    
  - address: 0x12BC83
    name: bios_timer_delay_ticks_far
    system: hardware_io
    category: timing
    size: 4
    
  - address: 0x12D4F6
    name: int7a_call_function_01
    system: hardware_io
    category: interrupt_wrapper
    size: 12
    
  - address: 0x12D525
    name: int7a_call_function_04
    system: hardware_io
    category: interrupt_wrapper
    size: 22
    
  # Resource Management
  - address: 0x139169
    name: resource_string_load_indexed
    system: resource
    category: string_loader
    size: 187
    
  # Campaign System
  - address: 0x13D744
    name: campaign_mission_display_enabled
    system: campaign
    category: state_query
    size: 56
    
  - address: 0x17DF4D
    name: campaign_score_total_get
    system: campaign
    category: data_aggregator
    size: 49
```

---

## Key Findings

1. **UI System Dominance**: 8 of 20 functions are UI-related, showing heavy focus on menu/text rendering
   - Multiple rendering pipelines with different feature sets
   - 16-byte UI element descriptors
   - Dual-dispatch pattern common (paired elements)

2. **Hardware Abstraction**: 5 interrupt/timing wrappers suggest modular hardware layer
   - INT 7Ah heavily used (custom driver or NetWare)
   - Standard UART and BIOS timer patterns

3. **Overlay Complexity**: State management functions are large (326B) and multi-phase
   - Table-driven dispatch common
   - Mask-based state checking

4. **3D Math**: Fixed-point rotation matrices with 2x scaling factor
   - Suggests 16.16 or similar fixed-point format

5. **Compression**: Bit-packing serialization with recursive handling
   - 2KB buffer size
   - Variable-width fields

## Next Steps

1. **Apply names to IDA database** using provided YAML
2. **Cross-reference with existing verified routines** to validate patterns
3. **Analyze next batch** (functions 421-440) to continue coverage
4. **Document UI element structure** (16-byte format)
5. **Investigate INT 7Ah handler** to understand driver architecture
