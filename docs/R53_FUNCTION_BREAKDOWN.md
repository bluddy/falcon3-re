# R53 Mission Briefing - Function Breakdown

**Date**: 2026-11-16  
**Status**: Initial Analysis Complete  
**Purpose**: Document R53 module structure and data flow

---

## Executive Summary

R53 is the mission briefing coordinator overlay (32KB, 48 functions). Analysis reveals:

1. **No direct function calls detected** - Uses far calls to external code
2. **Three key structure sizes**:
   - **0x42 (66 bytes)** - PilotRecord
   - **0x82 (130 bytes)** - FlightRecord  
   - **0x1C (28 bytes)** - MenuElement
3. **Primary data segment**: R14_5E0B (2112 bytes) at 0x6E0B0-0x6E8F0
4. **Key data structure**: byte_6E1C9 with multiple offset accesses

---

## R53 Segment Overview

**Segment**: R53_569Fs  
**Address**: 0x1820B0 - 0x189F10  
**Size**: 32,352 bytes  
**Functions**: 48

### Function List (by size)

| Rank | Function | Size | Instructions | Role |
|------|----------|------|--------------|------|
| 1 | game_mode_r53_main_coordinator | 12,693 | 3,846 | Main briefing loop |
| 2 | r53_script_opcode_interpreter | 5,048 | 1,794 | Mission script interpreter |
| 3 | overlay_r52_handler | 2,026 | 612 | Calls R52/R57 overlays |
| 4 | r53_map_window_quota_step | 1,324 | 464 | Map rendering |
| 5 | r53_head_garbage_fragment | 994 | 310 | Unknown |
| 6 | r53_far_call_case_block | 922 | 335 | Dispatch handler |
| 7 | undoc_189375 | 738 | 266 | Unknown |
| 8 | r53_farobj_pipeline_body | 603 | 195 | Object pipeline |
| 9 | sub_1891D3 | 418 | 140 | Unknown |
| 10 | r53_record_walk_main | 354 | 137 | Record iterator |

**Note**: All 48 functions show 0 internal calls - they use far calls to external code.

---

## Main Coordinator Analysis

**Function**: `game_mode_r53_main_coordinator`  
**Address**: 0x1820B0  
**Size**: 12,693 bytes  
**Instructions**: 3,846

### Key Patterns Found

#### 1. PilotRecord Access (0x42 = 66 bytes)

Pattern appears 31 times in disassembly:
```assembly
mov     ax, word ptr es:byte_6E1C9+17h
mov     dx, 42h         ; PilotRecord size
imul    dx              ; Calculate offset
mov     dx, 6E1Eh       ; Mission data segment
mov     es, dx
les     bx, dword ptr es:byte_6E1C9+47h  ; Base pointer
add     bx, ax          ; Add offset
; Access pilot record fields
```

**Offsets accessed**:
- +0x17 (23): Loop counter or pilot index
- +0x47 (71): Pointer to pilot array
- +0x41 (65): Pilot status field (within record)

#### 2. FlightRecord Access (0x82 = 130 bytes)

Pattern appears once:
```assembly
mov     ax, es:word_79B62       ; Flight index
mov     dx, 82h                  ; FlightRecord size
imul    dx
mov     dx, 7894h               ; Data segment
mov     es, dx
les     bx, es:dword_79BEC      ; Flight array pointer
add     bx, ax
cmp     byte ptr es:[bx+15h], 1  ; Check flight field at +0x15
```

**Fields accessed**:
- +0x15 (21): Flight status or type field

#### 3. MenuElement Access (0x1C = 28 bytes)

Pattern appears twice:
```assembly
mov     ax, word ptr es:byte_6E1C9+17h
mov     dx, 1Ch         ; MenuElement size
imul    dx
mov     dx, 4FC2h       ; UI segment
mov     bx, ax
; Access menu element
```

---

## Data Segment Analysis

### R14_5E0B (Mission Data Segment)

**Address**: 0x6E0B0 - 0x6E8F0  
**Size**: 2,112 bytes

### Key Variables

#### byte_6E1C9 (Mission Control Block?)

**Address**: 0x6E1C9  
**Size**: ~179 bytes  
**Type**: Structure with multiple fields

**Known Offsets** (from R53 disassembly):

| Offset | Size | Type | Usage |
|--------|------|------|-------|
| +0x17 | word | uint16_t | Loop counter / index (accessed 31 times) |
| +0x1B | dword | pointer | Far pointer to data |
| +0x45 | word | uint16_t | Bit flags (masked with 7) |
| +0x47 | dword | pointer | Pointer to pilot array base |
| +0x49 | word | uint16_t | Unknown data |
| +0x4D | word | uint16_t | Bit flags (masked with 1) |

**Access Pattern**:
```assembly
mov     ax, 6E1Eh               ; Load segment
mov     es, ax
mov     ax, word ptr es:byte_6E1C9+17h   ; Access field at +0x17
```

**Initial Data** (first 16 bytes):
```
0x6E1C9: 4D 41 54 48 20 43 4F 50 52 4F 43 45 53 53 4F 52
         M  A  T  H     C  O  P  R  O  C  E  S  S  O  R
```

**Hypothesis**: This appears to be a mission state/context structure. The string "MATH COPROCESSOR" at the start might be:
1. Debug marker/signature
2. Part of a larger string table
3. Overlapped data from different purposes

---

## Segment References

### Segment 0x7894 (Main Data)

Referenced 62 times in main coordinator:
- `word_79B56`, `word_79B60`, `word_79B62` - Flight/mission state
- `word_79E86`, `word_79E32`, `word_79D1E` - UI state
- `dword_79E3A`, `dword_79BEC` - Structure array pointers

### Segment 0x6E1E (Mission Data - R14)

Referenced 140+ times via `byte_6E1C9` base structure.

### Segment 0x4FC2 (UI/Menu Data)

Referenced for menu elements and UI control.

---

## Comparisons Analysis

**Total comparisons with small values**: 67

### Value Distribution:

| Value | Count | Potential Meaning |
|-------|-------|-------------------|
| 0 | 37 | Null checks, MISSION_FIGHTER_SCRAMBLE |
| 1 | 10 | Boolean flags, MISSION_STRIKE_SCRAMBLE |
| 2 | 4 | MISSION_BOMBER_SCRAMBLE |
| 3 | 4 | MISSION_UMF_SCRAMBLE |
| 6 | 2 | MISSION_AREACAP |
| 7 | 1 | MISSION_ESCORT_TRANSPORT |
| 8 | 6 | MISSION_ESCORT_STRIKE, loop bounds |
| 9 | 2 | MISSION_ESCORT_BOMBERS |
| 11 | 1 | MISSION_GROUND_STRIKE |

**Analysis**: Most comparisons are likely null/boundary checks rather than enum comparisons.

---

## Related Segments

| Segment | Address Range | Size | Purpose |
|---------|---------------|------|---------|
| R14_5E0B | 0x6E0B0 - 0x6E8F0 | 2,112 | Mission data |
| R52_569Es | TBD | 4,560 | Pilot assignment |
| R53_569Fs | 0x1820B0 - 0x189F10 | 32,352 | Briefing coordinator |
| R57_5693s | TBD | ~8KB | Weapons loadout |

---

## Function Call Pattern

R53 functions use **far calls** which IDA doesn't resolve automatically. Examples from disassembly:

```assembly
0x1820b8  call    far ptr sub_2C351
0x1820be  call    undoc_133535
0x1820e7  call    sub_2C761          ; Overlay bridge trampoline
0x182101  call    far ptr menu_finalize_render
0x182107  call    ui_text_render_setup
0x182265  call    far ptr sub_1364BA
0x1822be  call    sub_13504F
```

**Key External Functions Called**:
- `sub_2C351` - Unknown
- `undoc_133535` - Unknown
- `sub_2C761` - **Overlay bridge trampoline** (14 calls total)
- `menu_finalize_render` - Render menu
- `ui_text_render_setup` - Setup text rendering
- `sub_1364BA` - Unknown
- `sub_13504F` - Unknown
- `string_copy_with_offset` - String utilities
- `undoc_11D941`, `undoc_12661D` - Unknown
- `input_poll_handler` - **Main keyboard input handler**
- `sub_12805C` - Unknown (called multiple times)

---

## Next Steps

### 1. Define Mission Control Block Structure

Based on byte_6E1C9 analysis:

```c
struct MissionControlBlock {
    // +0x00: String or signature?
    char signature[16];  // "MATH COPROCESSOR"?
    
    // +0x17: Counter/Index
    uint16_t current_index;
    
    // +0x1B: Far pointer
    uint32_t data_ptr_1;
    
    // ... (more fields to be discovered)
    
    // +0x45: Bit flags
    uint16_t flags_1;
    
    // +0x47: Pilot array pointer
    uint32_t pilot_array_ptr;
    
    // +0x49: Data field
    uint16_t field_49;
    
    // +0x4D: Bit flags
    uint16_t flags_2;
};
```

### 2. Disassemble Script Interpreter

`r53_script_opcode_interpreter` (5KB, 1794 instructions) likely:
- Executes mission scripts
- Controls briefing flow
- May contain opcode handlers

### 3. Trace External Function Calls

- Manually identify far call targets
- Document overlay bridge mechanism (sub_2C761)
- Map input handler integration

### 4. Analyze R14 Segment Completely

- Extract all variables from 0x6E0B0 - 0x6E8F0
- Identify structure boundaries
- Document inter-structure relationships

### 5. Cross-Reference with Mission Strings

Match extracted strings (272 items) to:
- UI rendering code
- Data structure fields
- Script interpreter operations

---

## Files Generated

| File | Description |
|------|-------------|
| `analysis/r53_functions.json` | All 48 functions with metadata |
| `analysis/r53_functions_summary.txt` | Human-readable function list |
| `analysis/r53_main_disasm.txt` | Full disassembly of main coordinator (3846 instructions) |
| `analysis/r53_main_analysis.json` | Analysis of comparisons and data refs |
| `analysis/segment_6e1e_analysis.json` | R14 segment variable dump |
| `analysis/all_segments.json` | Complete segment map |

---

## Key Insights

1. **R53 is a coordinator**, not a data owner - it orchestrates UI and calls other modules
2. **Data lives in R14 (0x6E1C9)** - Mission state structure with pilot/flight arrays
3. **Three key record types** - PilotRecord (66B), FlightRecord (130B), MenuElement (28B)
4. **Far call architecture** - Functions call external code via trampolines
5. **Script-driven** - Large interpreter suggests mission logic is script-based

---

## Conclusion

R53 module structure is now understood at high level. The mission data structures are partially mapped but need:
1. Complete field definitions for byte_6E1C9 structure
2. Mission type field location
3. Waypoint array location
4. Target/objective data location

**Recommended**: Focus on script interpreter and external function tracing to understand complete mission data flow.
