# AI RFM Data Structure - Decoded

**Date**: 2026-11-18  
**Status**: Structure patterns decoded from code analysis  
**Source**: Analysis of 21 cs:word_3B830 references across 6 AI functions

---

## Executive Summary

RFM files contain **AI behavior parameter tables** indexed by context values at runtime.
The data structure uses **multiplication + shift** indexing to select maneuver parameters.

**Key Discovery**: Three distinct indexing formulas found in code:
1. `(word_3B830 * ([si+14h] + offset)) >> shift` - Main pattern
2. `word_3B830 * ([si+14h] negated + offset) >> shift` - Inverse pattern  
3. `word_3B830 << shift` - Direct shift pattern

---

## Indexing Patterns Discovered

### Pattern 1: Behavior Flag + Offset (Most Common)

**Formula**: `result = (rfm_ptr * (behavior_byte + constant)) >> shift`

**Examples from code:**
```asm
mov     ax, cs:word_3B830       ; Load RFM pointer
mov     ah, [si+15h]            ; Get behavior byte
add     ah, 10h                 ; Add constant offset
mul     ah                      ; Multiply
mov     cl, 4
shr     ax, cl                  ; Shift right by 4
; Result = maneuver parameter
```

**Observed variants:**
- `[si+14h] + 10h >> 4` (used 3 times)
- `[si+14h] + 1Bh >> 3` (used 3 times)
- `[si+14h] + 1Bh >> 2` (used 2 times)
- `[si+15h] + 10h >> 4` (used 1 time)
- `[si+15h] + 1Bh >> 3` (used 1 time)
- `[si+15h] + 1Bh >> 2` (used 1 time)

**Context offsets:**
- `[si+14h]` - AI behavior parameter byte 1
- `[si+15h]` - AI behavior parameter byte 2

### Pattern 2: Negated Behavior Flag (5 instances)

**Formula**: `result = (rfm_ptr * (-behavior_byte + constant)) >> shift`

**Examples from code:**
```asm
mov     ax, cs:word_3B830       ; Load RFM pointer
mov     ah, [si+14h]            ; Get behavior byte
neg     ah                      ; Negate it
add     ah, 74h                 ; Add large constant
mul     ah                      ; Multiply
mov     cl, 4
shr     ax, cl                  ; Shift right
; Result = inverse-indexed parameter
```

**Observed variants:**
- `-[si+14h] + 74h >> 4` (used 3 times)
- `-[si+14h] + 64h >> 7` (used 2 times)

**Purpose**: Likely for **defensive/evasive** maneuvers (opposite of aggressive).

### Pattern 3: Direct Shift (1 instance)

**Formula**: `result = rfm_ptr << shift`

**Example:**
```asm
mov     ax, cs:word_3B830       ; Load RFM pointer  
mov     cl, 6
shl     ax, cl                  ; Shift left by 6
; Result = base offset calculation
```

**Purpose**: Calculate base table offset without behavior indexing.

### Pattern 4: Bit Shift with Multiplication (1 instance)

**Formula**: `result = rfm_ptr * (([si+14h] >> 4) + 1)`

**Example:**
```asm
mov     ax, cs:word_3B830       ; Load RFM pointer
mov     ah, [si+14h]            ; Get behavior byte
mov     cl, 4
shr     ah, cl                  ; Shift right by 4 (upper nibble)
inc     ah                      ; Add 1
mul     ah                      ; Multiply
; Result = upper-nibble indexed parameter
```

**Purpose**: Uses **upper 4 bits** of behavior byte as index (0-15 range).

---

## AI Context Structure (Partial)

From the indexing patterns, we know:

```c
struct AIContext {
    uint8_t  unknown[0x0B];      // +0x00 to +0x0A
    uint16_t behavior_flags;     // +0x0B: 16-bit behavior flags (documented)
    uint8_t  unknown2[0x08];     // +0x0D to +0x13
    uint8_t  behavior_param_1;   // +0x14: Indexed into RFM data
    uint8_t  behavior_param_2;   // +0x15: Also indexed into RFM data
    uint8_t  unknown3[0x0D];     // +0x16 to +0x22
    uint16_t maneuver_result;    // +0x23: Where result is stored
    // ... more fields
};
```

**Key Fields:**
- `+0x0B`: Behavior flags (already decoded, 16 bits)
- `+0x14`: Behavior parameter byte 1 (used for indexing)
- `+0x15`: Behavior parameter byte 2 (used for indexing)
- `+0x23`: Result storage (maneuver parameter returned)

---

## RFM Data Structure Hypothesis

Based on indexing patterns, the RFM data is likely organized as:

```c
struct RFMData {
    // Data is indexed by: (ptr * index) >> shift
    // This suggests a table of small values (bytes)
    
    uint8_t maneuver_params[1008];  // 1008 bytes of parameter data
    
    // Possible organizations:
    // 1. Flat array indexed by calculated offset
    // 2. Multiple sub-tables for different maneuver types
    // 3. 2D array: [behavior_type][maneuver_variant]
};
```

### Indexing Formula Analysis

The formula `(ptr * index) >> shift` is equivalent to:
- `(ptr * index) / (1 << shift)`
- E.g., `(ptr * index) >> 4` = `(ptr * index) / 16`

**If ptr is typically small** (0-255), then:
- `(200 * 16) >> 4` = `3200 / 16` = 200
- This maps index values to offsets in the data array

**Likely interpretation**: 
- RFM data pointer (`cs:word_3B830`) is actually a **scalar multiplier**, not a memory pointer!
- The multiplication + shift produces an **index into a separate fixed table**
- The table is likely at a fixed address, not pointed to by word_3B830

### Alternative: word_3B830 is a Configuration Value

Looking at the initialization:
```asm
mov     ax, 2F64h               ; Load constant
mov     ds, ax
mov     ax, word_2F677          ; Read from data segment
mov     cs:word_3B830, ax       ; Store in code segment
```

**Possibility**: `word_3B830` is a **configuration/difficulty parameter**, not a pointer!
- Value loaded from mission file (RFM)
- Used as multiplier for AI parameter calculations
- Different values = different AI skill levels

**Evidence**:
1. DEFBFM1-6 files = 6 difficulty levels
2. Value is used as multiplier, not dereferenced
3. Small value (0-255 range likely)
4. Stored in code segment (unusual for pointers)

---

## Functions Using RFM Data

### High-Level Functions (4+ references)

**1. ai_combat_maneuver_selector @ 0x3E2D3 (505 bytes)**
- 4 references to cs:word_3B830
- Tests behavior flags, calculates maneuver parameters
- Main decision-making function for combat tactics

**2. entity_physics_and_ai_update @ 0x3D37F (1319 bytes)**
- 7 references to cs:word_3B830
- Large update function handling physics + AI
- Uses RFM data for weapon guidance and evasion

**3. ai_state_processor_core @ 0x3CF9D (886 bytes)**
- 4 references to cs:word_3B830
- Core state machine processing
- Uses RFM data for state-specific parameters

### Mid-Level Functions (2-3 references)

**4. sub_3C319 @ 0x3C319 (116 bytes)**
- 3 references
- Tests behavior flags 0x10 (Special) and 0x08 (Combat)
- Uses negated indexing (defensive maneuvers?)

### Low-Level Functions (1 reference)

**5. entity_slot_update_loop @ 0x3C1BD**
- 1 WRITE: Initializes cs:word_3B830 from word_2F677

**6. farobj_slot_table_copy @ 0x419FC**
- 1 WRITE: Restores cs:word_3B830 from savegame

**7. sub_3C38D @ 0x3C3A5**
- 1 READ: Uses RFM data for additional calculations

---

## Behavior Parameter Values

From code analysis, behavior parameter bytes at [si+14h] and [si+15h] are used with these constants:

**Additive offsets:**
- `+0x10` (16) - Used with shift 4
- `+0x1B` (27) - Used with shifts 2, 3
- `+0x64` (100) - Used with negated values
- `+0x74` (116) - Used with negated values

**Shift amounts:**
- `>> 2` (divide by 4)
- `>> 3` (divide by 8)
- `>> 4` (divide by 16)
- `>> 6` (divide by 64)
- `>> 7` (divide by 128)

---

## Next Steps to Decode

### 1. Extract word_3B830 Values at Runtime

Run game in DOSBox debugger:
```
# Set breakpoint after initialization
bp 3C1C7
# Run mission
# Print value
? word cs:3B830
```

Record values for different missions/difficulty levels.

### 2. Dump RFM File Header

Extract first 64 bytes of each DEFBFM file, compare:
- DEFBFM1.RFM (easiest)
- DEFBFM2.RFM (easy)
- ...
- DEFBFM6.RFM (ace)

Look for value that matches cs:word_3B830.

### 3. Identify Fixed Table Location

Search for the actual maneuver parameter table in memory/binary:
- Likely at fixed offset in code or data segment
- Contains byte-sized values (angles, speeds, percentages)
- Size: probably 256-1024 bytes

### 4. Test Hypothesis

Modify cs:word_3B830 value at runtime, observe AI behavior changes:
- Set to 0: AI should use minimum parameters
- Set to 255: AI should use maximum parameters
- Set to value from DEFBFM6: Should get ace-level AI

---

## Preliminary Conclusions

1. **cs:word_3B830 is likely a difficulty/skill SCALAR, not a memory pointer**
2. **RFM files contain this scalar value in their header**
3. **The scalar is used to calculate indices into a fixed maneuver table**
4. **Different RFM files = different skill levels for AI**
5. **Maneuver parameters are calculated dynamically, not stored in RFM**

**This means:**
- RFM files are smaller than we thought (header mostly)
- Most of the 1504 bytes may be unused padding
- The 1008 "active" bytes might be something else (mission setup?)
- AI behavior is primarily controlled by the scalar + fixed tables in code

---

## Files Updated

- `registry/globals.yaml` - Added RFM-related globals
- `registry/functions.yaml` - Updated 5 AI functions with RFM info
- `temp/ai_rfm_usage_analysis.txt` - Detailed pattern analysis

---

**Status**: 85% confident in scalar hypothesis. Need runtime verification.
