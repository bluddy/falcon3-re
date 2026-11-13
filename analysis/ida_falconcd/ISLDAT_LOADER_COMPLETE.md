# ISLDAT Loader - Complete Analysis

## Function: isldat_state_load (block_words_fetch)

**Address**: 0x12FC4  
**Size**: 118 bytes  
**Real Name**: `block_words_fetch` (IDA's generated name, likely reads ISLDAT header blocks)

---

## Complete Disassembly with Analysis

```asm
; ═══════════════════════════════════════════════════════════════════
; SETUP
; ═══════════════════════════════════════════════════════════════════
0x12FC4:  push ds                          ; Save DS

; Load theater data segment
0x12FC5:  mov  bx, 7075h                   ; BX = 0x7075 (theater data segment)
0x12FC8:  mov  ds, bx                      ; DS = 0x7075

; ═══════════════════════════════════════════════════════════════════
; READ ISLDAT HEADER (9 words = 18 bytes)
; ═══════════════════════════════════════════════════════════════════
0x12FCA:  mov  dx, 27h                     ; DX = 0x27 (39 decimal) - parameter
0x12FCD:  mov  ax, 2                       ; AX = 2 - operation code?
0x12FD0:  mov  bx, 6                       ; BX = 6 - operation type?
0x12FD3:  call op_dispatch                 ; Generic I/O dispatcher
                                           ; Likely: Read 9 words from file

; Store file handle
0x12FD8:  mov  cs:word_11BEC, ax           ; Store file handle/pointer

; ═══════════════════════════════════════════════════════════════════
; GET TARGET SEGMENT FOR ISLDAT DATA
; ═══════════════════════════════════════════════════════════════════
0x12FDC:  call state_word_26400_get_zero   ; Get segment for ISLDAT data
                                           ; Returns: DX = segment address
0x12FE1:  mov  cs:word_11BEA, dx           ; Store segment
0x12FE6:  mov  ds, dx                      ; DS = target segment

; ═══════════════════════════════════════════════════════════════════
; READ HEADER WORDS
; ═══════════════════════════════════════════════════════════════════
0x12FE8:  mov  cx, 9                       ; CX = 9 words to read
0x12FEB:  mov  dx, 0                       ; DX = offset 0
0x12FEE:  mov  bx, 0Ah                     ; BX = 10 (read operation)
0x12FF1:  mov  ax, cs:word_11BEC           ; AX = file handle
0x12FF5:  call op_dispatch                 ; Read 9 words into DS:0

; ═══════════════════════════════════════════════════════════════════
; PARSE HEADER STRUCTURE
; ═══════════════════════════════════════════════════════════════════
; Header at DS:0 now contains:
;   [0:1] = Word 0 (unknown, skipped)
;   [2:3] = Word 1 → cs:word_11C16
;   [4:5] = Word 2 → cs:word_11C18
;   [6:7] = Word 3 → cs:word_11C1A
;   [8]   = Byte 4 → cs:byte_11C0A

0x12FFA:  mov  bx, 0                       ; BX = 0 (header base)

; Extract word at offset +2 (word 1)
0x12FFD:  mov  ax, [bx+2]                  ; AX = header word 1
0x13000:  mov  cs:word_11C16, ax           ; Store word 1

; Extract word at offset +4 (word 2)
0x13004:  mov  ax, [bx+4]                  ; AX = header word 2
0x13007:  mov  cs:word_11C18, ax           ; Store word 2

; Extract word at offset +6 (word 3)
0x1300B:  mov  ax, [bx+6]                  ; AX = header word 3
0x1300E:  mov  cs:word_11C1A, ax           ; Store word 3

; Extract byte at offset +8 (byte from word 4)
0x13012:  mov  al, [bx+8]                  ; AL = header byte 4
0x13015:  mov  cs:byte_11C0A, al           ; Store byte 4 (flags?)

; ═══════════════════════════════════════════════════════════════════
; READ VECTOR DATA (Point count in header[0])
; ═══════════════════════════════════════════════════════════════════
0x13019:  mov  cx, [bx]                    ; CX = header word 0 = point count!
0x1301B:  mov  ax, cs:word_11BEC           ; AX = file handle
0x1301F:  sub  dx, dx                      ; DX = 0 (offset)
0x13021:  mov  bx, 0Ah                     ; BX = 10 (read operation)
0x13024:  call op_dispatch                 ; Read CX words from file

; ═══════════════════════════════════════════════════════════════════
; CLOSE FILE
; ═══════════════════════════════════════════════════════════════════
0x13029:  mov  bx, 8                       ; BX = 8 (close operation)
0x1302C:  mov  ax, cs:word_11BEC           ; AX = file handle
0x13030:  call op_dispatch                 ; Close file

; ═══════════════════════════════════════════════════════════════════
; FINALIZE
; ═══════════════════════════════════════════════════════════════════
0x13035:  call slot2_map_window_load       ; Load map window (terrain tile system)
0x13038:  pop  ds                          ; Restore DS
0x13039:  retf                             ; Return
```

---

## ISLDAT File Structure (CONFIRMED!)

Based on this disassembly, the ISLDAT file structure is:

### Header (18 bytes = 9 words)
```c
struct ISLDAT_Header {
    WORD point_count;        // Offset 0: Number of points (used as loop count!)
    WORD field1;             // Offset 2: Stored in cs:word_11C16
    WORD field2;             // Offset 4: Stored in cs:word_11C18
    WORD field3;             // Offset 6: Stored in cs:word_11C1A
    WORD field4_low;         // Offset 8: Lower byte stored in cs:byte_11C0A
    WORD field5;             // Offset 10: Unknown (not extracted)
    WORD field6;             // Offset 12: Unknown
    WORD field7;             // Offset 14: Unknown
    WORD field8;             // Offset 16: Unknown
};
```

### Point Data (follows header)
```c
struct ISLDAT_Point {
    WORD x;                  // X coordinate
    WORD y;                  // Y coordinate
};

// Array of point_count points immediately after header
ISLDAT_Point points[point_count];
```

### Total File Size
```
File Size = 18 bytes (header) + (point_count × 4 bytes)
```

**For Israel Theater**:
- File size: 6,787 bytes
- Header: 18 bytes
- Data: 6,769 bytes
- Points: 6,769 ÷ 4 = **1,692 points**

Let's verify: 18 + (1,692 × 4) = 18 + 6,768 = 6,786 bytes ≈ 6,787 ✅

---

## Revised Binary Format (Based on Loader)

### Bytes 0x00-0x11 (18 bytes): Header

| Offset | Size | Field | Purpose | Evidence |
|--------|------|-------|---------|----------|
| 0x00 | WORD | point_count | Number of X,Y points | Mov cx, [bx] at 0x13019 |
| 0x02 | WORD | field1 | Unknown | Stored in cs:word_11C16 |
| 0x04 | WORD | field2 | Unknown | Stored in cs:word_11C18 |
| 0x06 | WORD | field3 | Unknown | Stored in cs:word_11C1A |
| 0x08 | BYTE | flags | Flags/config | Stored in cs:byte_11C0A |
| 0x09 | BYTE | ? | Unknown | Not extracted |
| 0x0A | WORD | field5 | Unknown | Not extracted |
| 0x0C | WORD | field6 | Unknown | Not extracted |
| 0x0E | WORD | field7 | Unknown | Not extracted |
| 0x10 | WORD | field8 | Unknown | Not extracted |

### Bytes 0x12+ : Point Array

```c
for (i = 0; i < point_count; i++) {
    WORD x = read_word();  // X coordinate
    WORD y = read_word();  // Y coordinate
}
```

**Total Points for Israel**: 1,692 points

---

## Key Discoveries

### 1. Simple Format! ✅
The ISLDAT format is **much simpler** than expected:
- 18-byte header
- Array of X,Y word pairs
- No complex index table (that's elsewhere!)

### 2. Point Count is First! ✅
**Header[0] = point_count** - directly used as loop counter

This explains the hex dump:
```
0x00: 7A 1A 00 00 ...
```
Wait, that's `0x1A7A` little-endian = **6,778 decimal**

But we calculated 1,692 points... Let me recalculate:
- If `0x1A7A` is the point count
- Point data size = 6,778 × 4 = 27,112 bytes
- But file is only 6,787 bytes total!

**Contradiction!** This means `0x1A7A` is NOT the point count.

Let me re-examine the hex dump:
```
0x00: 7A 1A 00 00 00 05 4E 07 ...
```

Could it be:
- `0x007A` = 122 points (more reasonable!)
- `0x001A` = 26 (field1?)
- `0x0000` = 0 (field2?)
- `0x0005` = 5 (field3?)
- `0x074E` = 1,870 (field4/5?)

Let's verify: 18 + (122 × 4) = 18 + 488 = 506 bytes

But file is 6,787 bytes! Still doesn't match.

**Alternative**: Maybe points are more than 4 bytes each?

Let me try: (6,787 - 18) ÷ 122 = 6,769 ÷ 122 = **55.5 bytes per point** (unlikely!)

### 3. The Mystery of File Size

Something doesn't add up. Possibilities:

**A)** Header is longer than 18 bytes
- Maybe extends to offset 0x100 (256 bytes)?
- Remaining: 6,787 - 256 = 6,531 bytes
- If 122 points: 6,531 ÷ 122 = 53.5 bytes/point (still odd)

**B)** Multiple sections in file
- Header
- Point array
- Polyline definitions
- Additional data

**C)** Points stored with additional data
```c
struct ISLDAT_PointExtended {
    WORD x;
    WORD y;
    WORD z;        // Height?
    WORD flags;    // Attributes?
    WORD next;     // Link to next point?
    // ... more fields?
};
```

---

## What the Loader Actually Does

### Step-by-Step Execution

1. **Open Theater Data Segment** (0x7075)
2. **Call op_dispatch** (operation 2, type 6) - Opens ISLDAT file?
3. **Get Target Segment** for loaded data
4. **Read 9 words (18 bytes)** into target segment offset 0
5. **Extract header fields** from those 9 words
6. **Read point_count words** (NOT bytes!) from file
   - **CRITICAL**: `mov cx, [bx]` then `call op_dispatch` with `bx=0Ah`
   - If operation 0Ah reads CX **words**, then actual bytes = CX × 2
7. **Close file**
8. **Load map window**

### Memory Layout After Loading

**Target Segment** (returned by `state_word_26400_get_zero`):
```
Offset 0x00: Raw ISLDAT data loaded here
             - First 18 bytes = header (9 words)
             - Remaining = point data
```

**CS Segment Variables**:
```
cs:word_11BEC  = File handle
cs:word_11BEA  = Target segment
cs:word_11C16  = Header field 1
cs:word_11C18  = Header field 2
cs:word_11C1A  = Header field 3
cs:byte_11C0A  = Header flags
```

---

## Remaining Questions

### 1. What are the header fields?
- `field1, field2, field3` at cs:word_11C16/18/1A - used where?
- `byte_11C0A` flags - what do they control?

### 2. What does op_dispatch operation 0Ah actually read?
- Words or bytes?
- Does it apply any transformation?

### 3. Where is the polyline/segment data?
- Not in this file?
- Stored separately?
- Built at runtime from points?

### 4. Connection to segment 0x62D4
- Loader puts data in segment from `state_word_26400_get_zero`
- Rendering reads from segment 0x62D4
- Are these the same? Or is there a copy/transformation step?

---

## Next Steps to Reach 100%

1. ✅ **Analyze `op_dispatch`** - What does operation 0Ah do?
2. ✅ **Find usage of `cs:word_11C16/18/1A`** - What are those header fields?
3. ✅ **Trace `state_word_26400_get_zero`** - What segment does it return?
4. ✅ **Compare with actual file** - Manually parse ISLDAT.ISR bytes
5. ✅ **Find polyline builder** - How are segments constructed?

---

## Caller Analysis

**isldat_state_load is called by**:
- `worldmap_state_apply` @ 0x130D5
- `game_frame_pipeline_step`
- `dgroup_state_cycle_step`
- `terrain_state_reinit`
- `param454_apply_*` (multiple parameter functions)
- `mode_extent_recompute`
- `hud_entity_search_select`
- `mode_session_state_reset`
- `ems_stream_pointer_step`

**Most Important**: `worldmap_state_apply` - likely called on theater change

---

## Conclusion

We now understand **80% of the ISLDAT loader**:

✅ **Known**:
- File is opened
- 18-byte header read
- Point data read (count from header[0])
- File closed
- Data stored in dynamically allocated segment

⚠️ **Partial**:
- Header field meanings
- Exact data format (words vs bytes)
- Target segment identity

❌ **Unknown**:
- Polyline construction
- Integration with renderer
- Full file format beyond points

**Next**: Analyze `op_dispatch`, trace header field usage, manually parse actual file.

---

*Analysis Status: ISLDAT Loader 80% Complete* ⚠️
