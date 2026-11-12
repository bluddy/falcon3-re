# Level-0 Batch 6 Manual Decode (ranks 66-80)

## Overview
- **Batch size**: 15 functions
- **Call range**: 1,706 - 3,267 dyn_calls  
- **Size range**: 5-53B
- **Entering value cliff**: call frequencies dropped from 4.6K-9.2K (batch 5) to 1.7K-3.3K
- **All new functions**: 15 of 15 (no duplicates from batch 1)

---

## Rank 66: sub_25DEB (0x25DEB, 29B, dyn=3267, in=14)
```
Bytecode: 558bec56578b76068b7e088b5e0a8b460c8b560e2eff1e402a5f5e5dcb
```

**Decode:**
```asm
55                push bp
8b ec             mov bp, sp              ; stack frame setup
56                push si
57                push di
8b 76 06          mov si, [bp+6]          ; arg1 to SI
8b 7e 08          mov di, [bp+8]          ; arg2 to DI
8b 5e 0a          mov bx, [bp+10]         ; arg3 to BX
8b 46 0c          mov ax, [bp+12]         ; arg4 to AX
8b 56 0e          mov dx, [bp+14]         ; arg5 to DX
2e ff 1e 40 2a    call far cs:[0x2A40]    ; dispatch through CS pointer
5f                pop di
5e                pop si
5d                pop bp
cb                retf
```

**Analysis:**
- Stack frame + 5 arguments (10 bytes of args)
- Loads args to registers: SI, DI, BX, AX, DX
- Far indirect call through CS:[0x2A40] (dispatch table)
- Pattern: argument marshalling wrapper for dispatch

**Name:** `dispatch_5arg_via_cs_2a40`
**Category:** Complex dispatcher wrapper

---

## Rank 67: sub_256B2 (0x256B2, 6B, dyn=3227, in=4)
```
Bytecode: 2eff1ee429cb
```

**Decode:**
```asm
2e ff 1e e4 29    call far cs:[0x29E4]    ; indirect far call
cb                retf
```

**Analysis:**
- Dispatch stub through CS:[0x29E4]
- Near 0x29D0-0x29E8 region (finding 198)

**Name:** `stub_via_cs_29e4`
**Category:** Dispatch table stub

---

## Rank 68: sub_100B5 (0x100B5, 6B, dyn=2953, in=11)
```
Bytecode: 9adf616c1fcb
```

**Decode:**
```asm
9a df 61 6c 1f    call far 1F6C:61DF      ; direct far call
cb                retf
```

**Analysis:**
- Direct far call to 1F6C:61DF (overlay segment)
- This is the HIGH-FREQUENCY stub from batch 2 finding 187!
- Was named `stub_to_1f6c_61df` in batch 2

**Already named in batch 2, skip**

---

## Rank 69: sub_25E08 (0x25E08, 6B, dyn=2905, in=6)
```
Bytecode: 2eff1e402acb
```

**Decode:**
```asm
2e ff 1e 40 2a    call far cs:[0x2A40]    ; indirect far call
cb                retf
```

**Analysis:**
- Dispatch stub through CS:[0x2A40]
- Same pointer used by rank 66's 5-arg dispatcher

**Name:** `stub_via_cs_2a40`
**Category:** Dispatch table stub

---

## Rank 70: sub_2295E (0x2295E, 6B, dyn=2863, in=1)
```
Bytecode: 2eff1eec29cb
```

**Decode:**
```asm
2e ff 1e ec 29    call far cs:[0x29EC]    ; indirect far call
cb                retf
```

**Analysis:**
- Dispatch stub through CS:[0x29EC]
- Extends 0x29D0-0x29E8 region

**Name:** `stub_via_cs_29ec`
**Category:** Dispatch table stub

---

## Rank 71: sub_260BF (0x260BF, 53B, dyn=2792, in=2)
```
Bytecode: 1eb80e7b8ed8d1e3d1e3d1e3 8b87da3fa3d03f 8b87dc3fa3d23f 8b87de3fa3d43f 8b87e03fa3d63f d1e0d1e0d1e0d1e0 a3d83f 1fcb
```

**Decode:**
```asm
1e                push ds
b8 0e 7b          mov ax, 0x7B0E          ; segment 0x7B0E (view space)
8e d8             mov ds, ax
d1 e3             shl bx, 1               ; bx *= 8 (shift left 3 times)
d1 e3             shl bx, 1
d1 e3             shl bx, 1
8b 87 da 3f       mov ax, [bx+0x3FDA]     ; read 4 words from table
a3 d0 3f          mov [0x3FD0], ax        ; write to destination
8b 87 dc 3f       mov ax, [bx+0x3FDC]
a3 d2 3f          mov [0x3FD2], ax
8b 87 de 3f       mov ax, [bx+0x3FDE]
a3 d4 3f          mov [0x3FD4], ax
8b 87 e0 3f       mov ax, [bx+0x3FE0]
a3 d6 3f          mov [0x3FD6], ax
d1 e0             shl ax, 1               ; ax *= 16 (shift left 4 times)
d1 e0             shl ax, 1
d1 e0             shl ax, 1
d1 e0             shl ax, 1
a3 d8 3f          mov [0x3FD8], ax
1f                pop ds
cb                retf
```

**Analysis:**
- Segment 0x7B0E (view/projection space)
- Index BX scaled by 8, used to read 4-word record from table at DS:[BX+0x3FDA]
- Copy 4 words to DS:[0x3FD0-0x3FD6]
- Scale last word by 16, store to DS:[0x3FD8]
- Pattern: indexed table lookup with record copy + scaling

**Name:** `seg7b0e_table_3fda_copy_scale`
**Category:** Indexed table access with scaling

---

## Rank 72: sub_1FE54 (0x1FE54, 20B, dyn=2615, in=4)
```
Bytecode: 1eb80e7b8ed8d1e3d1e38b8752308b9754301fcb
```

**Decode:**
```asm
1e                push ds
b8 0e 7b          mov ax, 0x7B0E          ; segment 0x7B0E
8e d8             mov ds, ax
d1 e3             shl bx, 1               ; bx *= 4 (shift left 2 times)
d1 e3             shl bx, 1
8b 87 52 30       mov ax, [bx+0x3052]     ; read word from table
8b 97 54 30       mov dx, [bx+0x3054]     ; read second word
1f                pop ds
cb                retf
```

**Analysis:**
- Segment 0x7B0E table access
- Index BX scaled by 4 (dword entries)
- Read dword from DS:[BX+0x3052]
- Pattern: indexed dword table lookup

**Name:** `seg7b0e_table_3052_dword_get`
**Category:** Indexed dword table read

---

## Rank 73: sub_24CA4 (0x24CA4, 33B, dyn=2463, in=2)
```
Bytecode: 2ea1f8542ea300552ea0fc542ea2fd542ea0fa542ea2fe542ea0fb542ea2ff54cb
```

**Decode:**
```asm
2e a1 f8 54       mov ax, cs:[0x54F8]     ; read CS word
2e a3 00 55       mov cs:[0x5500], ax     ; write to CS:[0x5500]
2e a0 fc 54       mov al, cs:[0x54FC]     ; read CS byte (flags from finding 199)
2e a2 fd 54       mov cs:[0x54FD], al     ; write to CS:[0x5500]
2e a0 fa 54       mov al, cs:[0x54FA]     ; read CS byte
2e a2 fe 54       mov cs:[0x54FE], al     ; copy to CS:[0x54FE]
2e a0 fb 54       mov al, cs:[0x54FB]     ; read CS byte
2e a2 ff 54       mov cs:[0x54FF], al     ; copy to CS:[0x54FF]
cb                retf
```

**Analysis:**
- Copy CS:[0x54F8/FA/FB/FC] dispatcher params (finding 199) to CS:[0x5500/FD/FE/FF]
- Pattern: parameter block backup/save

**Name:** `cs_dispatcher_params_save_54f8_to_5500`
**Category:** CS-segment state backup

---

## Rank 74: sub_24D0D (0x24D0D, 24B, dyn=2440, in=4)
```
Bytecode: 2e883efc5481e3ff3fd1e32e8b87f0542ea3f854ba4a83cb
```

**Decode:**
```asm
2e 88 3e fc 54    mov cs:[0x54FC], bh     ; write BH to flags byte
81 e3 ff 3f       and bx, 0x3FFF          ; mask off top 2 bits
d1 e3             shl bx, 1               ; bx *= 2
2e 8b 87 f0 54    mov ax, cs:[bx+0x54F0]  ; indexed table read
2e a3 f8 54       mov cs:[0x54F8], ax     ; store to dispatcher param
ba 4a 83          mov dx, 0x834A          ; segment 0x834A (finding 199)
cb                retf
```

**Analysis:**
- Extract top 2 bits of BX to CS:[0x54FC] (flags byte from finding 199)
- Use lower 14 bits as index into CS:[0x54F0+] table
- Store result to CS:[0x54F8] (BP parameter from finding 199)
- Load segment 0x834A to DX
- Pattern: indexed parameter setup for dispatcher

**Name:** `cs_dispatcher_param_setup_bx_indexed`
**Category:** Dispatcher parameter initialization

---

## Rank 75: sub_24CC5 (0x24CC5, 33B, dyn=2433, in=3)
```
Bytecode: 2ea100552ea3f8542ea0fd542ea2fc542ea0fe542ea2fa542ea0ff542ea2fb54cb
```

**Decode:**
```asm
2e a1 00 55       mov ax, cs:[0x5500]     ; read saved params
2e a3 f8 54       mov cs:[0x54F8], ax     ; restore to dispatcher params
2e a0 fd 54       mov al, cs:[0x54FD]
2e a2 fc 54       mov cs:[0x54FC], al
2e a0 fe 54       mov al, cs:[0x54FE]
2e a2 fa 54       mov cs:[0x54FA], al
2e a0 ff 54       mov al, cs:[0x54FF]
2e a2 fb 54       mov cs:[0x54FB], al
cb                retf
```

**Analysis:**
- Restore CS:[0x54F8/FA/FB/FC] dispatcher params from CS:[0x5500/FD/FE/FF]
- Inverse of rank 73
- Pattern: parameter block restore

**Name:** `cs_dispatcher_params_restore_5500_to_54f8`
**Category:** CS-segment state restore

---

## Rank 76: sub_231D3 (0x231D3, 5B, dyn=2423, in=1)
```
Bytecode: 2ea16636cb
```

**Decode:**
```asm
2e a1 66 36       mov ax, cs:[0x3666]     ; read CS-segment word
cb                retf
```

**Analysis:**
- Simple CS-segment word read at 0x3666
- This was the CLAMPED setter target in batch 3 (finding 191)!
- Now we have the getter

**Name:** `cs_word_3666_get`
**Category:** CS-segment state accessor

---

## Rank 77: sub_263EA (0x263EA, 6B, dyn=2049, in=5)
```
Bytecode: 2eff1e002acb
```

**Decode:**
```asm
2e ff 1e 00 2a    call far cs:[0x2A00]    ; indirect far call
cb                retf
```

**Analysis:**
- Dispatch stub through CS:[0x2A00]
- Extends 0x2AA0+ dispatch region downward to 0x2A00

**Name:** `stub_via_cs_2a00`
**Category:** Dispatch table stub

---

## Rank 78: sub_25CCB (0x25CCB, 13B, dyn=1807, in=4)
```
Bytecode: 8b04d1e803d88b4402d1e803f8
```

**Decode:**
```asm
8b 04             mov ax, [si]            ; read word from [SI]
d1 e8             shr ax, 1               ; divide by 8 (shift right 3 times)
03 d8             add bx, ax              ; bx += (ax / 8)
8b 44 02          mov ax, [si+2]          ; read next word
d1 e8             shr ax, 1               ; divide by 8
03 f8             add di, ax              ; di += (ax / 8)
<missing retf>
```

**Analysis:**
- Read two words from [SI] and [SI+2]
- Divide both by 8 (shift right 3)
- Add first to BX, second to DI
- Pattern: coordinate scaling/transformation
- NOTE: Missing retf (might be 2B longer, or bytecode incomplete)

**Name:** `coord_pair_scale_div8_add`
**Category:** Coordinate transformation

---

## Rank 79: sub_22DFA (0x22DFA, 5B, dyn=1707, in=2)
```
Bytecode: 2ea36737cb
```

**Decode:**
```asm
2e a3 67 37       mov cs:[0x3767], ax     ; write AX to CS-segment
cb                retf
```

**Analysis:**
- Simple CS-segment word write at 0x3767
- New CS-segment state location

**Name:** `cs_word_3767_set`
**Category:** CS-segment state accessor

---

## Rank 80: sub_22DDC (0x22DDC, 10B, dyn=1706, in=3)
```
Bytecode: 2e891602372ea30437cb
```

**Decode:**
```asm
2e 89 16 02 37    mov cs:[0x3702], dx     ; write DX
2e a3 04 37       mov cs:[0x3704], ax     ; write AX
cb                retf
```

**Analysis:**
- Dual-word write: DX to CS:[0x3702], AX to CS:[0x3704]
- Part of 0x3662-0x3708 region (finding 191)

**Name:** `cs_dword_3702_set`
**Category:** CS-segment state accessor (dword write)

---

## Summary

**Named functions (14 new + 1 duplicate):**
1. dispatch_5arg_via_cs_2a40 (29B) - 5-argument marshalling wrapper
2. stub_via_cs_29e4 (6B) - dispatch stub
3. **sub_100B5 DUPLICATE** - already named `stub_to_1f6c_61df` in batch 2
4. stub_via_cs_2a40 (6B) - dispatch stub
5. stub_via_cs_29ec (6B) - dispatch stub
6. seg7b0e_table_3fda_copy_scale (53B) - indexed table with scaling
7. seg7b0e_table_3052_dword_get (20B) - indexed dword table
8. cs_dispatcher_params_save_54f8_to_5500 (33B) - param backup
9. cs_dispatcher_param_setup_bx_indexed (24B) - param init from table
10. cs_dispatcher_params_restore_5500_to_54f8 (33B) - param restore
11. cs_word_3666_get (5B) - CS-segment read (pairs with batch 3 setter)
12. stub_via_cs_2a00 (6B) - dispatch stub
13. coord_pair_scale_div8_add (13B) - coordinate transformation
14. cs_word_3767_set (5B) - CS-segment write
15. cs_dword_3702_set (10B) - CS-segment dword write

**New CS-segment ranges discovered:**
- 0x2A00 (dispatch pointer, extends 0x2AA0+ region downward)
- 0x2A40 (dispatch pointer, used by 5-arg wrapper)
- 0x29E4, 0x29EC (dispatch pointers, fill 0x29D0-0x29EC gap)
- 0x3702-0x3704 (dword, extends 0x3662-0x3708 region)
- 0x3767 (word, new isolated state)
- 0x5500-0x5503 (4 bytes: dispatcher param backup storage)
- 0x54F0+ (table: indexed dispatcher param source)
- 0x54FD-0x54FF (3 bytes: extends 0x54F8-0x54FC param block to 8 bytes)

**Segment 0x7B0E tables discovered:**
- 0x3052+ (dword table, indexed by BX*4)
- 0x3FDA+ (8-byte records, indexed by BX*8, 4 words per entry)

**Patterns:**
- **Dispatch infrastructure dominates**: 6 of 15 functions (40%) are dispatch stubs
- **Dispatcher parameter management**: 3 functions for save/restore/setup (ranks 73-75)
- **Segment 0x7B0E tables**: 2 indexed table access functions (view/projection data)
- **CS-segment accessors**: 4 functions (27%)
- **Coordinate transformation**: 1 function (scaling by 1/8)

**Value cliff confirmed:**
- Call frequencies: 1.7K-3.3K (down from 4.6K-9.2K in batch 5)
- Dropping into specialized/less-frequently-used operations
- Dispatcher infrastructure (save/restore) suggests nesting depth increasing
