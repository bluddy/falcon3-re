# AI State Transitions - Behavior Flag Modifications

**Date:** November 11, 2026  
**Purpose:** Map all behavior flag changes to understand AI state machine transitions  
**Progress:** 50%

---

## Behavior Flag Bits (Recap)

### Field +0x0Bh (Primary AI State)

| Bit | Hex | State | Meaning |
|-----|-----|-------|---------|
| 0 | 0x01 | Ground attack | Low-altitude attack mode |
| 1 | 0x02 | Landing | Landing approach |
| 2 | 0x04 | Cruise | Medium-altitude patrol |
| 3 | 0x08 | Combat | Active engagement |
| 4 | 0x10 | Special | Unknown mission mode |
| 5 | 0x20 | Bit 0x20 | (to be determined) |
| 6 | 0x40 | Bit 0x40 | (to be determined) |
| 7 | 0x80 | Target sync | Copied from target |

---

## State Initialization

### Entity Spawn (@ 0x3BCF1)

```asm
; Clear all behavior flags on spawn
0x3BCF1: mov    byte ptr [si+0Bh], 0      ; *** INIT: flags = 0 ***
0x3BCF5: mov    byte ptr [si+39h], 0
0x3BCF9: mov    word ptr [si+8], 0
0x3BCFE: mov    word ptr [si+0Ch], 0
0x3BD03: mov    byte ptr [si+0Eh], 0FFh
0x3BD07: mov    byte ptr [si+0Fh], 0FFh
0x3BD0B: mov    byte ptr [si+10h], 0FFh
0x3BD0F: mov    byte ptr [si+11h], 0FFh
0x3BD13: mov    word ptr [si+18h], 0FFFFh
0x3BD18: mov    byte ptr [si+29h], 0FFh   ; No target
```

**Purpose:** All entities start with **NO behavior flags set** (idle/default state)

---

## State Setting Operations

### 1. Set Bit 0x40 (@ 0x42088)

**Location:** sub_31EBF @ 0x42088

```asm
0x4207C: call   locret_30CB7              ; Load entity
0x4207F: mov    si, di
0x42081: call   sub_327BE (loc_328BD+4)   ; Audio check?
0x42084: or     ax, ax
0x42086: jz     loc_3206A+4               ; Skip if audio check failed
0x42088: or     byte ptr [si+0Bh], 40h    ; *** SET BIT 0x40 ***
```

**Trigger:** Audio check succeeded (0x327BE returned non-zero)

**Also set at 0x42133:**
```asm
0x42122: and    byte ptr [si+0Bh], 0DFh   ; Clear bit 0x20
0x4212D: mov    dx, 0A00h                 ; Audio param
0x42130: call   loc_32838                 ; Trigger audio
0x42133: or     byte ptr [si+0Bh], 40h    ; *** SET BIT 0x40 ***
```

**Also set at 0x3D455:**
```asm
; In behavior dispatcher (sub_3CE92)
0x3D450: call   loc_3DED9                 ; Weapon spawn gate
0x3D453: jnb    loc_3D459                 ; Skip if spawn failed
0x3D455: or     byte ptr [si+0Bh], 40h    ; *** SET BIT 0x40 ***
```

**Hypothesis:** Bit 0x40 = **Weapon armed / Fire enabled**
- Set after weapon spawn succeeds
- Set after audio confirmation
- Enables firing capability

### 2. Clear Bit 0x40 (@ 0x4218F, 0x421DA)

**Location:** sub_31EBF / hud_metric_rows_draw @ 0x4218F

```asm
0x4218B: or     ax, ax
0x4218D: jz     loc_32178+4
0x4218F: and    byte ptr [si+0Bh], 0BFh   ; *** CLEAR BIT 0x40 (mask ~0x40) ***
```

**Also cleared at 0x421DA:**
```asm
0x421D4: mov    bp, 1Dh
0x421D7: mov    dx, 1E00h
0x421DA: and    byte ptr [si+0Bh], 0BFh   ; *** CLEAR BIT 0x40 ***
```

**Trigger:** Some check failed (AX == 0)

**Hypothesis:** Disarm weapon / Fire disabled
- Cleared when condition no longer met
- Safety check

### 3. Clear Bit 0x20 (@ 0x42122)

```asm
0x4211C: mov    bx, 2EC3h
0x4211F: mov    bp, 19h
0x42122: and    byte ptr [si+0Bh], 0DFh   ; *** CLEAR BIT 0x20 (mask ~0x20) ***
0x42126: mov    cl, 0Ah                   ; Audio ID
0x4212D: mov    dx, 0A00h                 ; Audio param
0x42130: call   loc_32838                 ; Trigger audio
```

**Trigger:** Specific audio/state condition

**Hypothesis:** Bit 0x20 = some temporary state that needs clearing

### 4. Set Bits 0x60 (@ 0x42253)

**Location:** sub_321DD @ 0x42253

```asm
0x4224D: cmp    word ptr [si+0Ch], 1      ; Check field +0x0Ch
0x42251: jnz    loc_32265+3
0x42253: or     byte ptr [si+0Bh], 60h    ; *** SET BITS 0x20 + 0x40 ***
```

**Trigger:** Field +0x0Ch == 1 (some state counter?)

**Hypothesis:** Activates both bit 0x20 and 0x40 together
- Combined state: armed + special mode?

### 5. Copy Target's Bit 0x80 (@ 0x3D1D9)

**Location:** Behavior dispatcher sub_3CE92 @ 0x3D1D4-0x3D1D9

```asm
; During target tracking
0x3D1C8: mov    al, [di+0Ah]              ; Get target's flags 1
0x3D1CB: and    al, 0FCh                  ; Mask bits 2-7 only
0x3D1CD: and    byte ptr [si+0Ah], 3      ; Keep AI's bits 0-1
0x3D1D1: or     [si+0Ah], al              ; Merge target flags

0x3D1D4: mov    al, [di+0Bh]              ; Get target's flags 2
0x3D1D7: and    al, 80h                   ; Keep ONLY bit 0x80
0x3D1D9: or     [si+0Bh], al              ; *** COPY BIT 0x80 FROM TARGET ***
```

**Trigger:** Active target tracking

**Hypothesis:** Bit 0x80 = **Target's special state** (synced behavior)
- Allows AI to mirror target's high-level state
- Part of behavior mirroring mechanism

### 6. Clear Lower Bits 0-4 (@ 0x3C290)

**Location:** sub_3C1BD @ 0x3C290

```asm
0x3C28A: mov    si, 386Fh                 ; Entity array offset?
0x3C28D: mov    cx, 10h                   ; Loop counter: 16 entities
0x3C290: and    byte ptr [si+0Bh], 0E0h   ; *** KEEP ONLY BITS 5-7 (clear 0-4) ***
0x3C294: add    si, 5Ch                   ; Next entity (stride 0x5C = 92 bytes)
0x3C297: nop
; (loop continues)
```

**Trigger:** Batch operation on 16 entities

**Hypothesis:** **Mass state reset** - clear tactical states (bits 0-4: combat, cruise, ground attack, landing, special) while preserving high-level flags (bits 5-7)

**Context stride:** 0x5C (92 bytes) between entities suggests this is a **context structure**, not full entity

---

## State Reading (Tests)

### Test Bit 0x40 (Multiple Locations)

```asm
; @ 0x420BC
0x420BC: test   byte ptr [si+0Bh], 40h
0x420C0: jnz    loc_320CA                 ; Branch if bit 0x40 SET

; @ 0x420FA
0x420FA: test   byte ptr [si+0Bh], 40h
0x420FE: jz     loc_3212B+2               ; Branch if bit 0x40 CLEAR
```

**Usage:** Branching based on "armed" state

### Test Bit 0x20 (@ 0x420B2)

```asm
0x420B2: test   byte ptr [si+0Bh], 20h
0x420B6: jnz    loc_32110+4               ; Branch if bit 0x20 SET
```

**Usage:** Affects audio/behavior path selection

---

## Bit Meanings (Updated)

| Bit | Hex | State | Meaning | Set By | Cleared By |
|-----|-----|-------|---------|--------|------------|
| 0 | 0x01 | Ground attack | Low-altitude | (not found yet) | State reset @ 0x3C290 |
| 1 | 0x02 | Landing | Approach | (not found yet) | State reset @ 0x3C290 |
| 2 | 0x04 | Cruise | Medium alt | (not found yet) | State reset @ 0x3C290 |
| 3 | 0x08 | Combat | Engagement | (not found yet) | State reset @ 0x3C290 |
| 4 | 0x10 | Special | Mission mode | (not found yet) | State reset @ 0x3C290 |
| 5 | 0x20 | **Bit 0x20** | **Temp state?** | @ 0x42253 (with 0x60) | @ 0x42122 |
| 6 | 0x40 | **Armed** | **Weapon ready** | @ 0x42088, 0x42133, 0x3D455 | @ 0x4218F, 0x421DA |
| 7 | 0x80 | Target sync | Mirrored from target | @ 0x3D1D9 (copy) | State reset @ 0x3C290 |

---

## State Transition Patterns

### Pattern 1: Weapon Firing Sequence

```
1. Weapon spawn requested
2. Call weapon spawn gate (sub_3DC55 @ loc_3DED9)
3. If spawn succeeds:
   → Set bit 0x40 (armed) @ 0x3D455
4. Fire weapon
5. Condition check fails:
   → Clear bit 0x40 (disarmed) @ 0x4218F
```

**Purpose:** Enable and disable weapon firing capability

### Pattern 2: Audio-Triggered State

```
1. Audio check (sub_327BE @ loc_328BD+4)
2. If audio active (AX != 0):
   → Set bit 0x40 @ 0x42088
3. Later condition check:
   → Clear bit 0x40 @ 0x4218F if needed
```

**Purpose:** Audio feedback controls state (lock tone, engine sound)

### Pattern 3: Combined State Activation

```
1. Check field +0x0Ch == 1
2. If true:
   → Set bits 0x60 (0x20 + 0x40) @ 0x42253
```

**Purpose:** Activate compound state (armed + something)

### Pattern 4: Target Synchronization

```
1. Has valid target
2. Load target entity
3. Copy target's bit 0x80 → AI's bit 0x80 @ 0x3D1D9
4. AI behavior now synced with target
```

**Purpose:** Behavior mirroring (follow target's state)

### Pattern 5: Batch State Reset

```
1. Iterate through 16 entities
2. For each entity:
   → Clear bits 0-4 (tactical states)
   → Keep bits 5-7 (high-level states)
```

**Purpose:** Reset tactical AI states while preserving armed/sync flags

**Trigger:** Mission phase change? Waypoint reached?

---

## Missing: Tactical State Assignments

**Problem:** We found where bits 0x20, 0x40, 0x80 are SET/CLEARED, but **NOT where bits 0-4 are initially SET** (combat, cruise, ground attack, landing, special modes).

**Hypotheses:**

### Hypothesis A: Set from Data Tables
```asm
; Somewhere in entity init (not found yet)
; Load mission data
mov    al, [mission_data + some_offset]
and    al, 1Fh                          ; Mask bits 0-4
mov    [si+0Bh], al                     ; Set tactical state
```

**Evidence:**
- Type comes from data tables (@ offset +0x26)
- States might also come from data (waypoint actions)

### Hypothesis B: Set Based on Waypoint Actions
Manual mentions waypoint actions:
- CAP (Combat Air Patrol)
- CAS (Close Air Support)
- INTERCEPT
- LOITER
- S AND D (Search and Destroy)

These could map to behavior flags:
- CAP → bit 0x04 (cruise)
- CAS → bit 0x01 (ground attack)
- INTERCEPT → bit 0x08 (combat)
- LOITER → bit 0x04 (cruise)

### Hypothesis C: Set by Mission State Machine

**Location:** Unknown higher-level mission controller

```
Mission Controller
   ↓
Sets behavior flags based on:
   - Current waypoint action
   - Mission phase
   - Player proximity
   - Threat level
   ↓
Entity behavior dispatcher reads flags
```

---

## Field +0x0Ch (Related to States)

**Referenced at:**
- 0x4224D: `cmp word ptr [si+0Ch], 1` → sets bits 0x60
- 0x3BCFE: `mov word ptr [si+0Ch], 0` → initialized to 0
- 0x4209D: `cmp word ptr [si+0Ch], 4` → check for value 4
- 0x420A5: `cmp word ptr [si+0Ch], 1` → check for value 1
- 0x420D2: `cmp word ptr [si+0Ch], 2` → check for value 2

**Values observed:**
- 0: Initial state
- 1: Triggers bits 0x60 set
- 2: Different behavior branch
- 4: Exit condition

**Hypothesis:** Field +0x0Ch = **Mission phase** or **waypoint progress**
- Different values trigger different behavior flag combinations
- State machine counter

---

## Next Investigation Priorities

### Priority 1: Find Tactical State Initialization

**Goal:** Find where bits 0-4 (combat, cruise, ground attack, landing, special) are SET

**Search for:**
1. Writes to [si+0Bh] with values 0x01-0x1F
2. Waypoint action processing code
3. Mission data loading (near entity init)
4. References to field +0x0Ch that modify +0x0Bh

### Priority 2: Map Field +0x0Ch Values

**Goal:** Understand mission phase counter

**Approach:**
1. Find all reads/writes to [si+0Ch]
2. Map values 0, 1, 2, 4 to mission phases
3. See if it triggers behavior flag changes

### Priority 3: Weapon System Integration

**Goal:** Confirm bit 0x40 = armed state

**Approach:**
1. Trace weapon spawn gate (sub_3DC55) success path
2. Find what triggers bit 0x40 clear
3. Map to manual descriptions (weapon lock, in parameters)

### Priority 4: Audio System Connection

**Goal:** Understand why audio controls state flags

**Approach:**
1. Analyze sub_327BE (audio system, 499B)
2. See what audio IDs map to (lock tone, engine, warnings)
3. Understand audio→state feedback loop

---

## For IDA Synchronization

### Additional Annotations

```python
# Behavior flag bit definitions
FLAG_0BH_GROUND_ATTACK = 0x01
FLAG_0BH_LANDING       = 0x02
FLAG_0BH_CRUISE        = 0x04
FLAG_0BH_COMBAT        = 0x08
FLAG_0BH_SPECIAL       = 0x10
FLAG_0BH_BIT20         = 0x20  # TBD
FLAG_0BH_ARMED         = 0x40  # Weapon ready
FLAG_0BH_TARGET_SYNC   = 0x80  # Copied from target

# State transition addresses
0x3BCF1  # entity_behavior_init: set flags = 0
0x42088  # set_armed_flag: or [si+0Bh], 0x40
0x4218F  # clear_armed_flag: and [si+0Bh], 0xBF
0x42122  # clear_bit20: and [si+0Bh], 0xDF
0x42253  # set_bits_60: or [si+0Bh], 0x60
0x3D1D9  # copy_target_bit80: or [si+0Bh], al
0x3C290  # reset_tactical_states: and [si+0Bh], 0xE0
```

---

## Summary

### Discovered (50% of state machine)

✅ **Bit 0x40 = Armed/Weapon Ready**
- Set when weapon spawn succeeds
- Set when audio check passes
- Cleared when condition fails

✅ **Bit 0x80 = Target Sync**
- Copied from target during tracking
- Part of behavior mirroring

✅ **Bit 0x20 = Temporary State**
- Set with bit 0x40 (combined 0x60)
- Cleared before re-arming

✅ **Bits 0-4 Reset Pattern**
- Mass cleared by batch operation
- Preserves high-level flags 5-7

✅ **State Machine Structure**
- Lower bits (0-4): Tactical states (combat, cruise, etc.)
- Upper bits (5-7): Status flags (armed, temp, synced)

### Unknown (50% remaining)

❌ **Where tactical bits 0-4 are SET**
- Combat mode (0x08)
- Cruise mode (0x04)
- Ground attack (0x01)
- Landing (0x02)
- Special (0x10)

❌ **Field +0x0Ch purpose**
- Mission phase counter?
- Values: 0, 1, 2, 4 observed
- Triggers state changes

❌ **Bit 0x20 exact meaning**
- Related to arming sequence
- Temporary state

❌ **Higher-level controller**
- What sets initial tactical states?
- Mission controller? Waypoint system?

---

*Analysis: November 11, 2026*  
*Status: 50% state machine transitions mapped, tactical state initialization still unknown*


