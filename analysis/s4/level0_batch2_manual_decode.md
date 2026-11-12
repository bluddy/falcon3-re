# Level-0 Batch 2 Top 10 - Manual Decode

## Tiny Functions (5-6 bytes)

### 1. sub_100B5 (0x100B5, 6B, dyn=2953, in=11)
```
Bytecode: 9a df 61 6c 1f cb
Disasm:   call far 1F6C:61DF ; retf
```
**Purpose:** Far call trampoline to 1F6C:61DF  
**Callers:** 11 overlay entries (r17_e07, r22_e57, r23_e61, r24_e60, r25_e59, etc.)  
**Name:** `stub_to_1f6c_61df` or investigate target address  
**Note:** Common overlay stub pattern - warrants investigation of target

### 9. sub_22440 (0x22440, 5B, dyn=489, in=2)
```
Bytecode: 2e a3 76 2b cb
Disasm:   seg cs ; mov [0x2B76], ax ; retf
```
**Purpose:** Write AX to CS:[0x2B76]  
**Callers:** sub_30AE5, sub_30D5F  
**Name:** `cs_word_2b76_set`  
**Note:** COLLISION with batch 1! This writes to same location that cs_word_2b76_get reads from.
But wait - cs_word_2b76_get is 0x22436 (different address), so this is a setter for that getter's location.

## Small Functions (10-23 bytes)

### 2. sub_22DE6 (0x22DE6, 10B, dyn=1706, in=3)
```
Bytecode: 2e 89 16 06 37 2e a3 08 37 cb
Disasm:   seg cs
          mov [0x3706], dx    ; write DX to CS:[0x3706]
          seg cs
          mov [0x3708], ax    ; write AX to CS:[0x3708]
          retf
```
**Purpose:** Store DX:AX pair to CS:[0x3706:0x3708] (consecutive words)  
**Callers:** sub_3252B, sub_327C8, sub_329B1  
**Name:** `cs_dword_3706_set` or `cs_farptr_3706_set`  
**Pattern:** Dual-word storage, possibly far pointer or 32-bit value

### 4. sub_255F6 (0x255F6, 12B, dyn=1302, in=0)
```
Bytecode: fa 2e a1 d1 5d 2e 8b 1e d3 5d fb cb
Disasm:   cli                      ; disable interrupts
          seg cs
          mov ax, [0x5DD1]        ; read word from CS:[0x5DD1]
          seg cs
          mov bx, [0x5DD3]        ; read word from CS:[0x5DD3]
          sti                      ; enable interrupts
          retf
```
**Purpose:** Atomic read of CS:[0x5DD1:0x5DD3] word pair with interrupts disabled  
**Callers:** NONE (in_degree=0, indirect/far-call only via dispatch table)  
**Name:** `cs_dword_5dd1_get_atomic`  
**Pattern:** Critical section around dual-word read (timer/ISR data?)

### 5. sub_22F15 (0x22F15, 23B, dyn=603, in=5)
```
Bytecode: 1e 06 b9 0e 7b 8e d9 8e c1 be 08 38 bf 20 38 b9 09 00 f3 a5 07 1f cb
Disasm:   push ds
          push es
          mov cx, 0x7B0E           ; DS selector = 0x7B0E
          mov ds, cx
          mov es, cx
          mov si, 0x3808           ; source = DS:[0x3808]
          mov di, 0x3820           ; dest = ES:[0x3820] (same segment)
          mov cx, 9                ; count = 9 words
          rep movsw                ; copy 18 bytes
          pop es
          pop ds
          retf
```
**Purpose:** Copy 9 words (18 bytes) from DS:[7B0E:3808] → ES:[7B0E:3820]  
**Callers:** sub_2F400, sub_355E6, sub_3A8B1, sub_404F6, sub_405F7  
**Name:** `seg7b0e_copy_3808_to_3820` or `view_state_copy_forward`  
**Pattern:** Intra-segment memory copy, likely state/buffer management

### 6. sub_22EFE (0x22EFE, 23B, dyn=603, in=4)
```
Bytecode: 1e 06 b9 0e 7b 8e d9 8e c1 be 20 38 bf 08 38 b9 09 00 f3 a5 07 1f cb
Disasm:   push ds
          push es
          mov cx, 0x7B0E
          mov ds, cx
          mov es, cx
          mov si, 0x3820           ; source = DS:[0x3820] (REVERSED!)
          mov di, 0x3808           ; dest = ES:[0x3808]
          mov cx, 9
          rep movsw
          pop es
          pop ds
          retf
```
**Purpose:** Copy 9 words from DS:[7B0E:3820] → ES:[7B0E:3808] (REVERSE of sub_22F15!)  
**Callers:** sub_2F400, sub_355E6, sub_3A8B1, sub_404F6  
**Name:** `seg7b0e_copy_3820_to_3808` or `view_state_copy_back`  
**Pattern:** Paired with sub_22F15 - save/restore pattern for 18-byte state

### 7. sub_2305B (0x2305B, 23B, dyn=534, in=5)
```
Bytecode: 06 bf 0e 7b 8e c7 bf 8a 38 a5 a5 a5 a5 a5 a5 bf 96 38 a5 a5 a5 07 cb
Disasm:   push es
          mov di, 0x7B0E
          mov es, di
          mov di, 0x388A           ; dest 1 = ES:[7B0E:388A]
          movsw / movsw / movsw / movsw / movsw / movsw  ; copy 12 bytes from DS:SI
          mov di, 0x3896           ; dest 2 = ES:[7B0E:3896]
          movsw / movsw / movsw    ; copy 6 more bytes
          pop es
          retf
```
**Purpose:** Copy 18 bytes from DS:SI to ES:[7B0E:388A] (12B) + ES:[7B0E:3896] (6B)  
**Callers:** sub_31319, sub_3141A, sub_32393, sub_329B1, sub_3352A  
**Name:** `seg7b0e_copy_split_388a_3896` or `view_angles_copy_split`  
**Pattern:** Split-destination copy (12B + 6B = 18B total, same as sub_22F15/22EFE!)

### 8. sub_1024A (0x1024A, 30B, dyn=534, in=2)
```
Bytecode: 50 52 2e 8b 16 21 00 2e 8b 1e 0f 00 b8 00 00 b4 44 cd 67 43 b8 01 00 b4 44 cd 67 5a 58 cb
Disasm:   push ax
          push dx
          seg cs
          mov dx, [0x0021]        ; get word from CS:[0x0021]
          seg cs
          mov bx, [0x000F]        ; get word from CS:[0x000F]
          mov ax, 0
          mov ah, 0x44            ; AH=0x44
          int 0x67                ; EMS interrupt (AH=0x44, DX from CS:[0x21], BX from CS:[0xF])
          inc bx                  ; BX++
          mov ax, 1
          mov ah, 0x44            ; AH=0x44
          int 0x67                ; EMS interrupt again (AX=1, same DX, BX+1)
          pop dx
          pop ax
          retf
```
**Purpose:** Two EMS operations (int 0x67, AH=0x44) with params from CS globals  
**Callers:** sub_307A5, sub_4DE76  
**Name:** `ems_dual_op_44` or `ems_map_page_pair`  
**Pattern:** EMS page mapping, AH=0x44 is likely "Map Memory" function

### 10. sub_22445 (0x22445, 16B, dyn=489, in=2)
```
Bytecode: 2e a3 78 2b cb 2b c0 2e a3 76 2b 2e a3 78 2b cb
Disasm:   seg cs
          mov [0x2B78], ax        ; write AX to CS:[0x2B78]
          retf
          sub ax, ax              ; AX = 0
          seg cs
          mov [0x2B76], ax        ; write 0 to CS:[0x2B76]
          seg cs
          mov [0x2B78], ax        ; write 0 to CS:[0x2B78]
          retf
```
**Purpose:** TWO FUNCTIONS MERGED!
- First 5 bytes (0x22445..0x22449): cs_word_2b78_set (write AX to CS:[0x2B78])
- Next 11 bytes (0x2244A..0x22454): zero_pair_2b76_2b78 (write 0 to both CS:[0x2B76] and CS:[0x2B78])
**Callers:** sub_30AE5, sub_30D5F (which entry point do they use?)  
**Name:** Split needed! First function `cs_word_2b78_set`, second `cs_pair_2b76_2b78_clear`  
**Note:** BOUNDARY ERROR! Two functions merged, needs split at 0x2244A

## Medium Function

### 3. sub_22F2C (0x22F2C, 163B, dyn=1453, in=1)
Complex 163-byte function with:
- Sign testing and flag manipulation
- Division and multiplication by fixed constants (0x4000, 0xB4)
- Computed jump via `2e ff a7 0f 39` = `jmp cs:[bx + 0x390F]` (dispatch table)
- Multiple return paths with different transformations

**Purpose:** Fixed-point arithmetic with dispatch table (likely angle/trig normalization)  
**Caller:** sub_45270 (single caller, likely critical math routine)  
**Name:** `fixed_normalize_dispatch` or `angle_range_transform`  
**Pattern:** Range-based transformation with jump table

---

## Findings Summary

**Finding 184: Batch 2 CS-Segment State Block Extensions**
- Discovered 4 more CS-segment accessors:
  - `cs_word_2b76_set` (0x22440) - setter for 0x2B76 (batch 1 had getter)
  - `cs_dword_3706_set` (0x22DE6) - DX:AX pair write to CS:[0x3706:0x3708]
  - `cs_dword_5dd1_get_atomic` (0x255F6) - atomic read with CLI/STI (ISR-safe)
  - `cs_word_2b78_set` (0x22445) - at merged function boundary!

**Finding 185: View State 18-Byte Buffer Trio (seg 0x7B0E)**
- Three paired functions operating on same 18-byte buffer:
  - `seg7b0e_copy_3808_to_3820` (sub_22F15) - copy forward
  - `seg7b0e_copy_3820_to_3808` (sub_22EFE) - copy back (restore)
  - `seg7b0e_copy_split_388a_3896` (sub_2305B) - split-dest copy (12B + 6B)
- Pattern: save/restore mechanism for view angles or projection state
- Segment 0x7B0E is view/projection working space (finding 114 context)

**Finding 186: Boundary Error - sub_22445 Merged Function**
- Function at 0x22445 (16B) is TWO functions:
  - 0x22445..0x22449 (5B): `cs_word_2b78_set` (write AX to CS:[0x2B78])
  - 0x2244A..0x22454 (11B): `cs_pair_2b76_2b78_clear` (zero both words)
- Needs SPLIT at 0x2244A
- Both operate on CS-segment state block (0x2B76-0x2B78 range from batch 1)

**Finding 187: Overlay Stub Chain**
- `stub_to_1f6c_61df` (sub_100B5, 2953 calls, 11 callers) - investigate target 1F6C:61DF
- High call frequency suggests critical overlay function

**Finding 188: EMS Page Mapping Pair**
- `ems_dual_op_44` (sub_1024A) - two consecutive EMS int 0x67 AH=0x44 operations
- Likely maps two consecutive EMS pages using params from CS:[0x21] and CS:[0xF]

**Finding 189: Fixed-Point Math Dispatcher**
- `fixed_normalize_dispatch` (sub_22F2C, 163B) - range-based transformation with jump table
- Single caller (sub_45270), critical math routine

**Naming Batch 2 (10 functions, pending split of sub_22445):**
1. sub_100B5 → stub_to_1f6c_61df
2. sub_22DE6 → cs_dword_3706_set
3. sub_22F2C → fixed_normalize_dispatch
4. sub_255F6 → cs_dword_5dd1_get_atomic
5. sub_22F15 → seg7b0e_copy_3808_to_3820
6. sub_22EFE → seg7b0e_copy_3820_to_3808
7. sub_2305B → seg7b0e_copy_split_388a_3896
8. sub_1024A → ems_dual_op_44
9. sub_22440 → cs_word_2b76_set
10. sub_22445 → **NEEDS SPLIT** (two functions merged at 0x2244A)
