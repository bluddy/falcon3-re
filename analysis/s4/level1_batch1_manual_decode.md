# Level-1 Batch 1 Manual Decode (top 15 by dynamic calls)

## Overview
- **Batch size**: 15 functions
- **Call range**: 14 - 11,155 dyn_calls (steep cliff within batch)
- **Size range**: 8-114B (mostly tiny wrappers)
- **Pattern**: 12 of 15 call `tail_bridge_overlay_load` (sub_2AFBD)
- **Key insight**: These are **overlay entry point wrappers**

## Critical Discovery: sub_2AFBD = tail_bridge_overlay_load

This function appears in 12 of 15 callees. It's the overlay loader (131B):
- Manages overlay segment loading/unloading
- Called after overlay function returns
- This pattern: `call overlay_fn` → `call tail_bridge_overlay_load` → `ret`

**Pattern identified:** Most Level-1 functions are **overlay entry wrappers**
- Call the real function in an overlay segment
- Ensure overlay cleanup via tail_bridge_overlay_load
- Simple 8-byte pattern

---

## Rank 1: sub_2BEA1 (0x2BEA1, 8B, dyn=11155, in=2, out=2)
```
Bytecode: e819f1ea1000ad4d
Callees: sub_2AFBD (tail_bridge_overlay_load), sub_4DAE0
```

**Decode:**
```asm
e8 19 f1          call sub_2AFBD              ; tail_bridge_overlay_load
ea 10 00 ad 4d    jmp far 4DAD:0010           ; far jump to overlay
```

**Analysis:**
- Call overlay loader FIRST (unusual - others call it after)
- Then far jump to 4DAD:0010
- Pattern: pre-load then jump (vs call-then-cleanup)

**Name:** `overlay_4dad_0010_preload`
**Category:** Overlay entry wrapper (pre-load variant)

---

## Rank 2: sub_2241E (0x2241E, 24B, dyn=9210, in=1, out=2)
```
Bytecode: 9a23011011740f9a4b0310113c037c062ea1742bf8cbf9cb
Callees: sub_11223, sub_1144B
```

**Decode:**
```asm
9a 23 01 10 11    call far 1110:0123          ; overlay call
74 0f             jz +0x0F                    ; if zero, skip
9a 4b 03 10 11    call far 1110:034B          ; second overlay call
3c 03             cmp al, 0x03
7c 06             jl +0x06                    ; if < 3
2e a1 74 2b       mov ax, cs:[0x2B74]         ; read CS-segment word
f8                clc                          ; clear carry
cb                retf
f9                stc                          ; set carry
cb                retf
```

**Analysis:**
- Conditional two-stage overlay call (1110:0123, then maybe 1110:034B)
- Compare AL result to 3
- Return with carry flag set/clear based on result
- Reads CS:[0x2B74] (near 0x2B76-0x2B84 region from Level-0)

**Name:** `overlay_1110_conditional_dual_call`
**Category:** Complex overlay wrapper with conditional logic

---

## Rank 3: sub_254DC (0x254DC, 29B, dyn=977, in=0, out=1)
```
Bytecode: 2eff1e9c2acb558bec1e56c576068b4e0a8b5e0c0ee80500905e1f5dcb
Callees: sub_254F9
```

**Decode:**
```asm
2e ff 1e 9c 2a    call far cs:[0x2A9C]        ; dispatch through CS pointer
cb                retf
; --- Following code ---
55                push bp
8b ec             mov bp, sp
1e                push ds
56                push si
c5 76 06          lds si, [bp+6]              ; load far pointer arg
8b 4e 0a          mov cx, [bp+10]             ; arg3
8b 5e 0c          mov bx, [bp+12]             ; arg4
0e                push cs
e8 05 00          call +0x0005                ; near call (to sub_254F9)
90                nop
5e                pop si
1f                pop ds
5d                pop bp
cb                retf
```

**Analysis:**
- First 6 bytes: dispatch stub through CS:[0x2A9C]
- Following 23 bytes: stack frame wrapper calling sub_254F9
- Loads far pointer from stack, passes CX/BX args

**Name:** `stub_via_cs_2a9c` (for the 6B part)
**Note:** The full 29B includes two functions merged - need to check if this is a boundary error

---

## Rank 4: sub_2C80B (0x2C80B, 8B, dyn=112, in=2, out=2)
```
Bytecode: e8afe7eac7099f66
Callees: sub_1A35B7, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 af e7          call sub_2AFBD              ; tail_bridge_overlay_load
ea c7 09 9f 66    jmp far 669F:09C7           ; far jump to overlay
```

**Analysis:**
- Standard overlay wrapper pattern: load → jump
- Target: 669F:09C7

**Name:** `overlay_669f_09c7_entry`
**Category:** Overlay entry wrapper

---

## Rank 5: sub_2318C (0x2318C, 13B, dyn=93, in=1, out=1)
```
Bytecode: 2e03066236e8ec172ea36236cb
Callees: sub_24980
```

**Decode:**
```asm
2e 03 06 62 36    add ax, cs:[0x3662]         ; add CS-segment word (from Level-0 F191)
e8 ec 17          call sub_24980              ; near call
2e a3 62 36       mov cs:[0x3662], ax         ; store result back
cb                retf
```

**Analysis:**
- Add CS:[0x3662] to AX
- Call function (transform/validate)
- Store result back
- Pattern: read-modify-write with function call

**Name:** `cs_word_3662_add_transform_via_24980`
**Category:** CS-segment state modifier

---

## Rank 6: sub_2C351 (0x2C351, 8B, dyn=91, in=22, out=2)
```
Bytecode: e869ecea15009f66
Callees: sub_16F6D5, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 69 ec          call sub_2AFBD              ; tail_bridge_overlay_load
ea 15 00 9f 66    jmp far 669F:0015           ; far jump to overlay
```

**Analysis:**
- Standard overlay wrapper: 669F:0015
- 22 static callers = highly reused

**Name:** `overlay_669f_0015_entry`
**Category:** Overlay entry wrapper

---

## Rank 7: sub_2C4FF (0x2C4FF, 8B, dyn=44, in=13, out=2)
```
Bytecode: e8bbeaea00009f66
Callees: r36_e104, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 bb ea          call sub_2AFBD              ; tail_bridge_overlay_load
ea 00 00 9f 66    jmp far 669F:0000           ; far jump to overlay
```

**Analysis:**
- Overlay wrapper: 669F:0000 (segment base)
- Already has partial name: r36_e104 (RTLink record 36, entry 104)

**Name:** `overlay_669f_0000_entry` or keep `r36_e104`
**Category:** Overlay entry wrapper

---

## Rank 8: sub_2C81F (0x2C81F, 8B, dyn=38, in=2, out=2)
```
Bytecode: e89be7ea0f006f68
Callees: sub_1A2B1F, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 9b e7          call sub_2AFBD              ; tail_bridge_overlay_load
ea 0f 00 6f 68    jmp far 686F:000F           ; far jump to overlay
```

**Analysis:**
- Overlay wrapper: 686F:000F

**Name:** `overlay_686f_000f_entry`
**Category:** Overlay entry wrapper

---

## Rank 9: sub_2BE5B (0x2BE5B, 8B, dyn=31, in=0, out=2)
```
Bytecode: e85ff1ea190ff62c
Callees: sub_1020C9, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 5f f1          call sub_2AFBD              ; tail_bridge_overlay_load
ea 19 0f f6 2c    jmp far 2CF6:0F19           ; far jump to overlay
```

**Analysis:**
- Overlay wrapper: 2CF6:0F19

**Name:** `overlay_2cf6_0f19_entry`
**Category:** Overlay entry wrapper

---

## Rank 10: sub_23199 (0x23199, 13B, dyn=22, in=1, out=1)
```
Bytecode: 2e03066436e8e7172ea36436cb
Callees: sub_24988
```

**Decode:**
```asm
2e 03 06 64 36    add ax, cs:[0x3664]         ; add CS-segment word (from Level-0 F191)
e8 e7 17          call sub_24988              ; near call
2e a3 64 36       mov cs:[0x3664], ax         ; store result back
cb                retf
```

**Analysis:**
- Identical pattern to rank 5 but uses CS:[0x3664] (part of same 0x3662-0x3666 region)
- Pairs with rank 5

**Name:** `cs_word_3664_add_transform_via_24988`
**Category:** CS-segment state modifier

---

## Rank 11: sub_2C595 (0x2C595, 8B, dyn=18, in=1, out=2)
```
Bytecode: e825eaeacd039f66
Callees: r54_e118, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 25 ea          call sub_2AFBD              ; tail_bridge_overlay_load
ea cd 03 9f 66    jmp far 669F:03CD           ; far jump to overlay
```

**Analysis:**
- Overlay wrapper: 669F:03CD
- Already has partial name: r54_e118

**Name:** `overlay_669f_03cd_entry` or keep `r54_e118`
**Category:** Overlay entry wrapper

---

## Rank 12: sub_122AE (0x122AE, 114B, dyn=17, in=3, out=6)
```
Bytecode: (114 bytes - complex function)
Callees: sub_130D5, sub_133A8, sub_20598, sub_20ABC, sub_20B4D, sub_20B8D
```

**Analysis:**
- Much larger than others (114B vs 8B typical)
- 6 callees (vs 1-2 typical)
- Contains far calls: `9afc136c1f`, `9a2b3b6c1f`, `9a8d146c1f`, `9ad80e6c1f`
- Multiple near calls to sub_130D5, sub_133A8, etc.
- Segment setup: `b8c1718ed8` (mov ax, 0x71C1; mov ds, ax)
- Buffer initialization: bedf5a (mov si, 0x5ADF), multiple word writes

**Pattern:** Initialization/setup function with multiple subsystem calls

**Name:** `subsystem_init_multi_call` (tentative - needs deeper analysis)
**Category:** Complex initialization function

---

## Rank 13: sub_2BEBF (0x2BEBF, 8B, dyn=15, in=5, out=2)
```
Bytecode: e8fbf0ea0e00d84f
Callees: sub_2AFBD (tail_bridge_overlay_load), sub_4FD8E
```

**Decode:**
```asm
e8 fb f0          call sub_2AFBD              ; tail_bridge_overlay_load
ea 0e 00 d8 4f    jmp far 4FD8:000E           ; far jump to overlay
```

**Analysis:**
- Overlay wrapper: 4FD8:000E

**Name:** `overlay_4fd8_000e_entry`
**Category:** Overlay entry wrapper

---

## Rank 14: sub_2C77F (0x2C77F, 8B, dyn=15, in=1, out=2)
```
Bytecode: e83be8ea9d009f66
Callees: r54_e162, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 3b e8          call sub_2AFBD              ; tail_bridge_overlay_load
ea 9d 00 9f 66    jmp far 669F:009D           ; far jump to overlay
```

**Analysis:**
- Overlay wrapper: 669F:009D
- Already has partial name: r54_e162

**Name:** `overlay_669f_009d_entry` or keep `r54_e162`
**Category:** Overlay entry wrapper

---

## Rank 15: sub_2BFD7 (0x2BFD7, 10B, dyn=14, in=0, out=2)
```
Bytecode: e8e3efea2b00f62c0400
Callees: sub_10233B, sub_2AFBD (tail_bridge_overlay_load)
```

**Decode:**
```asm
e8 e3 ef          call sub_2AFBD              ; tail_bridge_overlay_load
ea 2b 00 f6 2c    jmp far 2CF6:002B           ; far jump to overlay
04 00             add al, 0x00                ; nop padding?
```

**Analysis:**
- Overlay wrapper: 2CF6:002B
- 2 extra bytes (add al, 0 = effective nop)

**Name:** `overlay_2cf6_002b_entry`
**Category:** Overlay entry wrapper

---

## Summary

**Named functions (13 overlay wrappers + 2 CS-segment modifiers):**

**Overlay Entry Wrappers (11):**
1. overlay_4dad_0010_preload (8B, 11.2K calls) - pre-load variant
2. overlay_669f_09c7_entry (8B, 112 calls)
3. overlay_669f_0015_entry (8B, 91 calls, 22 callers)
4. overlay_669f_0000_entry (8B, 44 calls) - or keep r36_e104
5. overlay_686f_000f_entry (8B, 38 calls)
6. overlay_2cf6_0f19_entry (8B, 31 calls)
7. overlay_669f_03cd_entry (8B, 18 calls) - or keep r54_e118
8. overlay_4fd8_000e_entry (8B, 15 calls)
9. overlay_669f_009d_entry (8B, 15 calls) - or keep r54_e162
10. overlay_2cf6_002b_entry (10B, 14 calls)

**CS-Segment State Modifiers (2):**
11. cs_word_3662_add_transform_via_24980 (13B, 93 calls)
12. cs_word_3664_add_transform_via_24988 (13B, 22 calls)

**Complex Functions (2):**
13. overlay_1110_conditional_dual_call (24B, 9.2K calls) - conditional logic
14. subsystem_init_multi_call (114B, 17 calls) - needs deeper analysis

**Deferred/Issues:**
- sub_254DC (rank 3, 29B) - appears to be two functions merged, needs split check

**Key Discovery:**
- **Level-1 is dominated by overlay entry wrappers** (11 of 15 = 73%)
- Pattern: `call tail_bridge_overlay_load` → `jmp far segment:offset`
- This explains why Level-1 functions are tiny (8B) - they're just trampolines
- Real game logic is in the overlay targets
- CS-segment state modifiers form a secondary pattern (read-modify-write)

**Overlay segments discovered:**
- 669F (5 entries: 0000, 0015, 009D, 03CD, 09C7)
- 2CF6 (2 entries: 002B, 0F19)
- 4DAD (1 entry: 0010)
- 4FD8 (1 entry: 000E)
- 686F (1 entry: 000F)
- 1110 (2 entries: 0123, 034B - conditional dual call)

**Naming strategy consideration:**
- Overlay wrappers are structurally trivial but architecturally important
- Should we name all overlay wrappers, or focus on unique patterns?
- The real value is in the overlay targets themselves (not Level-1)
