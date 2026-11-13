# Weapon Spawn Analysis - sub_3DC55 @ loc_3DED9

**Date:** November 11, 2026  
**Function:** Weapon spawn gate check  
**Entry Point:** 0x3DED9 (inside sub_3DC55)  
**Called From:** sub_3CE92 @ 0x3D2D8, 0x3D2E3 (behavior dispatcher)

---

## Overview

This is the **weapon spawn permission check** - determines if a weapon can be spawned based on game state and entity types.

---

## Disassembly @ 0x3DED9-0x3DF1D

```asm
; ========== WEAPON SPAWN GATE CHECK ==========
0x3DED9: push   ax
0x3DEDA: push   bx
0x3DEDB: push   di

; Check game mode flag
0x3DEDC: cmp    byte ptr ds:15B3h, 0    ; Game mode check (multiplayer? demo?)
0x3DEE1: jz     loc_3DF19                ; If 0, allow spawn (set carry flag)
                                          ; If non-zero, check restrictions below

; --- RESTRICTION CHECK FOR TYPE 0x16 ENTITIES ---
0x3DEE3: mov    di, [si+6]              ; Load entity pointer
0x3DEE6: mov    bl, [di+75h]            ; *** Get entity TYPE field ***
0x3DEE9: cmp    bl, 16h                 ; *** TYPE CHECK: 0x16 (decimal 22) ***
0x3DEEC: jnz    loc_3DEF8               ; Not type 0x16, skip to next check

; Type 0x16 specific restriction
0x3DEEE: test   word ptr ds:15B4h, 1    ; Check permission flag bit 0
0x3DEF4: jnz    loc_3DF19               ; If bit set, allow spawn
0x3DEF6: jmp    loc_3DF16               ; Else deny spawn (clear carry)

; --- CHECK TARGET ENTITY TYPE ---
0x3DEF8: mov    ax, [si+18h]            ; Get target/tracked entity slot
0x3DEFB: cmp    ax, 0FFFFh              ; Is there a target?
0x3DEFE: jz     loc_3DF0E               ; No target, check permission

0x3DF00: call   locret_30CB7            ; farobj_table_snapshot - Load target entity
0x3DF03: mov    di, [di+6]              ; Get target entity pointer
0x3DF06: mov    bl, [di+75h]            ; *** Get TARGET entity type ***
0x3DF09: cmp    bl, 16h                 ; *** Is target type 0x16? ***
0x3DF0C: jnz    loc_3DF19               ; Target not 0x16, allow spawn

; Target is type 0x16, check permission
0x3DF0E: test   word ptr ds:15B4h, 40h  ; Check permission flag bit 6
0x3DF14: jnz    loc_3DF19               ; If bit set, allow spawn
                                         ; Else fall through to deny

; --- DENY SPAWN ---
0x3DF16: clc                            ; Clear carry flag = DENY spawn
0x3DF17: jmp    loc_3DF1A

; --- ALLOW SPAWN ---
0x3DF19: stc                            ; Set carry flag = ALLOW spawn

; --- RETURN ---
0x3DF1A: pop    di
0x3DF1B: pop    bx
0x3DF1C: pop    ax
0x3DF1D: retn
```

---

## Logic Flow

```
Entry: Weapon spawn requested
    ↓
Check: ds:15B3h (game mode)
    ↓
    ├─ == 0 → ALLOW (multiplayer disabled? normal mode?)
    │
    └─ != 0 → Check restrictions:
        ↓
        Check: Self entity type [si+6][+75h]
        ↓
        ├─ == 0x16 → Check permission ds:15B4h bit 0
        │            ↓
        │            ├─ Bit set → ALLOW
        │            └─ Bit clear → DENY
        │
        └─ != 0x16 → Check target entity
            ↓
            Has target ([si+18h] != 0xFFFF)?
            ↓
            ├─ YES → Load target entity
            │        Check target type [target+75h]
            │        ↓
            │        ├─ == 0x16 → Check permission ds:15B4h bit 6
            │        │            ↓
            │        │            ├─ Bit set → ALLOW
            │        │            └─ Bit clear → DENY
            │        │
            │        └─ != 0x16 → ALLOW
            │
            └─ NO → Check permission ds:15B4h bit 6
                    ↓
                    ├─ Bit set → ALLOW
                    └─ Bit clear → DENY
```

---

## Key Fields & Flags

### Entity Type Field
- **Location:** [entity+0x75] (offset 117 decimal)
- **Type:** byte
- **Special value:** **0x16 (decimal 22)**

**Type 0x16 significance:**
- Has special weapon spawn restrictions
- Cannot spawn weapons against type 0x16 targets unless permission bit set
- Cannot spawn weapons from type 0x16 entity unless permission bit set

**Hypothesis:** Type 0x16 = **FRIENDLY AIRCRAFT** or **PLAYER TEAM**
- Prevents friendly fire
- Multiplayer blue/red team separation
- Campaign friendly AI protection

### Game Mode Flag
- **Location:** ds:15B3h
- **Type:** byte
- **Values:**
  - 0 = Normal mode (no restrictions)
  - Non-zero = Restricted mode (check permissions)

**Hypothesis:** ds:15B3h = **Multiplayer/Training mode flag**
- 0 = Single player campaign (all spawns allowed)
- 1+ = Multiplayer or training (friendly fire protection)

### Permission Flags
- **Location:** ds:15B4h
- **Type:** word (2 bytes, 16 bits)

**Bits used:**
- **Bit 0 (0x0001):** Allow type 0x16 entity to spawn weapons
- **Bit 6 (0x0040):** Allow weapons against type 0x16 targets

**Example permission configurations:**
```
ds:15B4h = 0x0000  →  No 0x16 spawns, no 0x16 targets (full friendly fire protection)
ds:15B4h = 0x0001  →  Type 0x16 can fire, but not at other 0x16 (one-way)
ds:15B4h = 0x0040  →  Can target 0x16, but 0x16 can't fire (asymmetric)
ds:15B4h = 0x0041  →  Both allowed (friendly fire enabled)
ds:15B4h = 0xFFFF  →  All permissions (no restrictions)
```

### Target Slot Field
- **Location:** [si+18h]
- **Type:** word
- **Special value:** 0xFFFF = no target
- **Purpose:** References tracked/targeted entity slot

---

## Weapon Spawn Call Sites

### From sub_3CE92 (Behavior Dispatcher)

**Call Site 1: @ 0x3D2D8**
```asm
0x3D2D8: call   loc_3DED9       ; Check spawn permission
0x3D2DB: jnb    loc_3D2E3       ; Jump if NOT below (carry clear = denied)
0x3D2DD: or     byte ptr [si+0Ah], 8  ; Set "weapon active" flag
```

**Context:** After collision detection, called when certain behavior conditions met.

**Call Site 2: @ 0x3D2E3**
```asm
0x3D2E3: call   loc_3DED9       ; Check spawn permission
0x3D2E6: jb     loc_3D30D       ; Jump if below (carry set = allowed)
```

**Context:** Alternative spawn path, behavior state machine.

**Call Site 3: @ 0x3D450** (from BEHAVIOR_DISPATCHER_ANALYSIS.md)
```asm
0x3D450: call   loc_3DED9       ; Check spawn permission
0x3D453: jnb    loc_3D459       ; Denied
0x3D455: or     byte ptr [si+0Bh], 40h  ; Set behavior flag bit 6
```

**Context:** Another behavior state, sets different flag on spawn.

---

## Weapon Spawn Flow (Complete)

```
[1] Player presses 'z' key
    ↓
[2] Input handler sets "fire requested" flag in aircraft entity
    (Exact flag location TBD - likely [entity+0x0A] or [entity+0x0B])
    ↓
[3] Next frame: sub_3CE92 (behavior dispatcher) runs for aircraft entity
    ↓
[4] sub_3CE92 checks behavior flags
    ↓
    Conditions checked:
    - Fire requested flag set?
    - Ammo available? (farobj_index_decrement_step)
    - Target locked? ([entity+0x29h] != 0xFF)
    - Weapon ready? (reload timer, weapon selected, etc.)
    ↓
[5] If all conditions met → Call loc_3DED9 (spawn permission check)
    ↓
    ├─ DENIED (carry clear) → Clear fire flag, abort spawn
    │
    └─ ALLOWED (carry set) → Continue to spawn
        ↓
[6] Actual spawn call (TBD - needs more analysis of sub_3DC55)
    Likely: object_farptr_dispatch @ loc_345FD (seen @ 0x3DECC)
    Creates new weapon entity with:
    - Position: At aircraft weapon hardpoint
    - Velocity: Aircraft velocity + launch velocity
    - Orientation: Aircraft heading or target direction
    - Type: Weapon type ID (missile, bomb, bullet)
    - Target: Locked target entity ([parent+0x29h])
    ↓
[7] Weapon entity spawned, gets its own sub_3CE92 updates
    ↓
[8] Weapon guidance (if missile):
    - Load target: sub_307A5
    - Pursue target: sub_2F6D0 (guidance algorithm)
    - Update physics: sub_30882
    - Check collision: sub_32453
    - Apply damage on hit: sub_32393
```

---

## Type 0x16 Detailed Analysis

### Evidence

1. **Special spawn restrictions** - Only type checked in spawn gate
2. **Permission bits required** - Two separate permission flags
3. **Both self and target checked** - Can't fire, can't be fired at
4. **Multiplayer mode dependent** - Only enforced when ds:15B3h != 0

### Hypothesis: Type 0x16 = Friendly Aircraft

**Supporting evidence:**
- Needs permission to attack → Friendly fire protection
- Needs permission to be attacked → Can't shoot friendlies
- Multiplayer mode specific → Blue vs Red teams
- Campaign mode bypass (ds:15B3h=0) → No friendlies in solo missions?

**Alternative hypothesis: Type 0x16 = Player Aircraft**
- Only player needs spawn permission checks
- Prevents player-on-player in multi?
- But why target check? Unless co-op mode exists

**Most likely:** Type 0x16 = **Team/Friendly designation**
- In multiplayer: Your team
- In campaign: Allied aircraft
- Permission system: Friendly fire on/off toggle

---

## Other Entity Types

From previous analysis:

| Type | Decimal | Hypothesis | Evidence |
|------|---------|------------|----------|
| **0x10** | 16 | Special class | 1× check in sub_3CE92 |
| **0x16** | 22 | **Friendly aircraft** | Spawn restrictions, FF protection |
| **0x33** | 51 | **Player/Advanced AI** | 4× checks, complex physics, target search |

**Weapon types (still TBD):**
- 0x12, 0x13 (missiles?)
- 0x14 (bombs?)
- 0x33-0x37 (bullets? - but 0x33 conflicts with aircraft type!)
- 0x38 (special weapon?)

**Note:** Type 0x33 collision - could be:
1. Context-dependent (different table lookup)
2. Type at different offset for weapons
3. Our hypothesis wrong about 0x33 being aircraft

Need to check farobj_queue_drain_dispatch @ sub_4C19E for weapon type dispatch.

---

## Next Steps

### Immediate
1. **Find actual weapon spawn call** - Where is entity created after permission granted?
2. **Trace object_farptr_dispatch** @ loc_345FD - Entity creation dispatcher
3. **Find fire flag location** - Which bit in [entity+0x0A] or [entity+0x0B]?
4. **Map permission system** - Full ds:15B4h bit meanings

### Medium
5. **Trace weapon type assignment** - Where does weapon get its type ID?
6. **Find weapon data tables** - Speed, damage, range per type
7. **Map weapon hardpoint system** - Where on aircraft are weapons mounted?
8. **Analyze ammo decrement** - farobj_index_decrement_step implementation

### Analysis
9. **Resolve type 0x33 conflict** - Aircraft or bullet type?
10. **Complete entity type table** - All type IDs and meanings
11. **Document friendly fire system** - Complete permission bit mask

---

## Key Insights

### Friendly Fire Protection is BUILT-IN!

This is sophisticated multiplayer design for 1991:
- Type-based team designation
- Permission system for FF control
- Clean separation of spawn logic from game mode

### Spawn is Multi-Step Validation

Not just "press button → spawn weapon". Instead:
1. Fire request flag
2. Behavior dispatcher checks conditions
3. Permission gate check
4. Actual entity creation
5. Physics/guidance updates

**Very robust and flexible architecture!**

### Carry Flag Return Convention

```c
bool check_spawn_permission(Entity* self) {
    // Returns via CPU carry flag:
    // carry SET (1) = ALLOWED
    // carry CLEAR (0) = DENIED
    
    // Caller checks with: jb (jump if below = jump if carry)
}
```

Standard x86 convention - carry flag for success/failure in low-level code.

---

## Remaining Questions

1. **What is ds:15B3h exactly?**
   - Multiplayer mode? Training mode? Mission type?

2. **What are other ds:15B4h bits?**
   - 16 bits total, only 2 documented (bits 0, 6)
   - Likely: weapon enable/disable, god mode, etc.

3. **Where is fire button → flag set?**
   - Input handler sets [entity+0x??] bit ??
   - Need to trace keyboard 'z' key processing

4. **How are weapon hardpoints selected?**
   - Left wing, right wing, fuselage, centerline
   - Load balancing, sequential launch, player choice?

5. **Do different weapons have different spawn logic?**
   - Missiles vs bombs vs guns
   - Different permission checks per type?

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: Spawn gate decoded, friendly fire system revealed, spawn flow mapped*

