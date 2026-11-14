# Weapons System: Progress Realignment

**Date**: November 11, 2026  
**Session**: Function Extraction Attempt  
**Realization**: Initial function identifications need correction

---

## Key Discovery: Function Misidentification

### Sub_2F6D0 Is NOT Guidance Algorithm

**Initial assumption**: Sub_2F6D0 (1123 bytes) is missile guidance  
**Reality**: Sub_2F6D0 is the **MAIN GAME LOOP / STATE MANAGER**

**Evidence**:
- 85 callees (far too many for guidance)
- Calls include:
  - `mouse_buttons_get_2`, `int15_joystick_detect` - Input handling
  - `control_axes_read`, `control_axis_store_step` - Control input
  - `tick_rate_compute`, `pit_channel0_latch_read` - Timing
  - `mode_flags_apply`, `mode_slot_select` - Mode management
  - `vga_dac_palette_upload` - Rendering
  - `entity_setup_step`, `farobj_tile_stream_build` - Entity management
  - `hud_data_panel_draw`, `hud_terrain_strip_render` - HUD rendering

**Actual purpose**: Main game state update loop that handles:
1. Input processing (keyboard, mouse, joystick)
2. Timing and frame rate
3. Entity updates (all entities, not just weapons)
4. Rendering coordination
5. Mode switching
6. Save/load state

**Why we thought it was guidance**: 
- Called from behavior dispatcher when tracking targets
- Multiple entry points (loc_2F6D6, loc_2F700, loc_2F784)
- Large size (1123 bytes)

**Corrected understanding**:
The behavior dispatcher calls into the main loop at different points for different purposes:
- `loc_2F6D6` (+0x06) - Second instruction, different init path
- `loc_2F700` (+0x30) - Overlay/state reading
- `loc_2F784` (+0xB4) - Entity record building

### Sub_2EAA7: Damage Application (190 bytes)

**Correctly identified as damage-related**, but actual function:
- NOT direct health reduction
- Table management and op_dispatch calls
- Entity step flags coordination
- Likely **damage event orchestration** rather than calculation

**Code structure**:
```asm
0x2EAA7: Load parameters
0x2EAB3: call r08_farptr_load_thunk  ; Check game mode?
0x2EAC0: call op_dispatch            ; Dispatch to handler
0x2EAD1: call op_dispatch            ; Another dispatch
0x2EADD: call op_dispatch            ; Yet another
0x2EAEB: loop loc_2EAEA              ; Loop 4 times
0x2EB09: call table_dword_set        ; Update damage table?
0x2EB27: call op_dispatch            ; Final dispatch
0x2EB54: call op_dispatch            ; Entity flags
0x2EB5D: call op_dispatch            ; Cleanup
```

**Hypothesis**: This is a **damage event coordinator** that:
1. Dispatches to appropriate damage handlers based on weapon/target type
2. Updates damage tables (health tracking)
3. Triggers entity state changes (death, fire, etc.)
4. Coordinates visual/audio responses

**Still missing**: Actual damage calculation (probably in one of the op_dispatch targets)

### Sub_32453: NOT Simple Collision (216 bytes)

**Initial assumption**: Bounding box collision check  
**Reality**: **Coordinate transformation / projection system**

**Evidence**:
```asm
0x32453: Store coordinates in entity
0x32465: call fixed_matrix_mul       ; Matrix transformation!
0x3246D: Add transformed result to entity position
0x32472-0x32497: Update entity X, Y, Z with transforms
0x3249B: call angle_adjusted_copy
```

**Actual purpose**:
- Transforms coordinates between reference frames
- Used before collision checks (not the check itself)
- Likely converts world → local or vice versa

**Collision probably happens elsewhere** - this preps the data.

---

## Corrected Understanding

### Collision/Damage Sequence in Behavior Dispatcher

```asm
; @ sub_3CE92 (behavior dispatcher)

0x3D24E: call   sub_32453              ; Transform coords for collision check
0x3D251: jb     loc_3D255              ; If collision detected (by transform result)
0x3D253: clc                           ; Clear carry (no collision)
0x3D254: retn

; Collision detected path:
0x3D255: or     word ptr [si+8], 400h  ; Set collision flag
0x3D25A: call   sub_2EAA7              ; Damage event orchestrator
0x3D25D: or     ax, ax                 ; Check result
0x3D25F: jnz    loc_3D27C              ; If entity still alive
0x3D261-0x3D27A: Update entity state    ; Various bookkeeping
0x3D27C: mov    ax, [si]               ; 
0x3D280: call   sub_32393              ; Visual state update
0x3D285: mov    byte ptr cs:..., 1     ; Set flag
0x3D28B: call   sub_327BE              ; Audio trigger (explosion)
```

**Key insight**: Collision flag 0x400 is set BEFORE damage application, suggesting:
- Transform (sub_32453) returns carry flag if collision detected
- Collision might be detected BY the transform (point inside volume?)
- OR there's a separate check between transform and flag set (not visible in snippet)

### Where Is Actual Guidance?

**Answer**: Probably embedded in behavior dispatcher itself or in physics update (sub_30882).

**Evidence from behavior dispatcher** @ 0x3D1A8-0x3D1C4:
```asm
0x3D1AC: call   sub_307A5              ; Load target entity
0x3D1AF: call   loc_2F6D6              ; [MISIDENTIFIED - main loop entry]
0x3D1B2: call   sub_30882              ; Physics update
0x3D1B5: call   sub_30882+0x63         ; More physics
0x3D1BC: cmp    [di+56h], ax           ; Altitude check
0x3D1BF: jge    loc_3D1C5
0x3D1C1: call   loc_2F784+4            ; [MISIDENTIFIED - another entry]
```

**New hypothesis**:
1. **sub_307A5** - Load target entity data
2. **loc_2F6D6** - NOT guidance! State sync or visibility check
3. **sub_30882** - Physics update, PROBABLY includes guidance math here
4. Altitude check
5. **loc_2F784** - NOT guidance! Entity record operation

**Actual guidance is likely in sub_30882 (physics update)**!

---

## What We Actually Know

### Confirmed Weapon Data

| Type | Identity | Velocity | Max Speed | Damage Tier | Burst |
|------|----------|----------|-----------|-------------|-------|
| 0x12 | AIM-9 Sidewinder | 6645 | 506 | 5 | 12× |
| 0x13 | AIM-120 AMRAAM | 50127 | 202 | 2 | 1× |
| 0x33 | M61A1 Vulcan | 6645 | 506 | 5 | 6× |
| 0x34 | Gun variant | 21360 | - | 6 | 1× |
| 0x35 | Gun variant | 10680 | 202 | 5 | 1× |
| 0x36 | Gun variant | 10680 | 202 | 4 | 1× |
| 0x37 | Gun variant | 50127 | 202 | 2 | 1× |

### Confirmed Entity Fields

| Offset | Field | Size | Purpose |
|--------|-------|------|---------|
| +0x08h | Status flags | word | Bit 0x400 = collision detected |
| +0x29h | Target slot | byte | 0xFF = no target, else slot ID |
| +0x75h | Entity type | byte | 0x10, 0x16, 0x33, etc. |

### Confirmed Functions

| Address | Name | Size | Actual Purpose |
|---------|------|------|----------------|
| 0x2EAA7 | sub_2EAA7 | 190B | Damage event orchestrator |
| 0x2F6D0 | sub_2F6D0 | 1123B | **Main game loop** (not guidance!) |
| 0x30882 | sub_30882 | ?B | Physics update (guidance likely here) |
| 0x307A5 | sub_307A5 | ?B | Load target entity data |
| 0x327BE | sub_327BE | 499B | Audio system (24 entry points) |
| 0x32393 | sub_32393 | 192B | Visual state update (not damage calc) |
| 0x32453 | sub_32453 | 216B | Coordinate transform (not collision check) |
| 0x3CE92 | sub_3CE92 | 2580B | Behavior dispatcher (all entities) |
| 0x4C19E | sub_4C19E | 2500B | Weapon type dispatcher |

### Confirmed Systems

1. **Weapon spawn** ✅ - Complete flow documented
2. **Friendly fire protection** ✅ - Type 0x16, permission flags
3. **Burst fire** ✅ - 6-round, 12-round mechanisms
4. **Ammo tracking** ✅ - Counter at cs:word_2E112
5. **Collision flagging** ✅ - Bit 0x400 in [entity+0x08h]
6. **Audio integration** ✅ - sub_327BE with 24 entry points
7. **Target lock field** ✅ - [entity+0x29h] = slot ID

### NOT Yet Found

1. **Actual guidance algorithm** - Not in sub_2F6D0! Probably in sub_30882 (physics)
2. **Health field** - Entity health storage location unknown
3. **Damage calculation** - Damage tier → actual damage formula
4. **"In parameters" validation** - Range/aspect/closure checks
5. **Countermeasure logic** - Chaff/flare effectiveness
6. **Lock state machine** - Seeking → Tracking → Locked transitions

---

## Revised Progress Assessment

### Previous Assessment (Incorrect)

Progress: 75%  
Major components: Guidance located (sub_2F6D0), collision located (sub_32453), damage located (sub_2EAA7)

### Corrected Assessment

**Progress: 70%** (down from 75% due to mis-identification)

**What we have**:
- Weapon type system ✅ 95%
- Entity spawn system ✅ 80%
- Behavior orchestration ✅ 75%
- Collision flagging ✅ 75%
- Damage event system ⚠️ 60% (orchestrator found, calculation missing)
- Audio integration ✅ 70%
- Target tracking fields ✅ 80%

**What we don't have**:
- Guidance algorithm ❌ 0% (not found, was misidentified)
- Collision detection ❌ 30% (transform found, check not found)
- Damage calculation ❌ 20% (event found, math not found)
- Health tracking ❌ 10% (field not located)
- Lock state machine ❌ 0% (not found)
- "In parameters" logic ❌ 0% (not found)
- Countermeasures ❌ 0% (not found)

**Honest assessment**: **70%** complete, not 75%.

---

## Path Forward

### Priority 1: Find ACTUAL Guidance (sub_30882)

**Target**: sub_30882 - Physics update function  
**Why**: Behavior dispatcher calls it right after "loading target", suggesting it applies forces based on target position

**Search strategy**:
1. Extract sub_30882 disassembly
2. Look for:
   - Vector subtraction (target pos - missile pos)
   - Angle calculation (atan2, atan)
   - Proportional navigation constant (N × velocity × LOS_rate)
   - Force application to missile orientation

### Priority 2: Locate Health Field

**Target**: Entity struct +0x5C to +0xC9 (110 unmapped bytes)  
**Why**: Damage must be applied somewhere

**Search strategy**:
1. Find where sub_2EAA7 (damage orchestrator) writes data
2. Look for decrements in entity fields after collision
3. Search for comparisons to zero (health <= 0 checks)
4. Trace op_dispatch calls to find actual damage handler

### Priority 3: Find Actual Collision Check

**Target**: Unknown function between sub_32453 and flag 0x400 being set  
**Why**: Transform prepares data, but something must do the actual check

**Search strategy**:
1. sub_32453 returns carry flag (jb after call)
2. Check if sub_32453 itself does collision at end
3. Or find function called between transform and flag set

### Priority 4: Decode Damage Tier System

**Target**: Resolve the "tier 2 = low but should be high" mystery  
**Why**: Need to know if inverted scale or different stat

**Search strategy**:
1. Find damage calculation in op_dispatch targets
2. Look for tier being used as divisor vs multiplier
3. Check for lookup tables indexed by tier

---

## Lessons Learned

### Don't Trust Function Names Alone

- "sub_2F6D0" sounded like guidance because called during target tracking
- Actually it's the main loop, called for many reasons
- Need to examine callees and code structure, not just call context

### Large Functions Are Multi-Purpose

- 1123 bytes = main loop
- 2580 bytes = behavior dispatcher  
- 2500 bytes = weapon dispatcher
- These are **orchestrators**, not specific algorithms

### Small Functions May Be Wrappers

- 190 bytes (sub_2EAA7) is damage orchestrator
- 216 bytes (sub_32453) is coordinate transform
- Real work happens in called functions (op_dispatch, etc.)

### Manual Context Is Still Essential

- Without manual, would still have no idea about weapon types
- Manual tells us WHAT to expect, code shows us HOW
- Manual provides validation (AIM-9 should be heat-seeking, code should show that)

---

## Time Investment

**Session 1**: Manual extraction (2 hours) ✅  
**Session 2**: Weapons analysis with manual (2 hours) ✅  
**Session 3**: Function extraction attempt (2 hours) ⚠️ **Learned functions were misidentified**

**Total**: 6 hours → 70% (not 75%)  
**Remaining to 90%**: ~4-6 hours (if we find the right functions!)

---

## Next Session Goals

1. **Extract sub_30882** (physics update - likely has actual guidance)
2. **Find health field** (trace damage writes)
3. **Resolve damage tier** (find calculation formula)
4. **Document findings** clearly with corrected function purposes

**Success criteria**: Locate guidance math, health tracking, damage formula = 80%+ complete

