# AI System Analysis - Initial Survey

**Date:** November 11, 2026  
**Session:** AI System - Session 1  
**Progress:** 10% (initial survey and planning)

---

## Goal

Reverse engineer the enemy AI behavior system in Falcon 3.0 to understand:
- How enemy aircraft make combat decisions
- State machines and behavior modes
- Target selection and engagement logic
- Formation flying and tactics
- Evasion and defensive maneuvers

---

## What We Know From Previous Sessions

### Entity Types (from Behavior Dispatcher Analysis)

| Type | Decimal | Hypothesis | Evidence |
|------|---------|------------|----------|
| **0x10** | **16** | **Enemy AI aircraft?** | Special handler in behavior dispatcher |
| **0x16** | **22** | **Friendly aircraft** | Spawn restrictions, no-friendly-fire checks |
| **0x33** | **51** | **Player aircraft** | Most complex, target search, weapon spawning |
| **0x12** | **18** | **AIM-9 Sidewinder** | Weapon type (not entity type) |
| **0x13** | **19** | **AIM-120 AMRAAM** | Weapon type (not entity type) |

**Note:** There are TWO classification systems:
1. **Entity type** (`[entity+0x75]`) - Behavioral class (0x10, 0x16, 0x33)
2. **Weapon init type** (used in sub_4C19E) - Weapon parameters (0x12, 0x13)

### Master Behavior Dispatcher: sub_3CE92

**Location:** 0x3CE92  
**Size:** 2,580 bytes (HUGE!)  
**Callees:** 25 functions  
**Purpose:** Central hub for ALL entity AI, physics, weapons, collision

**Key sections:**
1. Tile boundary wrapping (0x3CE92-0x3CEDC)
2. Spatial tile updates (0x3CEF4-0x3CF9C)
3. Type 0x33 special handler (0x3CF9D-0x3CFA9)
4. General AI/behavior (0x3CFAA-0x3D039)
5. Type 0x10 special handler (0x3D03F-0x3D087)
6. Behavior branching (0x3D08A-0x3D17F)
7. **Target tracking** (0x3D180-0x3D203) ← Key for AI!
8. Visibility/projection (0x3D204-0x3D229)
9. Collision detection (0x3D22A-0x3D318)

### AI-Relevant Entity Fields

| Offset | Name | Type | Purpose |
|--------|------|------|---------|
| **+0x0Ah** | **behavior_flags_1** | byte | AI state bits (0x01, 0x08, etc.) |
| **+0x0Bh** | **behavior_flags_2** | byte | AI state bits (0x01-0x40) |
| **+0x29h** | **target_slot_id** | byte | Locked target (0xFF = no target) |
| **+0x75h** | **entity_type** | byte | Type dispatch (0x10, 0x16, 0x33) |
| +0x0Ch | heading_current | word | Current orientation |
| +0x1Dh | heading_target | word | Desired orientation |
| +0x11h | countdown_timer | byte | Decremented each frame |
| +0x23h | target_speed | word | Desired speed |
| +0x2Eh | velocity_state | word | Acceleration/velocity |
| +0x56h | altitude | word | Height above ground |
| +0x74h | entity_flags | byte | Status bits for target validation |

### Target Tracking Sequence (0x3D180-0x3D203)

```asm
1. Check [si+29h] == 0xFF (no target)
2. If has target, load target entity (sub_307A5)
3. Validate target flags [bx+74h] (bits 0, 3, 4, 5)
4. If invalid, clear target: [si+29h] = 0xFF
5. If valid:
   - Copy target state to AI entity
   - Call sub_2F6D0 (target pursuit/guidance)
   - Call sub_30882 (physics update)
   - Check altitude change
   - Apply configuration delta
```

**This is the core AI tracking loop!**

### Behavior Flags

**Flag byte +0x0Bh** (from behavior dispatcher):
- **Bit 0x04:** Medium-altitude behavior
- **Bit 0x03:** Low-altitude / ground attack behavior  
- **Bit 0x02:** Landing/runway approach?
- **Bit 0x01:** Unknown

Different flag combinations trigger different AI branches:
- Different speed thresholds
- Different target acquisition logic
- Different physics constants

---

## AI System Architecture (Hypothesis)

```
┌─────────────────────────────────────────┐
│   Master Behavior Dispatcher            │
│   sub_3CE92 (2580 bytes)                │
│                                          │
│   ┌─────────────────────────────────┐   │
│   │  Entity Type Dispatch           │   │
│   │  [entity+0x75]                  │   │
│   └────┬────────────────────────────┘   │
│        │                                 │
│   ┌────▼────┐  ┌──────────┐  ┌──────┐  │
│   │Type 0x10│  │Type 0x16 │  │ 0x33 │  │
│   │Enemy AI │  │Friendly  │  │Player│  │
│   └────┬────┘  └────┬─────┘  └──┬───┘  │
│        │            │            │       │
│   ┌────▼────────────▼────────────▼────┐ │
│   │  Behavior State Machine            │ │
│   │  flags: +0x0Ah, +0x0Bh             │ │
│   └────┬───────────────────────────────┘ │
│        │                                 │
│   ┌────▼─────────────────────────────┐  │
│   │  Target Selection/Tracking        │  │
│   │  [entity+0x29h] = target slot    │  │
│   │  Validate, pursue, engage         │  │
│   └────┬──────────────────────────────┘  │
│        │                                 │
│   ┌────▼──────────────────────────────┐ │
│   │  Maneuver Execution               │ │
│   │  - Pursuit (sub_2F6D0?)           │ │
│   │  - Physics (sub_30882)            │ │
│   │  - Altitude adjustment            │ │
│   └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## Investigation Plan

### Phase 1: Target Selection & Acquisition (Priority 1)

**Goal:** Understand how AI picks targets

**Questions:**
- How does AI find potential targets?
- What criteria determine target priority? (distance, threat, type)
- How does lock-on work? ([entity+0x29h] = target slot)
- Can AI lose target? (flag validation @ [bx+74h])

**Functions to analyze:**
- `sub_307A5` - Load target entity
- `sub_2F6D0` - Target pursuit/guidance (1123B, analyzed in weapons but needs AI perspective)
- Target validation code @ 0x3D180-0x3D203

### Phase 2: Behavior State Machine (Priority 1)

**Goal:** Map the AI state machine

**Questions:**
- What do behavior flags mean? (+0x0Ah, +0x0Bh bits)
- What states exist? (idle, search, pursue, evade, attack, flee?)
- What triggers state transitions?
- How do timers affect behavior? (+0x11h countdown)

**Functions to analyze:**
- Behavior flag checks in sub_3CE92 @ 0x3CFAA-0x3D17F
- Flag modification sites (where flags are set/cleared)
- Timer decrement and threshold checks

### Phase 3: Combat Maneuvers (Priority 2)

**Goal:** Understand tactical movement

**Questions:**
- How does AI pursue targets? (pursuit curve, lead calculation)
- How does AI evade? (defensive maneuvers)
- How does AI manage altitude? (safe vs attack altitude)
- How does AI control speed? (target_speed @ +0x23h)

**Functions to analyze:**
- `sub_30882` - Physics update with AI input
- Heading calculations: +0x0Ch (current) → +0x1Dh (target)
- Speed constants: 0x258 (600), 0x15E (350), 0x1F40 (8000)

### Phase 4: Weapon Employment (Priority 2)

**Goal:** When and how AI fires weapons

**Questions:**
- What conditions trigger weapon fire?
- How does AI select weapon type? (gun vs missile)
- Does AI use missiles differently than guns?
- Does AI lead targets with guns?

**Functions to analyze:**
- Weapon spawn gate: sub_3DC55 @ 0x3DED9
- Weapon queue: 27-byte stride @ cs:word_2E10A
- Type dispatcher: sub_4C19E (2500B)

### Phase 5: Formation & Tactics (Priority 3)

**Goal:** Group behavior and coordination

**Questions:**
- Do AI aircraft fly in formations?
- How do wingmen follow leader?
- Do AI coordinate attacks?
- Is there squad-level AI?

**Functions to analyze:**
- Entity reference field: +0x18h (tracked_entity)
- Waypoint system (from manual: waypoints for computer-controlled aircraft)
- Group coordination (if exists)

### Phase 6: Type 0x10 vs 0x16 Differences (Priority 2)

**Goal:** Understand AI aircraft types

**Questions:**
- What's the difference between type 0x10 and 0x16?
- Are these enemy vs friendly? Or different AI levels?
- Do they use different AI algorithms?
- What makes type 0x33 (player) special from AI perspective?

**Functions to analyze:**
- Type 0x10 handler @ 0x3D087
- Type 0x16 restrictions @ 0x3DEE9
- Type 0x33 comparison (already documented)

---

## Known Functions for AI Analysis

| Address | Name/Purpose | Size | Priority | Notes |
|---------|--------------|------|----------|-------|
| **0x3CE92** | **Master behavior dispatcher** | 2580B | **DONE** | Already analyzed, hub for everything |
| **0x2F6D0** | **Target pursuit/guidance** | 1123B | **HIGH** | Called during tracking, may be AI brain |
| **0x307A5** | **Load target entity** | ~50B | **HIGH** | Target lookup for AI |
| **0x30882** | **Physics update** | 282B | **HIGH** | AI movement execution |
| **0x3DC55** | **Weapon spawn gate** | ~200B | **MED** | AI weapon firing |
| **0x32453** | **Collision detection** | 216B | **MED** | Collision avoidance? |
| 0x30CB8 | State management | ? | MED | Unknown purpose |
| 0x327BE | Audio system | 499B | LOW | Sound triggers, not core AI |
| 0x32393 | Visual update | 192B | LOW | Graphics, not AI |

---

## Search Strategy

### 1. Function Extraction
- Extract sub_2F6D0 (target pursuit) - likely contains pursuit algorithm
- Extract sub_307A5 (load target) - simple lookup
- Extract sub_30882 (physics) - AI input to movement
- Extract type 0x10 handler @ loc_3D087

### 2. Pattern Analysis
- Find all locations that SET behavior flags (+0x0Ah, +0x0Bh)
- Find all locations that CHECK behavior flags
- Map flag bit meanings from context

### 3. State Machine Mapping
- Document all behavior flag combinations
- Trace flag transitions
- Build state diagram

### 4. Manual Cross-Reference
- Manual mentions: CAP, INTERCEPT, LOITER, S AND D modes
- These are probably waypoint actions, not realtime AI states
- But may influence behavior flags

---

## Expected AI Complexity

**1991 DOS flight sim AI is probably:**
- ✅ Simple state machine (4-8 states)
- ✅ Basic pursuit (point at target, fly forward)
- ✅ Rule-based target selection (closest, threat level)
- ✅ Simple evasion (turn away, dive/climb)
- ❌ NOT advanced: no fuzzy logic, neural nets, complex tactics
- ❌ NOT realistic: simplified physics, instant decisions

**Realistic goal:** Understand 80% of AI behavior
- State machine and transitions
- Target selection criteria  
- Basic pursuit/evasion
- Weapon firing conditions

**Will probably NOT find:**
- Complex dogfight tactics (barrel roll, scissors, yo-yo)
- Squad coordination beyond simple follow
- Learning or adaptation
- Realistic pilot limitations (G-forces, awareness)

---

## First Steps

1. ✅ Review behavior dispatcher analysis (DONE - read BEHAVIOR_DISPATCHER_ANALYSIS.md)
2. ⏳ Extract and analyze target tracking section (0x3D180-0x3D203)
3. ⏳ Extract and analyze sub_2F6D0 (target pursuit, 1123B)
4. ⏳ Search for behavior flag modifications (SET operations on +0x0Ah, +0x0Bh)
5. ⏳ Map behavior flag meanings from context
6. ⏳ Extract type 0x10 handler
7. ⏳ Compare type 0x10 vs 0x16 vs 0x33 behavior

---

## Success Metrics

**70% Understanding:**
- State machine documented (states + transitions)
- Target selection logic understood
- Basic pursuit algorithm identified
- Weapon firing conditions known

**80% Understanding:**
- All behavior flag bits mapped
- AI aircraft types differentiated (0x10 vs 0x16)
- Evasion logic identified
- Formation/wingman behavior documented

**90% Understanding:**
- Complete AI state machine with all transitions
- Exact pursuit algorithm (angles, speeds)
- All tactical maneuvers identified
- Squad-level coordination understood

---

*Analysis started: November 11, 2026*  
*Next: Extract target tracking code and analyze sub_2F6D0*


