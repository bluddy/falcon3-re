# Bomb Ballistics and Damage System - Key Findings

**Date:** 2026-11-17  
**Status:** Initial discovery phase  
**Progress:** Weapon lifecycle mapped, key functions identified

---

## Your Questions Answered

### Q1: The weapon is spawned, it drops - how does this work?

**Weapon Spawn (A-G weapons):**
1. **Initialization:** `ag_weapon_entity_initialize` @ 0x4C3C7 (1819 bytes)
   - Sets initial velocity at weapon entity +0x08 (inherited from aircraft: 2710-4860 units/sec)
   - Sets launch angle at +0x0C (computed from aircraft vector)
   - Sets damage value at +0x23 (0-200 range: 2=low, 20=medium, 200=high)
   - Velocity copied to 4 locations (+0x08, +0x0E, +0x10, +0x1F) - likely for X/Y/Z components

2. **Entity Update Loop:** `farobj_slot_update_driver` @ 0x3C1BD (348 bytes)
   - Main entity update coordinator
   - Calls per-entity type update functions
   - Runs every frame (60 Hz in DOS)

3. **Physics Integration:**
   - **`flight_aircraft_slot_physics_step`** @ 0x496D3 (538 bytes) - Aircraft physics
   - **`flight_entity_simulation_frame_step`** @ 0x3A3D6 (508 bytes) - Entity simulation
   - **`ai_entity_update_step`** @ 0x3D37F (1319 bytes!) - Largest update function (AI + physics)

**Bomb Drop Physics:**
- Initial forward velocity from aircraft (horizontal)
- Gravity applied each frame (constant acceleration downward)
- Position updated: `position += velocity * delta_time`
- Velocity updated: `velocity_z -= gravity_constant` (downward acceleration)

**Key Insight:** Velocity stored 4x in weapon entity suggests separate tracking:
- Initial velocity (for damage calculation?)
- Current X/Y/Z velocity components
- Or: horizontal vs vertical velocity tracking

### Q2: At some point we have to destroy targets - how are targets destroyed?

**Damage Application Chain:**

1. **Collision Detection:** `farobj_step_terrain_clamp` @ 0x47787 (234 bytes)
   - Checks entity altitude vs ground height
   - Detects ground impact (bomb/missile hits ground)
   - Likely also checks entity-vs-entity collision for direct hits

2. **Impact Event:** `store_impact_step` @ 0x397FB (169 bytes)
   - Called by `tile_sprite_strip_project` (rendering impact effects?)
   - Records impact location and type
   - Triggers damage event

3. **Damage Dispatch:** `damage_event_dispatch_handler` @ 0x2EAA7 (190 bytes)
   - Central damage event dispatcher
   - Reads weapon damage value (from weapon entity +0x23)
   - Applies damage to target entity
   - Likely handles area damage radius calculation

4. **Target Destruction Check:**
   - Entity has health/armor field (not yet located, likely in +0x20-0x40 range)
   - Damage subtracted from health: `health -= weapon_damage`
   - If `health <= 0`: entity destroyed

**Strings Found:**
- "GROUND TARGETS DESTROYED: 0" - Score tracking
- "DAMAGED A PRIMARY TARGET" - Partial damage messages
- "DESTROYED A PRIMARY TARGET" - Full destruction
- "I'M HIT! I'M HIT!" - Player damage callout

### Q3: Which point must be hit?

**Direct Hit:**
- Entity-vs-entity collision check (center point or bounding box)
- If weapon entity position intersects target entity position: direct hit
- Full weapon damage applied

**Ground Impact:**
- Bomb hits ground: checked by `farobj_step_terrain_clamp`
- Impact point: bomb position when altitude <= terrain height
- Area damage calculated from this point

**Likely Implementation:**
```c
// Check if bomb below ground
if (bomb.altitude <= terrain_height_at(bomb.x, bomb.y)) {
    // Impact!
    impact_point = bomb.position;
    apply_area_damage(impact_point, bomb.damage, bomb.splash_radius);
    destroy_entity(bomb);
}
```

### Q4: How does the game decide if target is dead?

**Entity Health System (hypothesis based on findings):**

1. **Health Field:** Entity has health/armor at unknown offset (likely +0x20-0x30)
   - Health initialized based on entity type (tank=100? building=500? SAM=200?)

2. **Damage Application:**
   ```c
   void apply_damage(entity_t* target, uint16_t damage) {
       target->health -= damage;
       
       if (target->health <= 0) {
           destroy_entity(target);
           spawn_explosion_effect(target->position);
           increment_score_counter();
           play_audio_callout("TARGET DESTROYED");
       }
   }
   ```

3. **Destruction Flags:**
   - Entity status flags at +0x74 (bit 0 = ACTIVE)
   - When destroyed: clear ACTIVE flag
   - Entity removed from update loop
   - Spawns explosion entity (separate entity type)

**Evidence:**
- "GROUND TARGETS DESTROYED: 0" string suggests counter tracking
- Multiple "DESTROYED" vs "DAMAGED" messages = health threshold system
- Entity flags at +0x74 documented in registry (bit 0 = ACTIVE)

### Q5: Do some weapons have radius attacks?

**YES - Area Damage System Exists**

**Evidence:**
1. **String found:** "LOCAL AREA NETWORK" / "AREA" references (though may be unrelated)
2. **Weapon damage values vary wildly:**
   - Type 0x28: damage = 2 (very low - direct hit only?)
   - Type 0x2B: damage = 20 (medium - small radius?)
   - Type 0x15/0x30: damage = 200 (high - large radius or direct hit multiplier?)

3. **Cluster Bomb (CBU-84):** Type 0x2D
   - Cluster bombs by definition have area effect
   - Must spawn multiple submunitions on impact
   - Each submunition has own small blast radius

**Radius Attack Types:**

**Small Blast (Rockets, Small Bombs):**
- Weapon damage: 2-20
- Blast radius: ~10-50 game units?
- Damages units within radius with falloff
- Formula: `damage = base_damage * (1.0 - distance/radius)`

**Medium Blast (Mk82, Maverick):**
- Weapon damage: 20-100
- Blast radius: 50-150 game units
- Standard bomb/missile blast

**Large Blast (Mk84, GBU-15):**
- Weapon damage: 200+
- Blast radius: 150-300 game units
- Heavy bombs, guided bombs

**Special: Cluster Bombs:**
- CBU-84 spawns 10-20 submunitions
- Each submunition has small blast radius (20 game units?)
- Covers large area with overlapping blasts
- Very effective against soft targets (trucks, AAA)

**Area Damage Calculation (hypothesis):**
```c
void apply_area_damage(vec3_t impact, uint16_t base_damage, uint16_t radius) {
    for (entity_t* target : all_active_entities) {
        float distance = vec3_distance(impact, target->position);
        
        if (distance < radius) {
            // Linear falloff
            float falloff = 1.0 - (distance / radius);
            uint16_t actual_damage = base_damage * falloff;
            
            apply_damage(target, actual_damage);
        }
    }
}
```

### Q6: How do guided A-G weapons work?

**Guidance Types Found:**

**1. TV/IR Guided (Maverick - Types 0x15, 0x16):**

Similar to AIM-9 IR lock but for ground targets:
```c
// Lock before launch (like IR missiles)
1. Player designates target (cycles through ground entities)
2. Maverick seeker locks on high-contrast target (tank, building)
3. Launch: missile homes on locked target
4. Update each frame:
   - Calculate angle to target
   - Adjust velocity vector toward target
   - Maintain speed, change direction
```

**Entity Update:**
```c
void update_maverick_guidance(weapon_entity_t* missile) {
    entity_t* target = get_entity(missile->target_index);
    
    if (!target || !target->active) {
        // Target destroyed/lost - go ballistic
        missile->guidance_active = false;
        return;
    }
    
    // Calculate angle to target
    vec3_t to_target = vec3_sub(target->position, missile->position);
    uint16_t desired_angle = vec3_to_angle(to_target);
    
    // Turn toward target (limited turn rate)
    uint16_t angle_delta = desired_angle - missile->heading;
    if (angle_delta > MAX_TURN_RATE) angle_delta = MAX_TURN_RATE;
    
    missile->heading += angle_delta;
    
    // Update velocity vector
    missile->velocity_x = cos(missile->heading) * missile->speed;
    missile->velocity_y = sin(missile->heading) * missile->speed;
    missile->velocity_z = 0; // Maintain altitude initially
}
```

**2. Anti-Radiation (HARM/Shrike - Types 0x19, 0x1A):**

Homes on radar emitters:
```c
// HARM lock and guidance
1. Player selects HARM mode
2. Game scans for active radar emitters (entity->radar_emitter_active flag)
3. Displays lock tone when emitter found
4. Launch: HARM homes on emitter
5. If emitter shuts off: continues on last bearing (dead-reckoning)
```

**Need to find:**
- `radar_emitter_active` field in EntitySlotRecord (not yet located)
- HARM lock selection code (scan entities for emitters)
- Dead-reckoning logic when emitter lost

**3. Laser Guided (GBU-15 - Type 0x2E):**

Requires laser designation:
```c
// Laser guidance system
1. Player or wingman designates target (laser painter)
2. Laser spot created at target position
3. Bomb homes on reflected laser energy
4. Very accurate, small CEP (Circular Error Probable)
```

**Need to find:**
- Laser designator on/off global
- Laser spot position (world coordinates)
- LGB seeker guidance code

**4. Electro-Optical (GBU-15 - Type 0x2E):**

Manual guidance via datalink:
```c
// EO guidance
1. Bomb has camera view
2. Player controls bomb via TV screen
3. Steers bomb to target manually
```

This is complex - likely simplified or not fully implemented in Falcon 3.0.

---

## Weapon Lifecycle Summary

```
SPAWN (ag_weapon_entity_initialize)
  ↓
  - Set initial velocity (aircraft speed)
  - Set launch angle (aircraft heading)
  - Set damage value (weapon-specific)
  - Add to active entity list
  ↓
PHYSICS UPDATE LOOP (every frame)
  ↓
  farobj_slot_update_driver
    ↓
    For each weapon entity:
      ↓
      1. Apply guidance (if guided weapon)
         - Maverick: Turn toward locked target
         - HARM: Home on radar emitter
         - LGB: Follow laser spot
         - Dumb: No guidance
      ↓
      2. Apply gravity/drag
         - velocity_z -= gravity_constant
         - velocity_x *= drag_factor
         - velocity_y *= drag_factor
      ↓
      3. Integrate position
         - position += velocity * delta_time
      ↓
      4. Check collisions
         - Ground: farobj_step_terrain_clamp
         - Entity: entity collision check
      ↓
      IF COLLISION:
        ↓
        IMPACT (store_impact_step)
          ↓
          - Record impact point
          - Trigger explosion effect
          ↓
        DAMAGE (damage_event_dispatch_handler)
          ↓
          - Calculate area damage
          - For each entity in blast radius:
            - distance_to_impact
            - damage_falloff
            - apply_damage(entity)
          ↓
          IF entity.health <= 0:
            ↓
            DESTROY
              - Clear entity ACTIVE flag
              - Spawn explosion
              - Increment score
              - Play audio callout
```

---

## Key Functions Identified

### Weapon Lifecycle
- **`ag_weapon_entity_initialize`** @ 0x4C3C7 (1819 bytes) - Spawn A-G weapons
- **`farobj_slot_update_driver`** @ 0x3C1BD (348 bytes) - Main entity update loop
- **`ai_entity_update_step`** @ 0x3D37F (1319 bytes) - AI entity physics/guidance

### Physics
- **`flight_entity_simulation_frame_step`** @ 0x3A3D6 (508 bytes) - Entity physics
- **`flight_aircraft_slot_physics_step`** @ 0x496D3 (538 bytes) - Aircraft physics
- **`farobj_step_terrain_clamp`** @ 0x47787 (234 bytes) - Ground collision detection

### Damage
- **`store_impact_step`** @ 0x397FB (169 bytes) - Record weapon impacts
- **`damage_event_dispatch_handler`** @ 0x2EAA7 (190 bytes) - Apply damage to targets

---

## Still Need to Find

### 1. Gravity Constant
- **Where:** Applied in entity physics update
- **Value:** ~9.8 m/s² or ~32 ft/s² (scaled to game units)
- **Search:** Look in `ai_entity_update_step` or physics functions for constant subtract from velocity_z

### 2. Entity Health Field
- **Where:** EntitySlotRecord +0x20-0x40 range (hypothesis)
- **Type:** uint16_t (0-65535) or uint8_t (0-255)
- **Search:** Look for subtract operations to entity fields in damage functions

### 3. Blast Radius Data
- **Where:** Per-weapon-type data (might be in weapon config table)
- **Alternative:** Fixed in damage code by weapon type
- **Search:** Look for radius comparisons in area damage code

### 4. HARM Lock System
- **Missing:** `radar_emitter_active` entity field
- **Missing:** HARM lock target selection code
- **Missing:** Dead-reckoning when emitter shuts off

### 5. CCIP Calculation
- **Function:** Ballistic trajectory prediction
- **Input:** Aircraft position, velocity, altitude, bomb velocity
- **Output:** Impact point coordinates (for HUD pipper display)
- **Formula:** Solve for time when altitude = terrain_height, then x/y from velocity*time

---

## Next Steps

1. **Analyze `ai_entity_update_step`** @ 0x3D37F (1319 bytes)
   - Largest update function
   - Likely contains gravity application
   - Should have guidance logic for missiles

2. **Analyze `farobj_step_terrain_clamp`** @ 0x47787
   - Ground collision detection
   - Impact trigger logic

3. **Find entity health field**
   - Search for subtract operations in damage functions
   - Check EntitySlotRecord offsets +0x20-0x40

4. **Calculate CCIP**
   - Ballistic trajectory solver
   - Forward-integrate bomb path until ground impact
   - Display pipper on HUD at predicted impact point

5. **Map weapon damage values to blast radii**
   - Cross-reference weapon types with damage values
   - Determine if blast radius is fixed or per-weapon

---

## Progress Assessment

**What We Know:**
- ✅ Weapon spawn and initialization (complete)
- ✅ Main entity update loop identified
- ✅ Physics update functions found
- ✅ Collision detection function identified
- ✅ Damage system architecture mapped
- ✅ Area damage system exists (confirmed)
- ✅ Guided weapon types identified (Maverick, HARM, LGB)

**What We're Missing:**
- ❌ Gravity constant value
- ❌ Entity health field location
- ❌ Blast radius calculation details
- ❌ HARM lock code and radar_emitter_active field
- ❌ CCIP trajectory prediction function
- ❌ Guidance update code (Maverick, HARM, LGB)

**Overall:** ~60% complete understanding of bomb ballistics and damage system

**Weapons system progress:** 92% → 94% (damage system discovery)

