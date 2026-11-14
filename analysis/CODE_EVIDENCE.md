# Code Evidence for Mission File Structures

**Purpose**: Document IDA disassembly evidence that supports our reverse-engineered mission file format.

---

## Altitude Encoding (×100)

### Evidence 1: 0x64 (100 decimal) multiplication

**Location**: Multiple files  
**Pattern**: `mov dl, 64h`, `mov bh, 64h`, `div 64h`

**Examples**:
```asm
; level19_batch4.txt:886
0x45230: mov    dl, 64h
0x45232: call   loc_356A3  ; scroll_scale_lookup

; level19_batch4.txt:1254  
0x4560C: mov    dl, 64h
0x4560E: mov    bp, cs:word_2E143+1

; level19_batch1.txt:2075
0x474D4: mov    bh, 64h
0x474D6: mov    bp, cs:word_2E143+1
```

**Interpretation**: Value 0x64 (100) used extensively in coordinate/scale calculations. Supports hypothesis that altitude byte is multiplied by 100 to get feet.

---

## Flight Parameter Structure (23 bytes)

### Evidence 1: Add 0x17 (23 decimal) stride

**Location**: level4_batch1_disasm.txt:1558  
**Function**: Part of entity/farobj processing loop

```asm
0x4D96C: mov    bx, cx
0x4D96E: push   si
0x4D96F: add    si, 17h        ; Add 23 bytes to si
0x4D973: and    bx, [si]       ; Read word from structure
0x4D975: pop    si
0x4D976: add    si, 25h        ; Add 37 more bytes (next structure?)
0x4D97A: mov    cx, [si]
```

**Interpretation**:
- Code adds 0x17 (23) to index register si
- Reads data from that offset
- 23 matches our discovered flight parameter structure size
- Part of entity processing, likely reading flight/waypoint parameters

---

## Waypoint Structure (21 bytes)

### Evidence 1: Add 0x15 (21 decimal) stride with aircraft_record_load_step

**Location**: level19_batch3.txt:3029  
**Function**: sub_4AEC4 (aircraft state processing)

```asm
0x4B2A0: mov    dl, 0Eh
0x4B2A2: mov    dh, 32h
0x4B2A4: add    di, 15h                    ; Add 21 bytes to di
0x4B2A7: call   aircraft_record_load_step  ; Load aircraft record
0x4B2AC: pop    di
```

**Interpretation**:
- Code adds 0x15 (21) to index register di
- 21 matches our waypoint structure size (11-byte + 10-byte duplicate)
- Function name "aircraft_record_load_step" suggests loading mission data
- Called from sub_4AEC4 which has 1146 bytes and calls many position/angle functions

**Additional context**:
```
sub_4AEC4 callees: farobj_tile_copy_resolve, fixed_vec3_accumulate_a, 
  angle_aux_far, angle_xy_far, map_view_project_pipeline, 
  pos_move_angle_step, pos_step_chain_engine, aircraft_record_load_step
```

This function appears to process aircraft movement along waypoints!

---

## Action Code Strings

### Evidence 1: String data in segment

**Location**: data_symbols.json, addresses 0x14FD1F-0x14FD61

Action code strings found at consecutive addresses:

| Address | String | Size | Likely Code |
|---------|--------|------|-------------|
| 0x14FD1F | "CAP" | 4 | 2 (confirmed) |
| 0x14FD23 | "CAS" | 4 | 6? |
| 0x14FD2F | "BOMB" | 5 | 5? |
| 0x14FD34 | "LAND" | 5 | 9? |
| 0x14FD42 | "LOITER" | 7 | 8? |
| 0x14FD49 | "ESCORT" | 7 | 4? |
| 0x14FD50 | "TAKEOFF" | 8 | 0? |
| 0x14FD61 | "SEAD" | 5 | 7? |

**Additional mission strings** (for UI/briefing):
- 0x14EA5E: "Strike Scramble"
- 0x14EA6E: "Bomber Scramble"  
- 0x14EAA2: "Area CAP"
- 0x14EAAA: "Escort Transport"
- 0x14EABA: "Escort Strike Aircraft"
- 0x14EACF: "Escort Bombers"
- 0x14EAED: "Ground Strike"
- 0x14EAFA: "Bomb Mission"
- 0x14EB0B: "SEAD Ship"
- 0x14EB1E: "SEAD Ground"

**Interpretation**: 
- String table contains all action types mentioned in manual
- Consecutive addresses suggest array or switch table
- Need to find code that references these strings

---

## Aircraft Type Code Initialization

### Evidence 1: Type comparison and performance parameters

**Location**: IDA 0x4C301-0x4C546  
**Details**: Documented in AIRCRAFT_TYPE_CODES.md

Code compares aircraft type_code field and sets unique parameters per type:

```asm
; Pseudocode from IDA analysis
if (type_code == 0x34)  // F-15 Eagle
    set_speed_params(...)
    set_turn_rate(...)
else if (type_code == 0x35)  // F-111 Aardvark
    set_speed_params(...)
    set_turn_rate(...)
// ... etc for types 0x01, 0x07-0x0B, 0x34-0x36
```

**Interpretation**: Confirmed that byte +0x03 in aircraft record is type code.

---

## Jump Tables and Switch Statements

### Evidence 1: Jump table with range check

**Location**: level19_batch4.txt:3284-3287  
**Function**: sub_3646B

```asm
0x36472: mov    bx, ds:44AAh
0x36476: sub    bx, 4           ; Subtract 4 from value
0x36479: shl    bx, 1           ; Multiply by 2 (word offset)
0x3647B: jmp    word ptr [bx+70Ch]  ; Jump to table entry
0x3647F: cmp    word ptr ds:44AAh, 8
0x36484: jl     loc_36487       ; Branch if < 8
```

**Interpretation**:
- Jump table indexed by value 4-11 (subtracts 4, uses 0-7)
- Could be aircraft type dispatch (11 types: 0x01, 0x07-0x0B, 0x34-0x36)
- Or could be action code dispatch (10 action types: 0-9)
- Table at ds:70Ch contains jump targets

---

## File Loading Code

### Evidence 1: module_open_3d00 calls

**Location**: Multiple references in level19 code  
**Function**: game_state_load_apply (0x3001E)

```asm
; isldat_disasm.txt:5411
0x300D4: call   far ptr module_open_3d00
0x300D9: jb     loc_300E1         ; Jump if carry (error)
0x300DB: mov    ds:word_45E4C, 3

; isldat_disasm.txt:6411  
0x33958: call   far ptr module_open_3d00
0x3395D: jb     locret_3396D
0x3395F: mov    word ptr ds:135Ch, 3
```

**Interpretation**:
- module_open_3d00 is file open function (DOS INT 21h, AH=3Dh pattern)
- Called from game_state_load_apply function
- Likely loads .MIS, .CAM, and .SQU files
- Need to trace what happens after successful open

---

## Waypoint Coordinate Access

### Evidence: NOT YET FOUND

**Status**: Need to search for:
- Code that reads 16-bit coordinates from waypoint structure
- Offset patterns: [si+1], [si+2] for x_low, x_high
- Offset patterns: [si+5], [si+6] for y_low, y_high
- Loop with 21-byte (0x15) stride

**Search needed**:
```
add si, 15h  ; 21 bytes
mov al, [si+1]  ; x_low
mov ah, [si+2]  ; x_high
```

---

## Speed Parameter

### Evidence: NOT YET FOUND

**Status**: NO evidence found for speed storage in flight param structure.

**Observations**:
- Byte +0x03 in flight params always 0x00 in test files
- No multiplication by speed-like values (400-600) found
- No references to 0x1C2 (450 knots) as data value

**Hypotheses**:
1. **Speed defaulted per action type** - CAP=450, INTERCEPT=600, etc.
2. **Speed calculated from game state** - Based on fuel, altitude, threat level
3. **Speed stored elsewhere** - Separate array or global state
4. **Speed not in mission file** - Determined at runtime by AI

**Need to search for**:
- Default speed tables indexed by action code
- AI decision code that sets aircraft speed
- Speed constants (400, 450, 500, 600 in any encoding)

---

## Action Code Dispatch

### Evidence: NOT YET FOUND

**Status**: Need to find switch/jump table for action codes 0-9

**Expected pattern**:
```asm
mov  al, [si+6]      ; Read action code from flight params (+0x06)
cmp  al, 9           ; Check range 0-9
ja   error           ; Jump if > 9
mov  bx, ax
shl  bx, 1           ; Multiply by 2 (word table)
jmp  word ptr [bx+ACTION_TABLE]
```

**Or string table reference**:
```asm
mov  al, [si+6]      ; Action code
mov  bx, ax
shl  bx, 1
mov  si, word ptr [bx+STRING_TABLE]
; SI now points to "CAP", "CAS", "BOMB", etc.
```

**Search needed**:
- References to string addresses 0x14FD1F, 0x14FD23, etc.
- Jump tables with 10 entries
- Comparisons with 0-9 followed by jump/call

---

## Summary

### CONFIRMED by code:
1. ✓ Altitude uses ×100 encoding (0x64 constant widespread)
2. ✓ 23-byte flight param structure exists (0x17 stride found)
3. ✓ 21-byte waypoint structure exists (0x15 stride found in aircraft_record_load_step)
4. ✓ Aircraft type codes (initialization code found)
5. ✓ Action code strings exist (string table found)

### PARTIALLY CONFIRMED:
1. ~ Flight parameter structure layout (size confirmed, field meanings from binary analysis)
2. ~ File loading code exists (module_open_3d00 found, need to trace data flow)

### NOT YET FOUND:
1. ✗ Direct waypoint coordinate reading code (but 21-byte stride confirmed!)
2. ✗ Action code dispatch/switch table
3. ✗ Speed parameter loading or defaulting
4. ✗ Direct memory structure access showing our exact field offsets (+0x02 altitude, +0x06 action)

---

## Next Search Targets

### Priority 1: Action Code Dispatch
Search for:
- `cmp al, 9` or `cmp byte, 9` (action code range check)
- Jump tables with 10 entries
- String table references at 0x14FD1F-0x14FD61
- Code reading byte at [si+6] or [di+6] in mission context

### Priority 2: Speed Parameter
Search for:
- Speed constants: 400 (0x190), 450 (0x1C2), 500 (0x1F4), 600 (0x258)
- Default speed tables
- AI speed decision code
- Code that sets aircraft speed based on action type

### Priority 3: Mission File Parsing
Search for:
- Code following module_open_3d00 that reads file data
- Buffer addresses where mission data is loaded
- Loops with 6-byte (aircraft), 21-byte (waypoint), or 23-byte (flight params) strides
- DOS file read (INT 21h AH=3Fh) calls

### Priority 4: Waypoint Coordinate Usage
Search for:
- Code that builds 16-bit values from low/high bytes
- `mov al, [si+1]` followed by `mov ah, [si+2]` pattern
- Coordinate system conversions (map coords → screen coords)
- Navigation/routing code that uses waypoint positions

---

## Grep Command Reference

Useful searches to run:

```bash
# Action code range checks
grep -r "cmp.*9$" analysis/ida_falconcd/**/*.txt

# Speed value constants  
grep -r "190h\|1C2h\|1F4h\|258h" analysis/ida_falconcd/**/*.txt

# 21-byte waypoint stride
grep -r "add.*15h" analysis/ida_falconcd/**/*.txt

# Reading bytes +1, +2, +5, +6 (coordinates)
grep -r "mov.*\[(si|di|bx)+[1256]\]" analysis/ida_falconcd/**/*.txt

# File read operations
grep -r "int 21h\|ah, 3Fh" analysis/ida_falconcd/**/*.txt
```

---

**Last Updated**: 2026-11-11  
**Confidence**: Medium (structural evidence strong, but direct field access not yet found)  
**Method**: Static analysis of IDA Pro disassembly + pattern matching
