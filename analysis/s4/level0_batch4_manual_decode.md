# Level-0 Batch 4 Manual Decode (ranks 36-50)

## Overview
- **Batch size**: 15 functions
- **Call range**: 9,698 - 13,287 dyn_calls
- **Size range**: 2-79B
- **Already named**: 4 functions (ranks 41, 42, 49, 50 from batch 1)
- **New to name**: 11 functions

---

## Rank 36: sub_260A9 (0x260A9, 6B, dyn=13287, in=5)
```
Bytecode: 2eff1e042acb
```

**Decode:**
```asm
2e ff 1e 04 2a    call far cs:[0x2A04]
cb                retf
```

**Analysis:**
- Far call through CS-segment pointer at 0x2A04
- Part of CS:[0x2AA0+] dispatch table region (finding 192)
- Pattern: `call far cs:[offset]` + `retf`

**Name:** `stub_via_cs_2a04`
**Category:** Dispatch table stub (CS-segment pointer array)

---

## Rank 37: sub_22964 (0x22964, 50B, dyn=12896, in=2)
```
Bytecode: 2e8b0e602be324b823012bd2f7f13d04007307b80400bb4000cb8bd82bd28ad58ae12ac0b92301f7f193cbb80001bb0100cb
```

**Decode:**
```asm
2e 8b 0e 60 2b    mov cx, cs:[0x2B60]     ; load CS-segment word
e3 24             jcxz +0x26              ; if zero, skip to end
b8 23 01          mov ax, 0x0123
2b d2             sub dx, dx              ; dx = 0
f7 f1             div cx                  ; ax = 0x0123 / cx
3d 04 00          cmp ax, 0x0004
73 07             jnc +0x07               ; if >= 4
b8 04 00          mov ax, 0x0004
bb 40 00          mov bx, 0x0040
cb                retf
8b d8             mov bx, ax              ; bx = quotient
2b d2             sub dx, dx
8a d5             mov dl, ch              ; dl = high byte of cx
8a e1             mov ah, cl              ; ah = low byte of cx
2a c0             sub al, al
b9 23 01          mov cx, 0x0123
f7 f1             div cx
93                xchg ax, bx
cb                retf
b8 00 01          mov ax, 0x0100
bb 01 00          mov bx, 0x0001
cb                retf
```

**Analysis:**
- Loads CS:[0x2B60] (new CS-segment state variable)
- Division by CS-segment value, clamping result to [0, 4]
- Multiple return paths with different AX:BX pairs
- Constant 0x0123 (291 decimal) appears twice
- Complex: likely scaling/normalization based on CS-segment divisor

**Name:** `cs_word_2b60_scale_div` (tentative - needs deeper analysis)
**Category:** CS-segment state accessor + math

---

## Rank 38: sub_22884 (0x22884, 59B, dyn=12413, in=18)
```
Bytecode: 5053515256b3202aed0ac97d04f6d9eb080bc07d04b32df7d8fec1880c885c0103f149bb0a00887c012bd2f7f380c23088144ee2f45e5a595b58cb
```

**Decode:**
```asm
50                push ax
53                push bx
51                push cx
52                push dx
56                push si
b3 20             mov bl, 0x20            ; bl = ' ' (space char)
2a ed             sub ch, ch              ; ch = 0
0a c9             or cl, cl               ; test cl
7d 04             jge +0x04               ; if cl >= 0
f6 d9             neg cl
eb 08             jmp +0x08
0b c0             or ax, ax               ; test ax
7d 04             jge +0x04               ; if ax >= 0
b3 2d             mov bl, 0x2D            ; bl = '-' (minus sign)
f7 d8             neg ax
fe c1             inc cl
88 0c             mov [si], cl            ; write cl to [si]
88 5c 01          mov [si+1], bl          ; write sign char
03 f1             add si, cx
49                dec cx
bb 0a 00          mov bx, 0x000A          ; divisor = 10
88 7c 01          mov [si+1], bh          ; write 0 (null term?)
2b d2             sub dx, dx
f7 f3             div bx                  ; ax = ax / 10, dx = remainder
80 c2 30          add dl, 0x30            ; convert to ASCII digit
88 14             mov [si], dl            ; write digit
4e                dec si
e2 f4             loop -0x0C              ; repeat cx times
5e                pop si
5a                pop dx
59                pop cx
5b                pop bx
58                pop ax
cb                retf
```

**Analysis:**
- Number-to-ASCII decimal string conversion
- Input: AX = signed integer, SI = buffer pointer, CL = field width
- Output: ASCII decimal string at [SI], space or minus sign for padding
- Classic itoa/sprintf pattern: divide by 10, convert remainder to ASCII

**Name:** `itoa_decimal_signed`
**Category:** String formatting utility

---

## Rank 39: sub_2302B (0x2302B, 11B, dyn=12091, in=3)
```
Bytecode: 2e8b3622002eff940000cb
```

**Decode:**
```asm
2e 8b 36 22 00    mov si, cs:[0x0022]     ; load CS-segment word to SI
2e ff 94 00 00    call word ptr cs:[si+0] ; indirect call through CS:[SI]
cb                retf
```

**Analysis:**
- Load dispatch index from CS:[0x0022]
- Indirect call through CS-segment table at CS:[SI]
- Pattern: secondary dispatch (index stored in CS-segment)

**Name:** `dispatch_via_cs_0022_table`
**Category:** Indirect dispatcher

---

## Rank 40: sub_20AAA (0x20AAA, 18B, dyn=12091, in=3)
```
Bytecode: 06b80e7b8ec0bfbc0eb914002bc0f3ab07cb
```

**Decode:**
```asm
06                push es
b8 0e 7b          mov ax, 0x7B0E          ; segment 0x7B0E
8e c0             mov es, ax
bf bc 0e          mov di, 0x0EBC          ; offset 0x0EBC
b9 14 00          mov cx, 0x0014          ; count = 20 words
2b c0             sub ax, ax              ; ax = 0
f3 ab             rep stosw                ; zero-fill 20 words (40 bytes)
07                pop es
cb                retf
```

**Analysis:**
- Zero-fill 40 bytes at ES:7B0E:0EBC
- Segment 0x7B0E is view/projection space (finding 185)
- Buffer clear operation

**Name:** `seg7b0e_clear_0ebc_40bytes`
**Category:** Buffer initialization (segment 0x7B0E state)

---

## Rank 41: sub_12890 (ALREADY NAMED: cs_byte_00e8_get, batch 1)
```
Bytecode: 2ea0e800cb
```

Skipping (already in ledger).

---

## Rank 42: sub_2295C (ALREADY NAMED: zero_ax, batch 1)
```
Bytecode: 2bc0
```

Skipping (already in ledger).

---

## Rank 43: sub_22CD5 (0x22CD5, 68B, dyn=11084, in=12)
```
Bytecode: 50522ea1b7352ef726bd352ef736c3352e8916b7358bca2ea1b9352ef726bf352ef736c5352e8916b93503ca2ea1bb352ef726c1352ef736c7352e8916bb3503ca5a58cb
```

**Decode:**
```asm
50                push ax
52                push dx
2e a1 b7 35       mov ax, cs:[0x35B7]     ; load word
2e f7 26 bd 35    mul word ptr cs:[0x35BD] ; multiply
2e f7 36 c3 35    div word ptr cs:[0x35C3] ; divide
2e 89 16 b7 35    mov cs:[0x35B7], dx     ; store remainder back
8b ca             mov cx, dx
2e a1 b9 35       mov ax, cs:[0x35B9]     ; load second word
2e f7 26 bf 35    mul word ptr cs:[0x35BF]
2e f7 36 c5 35    div word ptr cs:[0x35C5]
2e 89 16 b9 35    mov cs:[0x35B9], dx     ; store remainder
03 ca             add cx, dx
2e a1 bb 35       mov ax, cs:[0x35BB]     ; load third word
2e f7 26 c1 35    mul word ptr cs:[0x35C1]
2e f7 36 c7 35    div word ptr cs:[0x35C7]
2e 89 16 bb 35    mov cs:[0x35BB], dx     ; store remainder
03 ca             add cx, dx
5a                pop dx
58                pop ax
cb                retf
```

**Analysis:**
- Three parallel (word * word / word) operations on CS-segment state
- State triplet: CS:[0x35B7], CS:[0x35B9], CS:[0x35BB]
- Parameter triplet: multipliers at 0x35BD/BF/C1, divisors at 0x35C3/C5/C7
- Accumulates remainders into CX
- Pattern: pseudo-random number generator (linear congruential or similar)

**Name:** `prng_step_triple_lcg`
**Category:** PRNG/random number generation

---

## Rank 44: sub_14C77 (0x14C77, 79B, dyn=10756, in=5)
```
Bytecode: 8b048b540283fa287c07ba28002bc0eb0a83fad87f05bad8ff2bc089058955028b44048b540683fa287c07ba28002bc0eb0a83fad87f05bad8ff2bc08945048955068b44088b540a89450889550acb
```

**Decode:**
```asm
8b 04             mov ax, [si]            ; load word from [SI]
8b 54 02          mov dx, [si+2]          ; load word from [SI+2]
83 fa 28          cmp dx, 0x0028
7c 07             jl +0x07                ; if dx < 40
ba 28 00          mov dx, 0x0028          ; clamp to 40
2b c0             sub ax, ax
eb 0a             jmp +0x0A
83 fa d8          cmp dx, 0xFFD8          ; -40 in signed 16-bit
7f 05             jg +0x05                ; if dx > -40
ba d8 ff          mov dx, 0xFFD8          ; clamp to -40
2b c0             sub ax, ax
89 05             mov [di], ax            ; write to [DI]
89 55 02          mov [di+2], dx          ; write to [DI+2]
; Repeat for [SI+4]/[SI+6] → [DI+4]/[DI+6]
8b 44 04          mov ax, [si+4]
8b 54 06          mov dx, [si+6]
83 fa 28          cmp dx, 0x0028
7c 07             jl +0x07
ba 28 00          mov dx, 0x0028
2b c0             sub ax, ax
eb 0a             jmp +0x0A
83 fa d8          cmp dx, 0xFFD8
7f 05             jg +0x05
ba d8 ff          mov dx, 0xFFD8
2b c0             sub ax, ax
89 45 04          mov [di+4], ax
89 55 06          mov [di+6], dx
; Repeat for [SI+8]/[SI+10] → [DI+8]/[DI+10]
8b 44 08          mov ax, [si+8]
8b 54 0a          mov dx, [si+10]
89 45 08          mov [di+8], ax
89 55 0a          mov [di+10], dx
cb                retf
```

**Analysis:**
- Copies 12 bytes (6 words) from [SI] to [DI]
- Clamps first two dword values to range [-40, 40] (sets high word to 0 on clamp)
- Third dword copied unchanged
- Pattern: 3D vector component clamping (velocity or acceleration limit)

**Name:** `vec3_copy_clamp_xy_40`
**Category:** 3D vector operation with range limiting

---

## Rank 45: sub_22C53 (0x22C53, 15B, dyn=10709, in=2)
```
Bytecode: 2ea3b1352e891eb3352e890eb535cb
```

**Decode:**
```asm
2e a3 b1 35       mov cs:[0x35B1], ax     ; write AX
2e 89 1e b3 35    mov cs:[0x35B3], bx     ; write BX
2e 89 0e b5 35    mov cs:[0x35B5], cx     ; write CX
cb                retf
```

**Analysis:**
- Triple-word write to CS-segment state at 0x35B1/B3/B5
- Input: AX, BX, CX
- Pattern: 3-register state save

**Name:** `cs_triple_35b1_set`
**Category:** CS-segment state accessor (triple write)

---

## Rank 46: sub_22C62 (0x22C62, 15B, dyn=10228, in=2)
```
Bytecode: 2ea1b1352e8b1eb3352e8b0eb535cb
```

**Decode:**
```asm
2e a1 b1 35       mov ax, cs:[0x35B1]     ; read to AX
2e 8b 1e b3 35    mov bx, cs:[0x35B3]     ; read to BX
2e 8b 0e b5 35    mov cx, cs:[0x35B5]     ; read to CX
cb                retf
```

**Analysis:**
- Triple-word read from CS-segment state at 0x35B1/B3/B5
- Output: AX, BX, CX
- Pairs with rank 45 (getter/setter pair)

**Name:** `cs_triple_35b1_get`
**Category:** CS-segment state accessor (triple read)

---

## Rank 47: sub_16579 (0x16579, 5B, dyn=10221, in=1)
```
Bytecode: 2ea12801cb
```

**Decode:**
```asm
2e a1 28 01       mov ax, cs:[0x0128]     ; read CS-segment word
cb                retf
```

**Analysis:**
- Simple CS-segment word read at 0x0128
- High call frequency (10,221 calls)

**Name:** `cs_word_0128_get`
**Category:** CS-segment state accessor

---

## Rank 48: sub_25567 (0x25567, 5B, dyn=10139, in=4)
```
Bytecode: 2ea1d95dcb
```

**Decode:**
```asm
2e a1 d9 5d       mov ax, cs:[0x5DD9]     ; read CS-segment word
cb                retf
```

**Analysis:**
- Simple CS-segment word read at 0x5DD9
- Near batch 2's 0x5DD1 range (finding 184)

**Name:** `cs_word_5dd9_get`
**Category:** CS-segment state accessor

---

## Rank 49: sub_22436 (ALREADY NAMED: cs_word_2b76_get, batch 1)
```
Bytecode: 2ea1762bcb
```

Skipping (already in ledger).

---

## Rank 50: sub_2243B (ALREADY NAMED: cs_word_2b78_get, batch 1)
```
Bytecode: 2ea1782bcb
```

Skipping (already in ledger).

---

## Summary

**Named functions (11 new):**
1. stub_via_cs_2a04 (6B) - dispatch table stub
2. cs_word_2b60_scale_div (50B) - CS-segment scaling with division
3. itoa_decimal_signed (59B) - number-to-ASCII conversion
4. dispatch_via_cs_0022_table (11B) - indirect dispatch
5. seg7b0e_clear_0ebc_40bytes (18B) - buffer clear in segment 0x7B0E
6. prng_step_triple_lcg (68B) - pseudo-random number generator
7. vec3_copy_clamp_xy_40 (79B) - 3D vector copy with clamping
8. cs_triple_35b1_set (15B) - triple-word CS-segment write
9. cs_triple_35b1_get (15B) - triple-word CS-segment read
10. cs_word_0128_get (5B) - CS-segment word read
11. cs_word_5dd9_get (5B) - CS-segment word read

**Already named (4):**
- cs_byte_00e8_get (rank 41, batch 1)
- zero_ax (rank 42, batch 1)
- cs_word_2b76_get (rank 49, batch 1)
- cs_word_2b78_get (rank 50, batch 1)

**New CS-segment ranges discovered:**
- 0x0022 (dispatch table index)
- 0x0128 (word)
- 0x2A04 (dispatch pointer, extends 0x2AA0+ region)
- 0x2B60 (word, scaling divisor)
- 0x35B1-0x35B5 (6-byte triple, PRNG/state save)
- 0x35B7-0x35C7 (17-byte PRNG state block)
- 0x5DD9 (word, extends 0x5DD1-0x5DD3 region)

**Patterns:**
- CS-segment state dominates (7 of 11 accessors)
- PRNG discovered (triple LCG at 0x35B7+)
- Number formatting utility (itoa)
- Vector math with clamping
- Segment 0x7B0E continues (view/projection space)
