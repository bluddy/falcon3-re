# AI System Analysis - Session 1 Summary

**Date:** November 11, 2026  
**Duration:** ~2 hours  
**Progress:** 10% → 30% (initial survey + state machine decoded)  
**Status:** Foundation established, ready for deep analysis

---

## Session Goals

✅ Understand AI system architecture  
✅ Map behavior state machine  
✅ Decode behavior flags  
✅ Find target tracking logic  
⏳ Identify enemy aircraft entity type (partially - ruled out type 0x10)

---

## Major Discoveries

### 1. AI State Machine Architecture

**Location:** Behavior dispatcher sub_3CE92 @ 0x3CFAA-0x3D180

**Structure:** Flag-based state machine with 4-5 operational modes:

| State | Flag Bits | Purpose | Update Rate |
|-------|-----------|---------|-------------|
| **Combat** | +0x0Bh: 0x08 | Active engagement | ÷16 (slow) |
| **Cruise** | +0x0Bh: 0x04 | Medium altitude patrol | ÷8 (medium) |
| **Ground Attack** | +0x0Bh: 0x01 | Low-level attack | ÷4 (fast) |
| **Landing** | +0x0Bh: 0x02 | Approach/landing | ÷4 (fast) |
| **Special** | +0x0Bh: 0x10 | Unknown mission mode | Unknown |

**Key insight:** Bits 0x01-0x04 are **altitude/mission modes** (mutually exclusive), bit 0x08 adds **combat** on top.

### 2. Behavior Mirroring Mechanism

**Location:** 0x3D1C5-0x3D1D9

**Discovery:** AI entities **copy target's behavior flags** during tracking:
- Copies bits 2-7 from target's +0x0Ah
- Copies bit 7 from target's +0x0Bh

**Implication:** AI doesn't independently calculate pursuit maneuvers - it **synchronizes** with target's state. This explains how "pursuit" works: AI inherits target's heading/speed changes.

**This is MUCH simpler than proportional navigation!**

### 3. Speed-Based Audio System

**5 speed tiers** with different engine sounds:

| Speed Range | Volume | Sound Type |
|-------------|--------|------------|
| > 8000 | 30720 | Afterburner (loud) |
| 2000-8000 | 20480 | High cruise |
| 2000-2000 | 10240 | Medium cruise |
| 0-2000 | 5120 | Low speed |
| 0 (stopped) | 2560 | Idle |

**Field +0xC5h confirmed:** Speed magnitude (current speed)

### 4. Type 0x10 is NOT Enemy Aircraft

**Critical finding:** Type 0x10 entities **skip the state machine entirely** and jump directly to target tracking (@ 0x3D180).

**Revised hypothesis:** 
- Type 0x10 = **guided missiles/weapons** (always tracking targets)
- Enemy AI aircraft = likely **Type 0x16** or another type (uses state machine)

### 5. State Progression Values

**Fields +0x14h, +0x15h:** Used in ALL state checks, averaged together:
- Combat threshold: 75
- Medium altitude threshold: 50
- Combined with random/timer (funcs_4E5C0)

**Hypothesis:** Mission progress counters, waypoint distance, or time-in-state

### 6. Target Tracking Loop

**Sequence @ 0x3D180-0x3D1E4:**
1. Validate target (check flags [target+74h])
2. Call sub_2F6D0 (main loop integration)
3. Call sub_30882 TWICE (physics update)
4. Check altitude change (collision avoidance?)
5. Copy target's behavior flags

**Field +0x29h:** Target slot ID (0xFF = no target)

---

## Architecture Understanding

```
Entity System
   │
   ├─ Entity Type (+0x75h)
   │    ├─ 0x10: Guided weapons → Direct to tracking
   │    ├─ 0x16: Friendly aircraft → State machine + restrictions
   │    ├─ 0x33: Player aircraft → Full control
   │    └─ ???: Enemy AI → State machine (to find)
   │
   ├─ Behavior Flags
   │    ├─ +0x0Ah: High-level state (altitude zones, friendly fire)
   │    └─ +0x0Bh: AI operational mode (combat, cruise, attack, landing)
   │
   ├─ State Machine (0x3CFAA-0x3D180)
   │    ├─ Combat mode (bit 0x08): Threshold 75, custom speed
   │    ├─ Cruise mode (bit 0x04): Threshold 50, max speed, collision check
   │    ├─ Ground attack (bit 0x01): Fast updates, low altitude
   │    └─ Landing (bit 0x02): Collision checks, approach logic
   │
   └─ Target Tracking (0x3D180+)
        ├─ Target validation
        ├─ Guidance integration (main loop + physics)
        ├─ Altitude monitoring
        └─ Behavior mirroring (copy target flags)
```

---

## Key Entity Fields Confirmed

| Offset | Name | Type | Purpose | Confidence |
|--------|------|------|---------|------------|
| **+0x0Ah** | behavior_flags_1 | byte | High-level state control | 95% |
| **+0x0Bh** | behavior_flags_2 | byte | AI operational mode | 95% |
| **+0x14h** | state_value_1 | byte | Mission progress counter | 60% |
| **+0x15h** | state_value_2 | byte | Mission progress counter | 60% |
| **+0x16h** | default_speed | word | Base speed for entity | 80% |
| **+0x23h** | target_speed | word | Desired speed (AI output) | 95% |
| **+0x29h** | target_slot_id | byte | Locked target (0xFF=none) | 100% |
| **+0x56h** | altitude | word | Height above ground | 100% |
| **+0x60h** | max_speed | word | Maximum allowed speed | 75% |
| **+0x74h** | entity_flags | byte | Target validation bits | 90% |
| **+0x75h** | entity_type | byte | Type dispatch | 100% |
| **+0xC5h** | speed_magnitude | word | Current speed | 100% |

---

## Functions Identified

| Address | Name/Purpose | Size | Role | Priority |
|---------|--------------|------|------|----------|
| **0x3CE92** | Behavior dispatcher | 2580B | Master hub | DONE |
| **0x3CFAA-0x3D180** | State machine | ~726B | AI decision logic | DONE |
| **0x3D180-0x3D204** | Target tracking | ~132B | Pursuit/guidance | DONE (flow) |
| 0x30CB8 | State validator | ? | Random/timer checks | TO ANALYZE |
| 0x307A5 | Load target entity | ~50B | Target lookup | TO ANALYZE |
| 0x30882 | Physics update | 282B | Movement execution | TO ANALYZE |
| 0x327BE | Audio system | 499B | Engine sounds | LOW PRIORITY |
| 0x3252B | Behavior completion | ? | State cleanup | TO ANALYZE |

---

## Insights on 1991 AI Complexity

**Expected (modern flight sim):**
- ❌ Proportional navigation (lead pursuit)
- ❌ Energy management (speed/altitude tradeoffs)
- ❌ Defensive maneuvers (barrel roll, split-S)
- ❌ Threat assessment (target prioritization)

**Actual (Falcon 3.0):**
- ✅ Simple state machine (altitude/mission modes)
- ✅ Speed tier selection (5 levels)
- ✅ **Target mirroring** (copy target's behavior)
- ✅ Audio immersion (engine sounds scale with speed)

**Conclusion:** AI is **much simpler** than expected. "Pursuit" is achieved by **syncing behavior flags** with target, not calculating intercept vectors. This is computationally cheap and works well enough for 1991 gameplay.

---

## Documents Created

1. **AI_SYSTEM_INITIAL.md** (337 lines)
   - Investigation plan
   - Known architecture
   - Function priorities
   - Success metrics

2. **AI_BEHAVIOR_STATE_MACHINE.md** (526 lines)
   - Complete state machine analysis
   - Behavior flag decoding
   - Speed tiers and audio
   - Target tracking flow
   - Behavior mirroring mechanism

**Total:** 863 lines of documentation

---

## What We Still Don't Know (70%)

### Critical Gaps

1. **Which entity type is enemy AI?**
   - Ruled out: Type 0x10 (missiles)
   - Candidates: Type 0x16 (if not player wingmen) or unknown type
   - Need: Entity spawn analysis

2. **State transitions**
   - How do behavior flags CHANGE during flight?
   - What triggers state switches?
   - Where are +0x0Bh bits SET/CLEARED?

3. **State value meaning**
   - What do +0x14h, +0x15h represent?
   - How are they updated?
   - Do they relate to waypoints, time, or distance?

4. **Target selection**
   - How is +0x29h (target_slot_id) initially set?
   - Can AI switch targets mid-flight?
   - Target prioritization logic?

5. **Physics integration**
   - How does target_speed (+0x23h) translate to actual movement?
   - Where is heading adjusted to face target?
   - Altitude management (climb/dive)?

6. **Maneuver execution**
   - Where are actual control inputs applied?
   - Does "behavior mirroring" just copy heading directly?
   - Any independent maneuvering (evasion, combat)?

---

## Next Session Plan

### Phase 1: Find Enemy Aircraft Type (Priority: CRITICAL)

**Goal:** Identify which entity type uses the state machine

**Approach:**
- Search entity initialization code (found @ 0x3BB8F)
- Look for type assignments (writes to [entity+75h])
- Cross-reference with manual (enemy aircraft names)
- Differentiate friendly (0x16) vs enemy

**Expected time:** 30 minutes

### Phase 2: Map State Transitions (Priority: HIGH)

**Goal:** Find where behavior flags are SET

**Approach:**
- Search for: `mov [si+0Bh]`, `or [si+0Bh]`, `and [si+0Bh]`
- Trace state value modifications (+0x14h, +0x15h)
- Build state transition diagram

**Expected time:** 1 hour

### Phase 3: Analyze Physics Integration (Priority: HIGH)

**Goal:** Understand how AI decisions become movement

**Approach:**
- Extract sub_30882 (physics update, 282B)
- Find heading adjustment code
- See how target_speed affects acceleration

**Expected time:** 1 hour

### Phase 4: Target Selection (Priority: MEDIUM)

**Goal:** Understand target acquisition

**Approach:**
- Search for writes to [si+29h] (target_slot_id)
- Find target search/selection logic
- Understand target switching

**Expected time:** 45 minutes

---

## Progress Assessment

**Session 1: 30% complete** (from 10% initial)

**Breakdown:**
- Architecture: 80% (state machine understood)
- Behavior flags: 90% (meanings decoded)
- Target tracking: 50% (flow known, details missing)
- State transitions: 10% (structure only)
- Physics integration: 5% (entry points known)
- Target selection: 0% (not started)

**Estimated total time to 80%:** 3-4 more hours
- Session 2: State transitions + enemy type (2 hours) → 50%
- Session 3: Physics + target selection (2 hours) → 70%
- Session 4: Integration + testing (1 hour) → 80%

**Estimated total time to 90%:** 6-8 more hours (diminishing returns)

---

## Lessons Learned

### 1. Don't Assume Complexity

**Mistake:** Expected sophisticated guidance algorithms (proportional navigation, energy management)  
**Reality:** Simple behavior mirroring (copy target's flags)

**Lesson:** 1991 DOS game with limited CPU → simple solutions that "feel" right, not realistic simulations

### 2. Type Classifications Matter

**Early assumption:** Type 0x10 = enemy AI  
**Correction:** Type 0x10 = missiles (skip state machine)

**Lesson:** Trace type dispatch carefully before making assumptions

### 3. Large Functions are Hubs, Not Algorithms

**Pattern:** 
- sub_2F6D0 (1123B, 85 callees) = main game loop
- sub_3CE92 (2580B, 25 callees) = behavior dispatcher

**Lesson:** Functions >1KB are usually orchestrators, not single-purpose algorithms

### 4. Audio is a Clue

**Discovery:** Detailed speed-based audio tiers revealed:
- Speed field (+0xC5h)
- State update frequencies
- Operational mode purposes

**Lesson:** Don't ignore "cosmetic" code - it reveals internal states

---

## Files Modified

- `analysis/AI_SYSTEM_INITIAL.md` (new, 337 lines)
- `analysis/AI_BEHAVIOR_STATE_MACHINE.md` (new, 526 lines)
- `analysis/AI_SYSTEM_SESSION1_SUMMARY.md` (this file)

**Git commits:** 2
- 312a09f: AI System: Initial survey and planning document
- 4ebf80c: AI System: Behavior state machine analysis

---

## Comparison to Weapons System

| Aspect | Weapons (70%) | AI (30%) |
|--------|---------------|----------|
| **Duration** | 10 hours, 4 sessions | 2 hours, 1 session |
| **Key challenge** | Guidance algorithms not found | State machine decoded quickly |
| **Surprise** | Main loop misidentified | Behavior mirroring (not pursuit math) |
| **Complexity** | Higher than expected | Lower than expected |
| **Docs created** | 9 docs, ~3,750 lines | 2 docs, 863 lines |

**Insight:** AI analysis is progressing faster because:
- Weapons work laid foundation (entity system, behavior dispatcher)
- State machine is explicit (flag checks visible)
- Behavior is simpler (no hidden algorithms)

---

*Session completed: November 11, 2026*  
*Next session: State transitions + enemy aircraft identification*  
*Target: 50% completion*


