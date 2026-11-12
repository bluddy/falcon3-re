# Level-0 Batch 5 Manual Decode (ranks 51-65)

## Overview
- **Batch size**: 15 functions
- **Call range**: 4,580 - 9,210 dyn_calls
- **Size range**: 5-92B
- **Already named**: 5 functions (ranks 52,54,56,57,58 from batch 1)
- **New to name**: 10 functions

---

## Rank 51: sub_222AA (0x222AA, 41B, dyn=9210, in=1)
```
Bytecode: ba9000f7e08ac48ae28bd03d12007d0bb8120083fa087d03ba08002ea36c2b2e89166e2b2ea3702bcb
```

**Decode:**
```asm
ba 90 00          mov dx, 0x0090          ; dx = 144
f7 e0             mul ax                  ; dx:ax = ax * ax (square)
8a c4             mov al, ah              ; al = high byte of low word
8a e2             mov ah, dl              ; ah = low byte of high word
8b d0             mov dx, ax              ; dx = shifted result (divide by 256)
3d 12 00          cmp ax, 0x0012          ; compare to 18
7d 0b             jge +0x0B               ; if >= 18
b8 12 00          mov ax, 0x0012          ; clamp to 18
83 fa 08          cmp dx, 0x0008          ; compare to 8
7d 03             jge +0x03               ; if >= 8
ba 08 00          mov dx, 0x0008          ; clamp to 8
2e a3 6c 2b       mov cs:[0x2B6C], ax     ; store AX
2e 89 16 6e 2b    mov cs:[0x2B6E], dx     ; store DX
2e a3 70 2b       mov cs:[0x2B70], ax     ; store AX again
cb                retf
```

**Analysis:**
- Input: AX (likely 0-255 range)
- Multiply by 144 (0x90), then divide by 256 (shift right 8 bits)
- Clamp AX to [18, ∞), DX to [8, ∞)
- Store results to three CS-segment words: 0x2B6C, 0x2B6E, 0x2B70
- Pattern: scaling/normalization with minimum bounds

**Name:** `cs_scale_144_clamp_store_2b6c`
**Category:** CS-segment math + state update

---

## Rank 52: sub_2284B (ALREADY NAMED: cs_word_2b82_set, batch 1)
```
Bytecode: 2ea3822bcb
```

Skipping (already in ledger).

---

## Rank 53: sub_10CBE (0x10CBE, 5B, dyn=9141, in=6)
```
Bytecode: 2ea10200cb
```

**Decode:**
```asm
2e a1 02 00       mov ax, cs:[0x0002]     ; read CS-segment word
cb                retf
```

**Analysis:**
- Simple CS-segment word read at 0x0002
- Extends 0x0000-0x0001 region (finding 190)

**Name:** `cs_word_0002_get`
**Category:** CS-segment state accessor

---

## Rank 54: sub_230D8 (ALREADY NAMED: trig_lookup_sin, batch 1)
```
Bytecode: 06bb64838ec325ff3f8bd8d1ebd1ebd1eba900107525a90020750f81eb0002f7dbd1e3268b87000007cb81eb0006f7dbd1e3268b870000f7d807cba90020750d81eb0002d1e3268b87000007cb81eb0006d1e3268b870000f7d807cb
```

Skipping (already in ledger).

---

## Rank 55: sub_22841 (0x22841, 5B, dyn=8386, in=1)
```
Bytecode: 2ea37e2bcb
```

**Decode:**
```asm
2e a3 7e 2b       mov cs:[0x2B7E], ax     ; write AX to CS-segment
cb                retf
```

**Analysis:**
- Simple CS-segment word write at 0x2B7E
- Extends 0x2B76-0x2B84 region

**Name:** `cs_word_2b7e_set`
**Category:** CS-segment state accessor

---

## Rank 56: sub_22846 (ALREADY NAMED: cs_word_2b80_set, batch 1)
```
Bytecode: 2ea3802bcb
```

Skipping (already in ledger).

---

## Rank 57: sub_23134 (ALREADY NAMED: trig_lookup_cos, batch 1)
```
Bytecode: 06bb64838ec325ff3f8bd8d1ebd1ebd1eba90010751da900207509d1e3268b87000007cb81eb0004d1e3268b870000f7d807cba90020751181eb0004f7dbd1e3268b870000f7d807cb81eb0008f7dbd1e3268b87000007cb
```

Skipping (already in ledger).

---

## Rank 58: sub_22850 (ALREADY NAMED: cs_word_2b84_set, batch 1)
```
Bytecode: 2ea3842bcb
```

Skipping (already in ledger).

---

## Rank 59: sub_25EA3 (0x25EA3, 5B, dyn=7449, in=2)
```
Bytecode: 2ea0c75dcb
```

**Decode:**
```asm
2e a0 c7 5d       mov al, cs:[0x5DC7]     ; read CS-segment byte
cb                retf
```

**Analysis:**
- CS-segment byte read at 0x5DC7
- Near 0x5DD1-0x5DD9 region (findings 184, 194)

**Name:** `cs_byte_5dc7_get`
**Category:** CS-segment state accessor

---

## Rank 60: sub_2033F (0x2033F, 21B, dyn=7271, in=3)
```
Bytecode: 2ea10c00ab2ea10e00ab2ea11000ab2ea11200abcb
```

**Decode:**
```asm
2e a1 0c 00       mov ax, cs:[0x000C]     ; read CS-segment word
ab                stosw                    ; [ES:DI] = AX, DI += 2
2e a1 0e 00       mov ax, cs:[0x000E]     ; read next word
ab                stosw
2e a1 10 00       mov ax, cs:[0x0010]     ; read next word
ab                stosw
2e a1 12 00       mov ax, cs:[0x0012]     ; read next word
ab                stosw
cb                retf
```

**Analysis:**
- Read 4 consecutive CS-segment words (0x000C-0x0012, 8 bytes)
- Write to buffer at ES:DI
- Pattern: block copy from CS-segment state to caller's buffer

**Name:** `cs_block_000c_to_esdi_8bytes`
**Category:** CS-segment block copy

---

## Rank 61: sub_24D64 (0x24D64, 60B, dyn=6981, in=10)
```
Bytecode: 06b84a838ec02ef606fc54c0741e535657432ef606fc54407401472ea0fb542e8b2ef8542eff1ee8295f5e5b2e8b2ef8542ea0fa542eff1ee82907cb
```

**Decode:**
```asm
06                push es
b8 4a 83          mov ax, 0x834A          ; segment 0x834A
8e c0             mov es, ax
2e f6 06 fc 54 c0 test byte ptr cs:[0x54FC], 0xC0  ; test bits 6+7
74 1e             jz +0x1E                ; if both clear, skip
53                push bx
56                push si
57                push di
43                inc bx
2e f6 06 fc 54 40 test byte ptr cs:[0x54FC], 0x40  ; test bit 6
74 01             jz +0x01                ; if clear, skip inc
47                inc di
2e a0 fb 54       mov al, cs:[0x54FB]     ; read byte
2e 8b 2e f8 54    mov bp, cs:[0x54F8]     ; read word to BP
2e ff 1e e8 29    call far cs:[0x29E8]    ; indirect far call
5f                pop di
5e                pop si
5b                pop bx
2e 8b 2e f8 54    mov bp, cs:[0x54F8]     ; read BP again
2e a0 fa 54       mov al, cs:[0x54FA]     ; read another byte
2e ff 1e e8 29    call far cs:[0x29E8]    ; indirect far call again
07                pop es
cb                retf
```

**Analysis:**
- Segment 0x834A setup (likely data segment)
- Conditional execution based on CS:[0x54FC] flags
- Two far indirect calls through CS:[0x29E8] (dispatch table pointer)
- Loads parameters from CS-segment state before each call
- Pattern: conditional dual-dispatch with CS-segment parameters

**Name:** `dispatch_dual_seg834a_cs54fc`
**Category:** Complex dispatcher with flags

---

## Rank 62: sub_24D46 (0x24D46, 6B, dyn=6623, in=0)
```
Bytecode: 2eff1ee829cb
```

**Decode:**
```asm
2e ff 1e e8 29    call far cs:[0x29E8]    ; indirect far call
cb                retf
```

**Analysis:**
- Simple dispatch through CS:[0x29E8] pointer
- Zero static callers (indirect dispatch target)
- Pairs with rank 61's dual-dispatch

**Name:** `stub_via_cs_29e8`
**Category:** Dispatch table stub

---

## Rank 63: sub_100AF (0x100AF, 6B, dyn=6537, in=1)
```
Bytecode: 2ea0000098cb
```

**Decode:**
```asm
2e a0 00 00       mov al, cs:[0x0000]     ; read CS-segment byte
98                cbw                      ; sign-extend AL to AX
cb                retf
```

**Analysis:**
- Read CS:[0x0000] byte, sign-extend to word
- Part of 0x0000-0x0002 region (ranks 53, finding 190)

**Name:** `cs_byte_0000_get_signext`
**Category:** CS-segment state accessor with sign extension

---

## Rank 64: sub_25EEE (0x25EEE, 6B, dyn=5673, in=1)
```
Bytecode: 2eff1e602acb
```

**Decode:**
```asm
2e ff 1e 60 2a    call far cs:[0x2A60]    ; indirect far call
cb                retf
```

**Analysis:**
- Dispatch through CS:[0x2A60] pointer
- Extends 0x2AA0+ dispatch pointer array region

**Name:** `stub_via_cs_2a60`
**Category:** Dispatch table stub

---

## Rank 65: sub_25E6C (0x25E6C, 6B, dyn=4580, in=6)
```
Bytecode: 2eff1ed029cb
```

**Decode:**
```asm
2e ff 1e d0 29    call far cs:[0x29D0]    ; indirect far call
cb                retf
```

**Analysis:**
- Dispatch through CS:[0x29D0] pointer
- New dispatch pointer region (0x29D0-0x29E8)

**Name:** `stub_via_cs_29d0`
**Category:** Dispatch table stub

---

## Summary

**Named functions (10 new):**
1. cs_scale_144_clamp_store_2b6c (41B) - scaling with min bounds + triple store
2. cs_word_0002_get (5B) - CS-segment word read
3. cs_word_2b7e_set (5B) - CS-segment word write
4. cs_byte_5dc7_get (5B) - CS-segment byte read
5. cs_block_000c_to_esdi_8bytes (21B) - block copy 4 words from CS-segment
6. dispatch_dual_seg834a_cs54fc (60B) - conditional dual-dispatcher
7. stub_via_cs_29e8 (6B) - dispatch table stub
8. cs_byte_0000_get_signext (6B) - byte read with sign extension
9. stub_via_cs_2a60 (6B) - dispatch table stub
10. stub_via_cs_29d0 (6B) - dispatch table stub

**Already named (5):**
- cs_word_2b82_set (rank 52, batch 1)
- trig_lookup_sin (rank 54, batch 1)
- cs_word_2b80_set (rank 56, batch 1)
- trig_lookup_cos (rank 57, batch 1)
- cs_word_2b84_set (rank 58, batch 1)

**New CS-segment ranges discovered:**
- 0x0002 (word, extends 0x0000-0x0001 to 0x0000-0x0002)
- 0x000C-0x0012 (7-byte block: 4 words copied to buffer)
- 0x29D0 (dispatch pointer)
- 0x29E8 (dispatch pointer, used by dual-dispatcher)
- 0x2A60 (dispatch pointer, extends 0x2AA0+ region)
- 0x2B6C-0x2B70 (5-byte block: scaled values with min clamps)
- 0x2B7E (word, extends 0x2B76-0x2B84 region)
- 0x54F8, 0x54FA, 0x54FB, 0x54FC (dispatcher parameter block)
- 0x5DC7 (byte, near 0x5DD1-0x5DD9 region)

**Segment 0x834A discovered:**
- First reference to this segment (used in rank 61 dispatcher)
- Likely a data segment for specialized operations

**Patterns:**
- CS-segment still dominates (7 of 10 accessors)
- Dispatch stubs emerging (4 new dispatch pointers discovered)
- Block copy operation (first CS-segment → buffer copy)
- Sign extension (first use of CBW instruction)
- Conditional dispatch (flags-based execution)
