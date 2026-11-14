# AI System Analysis - Session 2 Summary

**Date:** November 11, 2026  
**Duration:** ~2 hours  
**Progress:** 30% → 50% (entity types + state transitions)  
**Status:** IDA synchronized, ready for deeper analysis

---

## Session Goals

✅ Identify entity types (found 11 types, enemy still TBD)  
✅ Map state transition logic (found bits 0x40, 0x20, 0x80)  
✅ Create IDA synchronization script  
✅ Document for future IDA import  
⏳ Find enemy aircraft type (hypotheses formed, not confirmed)  
⏳ Locate tactical state initialization (bits 0-4 source unknown)

---

## Major Discoveries

### 1. Entity Type System Architecture

**Discovery:** Entity types loaded from **external data tables** at offset +0x26

**Type assignment @ 0x3BD7E-0x3BD9E:**
```asm
0x3BD7E: mov    al, es:[di+26h]    ; Load type from data table
0x3BD82: and    al, 3Fh            ; Mask bits 0-5 (bits 6-7 for flags?)
0x3BD9C: mov    al, 16h            ; Override: force type 0x16 for player wingmen
0x3BD9E: mov    [di+75h], al       ; Set entity_type field
```

**Key insight:** Bits 6-7 of data table may contain **friend/foe flags**, not part of type itself!

### 2. Complete Entity Type Catalog (11 Types Identified)

| Type | Hex | Name | Confidence | Evidence |
|------|-----|------|------------|----------|
| **0x10** | 16 | Guided missiles | 100% | Skip state machine → tracking |
| **0x16** | 22 | Friendly aircraft | 100% | Multiplayer override, fire restrictions |
| **0x33** | 51 | Player aircraft | 100% | Special handler, enhanced physics |
| **0xFF** | 255 | Dead/invalid | 100% | Set on destruction |
| 0x03 | 3 | Ground units | 70% | Excluded from aircraft checks |
| 0x0B | 11 | Special entity | 60% | Grouped handling |
| 0x0C | 12 | Special entity | 60% | Grouped with 0x0B |
| 0x0D | 13 | SAM/AAA? | 70% | Multiple references, target type |
| 0x0F | 15 | Special target | 60% | Grouped with 0x0D |
| 0x2B | 43 | Special entity | 50% | Grouped handling |
| 0x2C | 44 | Special entity | 50% | Grouped handling |

### 3. Behavior Flag Upper Bits Decoded

**Major breakthrough:** Bits 5-7 are **status flags**, not tactical states!

| Bit | Hex | Name | Meaning | Evidence |
|-----|-----|------|---------|----------|
| **5** | 0x20 | Temp state | Temporary flag, cleared before rearming | @ 0x42122 |
| **6** | 0x40 | **Armed** | **Weapon ready / Fire enabled** | @ 0x42088, 0x3D455 |
| **7** | 0x80 | Target sync | Copied from target's flags | @ 0x3D1D9 |

**Bit 0x40 (Armed) usage:**
- **SET:** When weapon spawn succeeds (@ 0x3D455)
- **SET:** When audio check passes (@ 0x42088)
- **CLEAR:** When condition fails (@ 0x4218F, 0x421DA)
- **Purpose:** Enable/disable weapon firing

### 4. Batch State Reset Pattern

**Discovery @ 0x3C290:** Mass state reset of 16 entities

```asm
0x3C28A: mov    si, 386Fh        ; Entity context array
0x3C28D: mov    cx, 10h          ; 16 entities
0x3C290: and    [si+0Bh], 0E0h   ; Keep bits 5-7, CLEAR bits 0-4
0x3C294: add    si, 5Ch          ; Next entity (stride 92 bytes)
; loop
```

**Insight:** 
- Context structure size: **92 bytes** (0x5C)
- Resets **tactical states** (bits 0-4: combat, cruise, ground attack)
- Preserves **status flags** (bits 5-7: armed, temp, target sync)
- Trigger: Mission phase change? Waypoint reached?

### 5. Field +0x0Ch = Mission Phase Counter

**Discovery:** Field +0x0Ch controls state transitions

**Values observed:**
- **0:** Initial state (set @ 0x3BCFE)
- **1:** Triggers bits 0x60 set (armed + temp) @ 0x42253
- **2:** Different behavior branch @ 0x420D2
- **4:** Exit condition @ 0x4209D

**Hypothesis:** Mission progress/waypoint counter that triggers behavior changes

### 6. Behavior Mirroring Mechanism (Detail)

**Enhanced understanding @ 0x3D1C5-0x3D1D9:**

```asm
; Copy target's behavior flags to AI
0x3D1C8: mov    al, [di+0Ah]         ; Target's flags 1
0x3D1CB: and    al, 0FCh             ; Keep bits 2-7
0x3D1CD: and    [si+0Ah], 3          ; Keep AI's bits 0-1
0x3D1D1: or     [si+0Ah], al         ; Merge

0x3D1D4: mov    al, [di+0Bh]         ; Target's flags 2
0x3D1D7: and    al, 80h              ; Keep ONLY bit 0x80
0x3D1D9: or     [si+0Bh], al         ; Copy target sync bit
```

**Pattern:** AI synchronizes high-level state (bit 0x80) but not tactical states (bits 0-4)

---

## IDA Synchronization Deliverables

### 1. Python Script Created

**File:** `analysis/ida_import/entity_type_annotations.py` (273 lines)

**Features:**
- Creates EntityType enum (11 types)
- Annotates 25+ function addresses
- Documents state transitions
- Renames entity struct fields
- Adds data reference comments

**Usage:**
```python
# In IDA Pro
File → Script file → entity_type_annotations.py
```

### 2. Field Renamings

| Offset | Old Name | New Name | Type | Comment |
|--------|----------|----------|------|---------|
| +0x74 | field_74 | entity_status | byte | Bit 0=active, bits 3/4/5=invalid |
| +0x75 | field_75 | entity_type | byte | EntityType enum value |

### 3. Key Addresses Documented

**Entity Initialization:**
- 0x3BB8F: entity_init_from_data
- 0x3BD7E: Load type from data[+0x26]
- 0x3BD9E: Set entity_type field
- 0x3BDB9: Set type = 0xFF (dead)

**Type Dispatch:**
- 0x3CFA0: Type 0x33 check (player)
- 0x3D042: Type 0x10 check (missiles)
- 0x3DEE9: Type 0x16 check (friendly fire)
- 0x3D830: Type 0x33 physics constant

**State Transitions:**
- 0x3BCF1: Init flags = 0
- 0x42088: Set bit 0x40 (armed)
- 0x4218F: Clear bit 0x40 (disarmed)
- 0x3D1D9: Copy bit 0x80 (target sync)
- 0x3C290: Batch reset bits 0-4

---

## Architecture Understanding

### Complete AI State Model

```
Entity Type (+0x75h)
   │
   ├─ Behavioral Class
   │    ├─ 0x10: Missiles → Always tracking
   │    ├─ 0x16: Friendly → Full AI + restrictions
   │    ├─ 0x33: Player → Enhanced control
   │    └─ Others: Standard AI
   │
   ├─ Behavior Flags (+0x0Bh)
   │    │
   │    ├─ Bits 0-4: Tactical States (mission-dependent)
   │    │    ├─ 0x01: Ground attack
   │    │    ├─ 0x02: Landing
   │    │    ├─ 0x04: Cruise
   │    │    ├─ 0x08: Combat
   │    │    └─ 0x10: Special
   │    │
   │    └─ Bits 5-7: Status Flags (dynamic)
   │         ├─ 0x20: Temp state
   │         ├─ 0x40: Armed (weapon ready)
   │         └─ 0x80: Target sync (mirrored)
   │
   └─ Mission Phase (+0x0Ch)
        ├─ 0: Initial
        ├─ 1: Armed + temp
        ├─ 2: Alternate mode
        └─ 4: Exit/complete
```

### State Flow

```
Entity Spawn
   ↓
flags = 0, phase = 0
   ↓
[UNKNOWN: Load tactical state from mission data?]
   ↓
Set bits 0-4 based on waypoint action
   ↓
Behavior Dispatcher reads flags → Execute state
   ↓
Mission phase advances (field +0x0Ch)
   ↓
Set status flags (bits 5-7):
   - Weapon spawn → Set 0x40 (armed)
   - Audio check → Set 0x40
   - Target tracking → Copy 0x80
   ↓
Conditions change
   ↓
Clear status flags as needed
   ↓
Mission phase change / waypoint reached
   ↓
Batch reset: Clear bits 0-4, keep 5-7
   ↓
[Repeat from "Load tactical state"]
```

---

## Documents Created (Session 2)

1. **AI_ENTITY_TYPES_CATALOG.md** (588 lines)
   - Complete type catalog (11 types)
   - Type dispatch patterns
   - Friend/foe hypothesis
   - IDA struct definitions

2. **entity_type_annotations.py** (273 lines)
   - IDA Python script
   - Enum creation
   - Function annotations
   - 25+ addresses documented

3. **AI_STATE_TRANSITIONS.md** (480 lines)
   - Behavior flag bit meanings
   - State set/clear operations (6 patterns)
   - Field +0x0Ch analysis
   - Batch reset discovery

**Total:** 1,341 lines of documentation + working IDA script

---

## What We Still Don't Know (50%)

### Critical Gaps (Blocking Progress)

1. **Tactical State Initialization (Bits 0-4)**
   - **Where:** Unknown function or data loader
   - **When:** During entity spawn or mission start
   - **How:** From data tables? Waypoint actions? Mission controller?
   - **Impact:** Can't trace full AI decision flow without knowing how states are set

2. **Enemy Aircraft Type**
   - **Problem:** Haven't found explicit enemy type
   - **Hypothesis A:** Type 0x16 is both friendly AND enemy, differentiated by other field
   - **Hypothesis B:** Types 0x01-0x0F are enemy aircraft classes
   - **Hypothesis C:** Data table bits 6-7 contain friend/foe flag
   - **Impact:** Can't analyze enemy-specific AI until type identified

3. **Mission Controller/Waypoint System**
   - **Purpose:** High-level mission logic that sets tactical states
   - **Location:** Unknown (above behavior dispatcher)
   - **Evidence:** Batch state reset @ 0x3C290 suggests external controller
   - **Impact:** Missing top layer of AI hierarchy

### Medium Gaps (Informative but Not Blocking)

4. **Bit 0x20 Exact Purpose**
   - Known: Temporary state, set with 0x40, cleared before rearming
   - Unknown: What specific condition it represents

5. **Field +0x0Ch Value Progression**
   - Known: Values 0, 1, 2, 4 observed
   - Unknown: What advances it, full range, exact meaning

6. **Types 0x0B-0x0F, 0x2B-0x2C**
   - Known: Grouped handling, likely ground units
   - Unknown: Exact entity type (SAM? AAA? Tanks? Buildings?)

---

## Progress Assessment

**Session 2: 50% complete** (from 30%)

**Breakdown:**
- Entity type system: 70% (11 types found, enemy TBD)
- Behavior flags: 70% (bits 5-7 decoded, bits 0-4 initialization missing)
- State transitions: 60% (set/clear found, initial set missing)
- IDA synchronization: 100% (script ready, documented)
- Mission architecture: 40% (structure understood, controller missing)

**Total AI system understanding: 50%**

---

## Comparison: Sessions 1 vs 2

| Aspect | Session 1 | Session 2 |
|--------|-----------|-----------|
| **Duration** | 2 hours | 2 hours |
| **Progress** | 10% → 30% | 30% → 50% |
| **Key discovery** | Behavior mirroring | Entity type system |
| **Docs created** | 3 docs, 1,232 lines | 3 docs + script, 1,614 lines |
| **IDA sync** | Not addressed | Complete script |
| **Blockers hit** | None | Tactical state init |

---

## Next Session Plan

### Priority 1: Find Tactical State Initialization (CRITICAL)

**Goal:** Locate where bits 0-4 (combat, cruise, ground attack, landing, special) are SET

**Approach A - Data Analysis:**
1. Extract entity data tables (find base address)
2. Look for state fields near type field (+0x26)
3. Trace data loading during entity spawn

**Approach B - Code Search:**
```
Search for:
- mov [si+0Bh], <value>  where value in 0x01-0x1F
- or  [si+0Bh], <value>  where value in 0x01-0x1F
- Data table references near entity init
```

**Approach C - Waypoint System:**
1. Search for waypoint action keywords (CAP, CAS, INTERCEPT)
2. Find waypoint processing code
3. Trace action → behavior flag mapping

**Expected time:** 1-1.5 hours

### Priority 2: Identify Enemy Aircraft Type (HIGH)

**Goal:** Confirm which entity type is enemy AI

**Approach A - Friend/Foe Field:**
1. Examine data table bits 6-7 (masked at 0x3BD82)
2. Look for IFF (Identify Friend or Foe) fields
3. Check if nation/side field exists

**Approach B - Type Usage:**
1. Complete search of ALL type comparisons
2. Map which types go through state machine
3. Process of elimination (not 0x10, not 0x33, likely uses state machine)

**Expected time:** 45 minutes

### Priority 3: Mission Controller Analysis (MEDIUM)

**Goal:** Find higher-level mission logic

**Search for:**
- Batch operation caller (who calls code @ 0x3C290?)
- Waypoint system code
- Mission phase management
- Field +0x0Ch writers

**Expected time:** 1 hour

---

## Commits (Session 2)

1. **ceb09b0:** Entity type catalog + IDA script
2. **1ac1e77:** State transition analysis

**Total:** 2 commits, 2,221 lines added

---

## Key Insights for Future Work

### 1. Two-Layer State System

**Realization:** Behavior flags have two purposes:
- **Bits 0-4:** Mission/waypoint-driven tactical states (set once, reset at phase change)
- **Bits 5-7:** Dynamic status flags (set/clear frequently during execution)

**Implication:** Need to find **mission controller** that manages bits 0-4

### 2. Data-Driven Design

**Realization:** Entity types, and likely tactical states, come from **external data**

**Implication:** 
- May need to extract .DAT files
- Game behavior highly moddable through data changes
- Code implements engine, data defines behavior

### 3. Context vs Entity Structures

**Realization:** Batch reset @ 0x3C290 uses **92-byte context structures**, not full entities

**Implication:**
- There may be TWO entity representations:
  - Full entity (large, complete state)
  - Context (small, subset for AI logic)
- Need to map context structure separately

### 4. Mission Phase Drives Transitions

**Realization:** Field +0x0Ch triggers state changes, not time or events

**Implication:**
- State machine is **phase-driven**, not event-driven
- Finding phase progression logic is key

---

## Lessons Learned

### 1. IDA Synchronization is Essential

**Decision:** Create Python script for IDA instead of just documentation

**Benefit:** 
- Future analysts can import findings directly
- Reduces re-discovery effort
- Standardizes naming across team

**Lesson:** Always create importable artifacts, not just documentation

### 2. Don't Ignore Data References

**Mistake:** Initially focused on code, ignored data table loading

**Correction:** Recognized that entity type comes from data @ +0x26

**Lesson:** In data-driven architectures, data layout is as important as code

### 3. Batch Operations Reveal Architecture

**Discovery:** Batch reset @ 0x3C290 revealed:
- Context structure (92 bytes)
- Two-layer flag system (tactical vs status)
- External controller exists

**Lesson:** Look for batch/loop operations - they reveal data structures and calling patterns

### 4. Upper Bits vs Lower Bits

**Pattern:** Lower bits set once (mission states), upper bits set frequently (runtime status)

**Insight:** Bit field design separates **configuration** (set at start) from **state** (changes dynamically)

**Lesson:** Analyze bit fields by update frequency, not just by testing

---

## Estimated Completion

**Current:** 50%

**To reach 70%:** 
- Session 3: Find tactical state init + enemy type (2-3 hours)
- **Result:** Can trace complete AI flow from spawn to action

**To reach 80%:**
- Session 4: Mission controller + waypoint system (2 hours)
- **Result:** Understand high-level mission logic

**To reach 90%:**
- Session 5: Physics integration + remaining unknowns (2-3 hours)
- **Result:** Complete AI system documented

**Total remaining:** 6-8 hours to 90% completion

---

*Session completed: November 11, 2026*  
*Next session: Tactical state initialization + enemy aircraft identification*  
*Target: 70% completion*


