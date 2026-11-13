# Weapons Launch Mechanism - Analysis

**Date:** November 11, 2026  
**Session:** 4  
**Status:** Building understanding of weapon firing flow

---

## Overview

This document traces the weapon launch mechanism from player input to weapon entity spawn.

---

## Launch Flow (Hypothesis)

```
Player Input (z key)
    ↓
Keyboard Handler
    ↓
Weapon Fire Command
    ↓
Check: Weapon Selected? Ammo Available? Target Lock (if required)?
    ↓
[YES] → Weapon Launch Function
    |       ↓
    |   Decrement Ammo (farobj_index_decrement_step)
    |       ↓
    |   Create Weapon Entity
    |       ↓
    |   entity_slot_create @ sub_2ECAC (Level 6)
    |       ↓
    |   Initialize Weapon State
    |       - Position: At aircraft weapon station
    |       - Velocity: Aircraft velocity + launch velocity
    |       - Orientation: Aircraft heading (or lock target direction)
    |       - Type: Weapon type ID (12h, 13h, 14h, etc.)
    |       - Target: Locked target entity (if guided)
    |       ↓
    |   Add to Entity Update List
    |       ↓
    |   farobj_slot_step_spawn @ sub_2FF24
    |       (called from game_frame_update_chain)
    |       ↓
[NO] → Return (no action)

Every Frame:
    ↓
farobj_behavior_dispatch_step @ sub_3CE92
    ↓
For each weapon entity:
    ↓
Check Weapon Type → Dispatch to handler
    ↓
    ├─ Guided Missile (12h, 13h?)
    │   ↓
    │   Target still valid?
    │   ↓
    │   Calculate steering toward target
    │   ↓
    │   Apply thrust/drag
    │   ↓
    │   Update velocity/orientation
    │
    ├─ Unguided Bomb (14h?)
    │   ↓
    │   Apply gravity
    │   ↓
    │   Apply drag
    │   ↓
    │   Update velocity
    │
    └─ Gun Bullet (33h-37h?)
        ↓
        Simple ballistics
        ↓
        Lifetime decrement
        ↓
        If lifetime == 0 → Remove entity
    ↓
Update Position (pos_step_chain_engine)
    ↓
Check Collision
    ↓
    ├─ Hit Target → Apply Damage, Explode, Remove entity
    └─ Miss → Continue or (Timeout/Ground hit → Remove entity)
```

---

## Key Functions Mapped

### Input Layer
- **Keyboard Handler:** Unknown function (needs tracing)
  - Monitors 'z' key for fire
  - Monitors 'e' key for A-A weapon cycle
  - Monitors 'B' key for A-G weapon cycle / mode switch
  
- **key_input_state_reset** @ sub_32C62 (caller) - Reset keyboard state

### Weapon Selection Layer
- **ui_loadout_menu_enter** @ multiple overlay thunks
  - sub_2C56D, sub_2C62B, sub_2C577, sub_2C6C1, sub_2C833, sub_2C4C3
  - Pattern: `call tail_bridge_overlay_load; jmp ui_loadout_menu_enter`
  - Overlay-based (code swapped in on demand)
  - Pre-mission weapon selection UI
  
- **Current Weapon State:** Unknown storage location (needs finding)
  - A-A vs A-G mode flag
  - Selected weapon index
  - Ammo remaining per weapon type

### Ammo Management
- **farobj_index_decrement_step** @ unknown address
  - Called from far_mode_event_dispatch @ sub_33443
  - Context: `mov ax, cs:word_2E126+1; call farobj_index_decrement_step`
  - Likely decrements weapon count when fired
  
### Entity Creation Layer
- **entity_slot_create** @ sub_2ECAC (Level 6)
  - Allocates entity slot
  - Initializes basic entity structure
  - Returns entity pointer/index
  
- **farobj_slot_create_gate** @ sub_3DC55 (Level 19)
  - Gate/guard function for farobj creation
  - May check resource limits, validity
  - Calls entity_slot_create if allowed
  
- **entity_spawn_from_tile** @ sub_301FB (Level 19)
  - Spawns entity from tile/map data
  - Used for static objects, may not be weapon-related
  - Called from game_state_load_apply @ sub_3001E
  
- **farobj_slot_step_spawn** @ sub_2FF24 (Level 19)
  - Spawn step in main frame update
  - Called from game_frame_update_chain @ sub_2FEF2 (300B)
  - Processes pending entity spawns each frame

### Behavior/Update Layer
- **farobj_behavior_dispatch_step** @ sub_3CE92 (2580B, Level 19, DATA class)
  - Master behavior dispatcher for all farobj entities
  - 25 callees including weapon-related functions
  - Called by multiple high-level functions
  - **This is where weapon guidance/ballistics happen!**
  
  **Key callees:**
  - fixed_vec3_accumulate_a (L0) - Vector math
  - far_obj_field_call (L1) - Dynamic field dispatch
  - farobj_field_set (L1) - Set entity fields
  - farobj_cfg_delta_apply (L1) - Apply configuration deltas
  - sub_2F6D0 (L19) - Large subsystem (1123B)
  - sub_3001E (L19) - game_state_load_apply (745B)
  - sub_307A5 (L19), sub_30882 (L19), sub_30CB8 (L19) - Unknown subsystems
  - sub_32393 (L19), sub_32453 (L19), sub_3252B (L19) - More subsystems
  - sub_3DC55 (L19) - farobj_slot_create_gate
  
- **farobj_queue_drain_dispatch** @ sub_4C19E (2500B, Level 19)
  - Drains farobj queue
  - Class-range dispatch on BX (12h/13h, 33h-37h)
  - Stride: 0x1B (27 bytes) per record
  - Pops from cs:word_2E10A
  - Calls sub_3CE92 (behavior_dispatch_step)

### Position Integration
- **pos_step_chain_engine** @ sub_3B338 (852B, Level 17)
  - Integrates position from velocity
  - Frame-rate independent (uses word_2E139 = 64)
  - Called for all entities including weapons

---

## Target Lock System

### A-A Mode (Air-to-Air)

**Visual Feedback:**
- Diamond in Aiming Reticle = missile seeking indicator
- Reticle FLASHES = lock maintained
- No flash = no lock

**Lock Conditions:**
1. Enemy in Aiming Reticle (angle cone)
2. Enemy within visual range (distance threshold)
3. Both conditions maintained = lock

**Lock State:**
- Per-frame check (not sticky)
- Lost immediately if conditions fail
- Player action: Press 'z' to fire while locked

### A-G Mode (Air-to-Ground)

**Guided Weapons (AGM-65, GBU-15):**
- Cross hairs appear in Aiming Reticle
- Auto-lock when target enters reticle
- Cross hairs FOLLOW target
- Press 'z' to fire
- **Fire-and-forget:** Weapon self-guides after launch
- Player can lock next target immediately

**Unguided Weapons (LAU, Gun):**
- Bombsight: targeting dot with circle
- Manual aiming (no lock)
- Press 'z' when dot on target

### Lock Implementation (Hypothesis)

**Data needed:**
- Player aircraft position & orientation
- Target entity position
- Aiming reticle cone angle (field of view)
- Visual range threshold (per weapon type?)
- Lock state flag (per weapon? or global?)

**Algorithm:**
```c
bool check_target_lock(Entity* aircraft, Entity* target, WeaponType weapon) {
    // 1. Calculate angle from aircraft to target
    vec3 to_target = target->pos - aircraft->pos;
    float distance = length(to_target);
    vec3 direction = normalize(to_target);
    
    // 2. Check if in reticle cone
    float dot_product = dot(aircraft->forward, direction);
    float cone_angle = weapon->lock_cone_angle;  // e.g., 10 degrees
    if (dot_product < cos(cone_angle)) {
        return false;  // Outside cone
    }
    
    // 3. Check distance (visual range)
    float visual_range = weapon->lock_range;  // e.g., 5000 meters
    if (distance > visual_range) {
        return false;  // Too far
    }
    
    // 4. Check line-of-sight (terrain occlusion?)
    if (terrain_blocks_los(aircraft->pos, target->pos)) {
        return false;  // Blocked
    }
    
    // All conditions met
    return true;
}
```

**Functions to find:**
- Target selection (T key cycles targets)
- Lock check per frame
- Lock state storage
- Visual feedback triggers (reticle flash)

---

## Missile Guidance (Hypothesis)

### Proportional Navigation

Classic guided missile algorithm:

```c
void missile_guidance_step(Entity* missile, Entity* target, float dt) {
    // 1. Calculate line-of-sight (LOS) to target
    vec3 to_target = target->pos - missile->pos;
    float distance = length(to_target);
    vec3 los = normalize(to_target);
    
    // 2. Calculate LOS rate (how fast angle changes)
    vec3 los_prev = missile->los_prev;  // Saved from last frame
    vec3 los_rate = (los - los_prev) / dt;
    missile->los_prev = los;  // Save for next frame
    
    // 3. Proportional navigation: acceleration perpendicular to LOS
    float nav_constant = 3.0;  // Typical value
    vec3 lateral_accel = nav_constant * missile->speed * los_rate;
    
    // 4. Apply steering (adjust velocity)
    missile->velocity += lateral_accel * dt;
    
    // 5. Maintain speed (thrust compensates for drag)
    missile->velocity = normalize(missile->velocity) * missile->speed;
    
    // 6. Update orientation to match velocity
    missile->forward = normalize(missile->velocity);
}
```

### Lead Pursuit (Simpler)

Point missile ahead of target:

```c
void missile_lead_pursuit(Entity* missile, Entity* target) {
    // 1. Calculate intercept point
    vec3 to_target = target->pos - missile->pos;
    float distance = length(to_target);
    float time_to_intercept = distance / missile->speed;
    
    // 2. Predict target position
    vec3 target_future = target->pos + target->velocity * time_to_intercept;
    
    // 3. Steer toward predicted position
    vec3 desired_dir = normalize(target_future - missile->pos);
    
    // 4. Apply steering (with turn rate limit)
    vec3 current_dir = normalize(missile->velocity);
    float max_turn_rate = missile->max_turn_rate;  // radians per second
    vec3 new_dir = steer_toward(current_dir, desired_dir, max_turn_rate * dt);
    
    // 5. Update velocity
    missile->velocity = new_dir * missile->speed;
}
```

**In farobj_behavior_dispatch_step @ sub_3CE92:**
- Check weapon type (12h, 13h for missiles?)
- Call guidance function
- Update velocity/orientation
- Check proximity to target
- If close enough → Detonate (spawn explosion, damage target, remove missile)

---

## Bomb Ballistics (Hypothesis)

Unguided bombs use simple physics:

```c
void bomb_ballistics_step(Entity* bomb, float dt) {
    // 1. Apply gravity
    vec3 gravity = vec3(0, 0, -9.8);  // m/s^2 downward
    bomb->velocity += gravity * dt;
    
    // 2. Apply drag (air resistance)
    float drag_coeff = bomb->drag_coefficient;
    float speed = length(bomb->velocity);
    vec3 drag = -0.5 * drag_coeff * speed * bomb->velocity;
    bomb->velocity += drag * dt;
    
    // 3. Update position (done in pos_step_chain_engine)
    // bomb->pos += bomb->velocity * dt;
    
    // 4. Check ground collision
    if (bomb->pos.z <= terrain_height(bomb->pos.x, bomb->pos.y)) {
        // Hit ground → Detonate
        spawn_explosion(bomb->pos);
        apply_area_damage(bomb->pos, bomb->blast_radius, bomb->damage);
        remove_entity(bomb);
    }
}
```

**Implementation likely in:**
- farobj_behavior_dispatch_step @ sub_3CE92
- Type 14h handler (if 14h == bombs)
- Much simpler than missile guidance

---

## Gun Ballistics (Hypothesis)

Bullets are high-speed projectiles:

```c
void bullet_step(Entity* bullet, float dt) {
    // 1. Velocity set at spawn (aircraft velocity + muzzle velocity)
    //    No guidance, no thrust
    
    // 2. Optional: slight drag (bullets are fast, drag minimal)
    // bullet->velocity -= drag * dt;
    
    // 3. Optional: gravity drop (small over short time)
    // bullet->velocity.z -= 9.8 * dt;
    
    // 4. Update position (pos_step_chain_engine)
    // bullet->pos += bullet->velocity * dt;
    
    // 5. Decrement lifetime
    bullet->lifetime -= dt;
    if (bullet->lifetime <= 0) {
        remove_entity(bullet);  // Despawn after ~2-3 seconds
    }
    
    // 6. Check collision each frame (expensive with many bullets!)
    //    May use spatial partitioning or simplified checks
}
```

**Why 5 gun bullet types (33h-37h)?**
- Different calibers? (unlikely, F-16 has M61A1 20mm)
- Tracer / non-tracer variants
- Hit registration (different damage per bullet?)
- Or: not all gun related (some might be other projectiles)

---

## Collision Detection (TBD)

Need to find:
- Bounding box/sphere for entities
- Collision check function
- Per-frame or spatial partitioning?
- Weapon vs target collision
- Weapon vs terrain collision

---

## Damage System (TBD)

Need to find:
- Target health field in entity
- Damage calculation (weapon damage value)
- Health decrement function
- Destruction trigger (health <= 0)
- Explosion spawn
- Score increment

---

## Next Steps

### High Priority
1. **Find keyboard fire handler**
   - Trace from key_input_state_reset or similar
   - Look for scan code 0x2C (z key)
   - Find weapon fire dispatch

2. **Extract sub_3CE92 disassembly**
   - 2580 bytes of farobj_behavior_dispatch_step
   - Find weapon type switch/dispatch
   - Identify guidance algorithms

3. **Find weapon state storage**
   - Current weapon selected (A-A/A-G, index)
   - Ammo remaining per type
   - Lock state

4. **Trace entity_slot_create**
   - Understand entity allocation
   - Find entity structure size
   - Map initialization

### Medium Priority
5. Find target selection function (T key)
6. Find lock check function
7. Find collision detection
8. Find damage calculation
9. Extract weapon data table (type → stats)
10. Map weapon entity structure fields

---

## Current Understanding

**Launch:** 30% ⚠️ (spawn functions found, trigger not found)  
**Guidance:** 25% ⚠️ (algorithm hypothesis, code not found)  
**Ballistics:** 20% ⚠️ (physics hypothesis, implementation TBD)  
**Collision:** 5% ❓ (not found)  
**Damage:** 5% ❓ (not found)

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: Launch flow mapped, awaiting code extraction*

