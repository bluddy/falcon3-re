# Falcon 3.0 Weapons System Architecture

**Status:** 75% Complete  
**Last Updated:** 2026-11-17  
**Based on:** WEAPONS_FINAL_ASSESSMENT.md, WEAPON_TYPES_DECODED.md, weapon_lock_search.json

---

## Overview

The Falcon 3.0 weapons system implements multiple weapon types with varying guidance systems:
- **Guns:** Ballistic, shoot-ahead prediction
- **IR Missiles (AIM-9):** Heat-seeking, require IR lock
- **Radar Missiles (AIM-120):** Radar-guided, require radar lock
- **A-G Missiles (AGM-88 HARM):** Anti-radiation, lock onto enemy radars
- **Dumb Bombs:** Simple gravity drop

---

## Weapon Type System

### Weapon Type IDs

| Type | Weapon | Guidance | Lock Required | Damage Tier |
|------|--------|----------|---------------|-------------|
| **0x12** | AIM-9 Sidewinder | IR heat-seeking | **YES** (IR) | 5 |
| **0x13** | AIM-120 AMRAAM | Radar-guided | **YES** (Radar) | 2 |
| **0x33** | M61A1 Vulcan 20mm | Ballistic | NO | 5 |
| **0x34-0x37** | Gun variants | Ballistic | NO | 2-6 |
| **0x14-0x32** | Bombs/A-G missiles | Various | Varies | Various |

**Source:** `weapon_type_initialize_dispatch` @ 0x4C19E (548 bytes)

### Type Ranges

**Missiles (0x12-0x13):**
```c
if (weapon_type >= 0x12 && weapon_type <= 0x13) {
    // Guided missiles - require lock
    initialize_missile_parameters();
}
```

**Guns (0x33-0x37):**
```c
if (weapon_type >= 0x33 && weapon_type <= 0x37) {
    // Ballistic guns - no lock required
    initialize_gun_parameters();
}
```

**Gap (0x14-0x32):**
- Likely bombs, A-G missiles (AGM-65 Maverick, AGM-88 HARM)
- Different initialization path or handled by separate dispatcher

---

## Weapon Parameters

### AIM-9 Sidewinder (Type 0x12)

**Initialization @ 0x4C20E-0x4C26B:**

```c
struct WeaponInit {
    void* entity_ptr;          // +0x00: Entity pointer
    uint16_t flags;            // +0x02: 0x0412
    uint16_t velocity;         // +0x04: 6645 (initial speed)
    uint16_t param_06;         // +0x06: 48
    uint16_t zero_08;          // +0x08: 0
    uint16_t param_0A;         // +0x0A: 4414
    uint16_t param_0C;         // +0x0C: 2088
    uint16_t param_0E;         // +0x0E: 103
    // ... +0x10-0x13 unused
    uint16_t max_speed;        // +0x14: 506 (max velocity)
    uint8_t  counter;          // +0x16: 0
    uint16_t param_18;         // +0x18: from cs:word_2E110
    uint8_t  damage_tier;      // +0x1A: 5 (damage level)
};

// Burst fire: 12 missiles (0x0C loop count)
for (int i = 0; i < 12; i++) {
    if (ammo_count < 128) {
        weapon->flags |= 0x1000;  // Set burst flag
    }
    spawn_missile();
}
```

**Key Parameters:**
- **Initial velocity:** 6645 units/sec
- **Max speed:** 506 units/sec
- **Damage tier:** 5 (high damage)
- **Burst:** 12 missiles spawned per fire event
- **Ammo check:** Max 128 rounds (cs:word_2E112)

### AIM-120 AMRAAM (Type 0x13)

**Different parameters @ 0x4C26C:**
- **Velocity:** 50127 units/sec (much faster)
- **Max speed:** 202 units/sec
- **Damage tier:** 2 (lower than Sidewinder)
- **Burst:** 1 missile (single shot)

### M61A1 Vulcan (Type 0x33)

**Gun parameters @ 0x4C2A0:**
- **Velocity:** 6645 units/sec (same as Sidewinder)
- **Max speed:** 506 units/sec
- **Damage tier:** 5
- **Burst:** 6 bullets per trigger pull
- **Ammo:** 512 rounds total

---

## Fire Control System

### Fire Request Flow

```
[Player presses fire button] (Space key, scan code 0x39?)
        │
        v
[Fire request flag set]
        │
        v
weapon_spawn_gate_validate (0x3DC55, 501 bytes)
        │
        ├─ Check game mode (DS:0x15B3)
        │   0 = normal combat (all weapons allowed)
        │   1+ = restricted mode (training, etc.)
        │
        ├─ Check friendly fire flags (DS:0x15B4)
        │   Type 0x16 = friendly aircraft
        │   Permission flags determine if fire allowed
        │
        ├─ Check ammo available (cs:word_2E112)
        │   Max 128 rounds per weapon type
        │
        └─ Check weapon lock status
            │
            ├─ Missiles (0x12, 0x13): Require lock
            │   └─ Check lock tone/status
            │
            └─ Guns (0x33-0x37): No lock required
                │
                v
        [PASS] → weapon_type_initialize_dispatch
                │
                v
        [Initialize weapon parameters]
                │
                v
        [Add to weapon queue]
        (27-byte stride @ cs:word_2E10A)
                │
                v
        [Burst fire loop]
        (6× for guns, 12× for Sidewinder, 1× for AMRAAM)
                │
                v
        [Entity slot allocation]
                │
                v
        [Weapon spawned in world]
```

### Fire Validation Functions

**1. weapon_spawn_gate_validate (0x3DC55)**
- **Size:** 501 bytes
- **Purpose:** Master fire gate - validates all fire conditions
- **Checks:**
  - Game mode restrictions
  - Friendly fire permissions
  - Ammo count
  - Lock status (for missiles)
  - Weapon compatibility

**2. ai_weapon_fire_check (0x3DED9)**
- **Size:** 69 bytes
- **Purpose:** AI-specific fire checks
- **Checks:**
  - AI behavior flags
  - Target validity
  - Range to target
  - Weapon ready state

**3. ai_weapon_range_check (0x3DE4A)**
- **Size:** 37 bytes
- **Purpose:** Check if target is within weapon range
- **Returns:** In-range / out-of-range boolean

---

## Lock Systems

### IR Lock (AIM-9 Sidewinder)

**Requirements:**
1. **Target must emit IR signature** (entity has heat source)
2. **Target must be within seeker cone** (typically ±10-20°)
3. **Target must be within range** (1-10 nm for rear-aspect)
4. **Lock tone must be achieved** (sustained track for ~1-2 seconds)

**Lock Process:**
```
[Player selects AIM-9]
        │
        v
[IR seeker scans for heat sources]
        │
        ├─ Check entity.heat_signature > threshold
        ├─ Check angle to target < seeker_cone
        └─ Check range < max_ir_range
        │
        v
[Lock tone begins] (audio feedback)
        │
        v
[Sustain lock for 1-2 seconds]
        │
        v
[Lock achieved] → Can fire
```

**Implementation Details:**
- **Entity field:** Likely +0x?? contains heat_signature value
- **Seeker cone:** Narrow (~10-20°) for all-aspect AIM-9M
- **Lock tone:** Generated by audio system, frequency increases with lock strength
- **Break lock:** Target maneuvers, flares, out of cone

### Radar Lock (AIM-120 AMRAAM)

**Requirements:**
1. **Target must be radar-visible** (entity.tracking_flags bit 0 = RADAR_VISIBLE)
2. **Radar must be in appropriate mode** (ACM or STT)
3. **Target must be tracked** (from radar system Z key lock)
4. **Target within missile range** (~20-40 nm)

**Integration with Radar System:**
```c
// From radar system analysis
if (radar_mode_state == 5) {  // STT (Single Target Track)
    // Target is locked by radar
    entity* target = get_locked_target();
    
    if (target->tracking_flags & ENTITY_TRACKING_RADAR_VISIBLE) {
        // Target has valid radar return
        amraam_lock_valid = true;
        
        // Check range
        uint16_t range = target->range;
        if (range >= amraam_min_range && range <= amraam_max_range) {
            can_fire_amraam = true;
        }
    }
}
```

**Lock Process:**
1. **Radar scan:** Detect target with radar system (F6 ACM mode)
2. **Z key:** Lock target (transitions radar to STT mode)
3. **AMRAAM select:** Weapon ready with radar lock
4. **Fire:** Launch missile with initial guidance from radar

**Missile Guidance Phases:**
- **Phase 1 (Launch):** Inertial navigation toward last known position
- **Phase 2 (Mid-course):** Radar updates from aircraft (datalink)
- **Phase 3 (Terminal):** Active radar seeker takes over

### HARM Lock (AGM-88)

**Requirements:**
1. **Enemy radar must be active** (entity emitting radar signal)
2. **HARM seeker detects radar emission**
3. **Lock onto radar frequency**
4. **Target within range** (~10-30 nm)

**Lock Process:**
```
[Player selects AGM-88 HARM]
        │
        v
[HARM seeker scans for radar emissions]
        │
        └─ Check entities with active_radar_emitter flag
           │
           ├─ SA-2/SA-3/SA-6 SAM radars
           ├─ Enemy aircraft radars
           └─ Ground radar stations
           │
           v
[Detect radar emission]
        │
        ├─ Identify frequency/type
        ├─ Measure bearing and strength
        └─ Check within HARM range
        │
        v
[Lock achieved] → Can fire
        │
        v
[Missile homes on radiation source]
        │
        ├─ If radar shuts off: Continue on last bearing (dead-reckoning)
        └─ If radar stays on: Active guidance to target
```

**Entity Field (Hypothetical):**
```c
struct Entity {
    // ... other fields ...
    uint8_t radar_emitter_active;  // Bit flag: radar is transmitting
    uint16_t radar_frequency;      // Frequency for HARM identification
    uint16_t radar_strength;       // Signal strength for HARM seeker
};
```

### No Lock Required (Guns & Bombs)

**Guns (0x33-0x37):**
- **Ballistic trajectory:** Bullets fly straight ahead
- **Lead computing gunsight:** Predicts target position
  - Compensates for target velocity
  - Compensates for bullet drop (gravity)
  - Displays pipper (aiming reticle) where bullets will hit
- **Player aims manually:** No automated tracking

**Dumb Bombs:**
- **Gravity drop:** Simple physics simulation
- **No guidance:** Bomb follows ballistic arc after release
- **CCIP (Continuously Computed Impact Point):**
  - HUD displays where bomb will impact
  - Updates based on aircraft speed, altitude, dive angle
  - Player maneuvers to place CCIP on target

---

## Weapon System Globals

### Code Segment Variables (CS:)

From WEAPON_TYPES_DECODED.md analysis of `weapon_type_initialize_dispatch` @ 0x4C19E:

- **`weapon_queue_head`** @ `cs:0x2E10A` (word)
  - Pointer to current weapon queue entry (27-byte stride)
  - Advanced by 0x1B after each processed weapon
  - Queue holds spawn requests waiting for type dispatch

- **`weapon_queue_count`** @ `cs:0x2E10C` (word)
  - Number of pending weapon spawn requests in queue
  - Decremented as weapons are processed
  - Checked against 0 before processing

- **`weapon_processed_count`** @ `cs:0x2E10E` (word)
  - Counter of weapons processed since last reset
  - Incremented after each weapon initialization

- **`weapon_spawn_value`** @ `cs:0x2E110` (word)
  - Value loaded during spawn (stored at weapon+0x18)
  - Purpose unclear - may be timestamp, sequence ID, or config index

- **`weapon_ammo_count`** @ `cs:0x2E112` (word)
  - Current ammunition count for selected weapon
  - Max 0x80 (128 rounds)
  - When at max, flag 0x1000 set during burst fire
  - Decremented per projectile in burst

### Data Segment Variables (DS:)

- **`weapon_game_mode`** @ `ds:0x15B3` (byte)
  - 0 = Normal combat
  - 1+ = Restricted fire modes (multiplayer/training)

- **`weapon_friendly_fire_flags`** @ `ds:0x15B4` (word)
  - Bit 0: Type 0x16 (friendly) can fire at all
  - Bit 6: Can target type 0x16 (friendly)
  - Used by spawn gate validation @ 0x3DED9

### Still Unidentified

These globals likely exist but have not been located yet:

- `radar_lock_status` - Radar missile lock state (integrates with radar STT mode @ 0x595B2)
- `harm_lock_status` - HARM lock state (tracking emitter)
- `selected_weapon_type` - Currently selected weapon (0x12/0x13/0x33/etc.)
- `trigger_pressed` - Fire button state (space bar)
- Entity field: `radar_emitter_active` for HARM lock targeting

### IR Lock System (AIM-9 Sidewinder) — ✅ IDENTIFIED

From analysis of `weapon_aim9_seeker_lock_check` @ 0x32B7F (IR_LOCK_ANALYSIS.md):

**Lock State Variables:**

- **`ir_lock_target_index`** @ `ds:0x44AA` (word)
  - Current IR lock target index or lock state
  - Values 0-3 in mode 0 (simple), 4-16 in mode 1 (extended)
  - When stable → IR lock acquired

- **`ir_lock_cycle_index_mode0`** @ `ds:0x44DB` (byte)
  - Cycle counter for simple search (4 targets, 0-3)
  - Incremented with (ax+1) & 3 pattern

- **`ir_lock_cycle_index_mode1`** @ `ds:0x44DC` (byte)
  - Cycle counter for extended search (13 targets, 4-16)
  - Wraps: if > 16, reset to 4

- **`ir_lock_status_byte`** @ `ds:0x4890` (byte)
  - Lock gate condition, compared to high byte of lock index
  - Enables/disables IR seeker

- **`ir_lock_entity_base`** @ `ds:0x48BA` (word)
  - Pointer to entity base for IR lock checks
  - Used as base for heat_signature field access @ [bx+si+0xAE]

- **`ir_lock_slot_mapping`** @ `ds:0x487E` (array[16])
  - Entity slot index mapping
  - Translates lock index (0-15) → entity slot ID

**IR Lock Algorithm:**
- 2 search modes controlled by `cs:ir_lock_search_mode`
- Mode 0: 4 potential targets (simple cycle 0-3)
- Mode 1: 13 potential targets (extended cycle 4-16)
- Cycles through targets each frame, checks `entity.heat_signature @ +0xAE`
- If heat_signature == 0: Target is cold, no lock
- If heat_signature != 0: Target is hot, can lock
- Lock tone triggered when `detection_mode_state` == 5

**Entity Field:**
- **`heat_signature`** @ EntitySlotRecord +0xAE (byte)
  - 0 = cold (no IR lock possible)
  - Non-zero = hot (IR lockable, likely from jet engines/exhaust)

**Next Steps:**
1. Analyze `weapon_aim9_seeker_lock_check` (0x32B8A) for IR lock globals
2. Analyze `weapon_ir_lock_tone_handler` (0x32C7F) for tone status global
3. Find radar lock integration with `radar_mode_state` (0x595B2) when STT=5
4. Trace keyboard handler for space bar → fire button flow

---

## Weapon Guidance Algorithms

### IR Missile Guidance (Proportional Navigation)

**Pseudocode:**
```c
void aim9_guidance_update(missile* m, entity* target) {
    // Get line-of-sight rate (how fast target moves across seeker view)
    float los_rate = compute_los_rate(m->position, m->velocity, 
                                      target->position, target->velocity);
    
    // Proportional navigation: Turn rate proportional to LOS rate
    float nav_constant = 3.0;  // Typical PN constant
    float commanded_accel = nav_constant * closing_velocity * los_rate;
    
    // Apply acceleration limits (missile G-limits)
    if (commanded_accel > max_g_accel) {
        commanded_accel = max_g_accel;
    }
    
    // Update missile orientation
    m->heading += commanded_accel * delta_time;
    m->pitch += commanded_accel * delta_time;
    
    // IR seeker continues tracking heat source
    if (target->heat_signature > threshold && 
        angle_to_target < seeker_fov) {
        // Maintain lock
        m->target_locked = true;
    } else {
        // Lost lock - go ballistic
        m->target_locked = false;
    }
}
```

### Radar Missile Guidance (Active Homing)

**Three Phases:**

**Phase 1: Inertial (0-10 seconds):**
```c
// Missile flies straight toward last known target position
vector3 target_position_last_known;
missile.velocity = missile.velocity + missile.thrust * delta_time;
// No corrections, saves fuel
```

**Phase 2: Mid-Course (~10-30 seconds):**
```c
// Aircraft radar provides target updates via datalink
if (datalink_active && range_to_target > active_seeker_range) {
    target_position = aircraft_radar_target_position;
    
    // Compute intercept course
    vector3 intercept_point = compute_lead_point(
        missile.position, 
        missile.velocity,
        target_position,
        target_velocity
    );
    
    // Proportional navigation to intercept
    missile.heading = turn_toward(intercept_point);
}
```

**Phase 3: Terminal (Last ~10 seconds):**
```c
// Missile's own radar seeker activates
if (range_to_target < active_seeker_range) {
    missile.active_radar_on = true;
    
    // Lock onto target with own radar
    if (target.radar_cross_section > threshold &&
        angle_to_target < seeker_cone) {
        // Active homing
        los_rate = compute_los_rate(...);
        commanded_accel = nav_constant * los_rate;
        missile.heading += commanded_accel * delta_time;
    }
}
```

### HARM Guidance (Passive Radiation Homing)

```c
void harm_guidance_update(missile* m) {
    // Scan for radar emissions
    entity* strongest_emitter = NULL;
    float max_signal_strength = 0;
    
    for (entity* e : all_entities) {
        if (e->radar_emitter_active) {
            float signal = e->radar_strength / distance_to(e);
            
            if (signal > max_signal_strength && 
                angle_to(e) < harm_seeker_cone) {
                strongest_emitter = e;
                max_signal_strength = signal;
            }
        }
    }
    
    if (strongest_emitter) {
        // Home on radiation source
        vector3 target_pos = strongest_emitter->position;
        float bearing = atan2(target_pos.y - m->position.y,
                             target_pos.x - m->position.x);
        
        // Proportional navigation
        float bearing_rate = (bearing - m->last_bearing) / delta_time;
        m->heading += nav_constant * bearing_rate * delta_time;
        m->last_bearing = bearing;
        
        m->target_locked = true;
    } else {
        // No radar detected - continue last bearing
        // (Dead-reckoning mode if radar shut off)
        m->target_locked = false;
    }
}
```

---

## Entity Fields for Weapons

### Weapon-Specific Entity Fields (Hypothetical)

| Offset | Name | Type | Purpose |
|--------|------|------|---------|
| +0x29 | `target_slot_id` | uint8 | Target entity ID (0xFF=none) |
| +0x?? | `heat_signature` | uint8 | IR emission level (0-255) |
| +0x?? | `radar_emitter_active` | flags8 | Bit 0: Radar transmitting |
| +0x?? | `radar_frequency` | uint16 | Frequency for HARM |
| +0x?? | `lock_timer` | uint16 | Frames lock sustained |
| +0x?? | `weapon_type_equipped` | uint8 | Current weapon selected |
| +0x?? | `lock_status` | flags8 | Bits: IR_LOCK, RADAR_LOCK, HARM_LOCK |

**From existing analysis:**
- **+0x74:** `status_flags` (ACTIVE, AIRCRAFT_TYPE)
- **+0x75:** `entity_type` (0x12=missile, 0x33=bullet)
- **+0x79:** `tracking_flags` (RADAR_VISIBLE)
- **+0x8E:** `angle_azimuth` (for guidance calculations)
- **+0x92:** `range` (distance to player/target)
- **+0x96/98/9A:** `position_x/y/z`

---

## Weapon Queue System

**Queue Structure @ cs:word_2E10A:**
- **Stride:** 27 bytes per entry (0x1B)
- **Max entries:** Unknown (likely 8-16)
- **Pointer:** cs:word_2E10A (queue head)
- **Count:** cs:word_2E10C (entries in queue)
- **Processed:** cs:word_2E10E (entries processed this frame)

**Queue Entry (27 bytes):**
```c
struct WeaponQueueEntry {
    void* entity_ptr;          // +0x00: Spawning entity
    uint16_t weapon_type;      // +0x02: Type ID (0x12/13/33-37)
    uint16_t flags;            // +0x04: Fire flags
    uint16_t velocity;         // +0x06: Initial velocity
    uint16_t params[8];        // +0x08-0x17: Type-specific params
    uint8_t damage_tier;       // +0x18: Damage level
    uint8_t burst_count;       // +0x19: Remaining burst
    uint8_t padding;           // +0x1A: Alignment
};
```

**Processing:**
```c
while (weapon_queue_count > 0) {
    WeaponQueueEntry* entry = weapon_queue_head;
    
    weapon_type_initialize_dispatch(entry);  // 0x4C19E
    
    weapon_queue_count--;
    weapon_queue_head += 27;  // Advance pointer
    weapon_queue_processed++;
}
```

---

## Globals

### Existing Weapon Globals

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| 0x15B3 | `weapon_game_mode` | byte | 0=normal, 1+=restricted fire |
| 0x15B4 | `weapon_friendly_fire_flags` | word | Friendly fire permissions |
| 0x5030 | `loadout_weapon_supply` | array[16] | Ammo counts (2B per type) |

### New Weapon Globals (To Add)

| Address | Name | Type | Purpose |
|---------|------|------|---------|
| cs:0x2E10A | `weapon_queue_head` | word | Weapon queue pointer |
| cs:0x2E10C | `weapon_queue_count` | word | Entries in queue |
| cs:0x2E10E | `weapon_queue_processed` | word | Entries processed |
| cs:0x2E110 | `weapon_param_word` | word | Shared weapon parameter |
| cs:0x2E112 | `weapon_ammo_count` | word | Current ammo (max 128) |
| DS:?? | `current_weapon_selected` | byte | Active weapon type |
| DS:?? | `ir_lock_status` | byte | IR lock strength (0-255) |
| DS:?? | `radar_lock_status` | byte | Radar lock validity |
| DS:?? | `harm_lock_status` | byte | HARM lock on emitter |
| DS:?? | `lock_tone_frequency` | word | Audio feedback for lock |

---

## Functions

### Key Weapon Functions

**Fire Control:**
- `weapon_spawn_gate_validate` (0x3DC55, 501B) - Master fire validation
- `ai_weapon_fire_check` (0x3DED9, 69B) - AI fire checks
- `ai_weapon_range_check` (0x3DE4A, 37B) - Range validation

**Weapon Initialization:**
- `weapon_type_initialize_dispatch` (0x4C19E, 548B) - Type dispatcher & init
- `weapon_helper_4d75f` (0x4D75F, 99B) - Weapon helper function

**Loadout Menu:**
- `ui_loadout_weapon_selector` (0x1632CD, 517B) - Weapon selection UI
- `menu_weapon_compatibility_check` (0x163C88, 69B) - Check weapon compatibility
- `menu_loadout_weapon_data_get` (0x163D33, 138B) - Get weapon data

**HUD/Tracking:**
- `hud_ai_target_tracking_draw` (0x425A2, 88B) - Draw target tracking box
- `hud_track_marker_draw` (0x42686, 70B) - Draw track marker
- `hud_track_distance_draw` (0x426CC, 101B) - Display range to target

---

## Remaining Analysis (25%)

### High Priority

1. **Lock Status Variables:**
   - Find `ir_lock_status` global location
   - Find `radar_lock_status` integration with radar system
   - Find `harm_lock_status` for anti-radiation missiles

2. **Fire Button Handler:**
   - Find keyboard scan code handler for fire button
   - Trace from input to `weapon_spawn_gate_validate`

3. **Entity Heat Signature:**
   - Find entity field for IR emission level
   - Determine how heat is computed (engine, afterburner, etc.)

4. **Radar Emitter Flags:**
   - Find entity field for radar transmission status
   - Map which entity types emit radar (SAMs, fighters)

5. **Guidance Algorithms:**
   - Find proportional navigation implementation
   - Analyze missile physics (thrust, drag, G-limits)
   - Find lead computation for guns

6. **Lock Tone Audio:**
   - Find audio system integration
   - Frequency modulation based on lock strength

### Medium Priority

7. **Bombs & A-G Weapons (Types 0x14-0x32):**
   - Find initialization for bomb types
   - CCIP (bomb impact point) calculation
   - Maverick missile guidance

8. **Countermeasures:**
   - Chaff (radar jamming)
   - Flares (IR decoy)
   - ECM (electronic counter-measures)

9. **Damage System Integration:**
   - How damage_tier maps to health reduction
   - Collision detection for bullets/missiles
   - Explosion effects

---

## Testing & Verification

### In-Game Testing

**IR Missiles (AIM-9):**
1. Select AIM-9 Sidewinder
2. Get behind enemy aircraft
3. Wait for lock tone (audio feedback)
4. Fire when tone is sustained
5. Observe missile tracking heat source

**Radar Missiles (AIM-120):**
1. Use radar F6 (ACM mode) to detect target
2. Press Z to lock target (radar enters STT mode)
3. Select AIM-120 AMRAAM
4. Fire - missile should guide to radar lock

**HARM:**
1. Select AGM-88 HARM
2. Wait for HARM seeker to detect radar emission
3. Lock indicator appears when emitter found
4. Fire - missile homes on radar source

**Guns:**
1. Select M61 Vulcan
2. Lead computing gunsight shows aim point
3. Fire - 6-round burst
4. No lock required - ballistic trajectory

### Memory Inspection

- `DS:0x15B3` = weapon_game_mode (0=normal)
- `DS:0x15B4` = weapon_friendly_fire_flags
- `cs:0x2E10C` = weapon_queue_count
- `cs:0x2E112` = weapon_ammo_count (max 128)
- Entity+0x29 = target_slot_id (0xFF if no target)

---

## Summary

✅ **Known (75%):**
- Weapon type system (0x12/13, 0x33-37)
- Fire control validation flow
- Weapon initialization parameters
- Queue system structure
- Integration with radar system (for AMRAAM)
- General guidance principles

❓ **Unknown (25%):**
- Exact lock status variables
- Fire button handler
- Heat signature fields
- Radar emitter fields
- Detailed guidance math
- Lock tone audio
- Bombs & A-G weapons (0x14-0x32)
- Countermeasures

**Next Steps:** Find lock status globals, fire button handler, and entity fields for heat/radar emissions.

---

**End of Weapons System Architecture Document**
