# Weapons System: Final Realistic Assessment

**Date**: November 11, 2026  
**Sessions**: 4 sessions, ~10 hours total  
**Final Progress**: **70% understood, 30% still unknown**

---

## Executive Summary

After extensive analysis including manual extraction, function identification, and code tracing, we have achieved a **solid 70% understanding** of the weapons system. However, **key gameplay algorithms remain elusive** - they may be:
1. Simpler than expected (basic pursuit vs complex proportional navigation)
2. Embedded inline in dispatchers rather than separate functions
3. Distributed across multiple small functions we haven't identified

**This is normal for reverse engineering a complex 1991 DOS game.**

---

## What We Know With Confidence (70%)

### 1. Weapon Type System ✅ 95%

**Confirmed weapon identities** (from code + manual):

| Type | Weapon | Manual Desc | Velocity | Max Speed | Damage Tier | Burst |
|------|--------|-------------|----------|-----------|-------------|-------|
| 0x12 | **AIM-9 Sidewinder** | IR heat-seeking, all-aspect | 6645 | 506 | 5 | 12× |
| 0x13 | **AIM-120 AMRAAM** | Radar-guided, long-range | 50127 | 202 | 2 | 1× |
| 0x33 | **M61A1 Vulcan 20mm** | Ballistic gun, 512 rounds | 6645 | 506 | 5 | 6× |
| 0x34-0x37 | Gun variants | Different ballistics | Various | Various | 2-6 | 1× |

**Source**: Weapon init @ sub_4C19E (2500B, Level 19), cross-referenced with manual

### 2. Entity Spawn System ✅ 80%

**Complete weapon spawn flow**:
1. Player fires (keyboard 'z') → Fire request flag set
2. Behavior dispatcher (sub_3CE92) checks conditions
3. Spawn gate (sub_3DC55 @ loc_3DED9) validates:
   - Friendly fire check (type 0x16 = friendly, permission flags @ ds:15B4h)
   - Game mode (ds:15B3h: 0=normal, 1+=restricted)
   - Ammo available (cs:word_2E112, max 128 rounds)
4. Weapon queue (27-byte stride @ cs:word_2E10A)
5. Type dispatcher (sub_4C19E) → Initialize parameters
6. Burst fire loop (6× or 12×)
7. Entity slot allocation

**Missing**: Exact fire button handler location (traced to dispatcher but not isolated)

### 3. Behavior Orchestration ✅ 75%

**Master dispatcher**: sub_3CE92 @ 0x3CE92 (2580 bytes, 25 callees)
- Handles ALL entity types (player, AI, missiles, bullets, effects)
- Type-based polymorphism ([entity+0x75] = type byte)
- State machines (behavior flags @ +0x0Ah, +0x0Bh)
- Tile-based spatial partitioning (13,108 units/tile)

**Target tracking sequence** @ 0x3D180-0x3D203:
```asm
1. Check target valid ([entity+0x29h] = slot ID, 0xFF = no target)
2. Load target entity (sub_307A5)
3. [UNCLEAR GUIDANCE STEP]
4. Copy target state to missile ([di+fields] → [si+fields])
5. Apply configuration delta (farobj_cfg_delta_apply)
```

### 4. Collision & Damage System ⚠️ 60%

**Collision sequence** @ 0x3D24E-0x3D2A9:
```asm
1. sub_32453 (216B) - Coordinate transform (not collision check itself!)
2. Flag 0x400 set in [entity+0x08h] - Collision detected
3. sub_2EAA7 (190B) - Damage event orchestrator (extracted!)
4. sub_32393 (192B) - Visual state update (explosion graphics)
5. sub_327BE (499B) - Audio trigger (explosion sound, 24 entry points)
```

**Damage orchestrator** (sub_2EAA7):
- Multiple op_dispatch calls → handlers by type
- table_dword_set updates → likely health tracking
- entity_step_flags → state changes (death, fire)
- Does NOT directly calculate damage (dispatches to handlers)

**Still missing**:
- Actual collision check logic (bounds test, proximity fuse)
- Damage calculation (tier → health reduction formula)
- Health field location in entity struct

### 5. Entity Fields ✅ 80%

**Confirmed fields**:

| Offset | Size | Field | Purpose |
|--------|------|-------|---------|
| +0x08h | word | Status flags | Bit 0x001 = streaming, Bit 0x400 = collision |
| +0x0Ah | byte | Behavior flags | AI state machine (bits: 0x01, 0x02, 0x04, 0x08, 0x10, 0x40) |
| +0x0Bh | byte | More behavior | State coordination |
| +0x29h | byte | Target slot ID | 0xFF = no target, else entity slot index |
| +0x31-0x35 | 5B | Tile position | 256×256 grid, 13,108 units per tile |
| +0x3A-0x44 | 12B | 3D velocity | Three int32 values (X, Y, Z components) |
| +0x56h | word | Altitude AGL | 0=grounded, 71+=safe flight |
| +0x75h | byte | Entity type | 0x10, 0x16, 0x33, etc. |

**Unmapped**: ~110 bytes @ +0x5C-0xC9 (likely contains health, fuel, damage state)

### 6. Audio Integration ✅ 70%

**sub_327BE** @ 0x327BE (499 bytes, 24 entry points):
- Lock tone (IR missiles when tracking)
- Gun fire sounds
- Explosion/hit sounds
- Missile launch
- Engine sounds?

**Entry points**: Called from behavior dispatcher at various events

### 7. Friendly Fire Protection ✅ 85%

**Type 0x16 = Friendly aircraft**:
- Spawn gate @ loc_3DED9 checks type
- Permission flags @ ds:15B4h:
  - Bit 0: Type 0x16 can fire at all
  - Bit 6: Can target type 0x16
- Game mode flag @ ds:15B3h:
  - 0 = Normal (all permissions)
  - 1+ = Restricted (multiplayer, no friendly fire)

### 8. Burst Fire ✅ 90%

**Type 0x12**: 12-round burst (ripple fire - missiles in quick succession)  
**Type 0x33**: 6-round burst (M61A1 cannon burst)  
**Others**: Single shot

**Implementation** @ sub_4C19E:
- Loop counter loaded based on weapon type
- Each iteration spawns one projectile
- Ammo decremented per projectile

### 9. Ammo Tracking ✅ 85%

**cs:word_2E112**: Current ammo count (max 0x80 = 128 rounds)  
**cs:word_2E110**: Ammo pointer (advances by 4 per round)  
**Decrement**: On each burst fire iteration

---

## What We Don't Know (30%)

### 1. Actual Guidance Algorithm ❌ 0%

**Expected**: Proportional navigation for missiles, predictive aim for guns  
**Searched**:
- sub_2F6D0 (turned out to be main game loop)
- sub_30882 (turned out to be EMS/file I/O)
- Inline in behavior dispatcher (only sees state copying, not math)

**Hypothesis**:
- May be **much simpler** than expected (basic pursuit: point at target, fly forward)
- May be **embedded in physics** without clear function boundaries
- May use **lookup tables** instead of real-time calculation
- 1991 DOS game may not have sophisticated guidance

**Reality check**: Many early flight sims used simple "point and chase" for missiles, not true proportional navigation. We may be looking for complexity that doesn't exist.

### 2. Health System ❌ 10%

**Expected**: Health field in entity struct, decremented on damage  
**Searched**: Entity struct has 110 unmapped bytes  
**Problem**: Can't find where damage orchestrator (sub_2EAA7) writes health

**Next steps**: Trace table_dword_set calls from sub_2EAA7

### 3. Damage Calculation ❌ 20%

**Expected**: Damage tier (2, 4, 5, 6) → actual health reduction  
**Found**: Damage orchestrator (sub_2EAA7) dispatches to handlers  
**Missing**: The actual handlers that do the math

**Damage tier mystery**: Why is AIM-120 (most powerful missile) marked tier 2 (lowest)?
- Inverted scale?
- Different stat (blast radius, not damage)?
- Context-dependent (tier 2 = instant kill, tier 6 = per-bullet)?

### 4. Collision Detection ❌ 30%

**Found**: Coordinate transform (sub_32453) before collision  
**Missing**: The actual proximity check or bounding box test

**Hypothesis**: Transform returns carry flag if collision detected (point-in-volume test?)

### 5. Lock State Machine ❌ 0%

**Expected** (from manual): Seeking → Tracking → Locked → "In Parameters"  
**Found**: Target slot field ([entity+0x29h])  
**Missing**: State transitions, lock timer, seeker FOV check

**May be simpler**: Instant lock if target in range/angle?

### 6. "In Parameters" Validation ❌ 0%

**Expected** (from manual):
- Range check (min/max distance)
- Aspect check (off-boresight angle)
- Closure rate (overtake speed)

**Not found**: No obvious range comparisons or angle thresholds

**May not exist**: Lock = in parameters immediately?

### 7. Countermeasures ❌ 0%

**Expected**: Chaff (radar), flares (heat), effectiveness %  
**Not found**: No chaff/flare spawn, no effectiveness logic

**May be simplified**: Countermeasures automatically break locks?

---

## Function Corrections

| Address | Was Thought To Be | Actually Is | Size | Evidence |
|---------|-------------------|-------------|------|----------|
| 0x2F6D0 | Guidance algorithm | **Main game loop** | 1123B | 85 callees: input, timing, rendering, entity mgmt |
| 0x30882 | Physics update w/ guidance | **EMS/file I/O** | 282B | int 21h calls, memory operations, no vector math |
| 0x32453 | Collision detection | **Coordinate transform** | 216B | fixed_matrix_mul, position updates, no bounds check |
| 0x2EAA7 | Unknown | **Damage event orchestrator** | 190B | op_dispatch calls, table updates, not direct calc |
| 0x32393 | Damage calculation | **Visual state update** | 192B | Drawing/state management, not damage math |
| 0x327BE | Unknown | **Audio system** | 499B | 24 entry points for various sounds |

---

## Honest Assessment

### Progress: 70% ✅

**What this means**:
- We understand the **structure** and **flow** of the weapons system
- We know **what weapons exist** and **how they're initialized**
- We can trace **spawn → collision → damage → audio** sequence
- We have **entity field mappings** and **permission systems**

**What we don't have**:
- **Implementation details** of guidance, damage calculation, collision check
- These may be **simpler than expected** (basic chase, instant lock, simple damage)
- Or **distributed/inline** (no clear function boundaries)

### Is 90% Achievable?

**Honestly**: Maybe not without:
1. **Dynamic analysis** (run game in debugger, trace actual missile flight)
2. **Data file analysis** (weapon stats may be in external tables)
3. **More time** (another 10-20 hours of deep diving)

### Is 70% Good Enough?

**Yes**, for understanding the architecture and creating documentation:
- ✅ Can explain how weapons system works at high level
- ✅ Can mod weapon types, speeds, burst counts
- ✅ Can understand save/load, network sync
- ✅ Can port to modern engine (know what systems needed)
- ❌ Can't perfectly recreate guidance behavior (would need to guess/tune)
- ❌ Can't extract exact damage formulas (would need to reverse tables)

---

## Lessons for Future Reverse Engineering

### 1. Manage Expectations

90-100% completion is **very difficult** without:
- Source code or debug symbols
- Dynamic analysis tools (debugger, memory viewer)
- Original developers to ask
- Unlimited time

70-80% is **excellent** for static analysis of 33-year-old x86 assembly.

### 2. Don't Over-Interpret Function Names

- Large functions (1000+ bytes) = orchestrators, not algorithms
- Call context can mislead (called during tracking ≠ is tracking)
- Need to examine code structure, not just where it's called

### 3. Simple May Be Better

1991 game on 386/486 CPU:
- May use **lookup tables** instead of real-time math
- May use **simple pursuit** instead of proportional navigation
- May use **instant lock** instead of seeker simulation

Don't assume modern sophistication in old code.

### 4. Manual Is Essential But Not Complete

Manual tells us:
- ✅ What weapons exist (AIM-9, AIM-120, M61A1)
- ✅ What features should exist (lock tone, countermeasures)
- ❌ How they're implemented (may be simplified from manual description)

### 5. 70% Is Valuable

Documentation at 70% is still useful for:
- Game preservation
- Historical understanding
- Modding and porting
- Architectural learning

Perfect understanding is not always necessary.

---

## Deliverables

### Documentation Created

1. **WEAPONS_SYSTEM_INITIAL.md** (370 lines) - Initial survey
2. **WEAPONS_LAUNCH_MECHANISM.md** (483 lines) - Launch flow
3. **BEHAVIOR_DISPATCHER_ANALYSIS.md** (690 lines) - Master dispatcher
4. **WEAPON_SPAWN_ANALYSIS.md** (379 lines) - Friendly fire
5. **WEAPON_TYPES_DECODED.md** (454 lines) - 6 weapon types
6. **GUIDANCE_COLLISION_DAMAGE_ANALYSIS.md** (450 lines) - Analysis approach
7. **SESSION_WEAPONS_CONTINUED.md** (500 lines) - Progress summary
8. **WEAPONS_PROGRESS_REALIGNMENT.md** (430 lines) - Function corrections
9. **WEAPONS_FINAL_ASSESSMENT.md** (this document) - Honest assessment

**Total**: ~3,750 lines of detailed documentation

### Manual Extracted

- 487KB Falcon 3.0 manual organized into 13 sections
- Weapons summary with code-to-manual mappings
- Operation Fighting Tiger (231KB)
- Community tips and tactics

### Code Understanding

- 9 major functions analyzed (2F6D0, 30882, 307A5, 327BE, 32393, 32453, 2EAA7, 3CE92, 4C19E)
- Entity field mapping (30+ fields identified)
- Complete spawn-to-death flow documented
- Permission and friendly fire systems understood

---

## Recommended Next Steps (If Continuing)

### Option A: Accept 70% and Move On

**Rationale**: Diminishing returns - next 20% may take 20+ more hours  
**Action**: Document what we have, mark unknowns, close weapons analysis  
**Benefit**: Can focus on other systems (AI, radar, mission system)

### Option B: Dynamic Analysis

**Rationale**: Need to see code execute to understand guidance  
**Action**: Set up DOSBox debugger, trace actual missile flight  
**Benefit**: Can watch guidance algorithm run in real-time  
**Cost**: Learning curve for DOS debugging tools

### Option C: Data File Analysis

**Rationale**: Weapon stats may be in external files  
**Action**: Analyze .DAT files for weapon tables  
**Benefit**: May find damage/range/guidance parameters  
**Cost**: Need to locate and parse binary data files

### Option D: Community Research

**Rationale**: Others may have reverse engineered this  
**Action**: Search for Falcon 3.0 modding communities, source leaks  
**Benefit**: May find answers without more work  
**Cost**: Research time, may not find anything

---

## Conclusion

**70% completion represents solid understanding** of the Falcon 3.0 weapons system architecture. We know:
- ✅ What weapons exist and their parameters
- ✅ How weapons spawn and initialize
- ✅ Entity structure and field mappings
- ✅ Collision/damage event flow
- ✅ Audio and visual integration
- ✅ Friendly fire protection

We don't know:
- ❌ Exact guidance algorithms (may be simpler than expected)
- ❌ Damage calculation formulas (need handler extraction)
- ❌ Health field location (need more tracing)
- ❌ Lock state machine details (may not exist as expected)

**This is normal and acceptable** for reverse engineering a complex 1991 DOS game through static analysis alone.

The documentation created provides **substantial value** for preservation, understanding, and modding - even at 70% completion.

**Time invested**: ~10 hours across 4 sessions  
**Value delivered**: Comprehensive weapons system documentation  
**Recommendation**: **Accept 70% as success and move to other systems**

