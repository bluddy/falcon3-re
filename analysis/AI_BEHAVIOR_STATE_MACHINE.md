# AI Behavior State Machine Analysis

**Date:** November 11, 2026  
**Function:** Behavior dispatcher sub_3CE92 @ 0x3CFAA-0x3D180  
**Focus:** AI state machine and behavior branching  
**Progress:** 30%

---

## Overview

The AI system uses a **flag-based state machine** with behavior stored in entity fields **+0x0Ah** and **+0x0Bh**. Different bit combinations trigger different AI behaviors (speed selection, altitude management, combat maneuvers).

---

## Behavior Flags

### Field +0x0Ah (Behavior Flags 1)

| Bit | Hex | Purpose | Evidence |
|-----|-----|---------|----------|
| 0 | 0x01 | Unknown | Referenced in init |
| 1 | 0x02 | Altitude/zone flag | Set during spawn if altitude check passes |
| 3 | 0x08 | High-speed mode | @ 0x3CFD0: if set + speed>8000, special audio |
| 7 | 0x80 | Friendly fire protection | @ 0x3EB60: multiplayer check |

### Field +0x0Bh (Behavior Flags 2) - **PRIMARY AI STATE**

| Bit | Hex | State Name (Hypothesis) | Evidence | Behavior |
|-----|-----|-------------------------|----------|----------|
| 0 | 0x01 | **Low-altitude / Ground attack** | @ 0x3D100: `test [si+0Bh], 3` | Landing approach or low-level flight |
| 1 | 0x02 | **Landing mode** | @ 0x3D100, 0x3D128, 0x3D0F0 | Final approach, checks altitude |
| 2 | 0x04 | **Medium-altitude / Cruise** | @ 0x3D08A | Normal flight, speed management |
| 3 | 0x08 | **Combat / Engagement** | @ 0x3D04E | Active combat, uses state fields +0x14h, +0x15h |
| 4 | 0x10 | **Special mission mode** | @ 0x3D048 | Unknown purpose |
| 7 | 0x80 | **Target state** (from target) | @ 0x3D1D7: copied from target's flags | Synchronized with target behavior |

**Key insight:** Bits 0-2 are **mutually exclusive altitude/mission modes**. Bit 3 adds **combat** on top. Bit 4 is special.

---

## State Machine Logic (0x3D03F-0x3D180)

### Entry: Type Dispatch

```asm
0x3D03F: mov    di, [si+6]              ; Load entity pointer
0x3D042: cmp    byte ptr [di+75h], 10h  ; Check if type 0x10
0x3D046: jz     loc_3D180               ; Type 0x10 → JUMP TO TARGET TRACKING

; Not type 0x10, continue with behavior state machine
```

**Critical:** **Type 0x10 entities SKIP the state machine** and go directly to target tracking @ 0x3D180!

**Hypothesis:** Type 0x10 = **missiles/weapons** (always tracking), NOT enemy aircraft

---

### State 1: Combat/Engagement Mode (Bit 0x08)

```asm
0x3D04E: test   byte ptr [si+0Bh], 8   ; Check combat mode bit
0x3D052: jz     loc_3D08A              ; Not in combat → check other states

; IN COMBAT MODE:
0x3D054: mov    ax, cs:funcs_4E5C0     ; Random seed or timer
0x3D058: mov    ah, [si+14h]           ; State value 1
0x3D05B: add    ah, 10h                ; Add offset 0x10
0x3D05E: mul    ah                     ; Multiply (randomness?)
0x3D060: mov    cl, 4
0x3D062: shr    ax, cl                 ; Divide by 16
0x3D064: call   sub_30CB8              ; State check function
0x3D067: or     ah, ah
0x3D069: jnz    loc_3D087              ; Failed check → exit

; Combat logic continues:
0x3D06B: mov    ax, [di+16h]           ; Load entity field +0x16h
0x3D06E: mov    [si+23h], ax           ; Set target_speed from +0x16h
0x3D071: mov    al, [si+14h]           ; state_value_1
0x3D074: add    al, [si+15h]           ; state_value_2
0x3D077: shr    al, 1                  ; Average = (val1 + val2) / 2
0x3D079: cmp    al, 4Bh                ; Compare with 75 (decimal)
0x3D07B: ja     loc_3D083              ; If > 75, finish behavior
```

**Purpose:** 
- Uses state fields **+0x14h** and **+0x15h** (unknown meaning, possibly threat level, distance, or mission phase)
- Sets **target_speed** from entity field **+0x16h** (desired combat speed)
- Has randomness/timing component (funcs_4E5C0, multiply, shift)
- Threshold check: average of state values vs 75

---

### State 2: Medium-Altitude Mode (Bit 0x04)

```asm
0x3D08A: test   byte ptr [si+0Bh], 4   ; Check medium-altitude bit
0x3D08E: jz     loc_3D100              ; Not medium → check low-altitude

; MEDIUM ALTITUDE MODE:
0x3D090: mov    ax, cs:funcs_4E5C0     ; Timer/random
0x3D094: mov    ah, [si+14h]           ; state_value_1
0x3D097: add    ah, 1Bh                ; Add offset 0x1B (27)
0x3D09A: mul    ah
0x3D09C: mov    cl, 3
0x3D09E: shr    ax, cl                 ; Divide by 8
0x3D0A1: call   sub_30CB8              ; State check
0x3D0A7: or     ax, ax
0x3D0A9: jnz    loc_3D087              ; Failed → exit

; Speed management:
0x3D0AB: mov    ax, [di+60h]           ; Load field +0x60h (max speed?)
0x3D0AE: cmp    ax, [si+23h]           ; Compare with current target_speed
0x3D0B1: jle    loc_3D0B6              ; If ≤, keep current
0x3D0B3: mov    [si+23h], ax           ; Else set target_speed = max

; State check:
0x3D0B6: call   unk_2E1C2              ; Unknown state function
0x3D0B9: or     ax, ax
0x3D0BB: jnz    loc_3D0C6              ; If non-zero, use custom speed
0x3D0BD: mov    di, [si+6]
0x3D0C0: mov    ax, [di+16h]           ; Else use default from +0x16h
0x3D0C3: mov    [si+23h], ax

; Audio check (engine sound?):
0x3D0C6: call   sub_327BE (loc_328A1)  ; Audio system
0x3D0C9: or     al, al
0x3D0CB: jz     loc_3D0E4
0x3D0CD: mov    cl, 0Eh                ; Sound ID 0x0E
0x3D0D1: call   sub_327BE (loc_3288C+2)
0x3D0D4: or     ax, ax
0x3D0D6: jz     loc_3D0E4
0x3D0D8: mov    bx, 31EBh              ; Audio params
0x3D0DB: mov    dx, 1E00h              ; 7680 decimal
0x3D0DE: mov    bp, 20h
0x3D0E1: call   sub_327BE (loc_32838)  ; Trigger sound

; Altitude check for state transition:
0x3D0E4: mov    al, [si+14h]           ; state_value_1
0x3D0E7: add    al, [si+15h]           ; state_value_2
0x3D0EA: shr    al, 1                  ; Average
0x3D0EC: cmp    al, 32h                ; Compare with 50 (decimal)
0x3D0EE: ja     loc_3D0FC              ; If > 50, finish
0x3D0F0: test   byte ptr [si+0Bh], 2   ; Check landing mode bit
0x3D0F4: jz     loc_3D0FC              ; Not landing, finish
0x3D0F6: call   loc_3D22A+1            ; Collision check?
0x3D0F9: jnb    loc_3D0FC              ; No collision, finish
0x3D0FB: retn                          ; Collision! Early exit
```

**Purpose:**
- Speed selection: chooses between max speed (+0x60h) or default (+0x16h)
- Audio trigger for engine sounds (constant 0x1E00 = 7680)
- State transition: if average < 50 AND landing mode, check collision
- If collision detected, abort (safety check)

**Field +0x60h:** Likely **max_speed** or **cruise_speed** parameter

---

### State 3: Low-Altitude / Ground Attack (Bits 0x01 or 0x02)

```asm
0x3D100: test   byte ptr [si+0Bh], 3   ; Check bits 0x01 or 0x02
0x3D104: jz     loc_3D180              ; Neither set → go to tracking

; LOW ALTITUDE MODE:
0x3D106: mov    ax, cs:funcs_4E5C0     ; Timer/random
0x3D10A: mov    ah, [si+14h]           ; state_value_1
0x3D10D: add    ah, 1Bh                ; Offset 0x1B (27)
0x3D110: mul    ah
0x3D112: mov    cl, 2
0x3D114: shr    ax, cl                 ; Divide by 4 (faster updates?)
0x3D117: call   sub_30CB8              ; State check
0x3D11D: or     ax, ax
0x3D11F: jnz    loc_3D180              ; Failed → tracking

; Audio check:
0x3D121: call   sub_327BE (loc_328A1)
0x3D124: or     al, al
0x3D126: jz     loc_3D15B

; Landing mode sub-check:
0x3D128: test   byte ptr [si+0Bh], 2   ; Bit 0x02 = landing
0x3D12C: jnz    loc_3D144              ; Landing → different path

; Ground attack audio:
0x3D12E: mov    cl, 2                  ; Sound ID 0x02
0x3D131: call   sub_327BE (loc_3288C+2)
0x3D134: or     ax, ax
0x3D136: jz     loc_3D15B
0x3D138: mov    bx, 3165h              ; Audio params
0x3D13B: mov    dx, 5000h              ; 20480 decimal
0x3D13E: mov    bp, 21h
0x3D141: call   sub_327BE (loc_32838)
```

**Purpose:**
- Fastest state update (divide by 4 vs 8 for medium, 16 for combat)
- Two sub-modes: **landing** (bit 0x02) or **ground attack** (bit 0x01)
- Different audio for ground attack (0x5000 vs 0x1E00)

---

## Speed-Based Branching (Before State Machine)

### High-Speed Branch (Speed > 8000, Bit 0x08 set)

```asm
0x3CFC8: cmp    word ptr [di+0C5h], 1F40h  ; Compare speed with 8000
0x3CFCE: jbe    loc_3CFF4                  ; ≤ 8000 → normal branch
0x3CFD0: test   byte ptr [si+0Ah], 8       ; Test high-speed flag
0x3CFD4: jz     loc_3D039                  ; Not set → skip

; HIGH SPEED MODE:
0x3CFD6: mov    ax, cs:funcs_4E5C0
0x3CFDA: mov    cl, 6
0x3CFDC: shl    ax, cl                     ; Multiply by 64
0x3CFDE: call   sub_30CB8                  ; Check
0x3CFE1: or     dx, dx
0x3CFE3: jnz    loc_3D039                  ; Failed → skip
0x3CFE5: mov    bx, 3013h                  ; Audio params
0x3CFE8: mov    cl, 0
0x3CFEC: mov    dx, 7800h                  ; 30720 decimal (LOUD!)
0x3CFEF: mov    bp, 1Eh
0x3CFF2: jmp    loc_3D036                  ; Trigger audio
```

**Purpose:** Afterburner/high-speed audio (volume 30720 vs normal 7680)

### Normal Speed Branch (Speed ≤ 8000)

```asm
0x3CFF4: call   sub_327BE (loc_328BD+4)    ; Audio check
0x3CFF7: or     ax, ax
0x3CFF9: jz     loc_3D039                  ; No audio → skip

; Three speed tiers with different audio params:

; Tier 1: Speed > 8000 (can't reach here, see above)

; Tier 2: 2000 < Speed ≤ 8000
0x3CFFB: mov    bx, 304Ch
0x3CFFE: mov    dx, 5000h                  ; Volume 20480
0x3D001: mov    bp, 35h
0x3D004: cmp    word ptr [di+0C5h], 1F40h
0x3D00A: ja     loc_3D036                  ; > 8000 → use these params

; Tier 3: 2000 < Speed ≤ 2000
0x3D00C: mov    bx, 3065h
0x3D00F: mov    dx, 2800h                  ; Volume 10240
0x3D012: mov    bp, 37h
0x3D015: cmp    word ptr [di+0C5h], 7D0h
0x3D01B: ja     loc_3D036                  ; > 2000 → use these params

; Tier 4: 0 < Speed ≤ 2000
0x3D01D: mov    bx, 307Fh
0x3D020: mov    dx, 1400h                  ; Volume 5120
0x3D023: mov    bp, 38h
0x3D026: cmp    word ptr [di+0C5h], 0
0x3D02B: ja     loc_3D036                  ; > 0 → use these params

; Tier 5: Speed = 0 (stopped)
0x3D02D: mov    bx, 3259h
0x3D030: mov    dx, 0A00h                  ; Volume 2560 (idle)
0x3D033: mov    bp, 2Dh

0x3D036: call   sub_327BE (loc_32838)      ; Trigger audio with params
```

**Audio Tiers:**

| Speed Range | Volume (hex) | Volume (dec) | Sound Type | BP |
|-------------|--------------|--------------|------------|-----|
| **> 8000** (high-speed flag) | 0x7800 | 30720 | Afterburner | 0x1E |
| **2000-8000** | 0x5000 | 20480 | High cruise | 0x35 |
| **2000-2000** | 0x2800 | 10240 | Med cruise | 0x37 |
| **0-2000** | 0x1400 | 5120 | Low speed | 0x38 |
| **0** (stopped) | 0x0A00 | 2560 | Idle | 0x2D |

**Field +0xC5h:** Confirmed **speed magnitude** (current speed)

---

## Target Tracking Section (0x3D180+)

Type 0x10 and all state-machine-finished entities jump here.

```asm
0x3D180: cmp    byte ptr [si+29h], 0FFh    ; Check target_slot_id
0x3D184: jz     loc_3D204                  ; No target → visibility update

; HAS TARGET:
0x3D186: call   sub_307A5                  ; Load target entity
0x3D189: mov    bx, [di+6]                 ; Target entity pointer → BX
0x3D18C: test   byte ptr [bx+74h], 1       ; Check target flag bit 0
0x3D190: jz     loc_3D198                  ; Not set → check more
0x3D192: test   byte ptr [bx+74h], 38h     ; Check bits 3, 4, 5
0x3D196: jz     loc_3D1A8                  ; None set → TARGET VALID

; TARGET INVALID:
0x3D198: mov    byte ptr [si+29h], 0FFh    ; Clear target_slot_id
0x3D19C: mov    word ptr [si+1Ah], 0       ; Clear related fields
0x3D1A1: mov    word ptr [si+1Ch], 0
0x3D1A6: jmp    loc_3D1C5                  ; Continue without target

; TARGET VALID - COPY TARGET STATE:
0x3D1A8: mov    ax, [di+4Ah]               ; Save field +0x4Ah
0x3D1AB: push   ax
0x3D1AC: call   sub_307A5                  ; Reload target (why?)
0x3D1AF: call   sub_2F6D0 (loc_2F6D6)      ; *** MAIN LOOP CALL (guidance?) ***
0x3D1B2: call   sub_30882+2                ; Physics update
0x3D1B5: call   sub_30882 (loc_308E5+2)    ; Physics update (2nd call)
0x3D1B8: pop    ax                         ; Restore saved value
0x3D1B9: mov    di, [si+6]
0x3D1BC: cmp    [di+56h], ax               ; Compare altitude with saved
0x3D1BF: jge    loc_3D1C5                  ; altitude ≥ saved → continue
0x3D1C1: call   sub_2F6D0 (loc_2F784+4)    ; Altitude loss → correction call

; COPY BEHAVIOR FLAGS FROM TARGET:
0x3D1C5: mov    di, [si+6]                 ; Load AI entity pointer
0x3D1C8: mov    al, [di+0Ah]               ; Get target's behavior flags 1
0x3D1CB: and    al, 0FCh                   ; Mask out bits 0, 1
0x3D1CD: and    byte ptr [si+0Ah], 3       ; Keep only AI's bits 0, 1
0x3D1D1: or     [si+0Ah], al               ; Merge target's bits 2-7
0x3D1D4: mov    al, [di+0Bh]               ; Get target's behavior flags 2
0x3D1D7: and    al, 80h                    ; Keep only bit 7
0x3D1D9: or     [si+0Bh], al               ; Set AI's bit 7 from target
```

**This is the AI tracking logic!**

**Key operations:**
1. **Target validation:** Checks target entity flags [bx+74h], bits 0, 3, 4, 5
2. **Guidance calls:** sub_2F6D0 (main loop integration) + sub_30882 (physics, called TWICE)
3. **Altitude monitoring:** Compares current altitude [di+56h] with saved value, corrects if dropping
4. **Behavior synchronization:** Copies target's behavior flags to AI entity
   - Copies bits 2-7 from target's +0x0Ah
   - Copies bit 7 from target's +0x0Bh

**Hypothesis:** AI mirrors target's behavior state to match their maneuvers!

---

## State Values (+0x14h, +0x15h)

Used in ALL state checks:
- Combat mode: `(val1 + val2) / 2` compared to 75
- Medium altitude: `(val1 + val2) / 2` compared to 50
- Combined with timer/random for state checks

**Hypothesis:** These are **mission progress** or **tactical state** counters
- Incremented/decremented during flight
- Thresholds trigger state transitions
- Combined with randomness for unpredictability

---

## AI Decision Flow

```
1. Check entity type:
   - Type 0x10 → SKIP to tracking (missiles/bombs)
   - Other types → State machine

2. State machine (checks +0x0Bh flags):
   - Bit 0x10 set → Special mode
   - Bit 0x08 set → Combat mode (threshold 75)
   - Bit 0x04 set → Medium altitude (threshold 50, collision check)
   - Bits 0x03 set → Low altitude/ground attack (fastest updates)
   - None → Fall through to tracking

3. Each state:
   - Random/timer check (sub_30CB8)
   - Speed selection (target_speed @ +0x23h)
   - Audio trigger (engine sounds, varies by speed)
   - State threshold check (state values vs thresholds)

4. Tracking (all paths lead here):
   - Validate target (flags @ [target+74h])
   - Guidance (sub_2F6D0, sub_30882)
   - Altitude correction
   - Behavior sync (copy target's flags)
```

---

## Key Findings

### 1. AI is NOT Complex

**No advanced tactics found:**
- ❌ No pursuit curves (lead calculation, proportional navigation)
- ❌ No evasion maneuvers (barrel roll, split-S, defensive spiral)
- ❌ No threat assessment (prioritize targets)
- ✅ Simple state machine (4-5 states based on altitude/mission)
- ✅ Speed management (5 speed tiers)
- ✅ Target mirroring (copy target's behavior)

**This is 1991-era simple AI:**
- Rule-based state selection
- Audio cues for immersion
- Target following (not true pursuit)

### 2. Type 0x10 is NOT Enemy Aircraft

Type 0x10 **skips the state machine** and goes directly to tracking.

**Hypothesis:** Type 0x10 = **guided weapons** (missiles that always track)

**Enemy aircraft would need state machine** → likely **Type 0x16** or another type

### 3. Behavior Flags are Altitude/Mission Modes

**+0x0Bh** bits represent **operational mode:**
- 0x01 = Ground attack
- 0x02 = Landing approach
- 0x04 = Cruise/patrol
- 0x08 = Combat engagement
- 0x10 = Special mission

**NOT tactical maneuvers** (turn, climb, dive) - those happen in physics layer

### 4. AI Mirrors Target Behavior

**@ 0x3D1C8-0x3D1D9:** AI copies target's behavior flags

**Implication:** AI doesn't independently decide maneuvers - it **matches** the target's state

**This explains "pursuit":** AI entity inherits target's heading/speed changes through flag sync

### 5. Speed Thresholds

| Threshold | Dec | Purpose |
|-----------|-----|---------|
| 0x1F40 | 8000 | Afterburner threshold |
| 0x7D0 | 2000 | High/med speed boundary |
| 0 | 0 | Stopped check |

**Speed tiers affect:**
- Audio volume/type
- State update frequency (combat=÷16, medium=÷8, low=÷4)

### 6. State Values (+0x14h, +0x15h) are Progression Counters

- Used in **every state check**
- Thresholds: 75 (combat), 50 (medium altitude)
- Averaged together: `(val1 + val2) / 2`

**Hypothesis:** Mission waypoint progress, time in state, or distance to target

---

## Unknown Functions

| Function | Purpose | Evidence |
|----------|---------|----------|
| **sub_30CB8** | State validation/timer | Called in every state with random/timer input |
| **sub_307A5** | Load target entity | Returns target pointer in DI |
| **sub_30882** | Physics update | Called twice during tracking |
| **sub_327BE** | Audio system | Multiple entry points for different sounds |
| **sub_3252B** | Behavior completion | Called at end of state branches |
| **unk_2E1C2** | Speed/state check | Returns speed override or 0 |

---

## Next Steps

### Phase 1: Identify Enemy Aircraft Type
- Search for entity type initialization
- Find which type uses state machine (NOT 0x10)
- Compare type 0x16 vs others

### Phase 2: Map State Transitions
- Find where behavior flags are SET (not just tested)
- Trace state value (+0x14h, +0x15h) modifications
- Build state transition diagram

### Phase 3: Understand State Values
- Trace where +0x14h, +0x15h are written
- Find increment/decrement logic
- Determine what they represent (time, distance, mission phase)

### Phase 4: Analyze sub_30882 (Physics)
- Extract physics update function
- See how target_speed (+0x23h) affects movement
- Find heading adjustment logic

### Phase 5: Target Selection
- Find where target_slot_id (+0x29h) is SET
- Understand target prioritization
- See if AI can switch targets

---

## Revised Progress Estimate

**Current: 30%**

What we know:
- ✅ State machine structure (4-5 states)
- ✅ Behavior flag meanings (altitude/mission modes)
- ✅ Speed-based branching
- ✅ Target tracking flow
- ✅ Behavior mirroring mechanism

What we don't know:
- ❌ Which entity type is enemy aircraft
- ❌ State transition logic (how flags change)
- ❌ State value meaning
- ❌ Target selection algorithm
- ❌ Actual maneuver execution (heading/altitude changes)

**80% achievable with:**
- State transition mapping
- Target selection analysis
- Physics integration (sub_30882)

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: State machine mapped, behavior flags decoded, AI architecture understood*


