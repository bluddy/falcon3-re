# Top 5 Unnamed Overlay Functions - Manual Decode

## Rank 1: sub_2BFC3 (30,515 calls, 8B)

```
Bytes: e8 f7 ef ea 01 0d f6 2c
```

**Disassembly:**
```assembly
0x2BFC3:  e8 f7 ef        call   sub_1AFBD     ; near call -4105 bytes
0x2BFC6:  ea 01 0d f6 2c  jmp    far 2CF6:0D01  ; far jump
```

**Analysis:**
- 8-byte trampoline: near call + far jump
- Calls sub_1AFBD (resident function at 0x1AFBD)
- Then far jumps to segment 0x2CF6, offset 0x0D01
- **Pattern**: Pre-call hook + overlay jump (common wrapper pattern)

**Likely purpose**: Overlay entry wrapper with state setup
**Confidence**: High (standard trampoline)

---

## Rank 2: sub_263F6 (18,079 calls, 122B)

```
Bytes: 2e ff 1e 10 2a cb 00 00 00 00 ff ff 00 00 00 00 00 00 00 00...
```

**Disassembly:**
```assembly
0x263F6:  2e ff 1e 10 2a     call   far dword ptr cs:[2A10h]  ; indirect far call
0x263FB:  cb                 retf
0x263FC:  00 00              [data: 116 bytes of structured data]
...
```

**Analysis:**
- Indirect far-call dispatcher (calls via CS:2A10)
- Followed by 116 bytes of embedded data (not code!)
- Data structure at 0x263FC:
  ```
  00 00 00 00   ; null dword
  ff ff 00 00   ; -1, 0
  00 00 00 00   ; nulls (repeated)
  ...
  6e 00 58 00   ; word pairs
  ...
  ```

**Data structure pattern**: Looks like a **jump table** or **dispatch table**
- Many null entries
- Word-sized entries (segment:offset pairs?)
- Total: ~30-40 entries

**Likely purpose**: Dispatch table for sub-menu or mode handlers
**Confidence**: Medium-high (dispatcher + embedded table)

---

## Rank 3: sub_2BEA1 (11,155 calls, 8B)

```
Bytes: e8 19 f1 ea 10 00 ad 4d
```

**Disassembly:**
```assembly
0x2BEA1:  e8 19 f1        call   sub_1AFBD     ; near call -3815 bytes
0x2BEA4:  ea 10 00 ad 4d  jmp    far 4DAD:0010  ; far jump
```

**Analysis:**
- Same pattern as rank 1!
- Calls sub_1AFBD (same resident function)
- Far jumps to segment 0x4DAD, offset 0x0010
- **Pattern**: Pre-call hook + overlay jump

**Likely purpose**: Overlay entry wrapper (different target than rank 1)
**Confidence**: High (identical pattern)

---

## Rank 4: sub_2295C (11,154 calls, 2B)

```
Bytes: 2b c0
```

**Disassembly:**
```assembly
0x2295C:  2b c0      sub    ax, ax    ; AX = 0
                    ; (implied retf from IDA function end)
```

**Wait, only 2 bytes but IDA thinks it's a function?**

Let me check if there's a hidden `retf` or if this is a fallthrough:
- `2b c0` = `sub ax, ax` (zero AX)
- Missing explicit `retf` (0xCB)

**Two possibilities:**
1. This is a **thunk fragment** that falls through to next function
2. IDA mis-classified this (should be part of larger function)
3. The bytes are incomplete (should check next 1-2 bytes)

**Need to check**: What's at 0x2295E (next 2 bytes)?

**Likely purpose**: Zero-return utility or thunk fragment
**Confidence**: LOW - needs verification

---

## Rank 5: sub_256A3 (10,222 calls, 15B)

```
Bytes: 1e bf 0e 7b 8e df bf 87 42 0e e8 2b b5 1f cb
```

**Disassembly:**
```assembly
0x256A3:  1e              push   ds
0x256A4:  bf 0e 7b        mov    di, 7B0Eh
0x256A7:  8e df           mov    ds, di        ; DS = 0x7B0E (DGROUP segment!)
0x256A9:  bf 87 42        mov    di, 4287h
0x256AC:  0e              push   cs
0x256AD:  e8 2b b5        call   near 0x10BDB  ; near call into resident
0x256B0:  1f              pop    ds
0x256B1:  cb              retf
```

**Analysis:**
- Saves DS
- Sets DS to 0x7B0E (this is the **DGROUP runtime segment**!)
- Sets DI to 0x4287 (offset into DGROUP)
- Calls resident function at 0x10BDB (which is sub_10BDB + offset)
- Restores DS
- Returns

**Pattern**: DGROUP accessor with specific offset
- 0x7B0E = DGROUP runtime (confirmed from VGRAPH analysis)
- 0x4287 = specific data structure offset
- sub_10BDB likely reads/writes [DS:DI]

**Likely purpose**: Access DGROUP data structure at offset 0x4287
**Confidence**: High (clear DGROUP access pattern)

---

## Summary of Top 5

| Rank | Function | Calls | Pattern | Purpose | Value |
|------|----------|-------|---------|---------|-------|
| 1 | sub_2BFC3 | 30,515 | Near call + far jump | Overlay wrapper | Medium |
| 2 | sub_263F6 | 18,079 | Dispatcher + table | Mode/menu dispatch | **HIGH** |
| 3 | sub_2BEA1 | 11,155 | Near call + far jump | Overlay wrapper | Medium |
| 4 | sub_2295C | 11,154 | `sub ax,ax` | Zero-return/thunk? | LOW |
| 5 | sub_256A3 | 10,222 | DGROUP accessor | Data structure access | **HIGH** |

## Recommendations

**Analyze first:**
1. **sub_263F6** (rank 2): Dispatcher with embedded table - reveals mode structure
2. **sub_256A3** (rank 5): DGROUP offset 0x4287 - what data structure?

**Then:**
3. **sub_2295C** (rank 4): Verify if valid function or misclassification
4. **sub_2BFC3** (rank 1): Trace through sub_1AFBD to understand wrapper mechanism
5. **sub_2BEA1** (rank 3): Same as #4

**Skip** the overlay wrappers for now (ranks 1, 3) - focus on the dispatcher and data accessor.
