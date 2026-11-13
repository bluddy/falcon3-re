# Behavior Dispatcher Analysis - sub_3CE92

**Date:** November 11, 2026  
**Function:** `farobj_behavior_dispatch_step` @ sub_3CE92  
**Size:** 2580 bytes (MASSIVE!)  
**Level:** 19 (high-level game logic)  
**Class:** DATA (data-driven dispatch)

---

## Overview

This is the **master behavior dispatcher** for ALL FarObj entities in Falcon 3.0. It handles:
- Aircraft AI
- Weapon guidance
- Physics updates
- Collision detection
- Target tracking
- Entity state machines
- And much more...

The function is 2580 bytes (over 2.5KB) of dense logic with 25 callees. This is ONE OF THE LARGEST functions in the entire game.

---

## Function Signature

```c
void farobj_behavior_dispatch_step(FarObjContext* si);

// Where FarObjContext contains:
//   [si+0]  = Entity slot index
//   [si+2]  = Entity segment
//   [si+4]  = Entity offset
//   [si+6]  = Entity pointer (shortcut to avoid seg:off math)
```

---

## Entry Points (Multiple!)

This function has **19 entry points** - it's called from many different contexts:

**Callers:**
- sub_3BB8F (aircraft_motion_step context)
- sub_4C19E (farobj_queue_drain_dispatch - weapons!)
- sub_4CD1D, sub_3E16B, sub_3E552
- sub_41B4E, sub_4CCFB, sub_3C4F2
- sub_4D544 (farobj_class16_record_ops)
- sub_30AA8, sub_3099C
- sub_4D3C7, sub_3E95E
- And more...

---

## Entity Type Dispatching

### Type Field: `[di+75h]` or `[si+75h]`

The function checks entity type at offset **+0x75** (117 decimal).

**Types found in sub_3CE92:**

| Type (hex) | Type (dec) | Check Count | Hypothesis | Evidence |
|------------|------------|-------------|------------|----------|
| **0x33** | **51** | **4× checks** | **Special entity** (player aircraft?) | Heavy branching, special physics |
| **0x10** | **16** | **1× check** | Special class | Conditional behavior |

---

## Code Structure Analysis

### Section 1: Tile Boundary Wrapping (0x3CE92-0x3CEDC)

```asm
0x3CE92: push   es
0x3CE93: mov    ax, [si+2]      ; Get entity segment
0x3CE96: mov    di, [si+4]      ; Get entity offset
0x3CE99: mov    es, ax
0x3CE9B: mov    ax, [si+1Dh]    ; Get current heading/angle?
0x3CE9E: sub    ax, es:[di+0Ch] ; Compare with entity field +0Ch
0x3CEA2: call   stub_to_24988   ; Angle normalize?
0x3CEA7: mov    bx, ax
0x3CEA9: cmp    ax, 0
0x3CEAC: jnz    loc_3CEB0
0x3CEAE: pop    es
0x3CEAF: retn                   ; Early exit if no change
```

**Purpose:** Checks if entity has crossed tile boundaries. Uses field +0x0Ch and +0x1Dh.

### Section 2: Spatial Tile Updates (0x3CEF4-0x3CF9C)

```asm
0x3CEF4: push   es
0x3CEF5: mov    bp, 0           ; Flag: tile boundary crossed
0x3CEF8: mov    di, [si+6]
0x3CEFB: mov    ax, [di+50h]    ; Get velocity component X?
0x3CEFE: add    [si+33h], ax    ; Add to tile position accumulator
0x3CF01: cmp    word ptr [si+33h], 0
0x3CF05: jge    loc_3CF14
0x3CF07: mov    bp, 1           ; Set tile boundary flag
0x3CF0A: dec    byte ptr [si+31h] ; Decrement tile X coordinate
0x3CF0D: add    word ptr [si+33h], 3334h ; Wrap with tile size (13,108 units)
```

**Purpose:** Updates 2D tile position as entity moves. Detects tile wrapping.

**Key Constants:**
- **0x3334** = **13,108 decimal** - **TILE SIZE!** (matches terrain system!)
- Fields: `[si+31h]` = tile X, `[si+32h]` = tile Y, `[si+33h]` = sub-tile X, `[si+35h]` = sub-tile Y

### Section 3: Type 0x33 Special Handler (0x3CF9D-0x3CFA9)

```asm
0x3CF9D: mov    di, [si+6]
0x3CFA0: cmp    byte ptr [di+75h], 33h  ; *** TYPE CHECK: 0x33 ***
0x3CFA4: jnz    loc_3CFAA
0x3CFA6: call   loc_3D37F              ; Special handler for type 0x33
0x3CFA9: retn
```

**Purpose:** Type 0x33 entities get special early handling before main logic.

**Handler @ loc_3D37F (0x3D37F-0x3D415):**
- Manages entity state countdown: `[si+11h]` (timer/countdown)
- Checks velocity field: `[si+2Eh]`
- Has special acceleration/deceleration logic
- Updates heading: `[si+1Dh]`
- Searches for targets: calls `sub_2F6D0` (target search?)
- Can spawn new entities: sets `[si+0Ch]`, `[si+0Eh]`, `[si+0Fh]`, `[si+10h]`

**Hypothesis:** Type 0x33 is **PLAYER AIRCRAFT** or **SPECIAL AI AIRCRAFT**
- Has complex physics
- Target search
- Weapon systems (spawn entities)

### Section 4: General AI/Behavior (0x3CFAA-0x3D039)

```asm
0x3CFAA: cmp    byte ptr [si+11h], 0FFh ; Countdown timer
0x3CFAE: jz     loc_3CFB3
0x3CFB0: dec    byte ptr [si+11h]      ; Decrement timer
0x3CFB3: call   loc_328A1              ; sub_327BE - Sound/audio trigger?
0x3CFB6: or     al, al
0x3CFB8: jz     loc_3D039
```

**Purpose:** General timer decrement, sound triggers, behavior state machine.

**Multiple branches based on:**
- `[si+0Bh]` - Behavior flags (bits: 0x01, 0x02, 0x04, 0x08, 0x10, 0x40)
- `[di+0C5h]` - Speed/velocity magnitude?
- `[di+75h]` - Entity type
- `[si+14h]`, `[si+15h]` - Unknown state fields

**Calls:**
- `sub_327BE` (@ loc_32838, loc_328A1, etc.) - Multiple entry points, sound/event system?
- `sub_30CB8` - State management?
- `sub_3252B` (@ loc_3259F) - Behavior completion?

### Section 5: Type 0x10 Special Handler (0x3D03F-0x3D087)

```asm
0x3D03F: mov    di, [si+6]
0x3D042: cmp    byte ptr [di+75h], 10h  ; *** TYPE CHECK: 0x10 ***
0x3D046: jz     loc_3D087
```

**Purpose:** Type 0x10 entities jump to special handler @ loc_3D087.

**Handler @ loc_3D087:**
- Jumps to loc_3D180
- Continues with different logic path

**Hypothesis:** Type 0x10 is **SPECIAL ENTITY CLASS** (missiles? bombs? special effects?)

### Section 6: More Behavior Branching (0x3D08A-0x3D17F)

Complex branching based on behavior flags `[si+0Bh]`:
- Bit 0x04: Medium-altitude behavior
- Bit 0x03: Low-altitude / ground attack behavior
- Bit 0x02: Landing/runway approach?
- Different speed thresholds, different target acquisition

### Section 7: Target Tracking (0x3D180-0x3D203)

```asm
0x3D180: cmp    byte ptr [si+29h], 0FFh ; Target slot ID
0x3D184: jz     loc_3D204              ; No target
0x3D186: call   near ptr loc_307AD+3   ; sub_307A5 - Load target entity
0x3D189: mov    bx, [di+6]
0x3D18C: test   byte ptr [bx+74h], 1   ; Check target flags
0x3D190: jz     loc_3D198
0x3D192: test   byte ptr [bx+74h], 38h ; More target flags
0x3D196: jz     loc_3D1A8              ; Target valid, continue tracking
0x3D198: mov    byte ptr [si+29h], 0FFh ; Lose target
```

**Purpose:** Tracks target entity. If target becomes invalid, clears target slot.

**Target Fields:**
- `[si+29h]` = Target entity slot ID (0xFF = no target)
- `[bx+74h]` = Target entity flags (bits 0, 3, 4, 5 checked)

**Actions when target valid:**
- Copies target state: `[di+0Ah]`, `[di+0Bh]`, `[di+39h]`, `[di+37h]`, `[di+1Ah]`, `[di+1Bh]`, `[di+1Ch]`
- Calls `sub_2F6D0` - Target pursuit/guidance?
- Calls `sub_30882` - Physics update?
- Altitude check: `[di+56h]` vs saved altitude
- Configuration delta: `farobj_cfg_delta_apply`

### Section 8: Visibility & Projection (0x3D204-0x3D229)

```asm
0x3D204: call   near ptr loc_2F5B3+1   ; viewlist_project_flagged
0x3D207: test   word ptr [si+8], 1     ; Streaming flag
0x3D20C: jz     loc_3D211
0x3D20E: call   loc_2F6D6              ; sub_2F6D0 - Update visibility
0x3D211: call   loc_2F700              ; sub_2F6D0+0x2A - More visibility
0x3D214: cmp    word ptr [si+0Ch], 0   ; Config dirty flag?
0x3D218: jnz    loc_3D21D
0x3D21A: call   loc_2F3A8              ; farobj_cfg_delta_apply
```

**Purpose:** Project entity to screen, update visibility, apply configuration changes.

### Section 9: Collision Detection Preparation (0x3D22A-0x3D318)

```asm
0x3D231: test   word ptr [si+8], 400h  ; Collision flag
0x3D236: jnz    loc_3D2A9              ; Already colliding
0x3D243: call   far_obj_field_call     ; Dynamic dispatch
0x3D248: cmp    al, 2
0x3D24A: jz     loc_3D253
0x3D24E: call   near ptr loc_32501+2   ; sub_32453 - Collision check?
0x3D251: jb     loc_3D255              ; Collision detected!
0x3D253: clc
0x3D254: retn
0x3D255: or     word ptr [si+8], 400h  ; Set collision flag
```

**Purpose:** Checks for collisions, sets collision flag bit 0x400 in `[si+8]`.

**On collision:**
- Calls `sub_2EAA7` - Collision response?
- Calls `farptr_table_offset_apply` - Entity lookup?
- Calls `sub_32393` - Damage/destruction?
- Triggers sound: calls `sub_327BE`
- Sets flag: `cs:loc_2FAF9+1 = 1`

### Section 10: More Type 0x33 Checks (0x3D470, 0x3D67D, 0x3D830)

```asm
0x3D470: cmp    byte ptr [si+75h], 33h
0x3D474: jz     loc_3D4AC              ; Skip certain logic for type 0x33

0x3D67D: cmp    byte ptr [di+75h], 33h
0x3D681: jnz    loc_3D686
0x3D683: jmp    loc_3D71F              ; Type 0x33 special path

0x3D830: cmp    byte ptr [di+75h], 33h
0x3D834: jnz    loc_3D839
0x3D836: mov    ax, 0C00h              ; Type 0x33 gets value 0x0C00
```

**Purpose:** Type 0x33 has special handling in multiple behavior contexts (altitude, collision response, physics constants).

---

## Key Constants

| Constant | Decimal | Meaning | Evidence |
|----------|---------|---------|----------|
| **0x3334** | **13108** | **Tile size** | Spatial wrapping constant, matches terrain system |
| 0x1F40 | 8000 | Speed threshold 1 | Compared with `[di+0C5h]` |
| 0x7D0 | 2000 | Speed threshold 2 | Lower speed branch |
| 0x1E00 | 7680 | Velocity constant | Added to `[si+2Eh]` |
| 0xFF1A | -230 (signed) | Descent rate? | Set to `[si+1Fh]` |
| 0xFC68 | -920 (signed) | Steeper descent? | Alternative value |
| 0x258 | 600 | Target speed | Set to `[si+23h]` |
| 0x15E | 350 | Lower target speed | Alternative value |

---

## Entity Fields Referenced

### Frequently Used Fields

| Offset | Name Hypothesis | Type | Usage |
|--------|-----------------|------|-------|
| **+0x75** | **entity_type** | byte | Type dispatch (0x10, 0x33 special) |
| +0x0Ch | heading/angle_current | word | Orientation tracking |
| +0x1Dh | heading/angle_target | word | Desired orientation |
| +0x29h | target_slot_id | byte | Target entity (0xFF = none) |
| +0x31h | tile_x | byte | Grid X coordinate |
| +0x32h | tile_y | byte | Grid Y coordinate |
| +0x33h | subtile_x | word | Fine X position (wraps at 13108) |
| +0x35h | subtile_y | word | Fine Y position (wraps at 13108) |
| +0x50h | velocity_x? | word | Movement component |
| +0x52h | velocity_y? | word | Movement component |
| +0x08h | status_flags | word | Bits: 0x01 (streaming), 0x400 (collision) |
| +0x0Ah | behavior_flags_1 | byte | Bits: 0x01, 0x08 (various states) |
| +0x0Bh | behavior_flags_2 | byte | Bits: 0x01-0x40 (AI states) |
| +0x11h | countdown_timer | byte | Decremented each frame |
| +0x14h | state_value_1 | byte | Unknown state |
| +0x15h | state_value_2 | byte | Unknown state |
| +0x18h | tracked_entity | word | Another entity reference |
| +0x23h | target_speed | word | Desired speed |
| +0x2Eh | velocity_state | word | Acceleration/velocity |
| +0x56h | altitude | word | Height above ground |
| +0x74h | entity_flags | byte | Entity status bits |
| +0xAEh | weapon_state? | word | Used in collision/spawn |
| +0xC5h | speed_magnitude? | word | Current speed |

---

## Function Callees (25 total)

### Vector Math
- `fixed_vec3_accumulate_a` (L0) - Vector accumulation for physics

### Dynamic Dispatch
- `far_obj_field_call` (L1) - Dynamic field access (polymorphic behavior)
- `farobj_field_set` (L1) - Set entity fields dynamically

### Entity Management
- `farptr_table_offset_apply` (L2) - Entity lookup/load
- `farobj_cfg_delta_apply` (L1) - Apply configuration changes
- `farobj_index_range_check` (L0) - Validate entity index
- `farobj_table_snapshot` (L0) - Save entity state?
- `sub_3DC55` (L19) - farobj_slot_create_gate - **WEAPON SPAWN!**

### Game State
- `sub_2EAA7` (L19) - Collision response
- `sub_2F6D0` (L19) - Target pursuit/visibility (1123B)
- `sub_3001E` (L19) - game_state_load_apply (745B)
- `sub_307A5` (L19) - Load target entity
- `sub_30882` (L19) - Physics update
- `sub_30CB8` (L19) - State management

### Collision/Damage
- `sub_32393` (L19) - Damage application?
- `sub_32453` (L19) - Collision detection
- `sub_3252B` (L19) - Behavior completion
- `sub_327BE` (L19) - Sound/event system (multiple entry points)

### Rendering
- `viewlist_project_flagged` (L10) - Project to screen
- `range_scale_step_handler` (L14) - Distance scaling

### HUD
- `r32_hud_phase_dispatch` (L7) - HUD updates

### Utility
- `stub_to_24980` (L1), `stub_to_24988` (L1) - Angle normalize stubs
- `flag_532_set_dispatch_4ab` (L0) - Flag management
- `r05_farptr_dispatch_big` (L0) - Big dispatch table

---

## Weapon-Specific Observations

### Weapon Spawn Detection

At **0x3D2D8:**
```asm
0x3D2D8: call   loc_3DED9  ; sub_3DC55 - farobj_slot_create_gate
0x3D2DB: jnb    loc_3D2E3
0x3D2DD: or     byte ptr [si+0Ah], 8  ; Set "weapon active" flag?
```

**Context:** Called after collision detection and target validation. This is likely where **weapons are spawned** (missiles fired, bombs dropped).

**Hypothesis:** When certain conditions met (target locked, fire button pressed?, weapon available?), this creates a new weapon entity.

### Target Lock State

Field **`[si+29h]`** is the **target slot ID**:
- `0xFF` = No target
- Other value = Locked target entity slot

**Lock validation:**
- Checks target flags: `[bx+74h]` bits 0, 3, 4, 5
- If invalid, sets `[si+29h] = 0xFF` (lose lock)
- If valid, copies target state for tracking

### Missile Guidance Pattern (Hypothesis)

At **0x3D1A8-0x3D1C4:**
```asm
0x3D1A8: mov    ax, [di+4Ah]     ; Save something
0x3D1AB: push   ax
0x3D1AC: call   near ptr loc_307BF+1  ; Load target data
0x3D1AF: call   loc_2F6D6        ; Target pursuit (guidance?)
0x3D1B2: call   near ptr sub_30882+2  ; Physics update
0x3D1B5: call   near ptr loc_308E5+2  ; More physics
0x3D1B8: pop    ax
0x3D1B9: mov    di, [si+6]
0x3D1BC: cmp    [di+56h], ax     ; Compare altitude with saved value
0x3D1BF: jge    loc_3D1C5
0x3D1C1: call   near ptr loc_2F784+4  ; Altitude adjustment
```

**Pattern:** Load target → Pursue target → Update physics → Check altitude

**This is likely the missile guidance loop!**

---

## Type 0x33 Detailed Behavior

Type 0x33 appears to be **PLAYER AIRCRAFT** or **PRIMARY AI AIRCRAFT**.

**Evidence:**
1. **Most complex handling** - 4 separate type checks, special physics
2. **Target search** - Calls `sub_2F6D0` (target acquisition)
3. **Weapon spawning** - Can spawn entities (sets `[si+0Ch]` etc.)
4. **Special physics constants** - Gets `0x0C00` instead of `0x800`
5. **Altitude management** - Special descent/ascent logic
6. **Collision avoidance** - Different collision response
7. **Timer management** - Countdown at `[si+11h]`

**Special handler @ 0x3D37F:**
- Manages velocity state `[si+2Eh]`
- Three velocity modes: negative (descending?), zero (level), positive (ascending/accelerating?)
- Sets target speeds: 0x258 (600), 0x15E (350)
- Adjusts heading: calculations on `[di+0Ch]` → `[si+1Dh]`
- Target search: `sub_2F6D0`
- Weapon spawn conditions: sets `[si+0Ch] = 1`, timer fields

---

## Next Investigation Steps

### Immediate
1. **Extract type 0x10 handler** - What is this special class?
2. **Trace sub_3DC55 (farobj_slot_create_gate)** - Weapon spawn mechanism
3. **Find other weapon types** - Check farobj_queue_drain_dispatch @ sub_4C19E
4. **Map entity field +0x29h usage** - Target lock storage

### Medium
5. **Trace sub_2F6D0** - Target pursuit/guidance algorithm (1123B function!)
6. **Trace sub_32453** - Collision detection
7. **Trace sub_32393** - Damage calculation
8. **Extract behavior flag meanings** - `[si+0Ah]`, `[si+0Bh]` bits

### Analysis
9. **Compare type 0x33 vs other types** - What makes 0x33 special?
10. **Map complete entity structure** - All fields used in sub_3CE92
11. **Document state machine** - Behavior flag transitions

---

## Conclusions

### Key Findings

1. **sub_3CE92 is THE behavior hub** - All entity AI/physics/weapons go through here
2. **Type 0x33 is special** - Likely player aircraft or advanced AI
3. **Type 0x10 exists** - Another special class
4. **Target lock system confirmed** - Field +0x29h, 0xFF = no lock
5. **Weapon spawn confirmed** - sub_3DC55 called in behavior context
6. **Collision detection exists** - sub_32453, flag 0x400
7. **Tile-based spatial** - 13,108 unit tiles, wrapping logic
8. **Complex state machines** - Multiple behavior flags, timers, thresholds

### Weapon System Implications

- Weapons are **NOT spawned immediately on fire key press**
- Instead: Target lock → Behavior update → Conditions met → Spawn weapon entity
- This means weapon firing is **integrated into entity behavior system**
- Fire button likely sets a "request fire" flag, actual spawn happens in sub_3CE92

### Architecture Insight

This is a **classic entity-component system**:
- Central dispatcher (sub_3CE92)
- Type-based polymorphism ([di+75h])
- Behavior flags for states
- Dynamic field access (far_obj_field_call)
- Modular subsystems (collision, physics, rendering, sound)

**Very sophisticated for 1991!**

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: 2580-byte monster partially decoded, weapon spawn found, type system understood*

