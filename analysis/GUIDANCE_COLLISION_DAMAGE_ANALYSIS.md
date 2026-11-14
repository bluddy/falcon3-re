# Weapons System: Guidance, Collision & Damage Analysis

**Date**: November 11, 2026  
**Session**: Weapons Deep Dive (65% → 90%)  
**Focus**: Understanding guidance algorithms, collision detection, and damage calculation using manual knowledge

---

## Overview

Based on manual knowledge, we now know:
- **Three guidance types**: Infrared (heat), Radar (active), Ballistic (gun)
- **Lock-on stages**: Seeking → Tracking → Locked → "In Parameters"
- **Countermeasures**: Chaff (radar), Flares (heat), Maneuvers
- **Weapons**: AIM-9 (IR), AIM-120 (radar), M61A1 (ballistic)

This session maps code findings to these documented behaviors.

---

## Part 1: Guidance System Analysis

### Known Call Sites

From behavior dispatcher @ sub_3CE92:

```asm
; When entity has valid target:
0x3D186: call   near ptr loc_307AD+3   ; sub_307A5 - Load target entity
0x3D1AF: call   loc_2F6D6              ; sub_2F6D0 - Guidance/pursuit
0x3D1B2: call   near ptr sub_30882+2   ; sub_30882 - Physics update
0x3D1B5: call   near ptr loc_308E5+2   ; sub_30882+0x63
0x3D1BC: cmp    [di+56h], ax           ; Altitude check
0x3D1BF: jge    loc_3D1C5
0x3D1C1: call   near ptr loc_2F784+4   ; sub_2F6D0+0xB4 - Special handling
```

**Tracking sequence**:
1. Load target entity (sub_307A5)
2. **Calculate pursuit vector (sub_2F6D0)** ← GUIDANCE ALGORITHM
3. Update entity physics (sub_30882)
4. Check altitude constraints
5. Apply result

### Function: sub_2F6D0 (1123 bytes, Level 19)

**Purpose**: Target pursuit/guidance calculation

**Hypothesis based on manual**:
- For IR missiles (AIM-9): Track heat signature, lead pursuit
- For radar missiles (AIM-120): Active radar guidance, proportional navigation
- For guns: Predictive aim-point calculation

**Entry points identified**:
- `loc_2F6D6` (offset +0x06) - Main guidance entry
- `loc_2F700` (offset +0x30) - Visibility/update
- `loc_2F784` (offset +0xB4) - Low-altitude special case

**Likely algorithm** (based on F-16 sims of this era):
```
Proportional Navigation:
  1. Calculate line-of-sight (LOS) vector to target
  2. Calculate LOS rate (angular velocity)
  3. Compute acceleration command: a = N * V_closing * LOS_rate
  4. Apply to missile orientation
  
For ballistic (gun):
  1. Calculate time-to-target
  2. Predict target position at impact
  3. Compute lead angle
  4. Return aim-point
```

**Fields accessed** (from known patterns):
- `[si+29h]` - Target slot ID (input)
- `[di+0Ah]`, `[di+0Bh]` - Target state (position/velocity?)
- `[di+39h]`, `[di+37h]` - More target data
- `[di+1Ah]`, `[di+1Bh]`, `[di+1Ch]` - Target vectors?
- `[di+56h]` - Altitude (constraint)

**Calls to**:
- Fixed-point vector operations
- Distance/angle calculations
- Physics transformation functions

### Lock-On State Machine

From manual: Seeking → Tracking → Locked → "In Parameters"

**Code search targets**:
1. **Seeker acquisition**: Angle/range checks, FOV cone
2. **Tracking state**: Lock timer, signal strength
3. **Audio tone trigger**: Sound system call when locked
4. **Reticle blink**: HUD update flag when "in parameters"
5. **Target diamond attach**: HUD element positioning

**Likely location**: Part of sub_2F6D0 or called by it

### "In Parameters" Validation

Manual emphasizes: Lock ≠ Hit. Must satisfy:
- **Range**: Within weapon envelope (min/max distance)
- **Aspect**: Target geometry relative to seeker
- **Closure**: Overtake speed sufficient
- **Environment**: No interference (sun, terrain, countermeasures)

**Code hypothesis**:
```asm
; Pseudocode
check_in_parameters:
  range = distance_to_target()
  if range < weapon.min_range or range > weapon.max_range:
    return FAIL
  
  aspect_angle = calculate_aspect()
  if aspect_angle > weapon.max_off_boresight:
    return FAIL
  
  closure_rate = relative_velocity()
  if closure_rate < weapon.min_closure:
    return FAIL
  
  environmental_check()  ; sun, flares, chaff, terrain
  
  return SUCCESS  ; Weapon will likely hit
```

**Search strategy**: Look for range comparisons, angle thresholds, multi-stage validation

---

## Part 2: Collision Detection

### Function: sub_32453 (216 bytes, Level Unknown)

Found via cross-reference in behavior dispatcher analysis.

**Purpose**: Check if weapon has intersected target

**Call site @ sub_3CE92**:
```asm
0x3D27C: call   sub_32453  ; Collision detection
; If collision detected:
0x3D27F: or     word ptr [si+8], 400h  ; Set collision flag
```

**Collision Flag**: Bit 0x400 in `[entity+0x08h]`

**Collision Types** (inferred):
1. **Proximity fuse**: Missile explodes when near target (common for missiles)
2. **Direct hit**: Overlapping bounding boxes/spheres
3. **Raycast**: For guns, trace bullet path

**Algorithm hypothesis**:
```
For missiles (AIM-9, AIM-120):
  1. Calculate distance to target
  2. If distance < proximity_radius:
     - Trigger explosion
     - Set collision flag
     - Return TRUE
  3. Check if paths intersected this frame (for fast-movers)
  
For guns (M61A1):
  1. Cast ray from gun muzzle
  2. Check intersection with target bounding volume
  3. Return TRUE if hit
```

**Entity fields likely used**:
- `[entity+0x31-0x35]` - Position (tiles + local coords)
- `[entity+0x3A-0x44]` - Velocity vector (3× int32)
- `[entity+0x75]` - Entity type (target vs projectile)
- `[entity+0x08]` - Collision result flag

**Bounding volumes**:
- Aircraft: Probably sphere or ellipsoid (10-20m radius?)
- Missiles: Small sphere (1-5m radius)
- Bullets: Point or tiny sphere (0.5m)

### Collision Response

After collision detected:

```asm
0x3D27C: call   sub_32453       ; Detect collision
0x3D27F: or     word ptr [si+8], 400h  ; Flag collision
0x3D283: call   sub_32393       ; Calculate damage
0x3D286: call   sub_2EAA7       ; Apply damage, spawn explosion
```

**Sequence**:
1. Detect collision (sub_32453)
2. Set collision flag
3. **Calculate damage** (sub_32393)
4. Apply damage & spawn effects (sub_2EAA7)

---

## Part 3: Damage System

### Function: sub_32393 (192 bytes, Level Unknown)

**Purpose**: Calculate damage from weapon hit

**Input** (hypothesized):
- Weapon type (from entity type or weapon ID)
- Damage tier (from weapon init: 2, 4, 5, 6)
- Hit location? (center vs wing vs tail)
- Target type (aircraft vs ground unit vs building)

**Output**:
- Damage value (numeric health reduction)
- Critical hit flag? (instant kill, fire, system failure)

**Damage Tiers from Code** (weapon init @ sub_4C19E):
```
Type 0x12 (AIM-9):   damage_tier = 5
Type 0x13 (AIM-120): damage_tier = 2
Type 0x33 (M61A1):   damage_tier = 5
Type 0x34 (Gun var): damage_tier = 6
Type 0x35 (Gun var): damage_tier = 5
Type 0x36 (Gun var): damage_tier = 4
Type 0x37 (Gun var): damage_tier = 2
```

**Interpretation**:
- Tier 2: Low damage (AIM-120, gun variant 0x37)
- Tier 4: Medium damage (gun variant 0x36)
- Tier 5: High damage (AIM-9, M61A1, gun variant 0x35)
- Tier 6: Very high damage (gun variant 0x34)

**Manual context**:
- AIM-9/AIM-120: Single hit usually kills aircraft
- M61A1 gun: Sustained burst needed, cumulative damage
- Different hit zones: Engine hit = fire, wing hit = control loss

**Algorithm hypothesis**:
```
calculate_damage(weapon_type, target_type, hit_location):
  base_damage = damage_table[weapon_type][damage_tier]
  
  if target_type == AIRCRAFT:
    damage *= aircraft_vulnerability
    
    if hit_location == ENGINE:
      damage *= 2.0  ; Critical hit
      set_fire_flag()
    elif hit_location == WING:
      damage *= 1.5
      reduce_control_authority()
    elif hit_location == COCKPIT:
      damage *= 3.0  ; Instant kill
  
  elif target_type == GROUND:
    damage *= ground_vulnerability
  
  return damage
```

**Critical hits**:
- Engine: Fire, gradual health drain
- Cockpit/pilot: Instant death
- Wings: Reduced maneuverability
- Fuel tanks: Leak, eventual crash

### Function: sub_2EAA7 (Unknown size, Level 19)

**Purpose**: Apply calculated damage to target

**Actions** (hypothesized):
1. Reduce target health by damage value
2. If health <= 0: Trigger death sequence
3. Spawn explosion VFX entity
4. Play explosion sound
5. Update target state flags
6. Award kill credit to shooter

**Entity health field**: Unknown location (likely in +0x5C-0xC9 range, 110 unmapped bytes)

**Death sequence**:
1. Set entity death flag
2. Spawn explosion (new entity, type unknown)
3. Spawn debris trail
4. Remove entity from slot table
5. Update mission statistics

---

## Part 4: Code Search Plan

### Priority 1: Find Lock-On State Machine

**Manual targets**:
- Audio tone on lock (heat-seeking missiles)
- Reticle blink when in parameters
- Target diamond attachment

**Search strategy**:
1. Search for audio system calls in sub_2F6D0 or nearby
2. Find HUD update flags for reticle blink
3. Look for angle/range threshold comparisons

**Keywords**: "tone", "lock", "track", "seeker"

### Priority 2: Extract Collision Detection (sub_32453)

**Goal**: Understand proximity fuse vs direct hit

**Approach**:
1. Find sub_32453 disassembly (216 bytes)
2. Look for distance calculation
3. Identify proximity threshold
4. Map to weapon types (missiles vs guns)

### Priority 3: Extract Damage Calculation (sub_32393)

**Goal**: Map damage tiers to actual values

**Approach**:
1. Find sub_32393 disassembly (192 bytes)
2. Look for damage table lookup
3. Find tier → damage mapping
4. Identify critical hit logic

### Priority 4: Trace Guidance Algorithm (sub_2F6D0)

**Goal**: Confirm proportional navigation or identify actual algorithm

**Approach**:
1. Extract sub_2F6D0 disassembly (1123 bytes - large!)
2. Identify vector calculations
3. Look for LOS rate computation
4. Map to known guidance laws (PN, PP, pure pursuit, lead pursuit)

---

## Part 5: Manual Cross-Reference Findings

### Weapon Specs from Manual

**AIM-9 Sidewinder (Type 0x12)**:
- Guidance: Infrared (heat-seeking)
- Range: Short (< 5 miles)
- Speed: High subsonic (~Mach 2.5)
- Warhead: ~20 lbs
- Seeker: Forward hemisphere (AIM-9M all-aspect)
- Lock tone: Audio cue for pilot
- Counters: Flares, sun, high-G maneuvers

**Code mapping**:
- velocity_base = 6645 (game units)
- max_speed = 506 (likely knots or game units/sec)
- damage_tier = 5 (high damage, expected for missile)
- 12× burst = ripple fire (multiple missiles in quick succession)

**AIM-120 AMRAAM (Type 0x13)**:
- Guidance: Active radar homing
- Range: Medium (20-30 miles)
- Speed: Mach 4
- Warhead: ~40 lbs (larger than AIM-9)
- Seeker: All-aspect, fire-and-forget
- No lock tone (radar-guided, not heat)
- Counters: Chaff, terrain masking, defensive maneuvers

**Code mapping**:
- velocity_base = 50127 (much higher - reflects Mach 4)
- max_speed = 202 (different scaling?)
- damage_tier = 2 (LOW?! - Unexpected, may be inverted scale or different stat)
- Single shot (no burst)

**M61A1 Vulcan 20mm (Type 0x33)**:
- Guidance: None (ballistic)
- Range: ~2000 feet effective
- Rate: 6000 rounds/min (100 rounds/sec)
- Ammo: 512 rounds (5 seconds sustained fire)
- Damage: Cumulative, requires sustained burst
- Counters: Evasive maneuvers

**Code mapping**:
- velocity_base = 6645 (same as AIM-9 - simplified ballistics?)
- max_speed = 506 (matches AIM-9 - shared params for simplicity)
- damage_tier = 5 (per-bullet damage, cumulative)
- 6× burst = 6-round burst per trigger pull

### Expected Code Behaviors

**IR Guidance (AIM-9)**:
```
every_frame:
  if target.heat_signature > threshold:
    angle_to_target = atan2(target_y - missile_y, target_x - missile_x)
    
    if abs(angle_to_target - missile_heading) < seeker_fov:
      if not locked:
        lock_timer++
        if lock_timer > lock_delay:
          set_locked()
          play_lock_tone()
      
      if locked:
        los_rate = calculate_los_rate()
        command_accel = navigation_constant * los_rate
        apply_acceleration(command_accel)
      
    else:
      lose_lock()
      lock_timer = 0
  
  check_countermeasures()  ; flares, sun
```

**Radar Guidance (AIM-120)**:
```
every_frame:
  ; Active radar seeker
  radar_return = scan_cone(seeker_fov)
  
  if radar_return.strength > threshold:
    target = strongest_return(radar_return)
    
    ; Fire-and-forget proportional navigation
    los_rate = calculate_los_rate(target)
    command_accel = N * closing_velocity * los_rate
    apply_acceleration(command_accel)
  
  check_countermeasures()  ; chaff
```

**Ballistic (Gun)**:
```
on_fire:
  ; Predict target position
  time_to_target = distance / bullet_velocity
  predicted_pos = target.pos + target.vel * time_to_target
  
  ; Lead angle
  lead_angle = atan2(predicted_pos - gun_pos)
  
  ; Spawn bullet
  bullet.pos = gun_pos
  bullet.vel = bullet_velocity * unit_vector(lead_angle)
  bullet.lifetime = max_range / bullet_velocity
  
every_frame(bullet):
  bullet.pos += bullet.vel * dt
  bullet.lifetime -= dt
  
  if bullet.lifetime <= 0:
    despawn(bullet)
  
  if check_collision(bullet):
    apply_damage()
    despawn(bullet)
```

---

## Part 6: Next Steps

### Immediate Actions

1. **Search for sub_32453 in disassembly files** (collision detection)
2. **Search for sub_32393 in disassembly files** (damage calculation)
3. **Map health field in entity struct** (search for damage application)
4. **Find audio trigger for lock tone** (search for sound calls near guidance)
5. **Identify HUD blink flag** (reticle flashing when in parameters)

### Medium-Term Goals

6. Extract sub_2F6D0 full disassembly (guidance algorithm - 1123 bytes)
7. Find countermeasure effectiveness tables (chaff/flare success rates)
8. Locate "in parameters" validation logic
9. Map proximity fuse radii per weapon type
10. Document complete weapon → damage flow

### Long-Term Goals

11. Complete weapons system to 90%
12. Create weapons modding tools
13. Document AI weapon usage patterns
14. Map bomb types (0x14-0x32, not yet analyzed)

---

## Summary

**What we now know**:
- Guidance system entry point: sub_2F6D0 (1123B)
- Collision detection: sub_32453 (216B)
- Damage calculation: sub_32393 (192B)
- Damage application: sub_2EAA7 (Level 19)
- Manual provides expected behaviors to validate against code

**What we need**:
- Actual disassembly of collision/damage functions
- Health field location in entity struct
- Lock-on state machine code
- "In parameters" validation
- Countermeasure logic

**Progress**: 65% → 70% (this analysis session)
**Target**: 90% (collision, damage, guidance decoded)

