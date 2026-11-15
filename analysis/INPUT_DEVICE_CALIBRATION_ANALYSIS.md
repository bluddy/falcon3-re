# Input Device Calibration Init — Rank #9 Analysis (CORRECTED)

**Function**: `input_device_calibration_init`  
**Address**: 0x101A12  
**Size**: 1,719 bytes  
**Caller Count**: 104 (Rank #9 in top 100)  
**Callee Count**: 26 distinct functions (ACTUAL, not estimated)  
**Pattern**: Input Device Initialization Coordinator  
**Overlay**: R03_1CF6s (0x101010-0x102200)  
**IDA Status**: ✅ Renamed (corrected from incorrect "r03_screen_coordinator")  
**Analysis Date**: 2026-11-11  
**Correction Date**: 2026-11-11 (fixed after reading actual disassembly)

---

## IMPORTANT: Analysis Correction

**Original (INCORRECT) Analysis**: Named "r03_screen_coordinator" based on pattern analysis without reading code.
- ❌ Guessed: Generic screen/menu coordinator
- ❌ Estimated: 50-70 callees
- ❌ Method: Pattern matching only (IDA extraction failed)

**Corrected Analysis**: Based on actual disassembly reading.
- ✅ Actual: Input device calibration and initialization
- ✅ Measured: 26 callees
- ✅ Method: Direct IDA database extraction

This serves as a reminder: **Always read the actual code before naming functions.**

---

## Purpose and Role

This function is an **input device initialization and calibration coordinator** that detects, validates, and configures joystick, mouse, and keyboard input systems. It performs joystick calibration with retry logic, saves/restores viewport state during initialization, and validates device readiness before allowing gameplay.

**Key Responsibilities**:
1. **Detect joystick presence** - Checks `es:byte_11171` for joystick availability
2. **Calibrate joystick** - Runs calibration sequences with retry logic
3. **Initialize mouse** - Calls `mouse_gate_far_entry` for mouse setup
4. **Save/restore viewport** - Preserves view extent shadow state during init
5. **Validate device state** - Multiple validation loops to ensure devices ready
6. **Activate input dispatchers** - Registers input handlers with dispatcher chains
7. **Early exit on failure** - Returns immediately if joystick detection fails

---

## Actual Code Analysis (From Disassembly)

### Function Structure

```asm
; Prologue: Save registers and setup
00101A12  push    ds
00101A13  push    es
00101A14  push    cs
00101A15  call    near ptr overlay_undecoded_body_1020c9  ; Overlay init
00101A18  push    cs
00101A19  call    near ptr sub_101668                     ; Helper
00101A1C  mov     ax, 1110h
00101A1F  mov     ds, ax                                  ; Set DS = 0x1110
00101A21  mov     es, ax                                  ; Set ES = 0x1110
00101A23  call    undoc_102124                            ; Init helper
```

### Phase 1: Joystick Detection (0x101A26-0x101A54)

```asm
; First joystick check
00101A26  push    bp
00101A27  push    cs
00101A28  call    near ptr joystick_detect_state_store
00101A2B  pop     bp
00101A2C  cmp     es:byte_11171, 0                        ; Check joystick flag
00101A32  jnz     short loc_101A55                        ; Jump if present

; Retry with different detection method
00101A34  mov     al, 4
00101A36  push    cs
00101A37  call    near ptr joystick_detect_state_store    ; Try again with mode 4
00101A3A  cmp     es:byte_11171, 1
00101A40  jge     short loc_101A55                        ; Jump if >= 1

; No joystick found - early exit
00101A42  mov     bx, 5
00101A45  call    far_cb_1                                ; Callback
00101A4A  call    sub_1016A8                              ; Cleanup
00101A4D  call    far_cb_0                                ; Final callback
00101A52  pop     es
00101A53  pop     ds
00101A54  retn                                            ; EXIT - no joystick
```

**Critical Finding**: This function **exits early** if no joystick is detected. This explains why it's called 104 times but has relatively low complexity - many calls exit immediately at this check.

---

### Phase 2: Viewport State Save (0x101A55-0x101A7F)

```asm
; Save viewport state to stack
00101A55  push    si
00101A56  push    cs:word_1011BE                         ; Save 6 words
00101A5B  push    cs:word_1011BC
00101A60  push    cs:word_1011BA
00101A65  push    cs:word_1011B8
00101A6A  push    cs:word_1011B6
00101A6F  push    cs:word_1011B4
00101A74  mov     si, sp
00101A76  push    ds
00101A77  push    ss
00101A78  pop     ds
00101A79  call    view_extent_shadow_save_far             ; Save viewport
00101A7E  pop     ds
00101A7F  add     sp, 0Eh                                 ; Clean 14 bytes
```

**Purpose**: Saves viewport/view extent state before initialization. This suggests the calibration process may need to display UI or modify the viewport temporarily.

---

### Phase 3: Data Structure Initialization (0x101A82-0x101AAB)

```asm
; Clear data area
00101A82  mov     di, 4
00101A85  mov     cx, 64h ; 'd'                          ; 100 bytes
00101A88  xor     ax, ax
00101A8A  rep stosb                                       ; Zero 100 bytes at DS:4

; Initialize specific offsets
00101A8C  mov     word ptr ds:16h, 0
00101A92  mov     word ptr ds:18h, 0
00101A98  mov     word ptr ds:2Ch, 0
00101A9E  mov     word ptr ds:2Eh, 0

; Initialize with config value
00101AA4  mov     al, es:71h                              ; Load config byte
00101AA8  call    undoc_1016D1                            ; Init with config
00101AAB  call    mouse_gate_far_entry                    ; Init mouse
```

**Data Structure**: Clears 100-byte buffer at DS:4, then initializes 4 specific word offsets. This is likely the input device state structure.

---

### Phase 4: Dispatcher Initialization (0x101AB0-0x101AE0)

```asm
; Register dispatcher callback #1
00101AB0  push    bx
00101AB1  push    di
00101AB2  mov     bx, 0C8h
00101AB5  mov     di, 0
00101AB8  call    dispatch_2211c_stub
00101ABD  pop     di
00101ABE  pop     bx

; Conditional call based on flag
00101ABF  cmp     word ptr es:78h, 1
00101AC5  jnz     short loc_101ACA
00101AC7  call    sub_101930                              ; Optional call

; Register dispatcher callback #2
00101ACA  call    mouse_gate_far_entry
00101ACF  push    bx
00101AD0  push    di
00101AD1  push    si
00101AD2  mov     bx, 0C8h
00101AD5  mov     di, 0
00101AD8  call    dispatch_220f4_stub
00101ADD  pop     si
00101ADE  pop     di
00101ADF  pop     bx
00101AE0  call    far_cb_1
```

**Dispatcher Registration**: Registers input handlers with two dispatcher chains (0x2211c and 0x220f4), both with parameter BX=0xC8 (200).

---

### Phase 5: Device Validation Loop 1 (0x101AF1-0x101B62)

```asm
; Validate device 0x103
00101AF6  mov     ax, 103h
00101AF9  push    cs
00101AFA  call    near ptr sub_1018B7
00101AFD  jnb     short loc_101B02                        ; Jump if no error
00101AFF  jmp     loc_101D58                              ; Exit on failure

; Get device state with retry
00101B02  mov     al, es:71h
00101B06  call    stub_to_1119c
00101B0B  jb      short loc_101B02                        ; Retry if below
00101B0D  mov     es:8, ax                                ; Store result
00101B11  mov     es:1Eh, bx

; Run calibration sequence
00101B16  pusha
00101B17  mov     cx, 2
00101B1A  mov     ax, 103h
00101B1D  push    cs
00101B1E  call    near ptr sub_1017D5                     ; Calibration call
00101B21  loop    loc_101B1A                              ; Repeat 2 times
00101B23  push    cs
00101B24  call    near ptr sub_101659
00101B27  mov     byte ptr ds:2, 0FFh
00101B2C  popa
```

**Retry Logic**: Calls `stub_to_1119c` in a loop with `jb` (jump if below/carry set), retrying until success. This is classic hardware polling with timeout/retry.

---

### Phase 6: Mouse Position Tracking Loop (0x101B62-0x101BD5)

```asm
; Main tracking loop
00101B71  mov     al, es:71h
00101B75  call    stub_to_1119c                           ; Get mouse/joystick state
00101B7A  jb      short loc_101B71                        ; Retry until success

; Check if position changed significantly
00101B7C  mov     cx, es:12h                              ; Load previous X
00101B81  sub     cx, 2
00101B84  cmp     cx, ax
00101B86  jg      short loc_101BAE
00101B88  mov     cx, es:12h
00101B8D  add     cx, 2
00101B90  cmp     cx, ax
00101B92  jl      short loc_101BAE
00101B94  mov     dx, es:28h                              ; Load previous Y
00101B99  sub     dx, 2
00101B9C  cmp     dx, bx
00101B9E  jg      short loc_101BAE
00101BA0  mov     dx, es:28h
00101BA5  add     dx, 2
00101BA8  cmp     dx, bx
00101BAA  jl      short loc_101BAE
00101BAC  jmp     short loc_101BD5                        ; Position stable

; Position changed - update and render
00101BAE  mov     es:12h, ax                              ; Store new X
00101BB2  mov     es:28h, bx                              ; Store new Y
00101BB7  push    bx
00101BB8  push    ax
00101BB9  push    bx
00101BBA  push    di
00101BBB  push    si
00101BBC  mov     bx, 0C8h
00101BBF  mov     di, 0
00101BC2  call    dispatch_220f4_stub                     ; Update display
00101BC7  pop     si
00101BC8  pop     di
00101BC9  pop     bx
00101BCA  pop     ax
00101BCB  pop     bx
00101BCC  mov     di, 1Ah
00101BCF  mov     si, 4
00101BD2  call    sub_10219A                              ; Render indicator
```

**Mouse Tracking**: Implements a ±2 pixel deadzone for position tracking. Only updates display if position changes by more than 2 pixels. This is **joystick center calibration** - showing cursor position while user centers the stick.

---

### Phase 7: Validation Loop 2 with Timeout (0x101BD5-0x101C10)

```asm
; Check for button press or timeout
00101BD5  mov     al, 3
00101BD7  push    cs
00101BD8  call    near ptr undoc_101850                   ; Check button/timeout
00101BDB  jb      short loc_101BDF                        ; Jump if pressed
00101BDD  jmp     short loc_101B71                        ; Continue waiting

; Button pressed or timeout - retry loop
00101BDF  mov     cx, 4                                   ; 4 retries
00101BE2  push    cx
00101BE3  mov     al, es:71h
00101BE7  call    stub_to_1119c                           ; Get state
00101BEC  jb      short loc_101BE3                        ; Retry if fail
00101BEE  mov     di, 1Ah
00101BF1  mov     si, 4
00101BF4  call    sub_10215B                              ; Process result
00101BF7  pop     cx
00101BF8  loop    loc_101BE2                              ; Repeat 4 times

; Final calibration sequence
00101BFA  pusha
00101BFB  mov     cx, 2
00101BFE  mov     ax, 103h
00101C01  push    cs
00101C02  call    near ptr sub_1017D5                     ; Calibration
00101C05  loop    loc_101BFE                              ; Repeat 2 times
00101C07  push    cs
00101C08  call    near ptr sub_101659
00101C0B  mov     byte ptr ds:2, 0FFh
00101C10  popa
```

**Calibration Sequence**: After user centers joystick (or timeout), performs 4 retry samples, then runs the calibration routine twice to ensure stable readings.

---

## Actual Callees (26 Functions)

| Address | Name | Purpose |
|---------|------|---------|
| 0x1020C9 | `overlay_undecoded_body_1020c9` | Overlay initialization |
| 0x101668 | `sub_101668` | Helper function |
| 0x102124 | `undoc_102124` | Initialization helper |
| 0x10175D | `joystick_detect_state_store` | **Joystick detection** (called 2×) |
| 0x25EC9 | `far_cb_1` | Callback dispatcher #1 |
| 0x1016A8 | `sub_1016A8` | State management |
| 0x25EBD | `far_cb_0` | Callback dispatcher #0 |
| 0x20843 | `view_extent_shadow_save_far` | **Save viewport state** |
| 0x1016D1 | `undoc_1016D1` | Config initialization |
| 0x100BB | `mouse_gate_far_entry` | **Mouse initialization** (called 2×) |
| 0x25E3C | `dispatch_2211c_stub` | Dispatcher registration #1 |
| 0x101930 | `sub_101930` | Conditional helper |
| 0x25E22 | `dispatch_220f4_stub` | Dispatcher registration #2 |
| 0x1017D5 | `sub_1017D5` | **Calibration routine** (called 4×) |
| 0x1018B7 | `sub_1018B7` | Device validation |
| 0x11198 | `stub_to_1119c` | **Device state polling** (called 10+ times) |
| 0x101659 | `sub_101659` | Post-calibration processing |
| 0x25E08 | `far_cb_4` | Callback #4 |
| 0x10219A | `sub_10219A` | **Render calibration indicator** |
| 0x101850 | `undoc_101850` | Button/timeout check |
| 0x10215B | `sub_10215B` | Sample processing |
| 0x10188A | `overlay_undecoded_body_10188a` | Overlay helper |
| 0x20897 | `view_extent_shadow_restore_far` | **Restore viewport state** |
| 0x100B5 | `stub_to_1f6c_61df` | Cleanup stub |
| 0x25247 | `flag_block_zero_5762_5c63` | Clear flag block |
| 0x251CF | `flag_table_pop` | Restore flags |

### Callee Analysis

**By Subsystem**:
- **Joystick**: 4 functions (detect, calibrate, poll, process)
- **Mouse**: 2 functions (init, gate entry)
- **Viewport**: 2 functions (save, restore)
- **Dispatchers**: 3 functions (register callbacks)
- **Rendering**: 1 function (calibration indicator)
- **Overlay**: 3 functions (init, helpers)
- **State**: 11 functions (helpers, flags, cleanup)

**Key Insight**: Only 26 callees, NOT 50-70 as I guessed. The function is focused and specialized for input device initialization.

---

## Execution Flow Summary

```
1. Prologue: Save DS/ES, call overlay init
2. Joystick Detection:
   ├─> Try detection method 1
   ├─> Try detection method 2 (mode 4)
   └─> If no joystick: EXIT EARLY (many of 104 calls end here)
3. Joystick Present Path:
   ├─> Save viewport state (6 words to stack)
   ├─> Clear 100-byte buffer at DS:4
   ├─> Initialize config from ES:71h
   ├─> Initialize mouse
   ├─> Register dispatcher callbacks (0x2211c, 0x220f4)
   ├─> Validate device 0x103
   ├─> Run calibration sequence (2× loop)
   ├─> CALIBRATION LOOP:
   │   ├─> Poll device state with retry
   │   ├─> Track position (±2 pixel deadzone)
   │   ├─> Render cursor/indicator if moved
   │   ├─> Wait for button press or timeout
   │   └─> Loop until calibration complete
   ├─> Final validation (4 retry samples)
   ├─> Final calibration (2× loop)
   └─> Restore viewport state and exit
```

---

## Why 104 Callers?

Given the early exit logic, the 104 callers likely represent:

1. **Game startup** - Initial device detection
2. **Options menu** - When user changes input settings
3. **Recalibration** - User requests joystick recalibration
4. **Mode transitions** - Each overlay mode checks input devices
5. **Hot-plug detection** - Periodic checks for device changes
6. **Multiplayer** - Each player's input needs initialization
7. **Training mode** - Input tutorials and calibration practice

**Many calls exit early** at the "no joystick" check, explaining why a 1,719-byte function with complex calibration logic is called so frequently.

---

## Pattern Classification: Input Initialization Coordinator

**NOT a "screen coordinator"** as originally guessed. This is a specialized **input device initialization and calibration coordinator**.

**Characteristics**:
- ✅ **Specialized purpose**: Input device calibration
- ✅ **Early exit pattern**: Many calls exit immediately (no joystick)
- ✅ **Retry logic**: Multiple validation loops with hardware polling
- ✅ **User interaction**: Calibration UI with visual feedback
- ✅ **State preservation**: Saves/restores viewport during calibration
- ✅ **Moderate size**: 1,719 bytes (complex but focused)

**NOT a Phase 2 "screen coordinator"**:
- ❌ Not a menu/dialog coordinator
- ❌ Not a general-purpose screen handler
- ❌ Highly specialized for one task

**Correct Classification**: **Input Subsystem Initialization Function**

---

## Comparison with Estimates

| Metric | Guessed (Wrong) | Actual (Measured) |
|--------|-----------------|-------------------|
| Purpose | Generic screen coordinator | Input device calibration |
| Callees | 50-70 (estimated) | **26** (measured) |
| Subsystems | UI/menu focus | Input/joystick focus |
| Structure | Sequential coordinator | Retry loops + calibration UI |
| Early exit | Not considered | **Critical** (many calls exit early) |

**Key Mistake**: Estimated callees from size ratio (1,719B / 945B × 41 = ~75) without considering that **specialized functions have fewer callees** than general coordinators.

---

## Related Functions

| Function | Address | Relationship |
|----------|---------|--------------|
| `joystick_detect_state_store` | 0x10175D | **Critical** - Called 2× for detection |
| `view_extent_shadow_save_far` | 0x20843 | Saves viewport before calibration |
| `view_extent_shadow_restore_far` | 0x20897 | Restores viewport after calibration |
| `mouse_gate_far_entry` | 0x100BB | Mouse initialization |
| `stub_to_1119c` | 0x11198 | **Critical** - Device polling (10+ calls) |
| `sub_1017D5` | 0x1017D5 | **Critical** - Calibration routine (4× calls) |
| `sub_10219A` | 0x10219A | Renders calibration cursor/indicator |
| `dispatch_2211c_stub` | 0x25E3C | Input dispatcher registration |
| `dispatch_220f4_stub` | 0x25E22 | Input dispatcher registration |

---

## Lessons Learned

### What Went Wrong

1. **Didn't read actual code** - Relied on pattern matching only
2. **IDA extraction failed silently** - Didn't investigate why output was empty
3. **Proceeded anyway** - Created analysis without verifying code
4. **Wrong assumptions** - Guessed "screen coordinator" from overlay location
5. **Bad estimation** - Scaled callee count from size without domain knowledge

### Correct Process (Used for Correction)

1. ✅ **Created proper IDA script** following docs/IDA_AUTOMATION_GUIDE.md
2. ✅ **Extracted actual disassembly** with callees to JSON
3. ✅ **Read the code line-by-line** to understand actual behavior
4. ✅ **Identified key functions** (joystick_detect, calibration loops)
5. ✅ **Understood execution flow** (early exit, retry logic, UI)
6. ✅ **Corrected the name** based on actual purpose
7. ✅ **Documented the mistake** to prevent future errors

### Rule for Future Analysis

**NEVER rename a function without reading its actual disassembly.**

Pattern analysis is useful for prioritization, but **actual code reading is mandatory** before making claims about a function's purpose.

---

## Conclusion

`input_device_calibration_init` (Rank #9) is an **input device initialization and calibration coordinator** measuring 1,719 bytes with 104 callers and 26 callees. It detects joystick presence, runs calibration sequences with retry logic, and provides visual feedback during calibration. Many of its 104 calls exit early when no joystick is detected, explaining its high call frequency despite complex calibration logic.

**Key Findings**:
- ✅ **Actual purpose**: Input device calibration (NOT screen coordinator)
- ✅ **Actual callees**: 26 functions (NOT 50-70 estimated)
- ✅ **Early exit pattern**: Critical for understanding high caller count
- ✅ **Calibration UI**: Renders cursor position with ±2 pixel deadzone
- ✅ **Retry logic**: Hardware polling with timeout/validation loops
- ✅ **Viewport preservation**: Saves/restores state during calibration

**Correction Applied**:
- ✅ Function renamed in IDA: `r03_screen_coordinator` → `input_device_calibration_init`
- ✅ Analysis document completely rewritten based on actual code
- ✅ Methodology documented to prevent future errors

---

**Original Analysis**: 2026-11-11 (INCORRECT - pattern-based guess)  
**Corrected Analysis**: 2026-11-11 (CORRECT - actual disassembly read)  
**Lesson**: Always read the actual code before naming functions.
