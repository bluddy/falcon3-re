# R53 Mission Briefing - Data Flow Analysis

**Date**: 2026-11-16  
**Status**: Deep Analysis in Progress  
**Purpose**: Trace mission data structures through R53 code

---

## Key Discovery: byte_6E1C9 is a String Table, Not a Structure!

Initial hypothesis was **wrong**. The analysis reveals:

**byte_6E1C9** at 0x6E1C9 contains:
```
"MATH COPROCESSOR" + "IS REQUIRED !" + "WRONG VERSION !" + 
"NOT ENOUGH EMS !" + "OVERWRITE? Y/N" + ... (error messages)
```

This is a **string table** for UI messages, not mission data.

---

## Correct Data Flow Pattern

### 1. Primary Data Pointer: dword_79E3A

**Location**: Segment 0x7894  
**Usage**: Referenced 14 times in script interpreter, 17 times in main coordinator  
**Type**: Far pointer (segment:offset)

**Pattern**:
```assembly
mov     ax, 7894h               ; Load data segment
mov     es, ax
mov     ax, word ptr es:dword_79E3A+2   ; Get segment
mov     dx, word ptr es:dword_79E3A     ; Get offset
add     dx, 3Dh                 ; Add 0x3D offset
; Now dx:ax points to pilot array base
```

**What dword_79E3A Points To**:
- +0x00 to +0x3C (60 bytes): Unknown header/metadata
- +0x3D onwards: **Pilot array** (30 pilots × 66 bytes = 1980 bytes)

### 2. Pilot Record Access Pattern

**Size**: 0x42 (66 bytes) - confirmed PilotRecord structure

**Fields Accessed** (from script interpreter):
- +0x22 (34): Skill field 1
- +0x23 (35): Skill field 2  
- +0x24 (36): Dogfighting skill
- +0x25 (37): Bombing skill
- +0x30 (48): Status/state field
- +0x31 (49): Data field
- +0x41 (65): Pilot type/status (checked for 0xFF = empty slot)

**Loop Pattern** (from script interpreter):
```assembly
xor     di, di                  ; di = pilot index (0)
jmp     loc_186CE0              ; Jump to loop condition

loc_186B3A:                     ; Loop body
mov     ax, di                  ; Load pilot index
mov     dx, 42h                 ; PilotRecord size (66 bytes)
imul    dx                      ; Calculate offset
les     bx, [bp+var_44]         ; Load pilot array base pointer
add     bx, ax                  ; Add offset
cmp     byte ptr es:[bx+41h], 0FFh  ; Check if pilot slot empty
jnz     process_pilot           ; If not empty, process
jmp     next_pilot

process_pilot:
; Access pilot fields at +0x22, +0x23, +0x24, +0x25, +0x30, +0x31, +0x41
; ... (processing code)

next_pilot:
inc     di                      ; Next pilot
loc_186CE0:                     ; Loop condition
cmp     di, 8                   ; Check if processed 8 pilots
jl      loc_186B3A              ; Loop back
```

**Note**: Loop only processes **8 pilots**, not all 30!

### 3. Flight Record Access Pattern

**Size**: 0x82 (130 bytes) - confirmed FlightRecord structure

**Access Pattern** (from main coordinator):
```assembly
mov     ax, 7894h
mov     es, ax
mov     ax, es:word_79B62       ; Get flight index
mov     dx, 82h                 ; FlightRecord size (130 bytes)
imul    dx                      ; Calculate offset
mov     dx, 7894h
mov     es, dx
les     bx, es:dword_79BEC      ; Load flight array base pointer
add     bx, ax                  ; Add offset
cmp     byte ptr es:[bx+15h], 1 ; Check flight field at +0x15 (21)
```

**Fields Accessed**:
- +0x15 (21): Flight status/type (compared with 1)

**Note**: Only **one flight** checked in this section - likely current/active flight.

---

## Segment 0x7894 (Main Data Segment)

This segment contains **pointers** to actual mission data, not the data itself.

### Key Variables:

| Variable | Type | Purpose |
|----------|------|---------|
| dword_79E3A | far pointer | Points to pilot array (base + 0x3D) |
| dword_79BEC | far pointer | Points to flight array |
| word_79B56 | word | Mode/state flag (compared with 1) |
| word_79B62 | word | Current flight index |
| word_79B60 | word | UI state (set to 0xFFFF or 0x28) |
| word_79E86 | word | State flag (set to 1) |
| word_79B5A | word | State flag (set to 1) |
| word_79D6A | word | State flag (set to 0) |
| word_79E32 | word | State flag (checked for 0) |
| word_79D1E | word | UI/string state |
| word_79E9C | word | State (set to 2) |

### Data Flow:

```
Segment 0x7894 (Pointers)
    ├─> dword_79E3A ──> [External Memory]
    │                    ├─ +0x00-0x3C: Header (60 bytes)
    │                    └─ +0x3D: Pilot Array (30 × 66 = 1980 bytes)
    │
    ├─> dword_79BEC ──> [External Memory]
    │                    └─ Flight Array (N × 130 bytes)
    │
    └─> word_79B62: Current flight index
```

---

## R14 Segment (R14_5E0B) Analysis

**Address**: 0x6E0B0 - 0x6E8F0  
**Size**: 2,112 bytes

### Contents:

1. **0x6E0B0 - 0x6E1C8**: Zeros and small data (tables?)
2. **0x6E1C9 onwards**: String table (error messages, UI strings)
3. **Rest**: More strings, VCR control data, script bytecode?

### String Table at byte_6E1C9:

```
0x6E1C9: "MATH COPROCESSOR"
0x6E1D9: "IS REQUIRED !"
0x6E1E6: "WRONG VERSION !"
0x6E1F6: "NOT ENOUGH EMS !"
0x6E206: "OVERWRITE? Y/N"
0x6E215: "ARE YOU SURE? Y/N"
0x6E227: "ENTER FILENAME"
0x6E236: "SAVE FAILED !!!"
0x6E245: "LOAD FAILED !!!"
0x6E254: "CANCEL"
0x6E25B: "ERASE AVTR"
0x6E266: "DELETE"
0x6E26D: "LOAD"
0x6E272: "SAVE"
0x6E277: "AVTR  V1.5"
0x6E282: "LOADING ..."
0x6E28E: "SAVING ..."
0x6E298: "VCRi"
0x6E2D0: "VCR.MIS"
0x6E2E0: "global.amo"
0x6E2EB: "local.amo"
0x6E2F5: "harpoon.dat"
```

**Conclusion**: R14 is an **overlay data segment** for R53, containing:
- String tables for UI
- Script bytecode (likely after strings)
- Configuration data

**Mission data lives elsewhere** - likely in main memory or different segments.

---

## Mission Data Location Hypothesis

Based on the analysis:

1. **Mission data is NOT in R53 or R14** - these are UI/script code
2. **Mission data is pointed to by dword_79E3A and dword_79BEC** in segment 0x7894
3. **These pointers are loaded at runtime** - data location varies
4. **Likely sources**:
   - Loaded from .CAM campaign files
   - Loaded from .MSN mission files
   - Generated dynamically in main memory

---

## Next Steps to Find Mission Structures

### 1. Trace dword_79E3A Initialization

Find where `dword_79E3A` is set - this reveals mission data source.

**Search for**:
```assembly
mov     word ptr es:dword_79E3A, offset
mov     word ptr es:dword_79E3A+2, segment
```

### 2. Analyze Campaign/Mission File Loaders

Look for functions that:
- Open .CAM or .MSN files
- Allocate memory for mission data
- Set up dword_79E3A pointer

### 3. Examine the 60-byte Header

The header at `[dword_79E3A + 0x00]` (before pilots at +0x3D) likely contains:
- Mission type
- Target info
- Waypoint count
- Flight count
- Pointers to flight/waypoint arrays

### 4. Trace dword_79BEC (Flight Array)

Similar to pilots, find where flight array is loaded and what structure it uses.

### 5. Check Segment 0x6E1E References

The main coordinator accesses segment 0x6E1E frequently, but we know byte_6E1C9 is strings. Check **other** variables in that segment range (0x6E0B0 - 0x6E1C8).

---

## Structure Definitions (Updated)

### PilotRecord (66 bytes, 0x42)

```c
struct PilotRecord {
    // +0x00-0x21: Unknown fields (status, name, callsign, etc.)
    uint8_t skill_field_1;      // +0x22 (34)
    uint8_t skill_field_2;      // +0x23 (35)
    uint8_t dogfighting_skill;  // +0x24 (36)
    uint8_t bombing_skill;      // +0x25 (37)
    // +0x26-0x2F: Unknown fields
    uint8_t status_state;       // +0x30 (48)
    uint8_t data_field;         // +0x31 (49)
    // +0x32-0x40: Unknown fields
    uint8_t pilot_type_status;  // +0x41 (65) - 0xFF = empty slot
};
```

### FlightRecord (130 bytes, 0x82)

```c
struct FlightRecord {
    // +0x00-0x14: Unknown fields
    uint8_t flight_status_type; // +0x15 (21)
    // +0x16-0x81: Unknown fields (likely loadouts, waypoints)
};
```

### Mission Context Block (Hypothesis)

Pointed to by `dword_79E3A`:

```c
struct MissionContext {
    uint8_t header[60];         // +0x00-0x3B (0x3C bytes)
                                 // Likely contains:
                                 // - Mission type
                                 // - Target coords
                                 // - Waypoint count
                                 // - Flight count
    
    PilotRecord pilots[30];     // +0x3D: 30 pilots × 66 bytes
    // Followed by other data?
};
```

---

## Files Generated

| File | Description |
|------|-------------|
| `analysis/r53_script_interpreter_disasm.txt` | Full interpreter disassembly (1794 instructions) |
| `analysis/r53_script_interpreter_analysis.json` | Interpreter analysis (opcodes, data refs) |
| `analysis/r14_mission_data_dump.txt` | Complete R14 segment hex dump |
| `analysis/r14_mission_data_analysis.json` | R14 segment analysis |

---

## Key Insights

1. **R53 is pure UI/coordinator** - no mission data stored here
2. **R14 is string tables + scripts** - not mission data
3. **Segment 0x7894 has pointers** to actual mission data
4. **Pilot array confirmed**: 30 pilots × 66 bytes starting at `[dword_79E3A + 0x3D]`
5. **Flight array confirmed**: N flights × 130 bytes at `[dword_79BEC]`
6. **Script interpreter loops 8 pilots** - likely current flight members
7. **Mission data loaded dynamically** - not compiled into executable

**Critical Finding**: To find MissionRecord structure, we need to:
1. Find where dword_79E3A is initialized
2. Analyze the 60-byte header before pilots
3. Find mission file loaders (.CAM, .MSN, .TAC)

---

## Revised Architecture

```
Campaign/Mission Files (.CAM, .MSN, .TAC)
            ↓
    [File Loader Functions]
            ↓
    Allocate Memory & Load Data
            ↓
    Set Pointers in Segment 0x7894:
        - dword_79E3A → Mission Context
        - dword_79BEC → Flight Array
            ↓
    R53 Mission Briefing Overlay
        - Reads via pointers
        - Displays UI
        - Calls R52 (pilots), R57 (loadout)
            ↓
    Mission Execution
```

The mission data structures exist, but they're **in dynamically loaded memory**, not in fixed segments. We need to find the file loaders next.
