# Map Display - Initial Findings
*Falcon 3.0 Tactical Display Analysis - Session 1*

**Date:** 2024  
**Status:** Research in progress (Day 1)  
**Based on:** Mission Editor 99% completion

---

## Summary

Started investigation of Falcon 3.0's tactical map display system. Successfully disassembled 4 key display functions and identified initial patterns.

---

## Functions Disassembled

| Function | Address | Size | Segment | Status |
|----------|---------|------|---------|--------|
| waypoint_coordinate_processor | 0x1A2441 | 871 bytes | R63 | ✅ Disassembled |
| waypoint_display_processor | 0x1A0F10 | Unknown | R63 | ✅ Disassembled |
| waypoint_display_helper | 0x1A163A | Unknown | R63 | ✅ Disassembled |
| tactical_screen_coordinator | 0x12DB6A | Unknown | R29 | ✅ Disassembled |

---

## Initial Observations from waypoint_coordinate_processor

### Pattern: Waypoint Structure Access

**Confirmed:** Function accesses waypoints using 21-byte stride (0x15)

```asm
mov     ax, si                   ; SI = waypoint index
mov     dx, 15h                  ; Waypoint size (21 bytes)
imul    dx                       ; AX = waypoint_offset
mov     dx, 7894h
mov     es, dx
mov     dx, es:word_7A2F6        ; Get waypoint array segment
add     ax, es:word_7A2F4        ; Add base offset
mov     bx, ax
mov     es, dx
mov     byte ptr es:[bx+9], 0Ah  ; Write to waypoint field +0x09
```

**Fields accessed:**
- +0x09: Constant field (wrote 0x0A)
- +0x0A: Another byte field (wrote 0x00)
- +0x13h: Unknown field
- +0x14h: Another field (wrote 0x00)

### Data Structures Referenced

**Waypoint array pointer:**
- Segment @ word_7A2F6 (0x7894:0x7A2F6)
- Offset @ word_7A2F4 (0x7894:0x7A2F4)

**Other pointers:**
- word_7A2EA / word_7A2E8 (another far pointer pair)
- word_7A2F2 (file handle or buffer pointer?)

### Loop Structure

```c
// Pseudo-code reconstruction
for (var_2 = 0; var_2 < 4; var_2++) {          // 4 iterations (flights?)
    if (arg_0[var_2 * 0x12]) {                 // 0x12 = 18 byte stride
        for (di = 0; di < 8; di++) {           // 8 iterations (planes/waypoints?)
            for (var_4 = 0; ...; var_4++) {    // Inner loop
                // Process waypoint
                si++;  // waypoint counter
            }
        }
    }
}
```

**Structure sizes identified:**
- 0x12 (18 bytes) - Unknown structure (arg_0)
- 0x15 (21 bytes) - Waypoint structure ✅
- 0x06 (6 bytes) - Output structure (arg_4)

---

## Data Pointer Analysis

### New Pointers Found

| Address | Segment | Name | Likely Purpose |
|---------|---------|------|----------------|
| 0x7A2F6 | 0x7894 | word_7A2F6 | Waypoint array segment |
| 0x7A2F4 | 0x7894 | word_7A2F4 | Waypoint array offset |
| 0x7A2EA | 0x7894 | word_7A2EA | Data segment (high) |
| 0x7A2E8 | 0x7894 | word_7A2E8 | Data offset (low) |
| 0x7A2F2 | 0x7894 | word_7A2F2 | File/buffer handle |

### Hypothesis

**word_7A2F6:word_7A2F4** might be an ALTERNATIVE waypoint array pointer

**Compare to mission editor:**
- Mission editor uses: 0x4FC2:0x168
- This function uses: [word_7A2F6]:[word_7A2F4]

**Possibilities:**
1. Different waypoint array (display vs. edit)
2. Same array, different access method
3. Temporary display buffer

**Need to verify:** Are these the same pointer or different?

---

## String Operations

Function starts with string concatenation:

```asm
push    7894h
push    0F32h              ; Destination
...
push    word ptr es:aStores; ";-.`STORES"
call    string_concatenate
```

**Hypothesis:** Building UI label string (e.g., "STORES" for waypoint labels?)

---

## Far Call Dispatcher Usage

Multiple calls to `op_dispatch_far_entry`:

```asm
push    0
push    0
push    6
call    op_dispatch_far_entry    ; Dispatch code 6

push    0Ah
call    op_dispatch_far_entry    ; Dispatch code 0Ah (10)
```

**Dispatch codes seen:**
- 6: Unknown operation
- 0Ah (10): Unknown operation

**Hypothesis:** These are graphics/UI operations dispatched to overlay handlers

---

## Output Structure (arg_4)

Function writes 6-byte records to arg_4:

```c
struct OutputRecord {  // 6 bytes
    uint16_t field_00;     // +0x00: Set to (si + 0x11)
    uint16_t field_02;     // +0x02: Set to 3
    uint8_t  field_04;     // +0x04: Set to 0
    uint8_t  field_05;     // +0x05: Set to 0x81
};
```

**Hypothesis:** Display list or render commands
- field_00 = waypoint ID/index
- field_02 = render type (3 = waypoint?)
- field_05 = flags (0x81 = visible/enabled?)

---

## Next Steps

### 1. Identify Coordinate Conversion

**Status:** Not yet found in waypoint_coordinate_processor

**Need to find:**
- Where X, Y coordinates are read from waypoint
- Mathematical operations (scaling, offset)
- Screen coordinate output

**Action:** Search for waypoint +0x01 and +0x05 access (X and Y coords)

### 2. Analyze waypoint_display_processor

**Status:** Disassembled but not yet analyzed

**Expectation:** This function likely does the actual rendering

**Action:** Read disassembly and look for graphics calls

### 3. Search for Graphics Primitives

**Create script to find:**
- INT 10h (BIOS video calls)
- 0xA000 segment (VGA memory access)
- Pixel plot patterns
- Line drawing code

### 4. Understand Dispatcher Codes

**Question:** What do codes 6 and 0xA (10) do?

**Action:**
- Search for op_dispatch_far_entry implementation
- Build dispatcher code table
- Match to graphics operations

### 5. Verify Waypoint Array Pointer

**Question:** Is word_7A2F6:word_7A2F4 the same as 0x4FC2:0x168?

**Action:**
- Check IDA cross-references
- Compare values in memory
- Understand why two different access methods

---

## Hypotheses to Test

### Hypothesis 1: Display List Architecture

**Theory:** Function builds display list, separate renderer draws it

**Evidence:**
- Writes 6-byte output records
- No obvious pixel/graphics operations
- Multiple waypoints processed in loop

**Test:** Find function that reads arg_4 output

### Hypothesis 2: Two-Pass Rendering

**Theory:** First pass = coordinate conversion, second pass = rendering

**Evidence:**
- waypoint_coordinate_processor (conversion)
- waypoint_display_processor (rendering)
- Names suggest separation of concerns

**Test:** Trace function call sequence

### Hypothesis 3: Overlay Dispatch for Graphics

**Theory:** Graphics operations called through dispatcher to save memory

**Evidence:**
- Multiple op_dispatch_far_entry calls
- Different dispatch codes (6, 0xA)
- Complex overlay system

**Test:** Reverse dispatcher implementation

---

## Comparison to Mission Editor

### Similarities

✅ Both access 21-byte waypoint structures  
✅ Both use waypoint index × 21 calculation  
✅ Both iterate over multiple waypoints  
✅ Both reference data segment 0x7894

### Differences

❓ Different waypoint array pointer (word_7A2F4:7A2F6 vs. 0x4FC2:0x168)  
❓ Display code uses 18-byte input structure  
❓ Display code outputs 6-byte records  
❓ Display code calls dispatcher, editor doesn't

---

## Open Questions

1. **Where is actual coordinate conversion?**
   - Not obvious in waypoint_coordinate_processor
   - Maybe in waypoint_display_processor?
   - Or called through dispatcher?

2. **What is the 18-byte structure?**
   - Input to waypoint_coordinate_processor
   - Stride of 0x12 bytes
   - Contains waypoint references

3. **What do dispatch codes mean?**
   - Code 6 = ?
   - Code 0xA (10) = ?

4. **How is screen resolution handled?**
   - 320×200? 640×480?
   - Where are dimensions stored?

5. **Is there a viewport structure?**
   - Zoom level?
   - Pan offset?
   - View center?

---

## Tools/Scripts Created

1. **disasm_map_display_functions.py**
   - Disassembles 4 display functions
   - Finds function calls
   - Generates annotated listings

**Output:**
- waypoint_coordinate_processor_disasm.txt (871 bytes, analyzed)
- waypoint_display_processor_disasm.txt (not yet analyzed)
- waypoint_display_helper_disasm.txt (not yet analyzed)
- tactical_screen_coordinator_disasm.txt (not yet analyzed)

---

## Session 1 Conclusion

**Progress:** 20% of map display analysis

**Achievements:**
- ✅ 4 functions disassembled
- ✅ Waypoint structure access confirmed
- ✅ New data pointers identified
- ✅ Output structure format documented
- ✅ Multiple hypotheses formed

**Blockers:**
- ❌ Coordinate conversion not yet found
- ❌ Graphics primitives not identified
- ❌ Dispatcher codes not decoded

**Next session priority:**
1. Find coordinate transformation math
2. Analyze waypoint_display_processor
3. Search for graphics primitives
4. Decode dispatcher operations

**Estimated remaining effort:** 8-10 hours for 80% understanding

---

*Map Display Research - Session 1*  
*Building on Mission Editor 99% foundation*  
*Status: Initial reconnaissance complete, diving deeper next*
