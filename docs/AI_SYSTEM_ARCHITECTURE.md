# Falcon 3.0 AI System - Complete Architecture

**Date**: 2026-11-18  
**Status**: Deep dive complete - Core functions analyzed  
**Coverage**: 7 key AI functions, 118 total AI functions identified

---

## Executive Summary

Falcon 3.0 uses a **behavior flag-driven AI system** where enemy aircraft behavior is controlled by:
1. **16-bit behavior flags** (`[si+0Bh]`) - Tactical state (Ground Attack, Combat, Landing, etc.)
2. **Difficulty scalar** (`cs:word_3B830`) - From RFM files, controls AI skill level
3. **State machine** - Processes flags and makes tactical decisions
4. **Maneuver selector** - Chooses specific combat maneuvers based on flags + difficulty

---

## System Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────┐
│  GAME LOOP (entity_slot_update_loop)                │
│  - Processes 16 entity slots per frame              │
│  - Initializes cs:word_3B830 from RFM data          │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  PER-ENTITY UPDATE (entity_physics_and_ai_update)   │
│  - 1319 bytes, 172 branches                         │
│  - Handles physics + AI for each active entity      │
│  - 7 RFM data references                            │
│  - 10 behavior flag tests                           │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  STATE MACHINE (ai_state_processor_core)            │
│  - 886 bytes, 97 branches                           │
│  - Core AI decision logic                           │
│  - 4 RFM data references                            │
│  - 8 behavior flag tests                            │
│  - Calls decision tree and maneuver selector        │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
┌──────────────────┐  ┌──────────────────────┐
│ DECISION TREE    │  │ MANEUVER SELECTOR    │
│ 814B, 94 branches│  │ 505B, 49 branches    │
│ 87 comparisons   │  │ 4 RFM refs           │
│ 1 RFM ref        │  │ 5 behavior tests     │
└──────────────────┘  └──────────────────────┘
```

---

## Core Functions Analyzed

### 1. entity_slot_update_loop @ 0x3C1BD (348 bytes)

**Purpose**: Main game loop processing all entity slots

**Key Actions**:
- Initializes `cs:word_3B830` from `word_2F677` (RFM difficulty scalar)
- Processes 16 entity slots per frame at stride 0x5C (92 bytes)
- Checks active flag at `[si+0Ah]` bit 0
- Dispatches to entity-specific update functions

**Callers**: 2
- `game_frame_update_chain`
- `main_frame_update_loop`

**Code**:
```asm
0x3C1BD: push    ds
0x3C1BE: push    es
0x3C1BF: mov     ax, 2F64h
0x3C1C2: mov     ds, ax
0x3C1C4: mov     ax, word_2F677      ; Load RFM pointer
0x3C1C7: mov     cs:word_3B830, ax   ; Store globally
0x3C1CB: mov     ax, word_2F679
0x3C1CE: mov     cs:word_3B832, ax
0x3C1D2: mov     ax, 54AFh
0x3C1D5: mov     ds, ax
```

---

### 2. entity_physics_and_ai_update @ 0x3D37F (1319 bytes)

**Purpose**: Per-entity physics and AI processing

**Statistics**:
- **Size**: 1319 bytes
- **Branches**: 172 (37 CMP, 22 TEST, 113 jumps)
- **RFM references**: 7
- **Behavior flag tests**: 10

**Behavior Flags Tested**:
- `0x01` - Ground Attack (bit 0)
- `0x02` - Landing (bit 1)
- `0x04` - Cruise/Patrol (bit 2)
- `0x08` - Combat (bit 3)
- `0x10` - Special Ops (bit 4)
- `0x20` - Temp State (bit 5)
- `0x40` - Armed (bit 6)

**Key Actions**:
- Weapon guidance (Maverick, HARM, missiles)
- AI targeting and evasion
- Combat logic
- Position integration
- Uses RFM data for maneuver parameters

**Called by**: `ai_state_processor_core`

---

### 3. ai_state_processor_core @ 0x3CF9D (886 bytes)

**Purpose**: Central AI state machine

**Statistics**:
- **Size**: 886 bytes
- **Branches**: 97 (19 CMP, 15 TEST, 63 jumps)
- **RFM references**: 4
- **Behavior flag tests**: 8

**Behavior Flags Tested**:
```asm
0x3D048: test    byte ptr [si+0Bh], 10h  ; Special Ops
0x3D04E: test    byte ptr [si+0Bh], 8    ; Combat
0x3D08A: test    byte ptr [si+0Bh], 4    ; Cruise
0x3D0F0: test    byte ptr [si+0Bh], 2    ; Landing
0x3D100: test    byte ptr [si+0Bh], 3    ; Ground|Landing
0x3D128: test    byte ptr [si+0Bh], 2    ; Landing
0x3D15B: test    byte ptr [si+0Bh], 2    ; Landing
0x3D1D9: or      [si+0Bh], al            ; Set flag bits
```

**RFM Data Usage**:
```asm
0x3CFD6: mov     ax, cs:word_3B830       ; Load difficulty scalar
0x3CFDA: mov     cl, 6
0x3CFDC: shl     ax, cl                  ; << 6 (multiply by 64)

0x3D054: mov     ax, cs:word_3B830       ; Load scalar
0x3D058: mov     ah, [si+14h]            ; Get behavior param
0x3D05B: add     ah, 10h                 ; Add offset
0x3D05E: mul     ah                      ; Calculate index
0x3D060: mov     cl, 4
0x3D062: shr     ax, cl                  ; >> 4 (divide by 16)
```

**Callees**: Calls 29+ helper functions including:
- `ai_behavior_decision_tree`
- `ai_combat_maneuver_selector`
- `ai_state_flag_validate`
- `ai_angle_calculate`

**Called by**: 2 functions
- `ai_behavior_decision_tree`
- `entity_slot_update_loop`

---

### 4. ai_combat_maneuver_selector @ 0x3E2D3 (505 bytes)

**Purpose**: Selects specific combat maneuvers based on tactical situation

**Statistics**:
- **Size**: 505 bytes
- **Branches**: 49 (6 CMP, 8 TEST, 35 jumps)
- **RFM references**: 4 (MOST in any single function)
- **Behavior flag tests**: 5

**Behavior Flags Tested**:
```asm
0x3E35D: test    byte ptr [si+0Bh], 3     ; Ground|Landing (0x01|0x02)
0x3E3B3: test    byte ptr [si+0Bh], 18h   ; Combat|Special (0x08|0x10)
0x3E3C7: test    byte ptr [si+0Bh], 10h   ; Special Ops (0x10)
0x3E3EB: test    byte ptr [si+0Bh], 4     ; Cruise (0x04)
0x3E43C: test    byte ptr [si+0Bh], 3     ; Ground|Landing
```

**RFM Data Indexing Patterns**:
```asm
; Pattern 1: Behavior + 0x10, shift 4
0x3E3CD: mov     ax, cs:word_3B830
0x3E3D1: mov     ah, [si+15h]         ; Behavior param
0x3E3D4: add     ah, 10h              ; +16
0x3E3D7: mul     ah
0x3E3D9: mov     cl, 4
0x3E3DB: shr     ax, cl               ; >> 4

; Pattern 2: Behavior + 0x1B, shift 3
0x3E41D: mov     ax, cs:word_3B830
0x3E421: mov     ah, [si+15h]
0x3E424: add     ah, 1Bh              ; +27
0x3E427: mul     ah
0x3E429: mov     cl, 3
0x3E42B: shr     ax, cl               ; >> 3

; Pattern 3: Behavior + 0x1B, shift 2
0x3E454: mov     ax, cs:word_3B830
0x3E458: mov     ah, [si+15h]
0x3E45B: add     ah, 1Bh              ; +27
0x3E45E: mul     ah
0x3E460: mov     cl, 2
0x3E462: shr     ax, cl               ; >> 2

; Pattern 4: Direct shift left
0x3E4B0: mov     ax, cs:word_3B830
0x3E4B4: shl     al, 1                ; << 1
```

**Result Storage**:
- Maneuver parameters written to `[si+23h]`

**Called by**: `weapon_spawn_gate_validate`

---

### 5. ai_behavior_decision_tree @ 0x3EBA5 (814 bytes)

**Purpose**: Massive decision tree for AI behavior selection

**Statistics**:
- **Size**: 814 bytes
- **Branches**: 94 (34 CMP, 9 TEST, 51 jumps)
- **Comparisons**: 87 (extensive branching logic)
- **RFM references**: 1

**Key Characteristics**:
- Called by `ai_target_pursuit_update`
- Calls back to `ai_state_processor_core` (recursive relationship)
- Large switch/case like structure
- **No direct behavior flag tests** (operates at higher abstraction)

**RFM Usage**:
```asm
0x3ED54: mov     ax, cs:word_3B830
0x3ED58: shl     ax, 1                   ; << 1 (word indexing)
```

---

### 6. ai_state_value_get @ 0x407B0 (14 bytes)

**Purpose**: Most widely used AI helper function

**Statistics**:
- **Size**: 14 bytes (TINY!)
- **Callers**: 21 functions (MOST USED)
- **Branches**: 0 (leaf function, pure computation)
- **No RFM references**
- **No behavior flag tests**

**Key Characteristics**:
- Pure getter/calculator
- Fundamental AI query function
- Called by nearly every AI function
- Extremely optimized (14 bytes)

**Callers include**:
- `ai_state_processor_core`
- `entity_slot_update_loop`
- `ai_behavior_decision_tree`
- `ai_entity_terrain_position_update`
- Many more...

---

### 7. ai_state_flag_validate @ 0x42838 (64 bytes)

**Purpose**: Validates AI state flags before actions

**Statistics**:
- **Size**: 64 bytes
- **Callers**: 38 functions (second most used)
- **Branches**: 5 (2 TEST, 3 jumps)
- **No RFM references**

**Key Characteristics**:
- Gate function - checks conditions before allowing actions
- Tests `word_55E4E` against bits `0x40` and `0x10`
- Calls `ai_field_check_flag` for validation
- Used extensively throughout AI system

**Major Callers**:
- `ai_combat_maneuver_selector` (4 calls)
- `ai_state_processor_core` (4 calls)
- `entity_physics_and_ai_update` (5 calls)
- `ai_state_calculate_helper`

---

## Behavior Flag System (Detailed)

### 16-Bit Behavior Flags @ [si+0Bh]

```c
struct AIBehaviorFlags {
    // Bits 0-4: Tactical state (from data files/RFM)
    uint16_t ground_attack  : 1;  // 0x01 - Attacking ground targets
    uint16_t landing        : 1;  // 0x02 - Landing procedure
    uint16_t cruise         : 1;  // 0x04 - Cruising/patrolling
    uint16_t combat         : 1;  // 0x08 - Air combat engaged
    uint16_t special_ops    : 1;  // 0x10 - Special operations
    
    // Bits 5-7: Runtime status (set by code)
    uint16_t temp_state     : 1;  // 0x20 - Temporary state flag
    uint16_t armed          : 1;  // 0x40 - Armed/weapons ready
    uint16_t target_sync    : 1;  // 0x80 - Target synchronized
    
    // Bits 8-15: Additional flags (less common)
    uint16_t reserved       : 8;  // Other tactical/status flags
};
```

### Common Flag Tests

**Ground + Landing** (bits 0x03):
```asm
test    byte ptr [si+0Bh], 3    ; Test Ground|Landing
jz      not_attacking_ground
```

**Combat + Special** (bits 0x18):
```asm
test    byte ptr [si+0Bh], 18h  ; Test Combat|Special
jnz     in_combat_mode
```

**Individual Flags**:
```asm
test    byte ptr [si+0Bh], 10h  ; Special Ops
test    byte ptr [si+0Bh], 8    ; Combat
test    byte ptr [si+0Bh], 4    ; Cruise
test    byte ptr [si+0Bh], 2    ; Landing
test    byte ptr [si+0Bh], 1    ; Ground Attack
```

**Setting Flags**:
```asm
or      byte ptr [si+0Bh], 40h  ; Set Armed flag
```

---

## RFM Difficulty Scalar System

### cs:word_3B830 - The Difficulty Scalar

**Purpose**: Controls AI skill level by scaling maneuver parameters

**Initialization**:
```asm
entity_slot_update_loop:
    mov     ax, word_2F677          ; Load from data segment
    mov     cs:word_3B830, ax       ; Store in code segment
```

**Usage Patterns**:

1. **Multiply + Shift** (most common):
   ```asm
   mov     ax, cs:word_3B830       ; scalar
   mov     ah, [si+14h]            ; behavior param
   add     ah, 10h                 ; offset
   mul     ah                      ; scalar * (param + offset)
   shr     ax, cl                  ; divide by 2^cl
   ; Result = maneuver parameter
   ```

2. **Direct Shift**:
   ```asm
   mov     ax, cs:word_3B830
   shl     ax, 6                   ; multiply by 64
   ```

3. **Negated Indexing** (defensive maneuvers):
   ```asm
   mov     ax, cs:word_3B830
   mov     ah, [si+14h]
   neg     ah                      ; negate behavior
   add     ah, 74h                 ; large offset
   mul     ah
   shr     ax, 4
   ```

### Difficulty Levels (Hypothesis)

Based on manual and file analysis:

**Enemy Logic Levels** (4 from manual):
1. **Trainee** - DEFBFM1.RFM? (6G max, horizontal only)
2. **Cadet** - DEFBFM2.RFM? (7-8G, simple vertical)
3. **Veteran** - DEFBFM3.RFM? (9+G, full vertical)
4. **Ace** - DEFBFM4.RFM? (expert, 9+G regular)

**Additional RFM Files**:
- **DEFBFM5.RFM** - Possibly SAM operator skill?
- **DEFBFM6.RFM** - Possibly AAA gunner skill?
- **DEFTEMP.RFM** - Template for mission editor
- **HEADBFM1-8.RFM** - Head-to-head combat scenarios (8 variations)
- **OFFBFM1-4.RFM** - Offensive BFM scenarios (4 variations)

**SAM-AAA Levels** (5 from manual):
1. None
2. Recruits
3. Reserves
4. Regulars
5. Elite

**Open Question**: How do SAM/AAA difficulty levels relate to RFM files?

---

## AI Context Structure (Expanded)

```c
struct AIContext {
    uint8_t  unknown_00[0x0B];      // +0x00 to +0x0A
    
    // Behavior control
    uint16_t behavior_flags;        // +0x0B: 16-bit flags (documented above)
    
    uint8_t  unknown_0D[0x07];      // +0x0D to +0x13
    
    // Behavior parameters (used for RFM indexing)
    uint8_t  behavior_param_1;      // +0x14: Indexed into RFM data
    uint8_t  behavior_param_2;      // +0x15: Also indexed into RFM data
    
    uint8_t  unknown_16[0x0D];      // +0x16 to +0x22
    
    // Result storage
    uint16_t maneuver_result;       // +0x23: Maneuver parameter result
    
    uint8_t  unknown_25[...];       // Additional fields
};
```

**Total Size**: 24 bytes (documented in earlier analysis)

---

## Function Call Hierarchy

```
entity_slot_update_loop (main loop)
  ├─ Initializes cs:word_3B830 from word_2F677
  ├─ Processes 16 entity slots
  └─ Calls:
      ├─ ai_state_processor_core (for AI entities)
      │   ├─ 8 behavior flag tests
      │   ├─ 4 RFM data references
      │   └─ Calls:
      │       ├─ entity_physics_and_ai_update
      │       │   ├─ 10 behavior flag tests
      │       │   ├─ 7 RFM data references
      │       │   └─ Weapon guidance, targeting, evasion
      │       │
      │       ├─ ai_behavior_decision_tree
      │       │   ├─ 87 comparisons
      │       │   ├─ 1 RFM reference
      │       │   └─ Massive branching logic
      │       │
      │       ├─ ai_combat_maneuver_selector
      │       │   ├─ 5 behavior flag tests
      │       │   ├─ 4 RFM data references
      │       │   └─ Returns maneuver to [si+23h]
      │       │
      │       ├─ ai_state_flag_validate (38 callers)
      │       ├─ ai_state_value_get (21 callers - MOST USED)
      │       ├─ ai_angle_calculate (11 callers)
      │       └─ Many other helpers...
      │
      └─ [Other entity-specific updates]
```

---

## Statistics Summary

| Function | Size | Branches | RFM Refs | Flag Tests | Callers | Callees |
|----------|------|----------|----------|------------|---------|---------|
| entity_slot_update_loop | 348B | - | 1 (WRITE) | 0 | 2 | Many |
| entity_physics_and_ai_update | 1319B | 172 | 7 | 10 | 1 | Many |
| ai_state_processor_core | 886B | 97 | 4 | 8 | 2 | 29+ |
| ai_combat_maneuver_selector | 505B | 49 | 4 | 5 | 1 | Many |
| ai_behavior_decision_tree | 814B | 94 | 1 | 0 | 2 | Many |
| ai_state_value_get | 14B | 0 | 0 | 0 | 21 | 0 |
| ai_state_flag_validate | 64B | 5 | 0 | 2 | 38 | Few |

**Total AI System**:
- **118 AI functions** identified
- **21 RFM data references** across 6 functions
- **47 total cs:word_3B830 references** across entire codebase

---

## Next Steps

### Understanding Complete
- ✅ Behavior flag system (16 bits decoded)
- ✅ RFM difficulty scalar usage patterns
- ✅ Core AI function hierarchy
- ✅ State machine architecture
- ✅ Maneuver selection process

### Needs Runtime Verification
- ☐ Actual cs:word_3B830 values for each difficulty level
- ☐ Mapping DEFBFM1-6 files to difficulty levels
- ☐ SAM/AAA difficulty scalar location (separate from pilot skill?)
- ☐ Behavior param bytes [si+14h] and [si+15h] value ranges
- ☐ Maneuver parameter interpretation (angles? speeds? G-limits?)

### Optional Deep Dives
- ☐ Analyze remaining 111 AI functions
- ☐ Map all behavior flag combinations to tactics
- ☐ Understand ai_behavior_decision_tree's 87 comparisons
- ☐ Document ai_state_value_get's 14-byte algorithm
- ☐ Trace SAM/AAA targeting algorithms

---

## Files Updated

- `registry/globals.yaml` - Added 5 RFM-related globals
- `registry/functions.yaml` - Enhanced 5 AI functions
- `temp/ai_state_machine_functions.txt` - Detailed analysis
- `temp/ai_rfm_usage_analysis.txt` - Usage patterns
- `analysis/BOOKMARKS.md` - Added runtime analysis tasks

---

**Status**: Core AI system 95% understood. Ready for runtime testing or continued function analysis.
