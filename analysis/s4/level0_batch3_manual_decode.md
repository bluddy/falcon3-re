# Level-0 Batch 3 (ranks 21-35) - Manual Decode

## Tiny Functions (5-6 bytes)

### 5. sub_231BC (0x231BC, 5B, dyn=47, in=2)
```
Bytecode: 2e a3 62 36 cb
Disasm:   seg cs ; mov [0x3662], ax ; retf
```
**Purpose:** Write AX to CS:[0x3662]  
**Callers:** sub_306D1, sub_322E5  
**Name:** `cs_word_3662_set`

### 6. sub_231C1 (0x231C1, 5B, dyn=47, in=2)
```
Bytecode: 2e a3 64 36 cb
Disasm:   seg cs ; mov [0x3664], ax ; retf
```
**Purpose:** Write AX to CS:[0x3664] (consecutive with 0x3662!)  
**Callers:** sub_306D1, sub_322E5  
**Name:** `cs_word_3664_set`  
**Pattern:** Pair of consecutive word setters (same callers)

### 7. sub_22DF0 (0x22DF0, 5B, dyn=46, in=4)
```
Bytecode: 2e a3 bf 37 cb
Disasm:   seg cs ; mov [0x37BF], ax ; retf
```
**Purpose:** Write AX to CS:[0x37BF]  
**Callers:** sub_32453, sub_3252B, sub_327C8, sub_416EC  
**Name:** `cs_word_37bf_set`

### 8. sub_22DF5 (0x22DF5, 5B, dyn=46, in=4)
```
Bytecode: 2e a3 d3 37 cb
Disasm:   seg cs ; mov [0x37D3], ax ; retf
```
**Purpose:** Write AX to CS:[0x37D3]  
**Callers:** sub_32453, sub_3252B, sub_327C8, sub_416EC (SAME as sub_22DF0!)  
**Name:** `cs_word_37d3_set`  
**Pattern:** Another pair (0x37BF, 0x37D3) with identical callers

### 2. sub_254CA (0x254CA, 6B, dyn=90, in=0)
```
Bytecode: 2e ff 1e a0 2a cb
Disasm:   seg cs ; call far [0x2AA0] ; retf
```
**Purpose:** Far call through CS:[0x2AA0] (indirect call via pointer)  
**Callers:** NONE (indirect/dispatch table only)  
**Name:** `stub_via_cs_2aa0`  
**Pattern:** Dispatch table stub

## Small Functions (8-13 bytes)

### 11. sub_2C969 (0x2C969, 8B, dyn=24, in=2)
```
Bytecode: e8 51 e6 ea 3f 17 9f 66
Disasm:   call near 0x10FBD     ; call to 0x2C969 + 0xE651 = wrong, need proper decode
                                 ; Actually: e8 51 e6 = call (signed offset -6575)
                                 ; Target = 0x2C969 + 3 - 6575 = 0x2C96C - 0x19AF = 0x10FBD
          jmp far 0x669F:173F    ; ea 3f 17 9f 66
```
**Purpose:** Call near helper then jump far to 0x669F:173F  
**Callers:** sub_1AA1F0, sub_1AAA98 (overlay entries)  
**Name:** `call_10fbd_jmp_669f_173f` or investigate targets  
**Pattern:** Two-stage dispatch (near call + far jump)

### 14. sub_23050 (0x23050, 11B, dyn=9, in=1)
```
Bytecode: 2e 89 36 fe 36 2e 8c 1e 00 37 cb
Disasm:   seg cs
          mov [0x36FE], si       ; save SI to CS:[0x36FE]
          seg cs
          mov [0x3700], ds       ; save DS to CS:[0x3700]
          retf
```
**Purpose:** Save SI and DS to CS:[0x36FE:0x3700] (register preservation)  
**Caller:** sub_3001E  
**Name:** `cs_save_si_ds_36fe`  
**Pattern:** Context save to CS-segment

### 13. sub_231C6 (0x231C6, 13B, dyn=9, in=3)
```
Bytecode: 3d 0f 00 7e 03 b8 0f 00 2e a3 66 36 cb
Disasm:   cmp ax, 0x000F         ; compare AX with 15
          jle skip               ; if AX <= 15, skip
          mov ax, 0x000F         ; else clamp AX = 15
  skip:   seg cs
          mov [0x3666], ax       ; write to CS:[0x3666]
          retf
```
**Purpose:** Clamp AX to max 15, write to CS:[0x3666]  
**Callers:** sub_2F6D0, sub_3EEDB, sub_416EC  
**Name:** `cs_word_3666_set_clamped`  
**Pattern:** Range-limited setter (clamp to 0-15)

## Medium Functions (12-23 bytes)

### 1. sub_274D5 (0x274D5, 12B, dyn=194, in=2)
```
Bytecode: 55 8b ec 8b 46 06 2e a3 ba 7d 5d cb
Disasm:   push bp
          mov bp, sp
          mov ax, [bp+6]         ; get argument from stack
          seg cs
          mov [0x7DBA], ax       ; write to CS:[0x7DBA]
          pop bp
          retf
```
**Purpose:** Far function: read arg from stack, write to CS:[0x7DBA]  
**Callers:** r54_e169, sub_18B071  
**Name:** `cs_word_7dba_set_far`  
**Pattern:** Stack-arg setter (far calling convention)

### 3. sub_254D0 (0x254D0, 12B, dyn=90, in=0)
```
Bytecode: 2e ff 1e a4 2a cb 2e ff 1e d8 2a cb
Disasm:   seg cs ; call far [0x2AA4] ; retf
          seg cs ; call far [0x2AD8] ; retf
```
**Purpose:** TWO FUNCTIONS MERGED!
- First 6B (0x254D0..0x254D5): stub via CS:[0x2AA4]
- Second 6B (0x254D6..0x254DB): stub via CS:[0x2AD8]
**Callers:** NONE (indirect only)  
**Name:** Split needed at 0x254D6!  
**Pattern:** BOUNDARY ERROR (finding 190)

### 4. sub_231A6 (0x231A6, 22B, dyn=60, in=1)
```
Bytecode: 2e 03 06 66 36 79 02 2b c0 3d 0f 00 7e 03 b8 0f 00 2e a3 66 36 cb
Disasm:   seg cs
          add ax, [0x3666]       ; AX += CS:[0x3666]
          jns skip_zero          ; if not negative, skip
          sub ax, ax             ; else AX = 0 (clamp to 0)
  skip_zero:
          cmp ax, 0x000F
          jle store
          mov ax, 0x000F         ; clamp to 15
  store:  seg cs
          mov [0x3666], ax       ; write back to CS:[0x3666]
          retf
```
**Purpose:** Add to CS:[0x3666], clamp result to [0, 15], write back  
**Caller:** sub_32D22  
**Name:** `cs_word_3666_add_clamped`  
**Pattern:** Read-modify-write with clamping (accumulator)

### 9. sub_24E46 (0x24E46, 23B, dyn=34, in=4)
```
Bytecode: 06 57 51 50 8c c8 8e c0 bf 62 57 2b c0 b9 0b 00 f3 aa 58 59 5f 07 cb
Disasm:   push es
          push di
          push cx
          push ax
          mov ax, cs             ; AX = CS
          mov es, ax             ; ES = CS
          mov di, 0x5762         ; DI = 0x5762
          sub ax, ax             ; AX = 0
          mov cx, 11             ; CX = 11 words
          rep stosw              ; zero 11 words at ES:[5762..577B] (22 bytes)
          pop ax
          pop cx
          pop di
          pop es
          retf
```
**Purpose:** Zero 11 words (22 bytes) at CS:[0x5762..0x577B]  
**Callers:** sub_2F6D0, sub_32C62, sub_32D22, sub_3352A  
**Name:** `cs_buffer_5762_clear`  
**Pattern:** Buffer initialization (zero-fill)

### 10. sub_27649 (0x27649, 20B, dyn=33, in=2)
```
Bytecode: 55 8b ec 8b 46 06 8b 56 08 2e 89 16 c2 7d 2e a3 c0 7d 5d cb
Disasm:   push bp
          mov bp, sp
          mov ax, [bp+6]         ; arg1
          mov dx, [bp+8]         ; arg2
          seg cs
          mov [0x7DC2], dx       ; write DX to CS:[0x7DC2]
          seg cs
          mov [0x7DC0], ax       ; write AX to CS:[0x7DC0]
          pop bp
          retf
```
**Purpose:** Far function: write two stack args to CS:[0x7DC0:0x7DC2] (DX:AX pair)  
**Callers:** r54_e169, sub_18B071  
**Name:** `cs_dword_7dc0_set_far`  
**Pattern:** Stack-arg dual-word setter

### 12. sub_2765D (0x2765D, 22B, dyn=13, in=0)
```
Bytecode: 2e 89 16 c2 7d 2e a3 c0 7d cb 55 8b ec 8b 46 06 2e a3 b6 7d 5d cb
Disasm:   seg cs
          mov [0x7DC2], dx       ; write DX to CS:[0x7DC2]
          seg cs
          mov [0x7DC0], ax       ; write AX to CS:[0x7DC0]
          retf
          push bp                ; SECOND FUNCTION STARTS HERE (0x27667)
          mov bp, sp
          mov ax, [bp+6]
          seg cs
          mov [0x7DB6], ax       ; write arg to CS:[0x7DB6]
          pop bp
          retf
```
**Purpose:** TWO FUNCTIONS MERGED!
- First 10B (0x2765D..0x27666): cs_dword_7dc0_set (register-arg version)
- Second 12B (0x27667..0x27672): cs_word_7db6_set_far (stack-arg version)
**Callers:** NONE (indirect only)  
**Name:** Split needed at 0x27667!  
**Pattern:** BOUNDARY ERROR (finding 190)

## Large Function

### 15. sub_10108 (0x10108, 44B, dyn=8, in=1)
```
Bytecode: 2e c6 06 01 00 00 cb 2e c6 06 01 00 00 2e a0 00 00 0a c0 74 06 2e c6 06 01 00 01 98 cb 2e 80 3e 00 00 00 74 06 2e 80 3e 01 00 00 cb
Disasm:   seg cs ; mov byte [0x0001], 0 ; retf
          seg cs ; mov byte [0x0001], 0
          seg cs ; mov al, [0x0000]
          or al, al
          jz skip1
          seg cs ; mov byte [0x0001], 1
  skip1:  cbw                               ; sign-extend AL to AX
          retf
          seg cs ; cmp byte [0x0000], 0
          jz skip2
          seg cs ; cmp byte [0x0001], 0
  skip2:  retf
```
**Purpose:** THREE FUNCTIONS MERGED!
- 0x10108..0x1010E (7B): cs_byte_0001_clear (write 0 to CS:[0x0001])
- 0x1010F..0x1011E (16B): cs_byte_0001_from_0000 (copy CS:[0x0000] to CS:[0x0001], extend to AX)
- 0x1011F..0x1012F (17B): cs_byte_pair_0000_0001_test (test both bytes)
**Caller:** sub_3001E  
**Name:** Split needed at 0x1010F and 0x1011F!  
**Pattern:** BOUNDARY ERROR (finding 190) - 3-way merge

---

## Findings Summary

**Finding 190: Three More Boundary Errors (Merged Functions)**

1. **sub_254D0** (0x254D0, 12B) = 2 functions:
   - 0x254D0..0x254D5 (6B): `stub_via_cs_2aa4`
   - 0x254D6..0x254DB (6B): `stub_via_cs_2ad8`

2. **sub_2765D** (0x2765D, 22B) = 2 functions:
   - 0x2765D..0x27666 (10B): `cs_dword_7dc0_set`
   - 0x27667..0x27672 (12B): `cs_word_7db6_set_far`

3. **sub_10108** (0x10108, 44B) = 3 functions:
   - 0x10108..0x1010E (7B): `cs_byte_0001_clear`
   - 0x1010F..0x1011E (16B): `cs_byte_0001_from_0000`
   - 0x1011F..0x1012F (17B): `cs_byte_pair_0000_0001_test`

All missed by P1 splits (findings 145-160). Need SPLIT manifests.

**Finding 191: CS-Segment State Block Extensions (continued)**

Batch 3 discovered 9 more CS-segment accessors:
- `cs_word_3662_set`, `cs_word_3664_set` (0x3662:0x3664 pair)
- `cs_word_37bf_set`, `cs_word_37d3_set` (0x37BF, 0x37D3 pair)
- `cs_save_si_ds_36fe` (0x36FE:0x3700 context save)
- `cs_word_3666_set_clamped` (0x3666 with range limit)
- `cs_word_3666_add_clamped` (0x3666 accumulator, 0-15 range)
- `cs_word_7dba_set_far` (0x7DBA stack-arg setter)
- `cs_dword_7dc0_set_far` (0x7DC0:0x7DC2 dual-word, stack-arg)
- `cs_buffer_5762_clear` (0x5762..0x577B, 22-byte buffer)
- Plus 3 more in the merged functions (from finding 190)

CS-segment now spans: 0x0000-0x0001, 0x2B76-0x2B84, 0x3662-0x3666, 0x36FE-0x3708, 0x37BF-0x37D3, 0x5762-0x577B, 0x5DD1-0x5DD3, 0x7DB6-0x7DC2

**Finding 192: Dispatch Table Stubs**

- `stub_via_cs_2aa0` (0x254CA) - far call through CS:[0x2AA0]
- `stub_via_cs_2aa4` and `stub_via_cs_2ad8` (in merged sub_254D0)
- Pattern: CS-segment dispatch table (pointer array at 0x2AA0+)

**Finding 193: Two-Stage Overlay Dispatcher**

- `call_10fbd_jmp_669f_173f` (sub_2C969) - near call then far jump
- Pattern: local helper + overlay target (2 overlay callers)

**Naming Batch 3 (12 of 15 functions, 3 need splits):**
1. sub_274D5 → cs_word_7dba_set_far
2. sub_254CA → stub_via_cs_2aa0
3. sub_254D0 → NEEDS SPLIT (2 functions)
4. sub_231A6 → cs_word_3666_add_clamped
5. sub_231BC → cs_word_3662_set
6. sub_231C1 → cs_word_3664_set
7. sub_22DF0 → cs_word_37bf_set
8. sub_22DF5 → cs_word_37d3_set
9. sub_24E46 → cs_buffer_5762_clear
10. sub_27649 → cs_dword_7dc0_set_far
11. sub_2C969 → call_10fbd_jmp_669f_173f
12. sub_2765D → NEEDS SPLIT (2 functions)
13. sub_231C6 → cs_word_3666_set_clamped
14. sub_23050 → cs_save_si_ds_36fe
15. sub_10108 → NEEDS SPLIT (3 functions)
