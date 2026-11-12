# Top 10 Level-0 Functions - Manual Decode

## Tiny Functions (2-5 bytes) - High-Frequency Accessors

### 1. sub_12890 (0x12890, 5B, dyn=11513, in=1)
```
Bytecode: 2e a0 e8 00 cb
Disasm:   seg cs ; mov al, [0x00E8] ; retf
```
**Purpose:** Read single byte from CS:[0x00E8], return in AL  
**Caller:** r05_e19 (overlay record 5, entry 19)  
**Name:** `cs_byte_00e8_get` or `flight_state_byte_e8_get`

### 2. sub_2295C (0x2295C, 2B, dyn=11154, in=6)
```
Bytecode: 2b c0
Disasm:   sub ax, ax ; (implicit retf)
```
**Purpose:** Zero AX register (return 0)  
**Callers:** r54_e169, sub_18B071, sub_18B489, sub_2F6D0, sub_31138, r46_e32  
**Name:** `zero_ax` or `return_zero`

### 3. sub_22436 (0x22436, 5B, dyn=9698, in=5)
```
Bytecode: 2e a1 76 2b cb
Disasm:   seg cs ; mov ax, [0x2B76] ; retf
```
**Purpose:** Read word from CS:[0x2B76], return in AX  
**Callers:** sub_2FC79, sub_307A5, sub_309A7, sub_30D5F, sub_34C31  
**Name:** `cs_word_2b76_get`

### 4. sub_2243B (0x2243B, 5B, dyn=9698, in=5)
```
Bytecode: 2e a1 78 2b cb
Disasm:   seg cs ; mov ax, [0x2B78] ; retf
```
**Purpose:** Read word from CS:[0x2B78], return in AX (consecutive to 2B76)  
**Callers:** sub_2FC79, sub_307A5, sub_309A7, sub_30D5F, sub_34C31  
**Name:** `cs_word_2b78_get`

### 5. sub_2284B (0x2284B, 5B, dyn=9189, in=1)
```
Bytecode: 2e a3 82 2b cb
Disasm:   seg cs ; mov [0x2B82], ax ; retf
```
**Purpose:** Write AX to CS:[0x2B82]  
**Caller:** sub_31022  
**Name:** `cs_word_2b82_set`

### 6. sub_22846 (0x22846, 5B, dyn=8066, in=1)
```
Bytecode: 2e a3 80 2b cb
Disasm:   seg cs ; mov [0x2B80], ax ; retf
```
**Purpose:** Write AX to CS:[0x2B80]  
**Caller:** sub_31022  
**Name:** `cs_word_2b80_set`

### 7. sub_22850 (0x22850, 5B, dyn=7528, in=1)
```
Bytecode: 2e a3 84 2b cb
Disasm:   seg cs ; mov [0x2B84], ax ; retf
```
**Purpose:** Write AX to CS:[0x2B84]  
**Caller:** sub_31022  
**Name:** `cs_word_2b84_set`

## Pattern: CS-Segment State Block (0x2B76 - 0x2B84+)

These 7 tiny functions are accessors for a **CODE-segment state block** starting at CS:[0x2B76]:

| Offset | Access | Function | Size | Purpose |
|--------|--------|----------|------|---------|
| 0x2B76 | GET | sub_22436 | word | Read state variable 1 |
| 0x2B78 | GET | sub_2243B | word | Read state variable 2 |
| 0x2B80 | SET | sub_22846 | word | Write state variable 3 |
| 0x2B82 | SET | sub_2284B | word | Write state variable 4 |
| 0x2B84 | SET | sub_22850 | word | Write state variable 5 |

**Analysis:** Code-segment storage was common in DOS overlays (data persists across overlay swaps). The 2B76-2B84 range is likely flight state (view angles, control inputs, or physics parameters).

---

## Medium Functions (88-122 bytes)

### 8. sub_263F6 (0x263F6, 122B, dyn=18079, in=8)
**Purpose:** 122-byte data structure/table (starts with `2e ff 1e 10 2a cb` = far call through pointer)  
**Callers:** sub_34C31, sub_35BCE, sub_3718D, sub_378A9, sub_3A3D6, sub_3A79C, sub_3AADF, sub_3AE31  
**Analysis:** Likely a **dispatch table** or **vtable** for polymorphic objects. First 6 bytes are executable, rest is data pointers (pairs like `0e 90 6c 1f`, `b4 90 6c 1f` = segment:offset far pointers).  
**Name:** `farobj_dispatch_table` or `entity_vtable`

### 9. sub_230D8 (0x230D8, 92B, dyn=8914, in=2)
**Purpose:** Complex bit manipulation and table lookup  
**Callers:** sub_4486B, sub_6D29F  
**Pattern:**
- Mask with 0x3FFF (14-bit index)
- Shift right by 3 (divide by 8)
- Test bits 0x1000, 0x2000 (flags)
- Conditional table lookups from ES:[BX+offset]
- Negate results conditionally

**Analysis:** **Trigonometric or fixed-point math lookup** (sin/cos table indexed by angle, with quadrant flags).  
**Name:** `trig_lookup_table` or `fixed_sin_cos`

### 10. sub_23134 (0x23134, 88B, dyn=7994, in=1)
**Purpose:** Similar to sub_230D8 (bit masking, shifts, table lookups)  
**Caller:** sub_399F2  
**Pattern:** Nearly identical to sub_230D8 but with different offsets (0x04, 0x08 instead of 0x02, 0x06).  
**Analysis:** Paired lookup function (e.g., sin vs cos, or X vs Y component).  
**Name:** `trig_lookup_alt` or `fixed_sin_cos_y`

---

## Findings Summary

**Finding 180: CS-Segment State Block (0x2B76-0x2B84+)**
- 5+ word variables stored in CODE segment (overlay-persistent)
- 7 tiny accessor functions (sub_22436/2243B/2284B/22846/22850)
- High call frequency (7K-10K calls each)
- Likely flight physics state or view parameters

**Finding 181: Far-Object Dispatch Table (0x263F6)**
- 122-byte structure with executable header + 14+ far pointer pairs
- Called by 8 high-level object managers
- 18K dynamic calls (hottest Level-0 function)
- Polymorphic dispatch for entity types

**Finding 182: Trigonometric Lookup Pair (sub_230D8 / sub_23134)**
- Fixed-point sin/cos tables with 14-bit angle indices
- Quadrant flags (0x1000, 0x2000) for sign/symmetry
- 88-92 byte functions (similar structure, different offsets)
- 8K-9K calls each

**Naming Batch 1 (10 functions):**
1. sub_263F6 → farobj_dispatch_table
2. sub_12890 → cs_byte_00e8_get
3. sub_2295C → zero_ax
4. sub_22436 → cs_word_2b76_get
5. sub_2243B → cs_word_2b78_get
6. sub_2284B → cs_word_2b82_set
7. sub_230D8 → trig_lookup_sin
8. sub_22846 → cs_word_2b80_set
9. sub_23134 → trig_lookup_cos
10. sub_22850 → cs_word_2b84_set
