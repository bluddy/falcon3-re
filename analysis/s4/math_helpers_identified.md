# Math Helper Functions - Identified Operations

**Date:** 2026-11-12  
**Status:** Preliminary identification from bytecode analysis  
**Confidence:** Medium (needs IDA confirmation)

## Summary

Analyzed 10 entry points called exclusively by view_projection. Identified likely operations based on bytecode patterns and x86 instruction analysis.

## Function Catalog

### seg015:0C65 (+0x002A in sub_1CC2D) - 21 bytes
**Likely: Segment Setup / Context Switcher**

Key operations:
- `push ss; pop cx` - Save stack segment
- `mov ax, 0x7772; mov es, ax` - Setup ES to data segment (0x7772)
- Multiple ES: overrides for data access

**Purpose:** Prepare segment registers for math operations accessing shared data tables.

**Confidence:** HIGH

---

### seg015:0C7A (+0x003F in sub_1CC2D) - 97 bytes
**Likely: Complex Math Dispatcher or State Machine**

Key operations:
- Multiple ES: segment overrides
- Large jump (`jmp +399`)
- Complex control flow

**Purpose:** Unknown without full disassembly. Size and complexity suggest either:
1. Dispatcher for multiple math operations
2. State machine for coordinate transformation
3. Complex conditional calculation

**Confidence:** LOW - needs IDA review

---

### seg015:0CDB (+0x00A0 in sub_1CC2D) - 21 bytes
**Likely: 32-bit Left Shift or Fixed-Point Multiply Setup**

Key operations:
```assembly
mov bh, 0
push ax
mov ax, bx
push dx
cwd              ; Sign-extend AX to DX:AX
pop bx
pop cx
add cx, cx       ; 32-bit addition
adc dx, dx
mov [bp-2], bx
mov [bp-4], cx
```

**Purpose:** Performs 32-bit shift left by 1 (multiply by 2) with sign extension.  
Used in fixed-point arithmetic scaling.

**Confidence:** HIGH

---

### seg015:0CF0 (+0x00B5 in sub_1CC2D) - 97 bytes
**Likely: Far Call to External Math Library**

Key operations:
- `push [bp-4]` - Push parameter
- `call far 0x1994:0D94` - Far call to external segment
- `pop cx; pop cx` - Cleanup 2 words from stack

**Purpose:** Wrapper for external math function (possibly in ROM or separate module).  
Could be sin/cos, sqrt, or other complex operation.

**Confidence:** MEDIUM

---

### seg015:0D51 (+0x0116 in sub_1CC2D) - 21 bytes
**Likely: Wrapper Function with Cleanup**

Key operations:
- `call 0x1CBA7` (rel -2206)
- `add sp, 6` - Clean up 3 words (6 bytes) from stack
- `jmp +184` - Jump to common epilogue

**Purpose:** Calls another function with 3 parameters, cleans stack, returns.

**Confidence:** HIGH

---

### seg015:0D66 (+0x012B in sub_1CC2D) - 64 bytes
**Likely: Conditional Math Operation**

Key operations:
- ES: segment overrides
- Comparison and conditional jumps
- `jg +116` - Jump if greater

**Purpose:** Performs different operations based on input conditions.  
Possibly: clamping, bounds checking, or sign-dependent calculation.

**Confidence:** MEDIUM

---

### seg017:01FE (+0x0008 in sub_1D88C) - 30 bytes
**Likely: 4-Byte Table Lookup**

Key operations:
```assembly
push es
shl bx, 2           ; Multiply index by 4
mov ax, 0x7772
mov es, ax
mov ax, [es:bx+0x0F36]   ; Load word 1
mov dx, [es:bx+0x0F34]   ; Load word 2
mov [bp-2], ax
mov [bp-4], dx
```

**Purpose:** Looks up a 32-bit value (2 words) from a table at ES:0x0F34.  
Index in BX, result in DX:AX.

**Table location:** Segment 0x7772, offset 0x0F34  
**Entry size:** 4 bytes  
**Likely contents:** Trigonometric values, scaling factors, or transformation matrices

**Confidence:** VERY HIGH

---

### seg017:021C (+0x0026 in sub_1D88C) - 64 bytes
**Likely: Multiply-Accumulate Loop**

Key operations:
- `xor ax, ax` / `xor si, si` - Zero accumulator
- `inc ax; shl ax, 1` - Index calculation
- IMUL instruction
- LOOP instruction
- Multiple segment accesses

**Purpose:** Performs repeated multiply-add operations in a loop.  
Likely: dot product, matrix-vector multiply, or polynomial evaluation.

**Confidence:** HIGH

---

### seg017:01E3 (+0x009F in sub_1D7DA) - 19 bytes
**Likely: Epilogue / Early Return Path**

Key operations:
```assembly
cmp ...
jle +3
jmp -160        ; Jump backwards
popf
pop di
pop si
leave
retf
```

**Purpose:** Function epilogue with conditional early return.  
Restores registers and returns to caller.

**Confidence:** VERY HIGH

---

### seg020:1A2F (+0x00E0 in sub_2100F) - 64 bytes
**Likely: Absolute Value or Min/Max Calculation**

Key operations:
```assembly
cmp dx, cx
jae +2
xchg dx, cx           ; Swap if needed
mov ax, [di+4]
CS: mov dx, [0x0032]
or dx, dx
jns +7                ; Jump if not negative
neg dx; neg ax; sbb dx, 0  ; Two's complement negation of DX:AX
```

**Purpose:** Performs 32-bit absolute value or ensures DX:AX is positive.  
Also does comparison/swap of DX and CX (min/max operation).

**Confidence:** HIGH

---

## Segment 0x7772 - Data Segment

Multiple functions reference segment 0x7772, which appears to be a shared data segment containing:
- Math tables (lookup at 0x0F34)
- Global variables
- Transformation matrices
- Possibly trigonometric tables

**This segment is critical for understanding the math library.**

## Call Graph

```
view_projection (seg020:151B)
    ├─ seg015:0C65 - Segment setup
    ├─ seg015:0C7A - Complex math/dispatcher
    ├─ seg015:0CDB - 32-bit shift left
    ├─ seg015:0CF0 - Far call to external math
    ├─ seg015:0D51 - Wrapper with cleanup
    ├─ seg015:0D66 - Conditional math
    ├─ seg017:01FE - Table lookup (4-byte entries)
    ├─ seg017:021C - Multiply-accumulate loop
    ├─ seg017:01E3 - Epilogue/early return
    └─ seg020:1A2F - Absolute value / min-max
```

## Naming Recommendations

| Current | Segment:Offset | Recommended Name | Rationale |
|---------|----------------|------------------|-----------|
| sub_1CC2D+2A | seg015:0C65 | math_segment_setup | Sets up ES for data access |
| sub_1CC2D+3F | seg015:0C7A | math_complex_dispatcher | Large, complex control flow |
| sub_1CC2D+A0 | seg015:0CDB | fixed_shift_left_32 | 32-bit left shift |
| sub_1CC2D+B5 | seg015:0CF0 | math_farcall_wrapper | Calls external math function |
| sub_1CC2D+116 | seg015:0D51 | math_call_with_cleanup | Wrapper with stack cleanup |
| sub_1CC2D+12B | seg015:0D66 | math_conditional_op | Conditional branching |
| sub_1D88C+8 | seg017:01FE | table_lookup_32bit | 4-byte table lookup |
| sub_1D88C+26 | seg017:021C | multiply_accumulate_loop | MAC operation |
| sub_1D7DA+9F | seg017:01E3 | function_epilogue_cond | Conditional return |
| sub_2100F+E0 | seg020:1A2F | abs_value_32bit | Absolute value DX:AX |

## Next Steps for Full Understanding

### 1. IDA Disassembly (Priority 1)

Navigate to each address in IDA and:
- Get full, accurate disassembly
- Identify all registers used
- Trace data flow
- Confirm/correct our guesses

### 2. Segment 0x7772 Investigation (Priority 2)

- Navigate to segment 0x7772 in IDA
- Examine data at offset 0x0F34 (table used by seg017:01FE)
- Check for sin/cos tables, matrices, scaling factors
- Document table structure

### 3. External Call Investigation (Priority 3)

- seg015:0CF0 calls far 0x1994:0D94
- This could be ROM BIOS, math coprocessor emulation, or external library
- Identify what segment 0x1994 is
- Determine function at 0x1994:0D94

### 4. view_projection Call Context (Priority 4)

For each helper, identify:
- What parameters view_projection passes
- What registers contain inputs
- What registers/memory contain outputs
- When in the projection pipeline each is called

## Integration with view_projection

Based on identified operations, view_projection likely follows this pipeline:

```
1. Setup segment (seg015:0C65)
2. Load transformation data (seg017:01FE table lookup)
3. Perform coordinate calculations:
   - 32-bit shifts (seg015:0CDB)
   - Multiply-accumulate (seg017:021C)
   - Absolute values (seg020:1A2F)
   - Conditional operations (seg015:0D66)
4. Complex transformations (seg015:0C7A, seg015:0CF0)
5. Return (seg017:01E3)
```

## Files Created

- extract_math_bytecode.py - Bytecode extraction script
- disassemble_math_helpers.py - Simple x86 disassembler
- math_helper_bytecode.json - Extracted bytecode data
- math_helpers_identified.md - This document

---

**Status:** Preliminary analysis complete  
**Next:** IDA disassembly verification  
**Blockers:** None - can proceed with IDA review  
**Confidence:** Medium-High (60-80% accuracy expected)
