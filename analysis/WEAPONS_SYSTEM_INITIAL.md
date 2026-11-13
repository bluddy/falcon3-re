# Weapons System - Initial Investigation

**Date:** November 11, 2026  
**Status:** Starting from 30% → Building foundation

---

## Overview

Weapons in Falcon 3.0 are **FarObj entities** with specific type/class IDs that determine their behavior.

---

## Evidence Collected

### Weapon-Related Strings Found

**Data Symbols:**
- `aMissile` @ 0x54E90 (347664 decimal) - "Missile" string
- `aGunsGunsGuns` @ 0x57E9B (359579 decimal) - "Guns Guns Guns" string  
- `aBombsAway` @ 0x57EAD (359597 decimal) - "Bombs Away" string

**Context:** These are likely displayed during weapon firing/release

### Entity Type System

**Key Finding:** FarObj entities have type/class fields that determine behavior

**Functions:**
- `farobj_type_field_get` @ sub_2647E (46B, Level 3) - Lookup entity type via table @ 7B0E:3052
- `farobj_type_gate_test` @ sub_4BF8B (45B) - Tests if type in {12h, 14h, 33h, 38h}
- `object_type3_table_step` @ sub_264C5 (64B) - Process type==3 objects
- `farobj_class16_record_ops` @ sub_4D544 (638B) - Handle class==16h entities

**Type Field Locations:**
- `[di+22h]` = Type field (used by farobj_type_field_get)
- `[es:di+14h]` = Type check field (values: 12h, 14h, 33h, 38h)
- `[es:di+75h]` = Class field (value: 16h for special processing)
- `[es:di+3]` = Type nibble (used in tile_object_interpreter)

### Behavior/AI System

**Master Function:** `farobj_behavior_dispatch_step` @ sub_3CE92 (2580B, Level 19)

**Description:**
> "Master farobj entity behavior/AI step: many entry points; 3334h tile-wrap on si+31/32/33/35, far_obj_field_call + farobj_field_set type-3 thresholds, [si+0Bh] mode gates, speed/alt clamps"

**This likely handles:**
- Missile guidance
- Bomb ballistics
- Gun bullet trajectories
- AI aircraft behavior

### Queue & Dispatch System

**Function:** `farobj_queue_drain_dispatch` @ sub_4C19E (2500B)

**Description:**
> "FAR farobj queue drain: class-range dispatch on bx (12h/13h, 33h-37h), pops cs:word_2E10A records at 1Bh stride"

**Class Ranges:**
- 12h, 13h - One category
- 33h-37h - Another category (5 types)

**Hypothesis:** Different weapon types in different class ranges?

### HUD Tracking

**Functions:**
- `hud_track_label_strip` (mentioned in display_palette_hud_refresh_step)
- `hud_track_strip_pipeline` @ sub_4B36A
- `far_obj_visibility_gate` (291B) - Target selection with distance test

**Purpose:** Display weapon status and target tracking on HUD

---

## Hypothesis: Weapon Type System

### Likely Type Assignments

Based on class/type values found:

| Type/Class | Likely Weapon | Evidence |
|------------|---------------|----------|
| 12h | Missiles? | In farobj_type_gate_test set |
| 13h | Missiles? | In queue_drain class-range |
| 14h | Bombs? | In farobj_type_gate_test set |
| 33h-37h | Bullets/Projectiles? | 5 types in queue range |
| 38h | Unknown weapon | In farobj_type_gate_test set |
| 16h (class) | Special weapon? | Has dedicated handler |

### Weapon Categories (Hypothesis)

**1. Guided Missiles (types 12h, 13h?)**
- Active guidance via farobj_behavior_dispatch_step
- Target tracking
- Complex physics (thrust, drag, steering)
- Examples: AIM-9 Sidewinder, AIM-120 AMRAAM

**2. Unguided Bombs (type 14h?)**
- Ballistic trajectory
- Simpler physics (gravity, drag)
- No guidance after release
- Examples: Mk-82, Mk-84

**3. Gun Bullets (types 33h-37h?)**
- High-speed projectiles
- Short lifetime
- Simple ballistics
- 5 types might be: different calibers, tracer types, etc.

**4. Special Weapons (type 38h, class 16h?)**
- Unknown purpose
- Might be: AGM-65 Maverick, countermeasures, etc.

---

## Entity Structure (Weapons)

Based on FarObj entity knowledge:

```c
struct WeaponEntity {  // Extends FarObj
    // Standard FarObj fields (from Entity System)
    uint8_t  type;           // +0x03 or [di+22h] - Weapon type ID
    // ... position, velocity, orientation ...
    uint8_t  class_id;       // +0x75 or [es:di+75h] - Class (16h special?)
    uint16_t behavior_field; // +0x14 or [es:di+14h] - Behavior type
    
    // Weapon-specific fields (TBD)
    uint16_t target_id;      // Target entity reference?
    uint16_t damage;         // Damage value?
    uint16_t fuse_timer;     // Time to detonation?
    // ...
};
```

---

## Key Systems to Investigate

### 1. Weapon Launch/Fire

**Need to find:**
- Trigger function (when player presses fire button)
- Weapon selection code (which weapon to fire)
- Entity creation (spawn weapon entity)
- Initial velocity/heading assignment
- Ammo tracking/decrement

**Search for:**
- Key bindings for weapon fire
- Input handler for trigger
- Entity spawn for weapons
- Ammo counter decrements

### 2. Guidance Algorithms

**For Missiles:**
- Target acquisition/lock
- Proportional navigation?
- Lead calculation
- Steering commands to entity physics

**In farobj_behavior_dispatch_step:**
- Check for target tracking code
- Velocity/heading adjustments toward target
- Fuel/motor burn time
- Proximity detection for detonation

### 3. Ballistics

**For Bombs/Bullets:**
- Gravity application
- Drag calculation
- Wind effects?
- Ground impact detection

**Should be in:**
- Position integration (pos_step_chain_engine we already know)
- Or separate ballistics function
- Terrain collision detection

### 4. Damage System

**Need to find:**
- Hit detection (collision with target)
- Damage calculation (based on weapon type)
- Target health/damage tracking
- Kill confirmation
- Score tracking

**Search for:**
- Collision detection functions
- Health/damage fields in entities
- Explosion/destruction triggers

### 5. Weapon Loadout

**From menu system:**
- Player selects weapons before mission
- Stored in aircraft configuration
- Different aircraft → different weapon options
- Weight/performance impact?

**Search for:**
- Loadout menu code
- Weapon inventory structure
- Aircraft capability tables

---

## Next Investigation Steps

### Immediate (understand structure):
1. Find weapon entity spawn function
2. Map weapon type table @ 7B0E:3052
3. Trace farobj_behavior_dispatch_step for weapon handling
4. Find weapon fire trigger in input system

### Short-term (understand guidance):
5. Extract missile guidance algorithm from behavior dispatch
6. Find target selection/lock code
7. Document bomb ballistics
8. Map gun firing mechanism

### Medium-term (complete system):
9. Find damage calculation
10. Map weapon loadout system
11. Document ammo tracking
12. Extract weapon data (speed, damage, range per type)

---

## Key Functions Found (Session 4)

### Entity Creation & Spawning
- `entity_slot_create` @ sub_2ECAC (Level 6) - Main entity slot allocation
- `farobj_slot_create_gate` @ sub_3DC55 - FarObj creation with gate/guard
- `entity_spawn_from_tile` @ sub_301FB - Spawn entity from tile/map data
- `farobj_slot_step_spawn` @ sub_2FF24 - Spawn step in frame update loop
- Called from `game_frame_update_chain` @ sub_2FEF2 (300B, Level 19)

### Weapon Management
- `farobj_index_decrement_step` @ unknown - Decrements weapon/entity index (likely ammo tracking!)
- `ui_loadout_menu_enter` @ multiple overlay entries - Enter weapon loadout menu
  - Multiple thunks: sub_2C56D, sub_2C62B, sub_2C577, sub_2C6C1, sub_2C833, sub_2C4C3
  - All: `call tail_bridge_overlay_load; jmp ui_loadout_menu_enter`
  - Overlay-based (swapped in on demand)

### Input System
- `key_input_state_reset` @ sub_32C62 caller - Keyboard state management
- Fire key: 'z' (confirmed from manual)
- Mode switch: 'e' (A-A weapons), 'B' (A-G weapons or cycle A-G)

### Target Lock Mechanics (from Manual)
**A-A Mode (Air-to-Air):**
- Diamond appears in Aiming Reticle (missile seeking indicator)
- Automatic lock-on when enemy enters reticle AND within visual range
- Reticle FLASHES during lock maintenance
- Press 'z' to fire

**A-G Mode (Air-to-Ground):**
- AGM-65B/D, GBU-15: Cross hairs auto-lock and follow target
- Press 'z' to fire guided weapons
- Self-guiding after launch (fire-and-forget)
- Can lock onto next target immediately

**Lock Implementation Hypothesis:**
- Visual range check (distance threshold)
- Angle check (target in reticle cone)
- Lock state flag (maintained per frame)
- Visual feedback: flashing reticle

## Progress Estimate

**Current Understanding:**
- Entity type system: 60% ✅ (types found, structure TBD)
- Behavior dispatch: 40% ⚠️ (function found, internals TBD)
- Weapon types: 35% ⚠️ (hypothesis with categories)
- Launch mechanism: 30% ⚠️ (spawn functions found, trigger TBD)
- Guidance: 20% ⚠️ (lock mechanics from manual, algorithm TBD)
- Damage: 5% ❓ (no code evidence yet)
- UI/HUD: 40% ✅ (loadout menu, stores panel found)
- Ammo tracking: 25% ⚠️ (decrement function found)

**Overall Weapons System:** 30% → 40% after Session 4 investigation

---

## Questions to Answer

1. **How many weapon types exist?**
   - At least 8+ (based on types seen: 12h, 13h, 14h, 33h-37h, 38h, 16h)
   
2. **What's the difference between type and class?**
   - Type might be specific weapon (AIM-9 vs AIM-120)
   - Class might be category (missile vs bomb vs bullet)
   
3. **How does player fire weapons?**
   - Key binding? Joystick button?
   - Where in input system?
   
4. **Do different missiles use different guidance?**
   - AIM-9 = IR homing (heat-seeking)
   - AIM-120 = Radar guided
   - Different algorithms in behavior dispatch?
   
5. **How is ammo tracked?**
   - Per-weapon counters?
   - In aircraft entity or separate structure?
   
6. **What determines hit vs miss?**
   - Distance threshold?
   - Bounding box collision?
   - Probabilistic calculation?

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: Foundation built, ready for deep dive*
