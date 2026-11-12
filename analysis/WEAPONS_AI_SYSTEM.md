# Falcon 3.0 Weapons & AI System Deep Dive

**Version:** 1.0  
**Status:** Active Analysis  
**Last Updated:** 2026-11-11

## Executive Summary

The Weapons & AI system is Falcon 3.0's **largest subsystem** with **262 functions**, encompassing combat simulation, enemy AI, weapons physics, and engagement logic. This combined system handles everything from dogfighting AI to missile guidance to bomb ballistics.

**Why Combined:** Weapons and AI are tightly coupled - AI makes decisions about weapon employment, weapons affect AI behavior, and both share targeting and engagement logic.

**System Profile:**
- Functions: 262 identified (largest subsystem)
- Scope: AI decision-making + weapons physics + targeting
- Complexity: Very High (combat simulation core)
- Update Rate: AI decisions ~1-5 Hz, weapons physics every frame
- Code Size: Estimated 50-70 KB (25-35% of total codebase)

**Analysis Progress:** 5% - Function count known, architecture to be mapped

## System Architecture

### High-Level Organization

```
[WEAPONS & AI SYSTEM - 262 functions]
    ↓
    ├─ AI Subsystem (~100 functions)
    │   ├─ Decision Making (25)
    │   ├─ Maneuver Execution (30)
    │   ├─ Situation Assessment (20)
    │   └─ Formation & Comms (25)
    │
    ├─ Weapons Subsystem (~100 functions)
    │   ├─ Ballistics (20)
    │   ├─ Missile Guidance (30)
    │   ├─ Gun Fire Control (15)
    │   ├─ Damage Model (20)
    │   └─ Weapons Management (15)
    │
    └─ Shared Targeting (~62 functions)
        ├─ Target Selection (15)
        ├─ Threat Assessment (15)
        ├─ Radar Simulation (20)
        └─ Sensor Fusion (12)
```

### Data Flow

```
game_frame_pipeline_step (0x2D98F)
    ↓
[AI UPDATE PHASE]
    ↓ For each AI aircraft:
    ↓   Assess situation (threats, targets, objectives)
    ↓   Make tactical decision (engage, evade, navigate)
    ↓   Select maneuver (BFM - Basic Fighter Maneuvers)
    ↓   Choose weapon and firing solution
    ↓   Generate control inputs
    ↓
[WEAPONS UPDATE PHASE]
    ↓ For each active weapon (missiles, bombs in flight):
    ↓   Update guidance (missile tracking target)
    ↓   Update ballistics (bomb trajectory)
    ↓   Check for impact/proximity
    ↓   Apply damage if hit
    ↓
[TARGETING UPDATE PHASE]
    ↓ Update radar contacts
    ↓ Update threat warnings (RWR - Radar Warning Receiver)
    ↓ Update target lock status
    ↓
[Updated combat state]
```

## AI Subsystem (~100 functions)

### AI Architecture

**Decision Hierarchy:**
```
Strategic Layer (Mission)
    ↓ What to do? (CAP, Strike, CAS, etc.)
    ↓
Tactical Layer (Engagement)
    ↓ Engage this target or evade that threat?
    ↓
Maneuver Layer (BFM)
    ↓ Which maneuver? (Turn, climb, dive, barrel roll)
    ↓
Control Layer (Inputs)
    ↓ Stick/throttle inputs to execute maneuver
```

### AI Function Categories

#### 1. Decision Making (~25 functions)

**High-Level AI:**
- `ai_decide_action`: Main decision function (engage/evade/navigate)
- `ai_evaluate_threats`: Assess threat priority
- `ai_evaluate_targets`: Assess target priority
- `ai_choose_target`: Select best target to engage
- `ai_decide_weapon`: Choose weapon type (gun/missile/bomb)
- `ai_check_break_off`: Decide when to disengage

**Rules-Based or FSM (Finite State Machine):**
- States: PATROL, ENGAGE, EVADE, RTB (Return to Base), DEAD
- Transitions based on threats, ammo, fuel, damage

#### 2. Maneuver Execution (~30 functions)

**BFM (Basic Fighter Maneuvers):**
- `ai_maneuver_pure_pursuit`: Fly directly at target
- `ai_maneuver_lead_pursuit`: Lead target for gun solution
- `ai_maneuver_lag_pursuit`: Stay behind target
- `ai_maneuver_high_yo_yo`: Vertical maneuver to maintain energy
- `ai_maneuver_low_yo_yo`: Dive to gain speed
- `ai_maneuver_barrel_roll`: Roll around target's flight path
- `ai_maneuver_scissors`: Defensive scissors (turn reversal)
- `ai_maneuver_split_s`: Reversal maneuver
- `ai_maneuver_immelmann`: Climbing reversal
- `ai_maneuver_break_turn`: Maximum turn rate defensive
- `ai_maneuver_jink`: Random defensive jinking
- `ai_maneuver_dive_for_speed`: Dive to escape
- `ai_maneuver_zoom_climb`: Trade speed for altitude

**Maneuver Parameters:**
- Target lead angle
- Desired G-load
- Desired heading/altitude
- Control deflections

#### 3. Situation Assessment (~20 functions)

**Awareness:**
- `ai_scan_for_threats`: Find hostile aircraft
- `ai_scan_for_targets`: Find targets to engage
- `ai_check_tally`: Do I see the bandit?
- `ai_check_missile_launch`: Detect incoming missile
- `ai_assess_position`: Am I offensive or defensive?
- `ai_compute_angle_off`: Aspect angle to target
- `ai_compute_range`: Distance to target/threat
- `ai_check_six`: Check tail for threats
- `ai_energy_state`: Compare energy (speed/altitude) to opponent

**Tactical Geometry:**
- Offensive: Behind target, good firing position
- Defensive: Target behind, need to evade
- Neutral: Merging or co-altitude/co-speed

#### 4. Formation & Communications (~25 functions)

**Formation Flight:**
- `ai_maintain_formation`: Stay in formation position
- `ai_rejoin_formation`: Return to formation after engagement
- `ai_formation_lead`: Lead aircraft logic
- `ai_formation_wingman`: Wingman logic (follow lead)
- `ai_check_formation_integrity`: Is formation intact?

**Communications (Simulated):**
- `ai_radio_tally`: "Tally two, eleven o'clock"
- `ai_radio_engaged`: "Engaged, defensive"
- `ai_radio_winchester`: "Winchester" (out of ammo)
- `ai_radio_bingo`: "Bingo fuel" (must RTB)

### AI Skill Levels

**Expected Implementation:**
- Beginner: Simple pursuit, poor situational awareness, slow reactions
- Veteran: Better maneuvers, checks six, uses energy tactics
- Ace: Optimal BFM, excellent awareness, aggressive but smart

**Implementation:**
- Skill level affects: reaction time, decision quality, maneuver precision
- Possibly randomization to add unpredictability

## Weapons Subsystem (~100 functions)

### Weapon Types

1. **Gun (M61 Vulcan 20mm cannon)**
2. **Air-to-Air Missiles (AIM-9 Sidewinder, AIM-120 AMRAAM)**
3. **Air-to-Ground Missiles (AGM-65 Maverick)**
4. **Bombs (Mk82, Mk84, CBU, LGB)**
5. **Rockets (unguided)**

### Weapons Function Categories

#### 1. Gun Fire Control (~15 functions)

- `gun_compute_lead`: Compute lead angle for gun solution
- `gun_check_in_range`: Is target within gun range?
- `gun_check_pipper_on_target`: Is gun sight on target?
- `gun_fire`: Fire gun burst
- `gun_update_ammo`: Decrement ammo count
- `gun_apply_ballistics`: Compute bullet trajectory
- `gun_check_hit`: Did bullets hit target?
- `gun_apply_damage`: Apply damage to target

**Gun Ballistics:**
- Initial velocity: Muzzle velocity + aircraft velocity
- Gravity drop
- Air resistance (drag)
- No guidance (ballistic trajectory)

**Lead Computing Sight:**
- Predict target future position
- Account for bullet time-of-flight
- Display lead indicator on HUD

#### 2. Missile Guidance (~30 functions)

**Guidance Types:**
- IR (Infrared) homing: AIM-9 Sidewinder (heat-seeking)
- Radar homing: AIM-120 AMRAAM (active radar)
- TV/EO (Electro-Optical): AGM-65 Maverick (man-in-loop or autonomous)

**Guidance Functions:**
- `missile_init`: Initialize missile after launch
- `missile_update_guidance`: Main guidance update (every frame)
- `missile_track_target`: Keep target in seeker FOV
- `missile_compute_lead`: Proportional navigation
- `missile_check_lock`: Is target locked?
- `missile_check_seeker_limits`: Is target within seeker gimbal limits?
- `missile_motor_burn`: Motor thrust profile over time
- `missile_check_fuel`: Has motor burned out?
- `missile_apply_drag`: Missile drag force
- `missile_integrate_trajectory`: Update missile position/velocity
- `missile_proximity_fuse`: Detect if close enough to target for detonation
- `missile_impact_fuse`: Detect direct hit
- `missile_detonate`: Trigger warhead explosion
- `missile_apply_blast_damage`: Damage to target from warhead

**Proportional Navigation:**
- Standard missile guidance algorithm
- Turn rate proportional to line-of-sight rate
- Leads target for intercept

#### 3. Bomb Ballistics (~20 functions)

- `bomb_release`: Release bomb from aircraft
- `bomb_init_trajectory`: Initial velocity = aircraft velocity
- `bomb_update_ballistics`: Update position under gravity and drag
- `bomb_check_impact`: Has bomb hit ground?
- `bomb_detonate`: Trigger explosion
- `bomb_apply_blast`: Damage to targets within blast radius
- `bomb_ccip`: Continuously Computed Impact Point (HUD cue)
- `bomb_ccrp`: Continuously Computed Release Point (for level bombing)

**Bomb Types:**
- Free-fall: Ballistic trajectory, no guidance
- LGB (Laser-Guided Bomb): Guided to laser designation
- Cluster: CBU disperses submunitions

#### 4. Damage Model (~20 functions)

- `damage_apply_bullet`: Apply bullet hit damage
- `damage_apply_missile`: Apply missile warhead damage
- `damage_apply_blast`: Apply explosion damage
- `damage_check_kill`: Is target destroyed?
- `damage_system_degradation`: Reduce capability (engine, flight controls, etc.)
- `damage_visual_effects`: Smoke, fire, pieces falling off
- `damage_kill_aircraft`: Destroy aircraft
- `damage_kill_ground_target`: Destroy ground target

**Damage Systems:**
- Hit points model (simple)
- Or subsystem damage model (engine, hydraulics, avionics)

#### 5. Weapons Management (~15 functions)

- `weapons_select`: Change selected weapon
- `weapons_check_available`: Is weapon available?
- `weapons_check_employment_zone`: Can weapon be employed now?
- `weapons_get_count`: How many weapons of this type remain?
- `weapons_launch_constraints`: G-limits, speed limits, altitude limits
- `weapons_arm`: Arm weapon for release
- `weapons_jettison`: Emergency jettison

## Targeting Subsystem (~62 functions)

### Radar Simulation

**Functions:**
- `radar_scan`: Sweep radar beam across search volume
- `radar_detect_target`: Detect aircraft in beam
- `radar_track_target`: Track mode (STT - Single Target Track)
- `radar_lock_target`: Achieve radar lock
- `radar_break_lock`: Lose lock (chaff, maneuvers, jamming)
- `radar_compute_range`: Range to target
- `radar_compute_closure`: Closure rate
- `radar_compute_aspect`: Target aspect angle

**Radar Modes:**
- Search: Wide scan, detect multiple targets
- Track: Narrow beam, track single target
- TWS (Track While Scan): Track multiple while scanning
- STT (Single Target Track): High-quality track for missile launch

**Radar Limitations:**
- Range: Depends on target RCS (Radar Cross Section) and aspect
- Clutter: Ground returns can mask targets (look-down limitation)
- Notch: Target perpendicular to radar beam (no closure rate) hard to detect
- Jamming: ECM can break lock

### Target Selection

**Functions:**
- `target_select_closest`: Choose closest target
- `target_select_most_threatening`: Choose biggest threat
- `target_select_in_hud`: Choose target under HUD reticle
- `target_cycle_next`: Cycle to next target
- `target_designate`: Lock designated target

**Targeting Priorities:**
- Closest threat
- Highest priority (enemy type)
- Best firing opportunity

### Threat Assessment

**RWR (Radar Warning Receiver):**
- `rwr_detect_radar`: Detect enemy radar emissions
- `rwr_identify_emitter`: Identify radar type (fighter, SAM, AAA)
- `rwr_compute_bearing`: Direction to threat
- `rwr_assess_threat_level`: How dangerous?
- `rwr_launch_warning`: Missile launch detected

**Threat Display:**
- Shows threat bearing on scope
- Symbol indicates threat type
- Audio warnings (beeping, "Beep beep beep" for launch)

## Data Structures

### Expected Structures (Need Verification)

```c
// AI aircraft state
struct AIAircraft {
    AircraftState physics;       // Position, velocity, orientation (from physics system)
    
    // AI state
    uint8_t ai_state;            // PATROL, ENGAGE, EVADE, RTB, DEAD
    uint8_t skill_level;         // 0=beginner, 1=veteran, 2=ace
    uint16_t target_id;          // ID of current target (0=none)
    uint16_t threat_id;          // ID of current threat
    
    // Maneuver state
    uint8_t current_maneuver;    // Maneuver type enum
    int16_t desired_heading;
    int16_t desired_altitude;
    int16_t desired_gforce;
    
    // Timers
    uint16_t decision_timer;     // Time until next decision
    uint16_t maneuver_timer;     // Time to complete maneuver
    
    // Formation
    uint8_t formation_slot;      // 0=lead, 1-3=wingman
    uint16_t lead_id;            // ID of formation leader
};

// Missile in flight
struct MissileState {
    uint8_t active;              // 0=inactive, 1=in flight
    uint8_t type;                // AIM-9, AIM-120, etc.
    uint16_t target_id;          // Target being tracked
    
    int32_t x, y, z;             // Position
    int16_t vx, vy, vz;          // Velocity
    int16_t heading, pitch;      // Orientation
    
    uint8_t motor_burning;       // 0=burned out, 1=burning
    uint16_t time_of_flight;     // Time since launch (deciseconds)
    uint16_t fuel_remaining;     // Motor fuel
    
    int16_t seeker_gimbal_limit; // Max angle seeker can look off-axis
    uint8_t lock_status;         // 0=no lock, 1=locked
};

// Weapon loadout
struct WeaponLoadout {
    uint8_t gun_ammo;            // Rounds remaining (e.g., 0-511)
    uint8_t aim9_count;          // Sidewinder count (e.g., 0-6)
    uint8_t aim120_count;        // AMRAAM count
    uint8_t agm65_count;         // Maverick count
    uint8_t bombs[4];            // Bomb types and counts
    uint8_t selected_weapon;     // Currently selected weapon
};

// Radar contact
struct RadarContact {
    uint8_t valid;               // 0=no contact, 1=valid
    uint16_t target_id;          // Target ID
    int16_t range;               // Range (nm or km)
    int16_t bearing;             // Bearing (degrees)
    int16_t elevation;           // Elevation (degrees)
    int16_t closure_rate;        // Closing speed (knots)
    uint8_t lock_status;         // 0=detected, 1=tracked, 2=locked
    uint8_t track_quality;       // 0-100%
};
```

### Memory Locations (Need Discovery)

- AI aircraft array: Unknown (likely DGROUP, large structure)
- Missile array: Unknown (likely static array, 16-32 slots)
- Radar contacts: Unknown
- Weapon loadout: Unknown (part of player/AI aircraft state)

## Performance Characteristics

### Expected Timings (1991 Hardware)

**AI Update Budget:** 5-10ms per frame (for all AI aircraft)

**Per-AI-Aircraft Costs (estimated):**
- Decision making: 200-500 µs (rules evaluation, target selection)
- Maneuver computation: 100-300 µs (compute desired control inputs)
- Control generation: 50-100 µs (translate maneuver to stick/throttle)

**Weapons Update Budget:** 2-5ms per frame

**Per-Weapon Costs (estimated):**
- Missile guidance: 200-400 µs (proportional navigation, trig)
- Bomb ballistics: 50-100 µs (simple integration)
- Hit detection: 100-200 µs (proximity check, collision)

**Total AI+Weapons:** 7-15ms (significant! 13-27% of 55ms frame)

**Optimization Strategies:**
- Update AI at lower rate (1-5 Hz, not 18 Hz)
- Limit active AI count (e.g., max 8-12 AI aircraft)
- Simplify distant AI (no maneuver execution, just path following)
- Stagger updates (update different AI on different frames)

## Integration with Other Systems

### Physics System

**AI generates control inputs:**
- AI decision → maneuver → stick/throttle inputs
- Physics system updates AI aircraft state

### Rendering System

**Rendering displays AI aircraft and weapons:**
- AI aircraft positions → 3D rendering
- Missiles in flight → rendered as objects
- Explosions → visual effects

### HUD System

**HUD displays targeting and weapons:**
- Current target → target box
- Radar contacts → radar scope
- Weapon status → HUD readouts
- RWR warnings → threat display

### Input System

**Player inputs affect targeting:**
- Target select button
- Weapon select button
- Trigger (fire gun/launch missile)

## Discovery Status

### ✅ Completed

1. **Function Count:** 262 functions identified (largest subsystem)

### 🔄 In Progress

1. **Function List:** Need to extract actual function names
2. **Architecture:** Need to separate AI vs. weapons vs. targeting functions
3. **Data Structures:** Need to find AI state, missile state, etc.

### 📋 Next Steps

1. **Search for Weapons/AI Functions:**
   - Pattern: "ai_*"
   - Pattern: "weapon_*", "missile_*", "gun_*", "bomb_*"
   - Pattern: "target_*", "radar_*", "rwr_*"
   - Search for strings: "engage", "evade", "lock", "launch"

2. **Categorize Functions:**
   - AI decision making
   - AI maneuvers
   - Weapons ballistics
   - Missile guidance
   - Targeting/sensors

3. **Analyze AI Update:**
   - Find AI main loop
   - Trace decision tree
   - Map maneuver execution

4. **Analyze Weapons Update:**
   - Find missile guidance loop
   - Analyze guidance algorithm
   - Map damage model

5. **Profile Performance:**
   - Measure AI update cost per aircraft
   - Measure weapons update cost
   - Identify optimization opportunities

## Open Questions

### AI System
1. **AI Update Rate:** Every frame or lower rate?
2. **Decision Model:** Rules-based, FSM, or behavior tree?
3. **Skill Implementation:** How do skill levels affect behavior?
4. **Formation Logic:** How complex is formation flying?

### Weapons System
5. **Missile Guidance:** Proportional navigation or simpler?
6. **Damage Model:** Hit points or subsystem damage?
7. **Weapon Limits:** How many active missiles simultaneously?
8. **Radar Model:** How realistic? Does it model clutter, jamming?

### Performance
9. **AI Count:** How many AI aircraft supported?
10. **Update Staggering:** Are AI updates staggered across frames?
11. **Bottleneck:** Is AI/weapons the frame-rate limiter?

### Data
12. **AI State Location:** Where is AI aircraft array in memory?
13. **Missile Array:** Where are active missiles stored?
14. **Targeting Data:** Where are radar contacts stored?

## Next Steps

1. **Search for all 262 functions** - Build complete categorized list
2. **Analyze AI decision loop** - Understand AI architecture
3. **Analyze missile guidance** - Understand guidance algorithm
4. **Locate AI/weapon data** - Find data structures in memory
5. **Profile execution** - Measure AI and weapons costs
6. **Document key functions** - Deep dive into critical AI and weapons logic
7. **Update ARCHITECTURE.md** - Add weapons/AI system details

## References

- **ARCHITECTURE.md**: Overall system structure
- **PHYSICS_SYSTEM.md**: Physics consumed by AI and weapons
- **HUD_SYSTEM.md**: Displays targeting and weapons status
- **RENDERING_SYSTEM.md**: Renders AI aircraft and weapons
- **SYSTEM_MAP.md**: Initial discovery of 262 functions

---

**Analysis Status:** Stage 1 - Function count known, architecture estimated, detailed analysis needed  
**Confidence:** Low-Medium (architecture based on typical combat flight sims)  
**Verification:** 5% (function count known, everything else needs IDA analysis)
