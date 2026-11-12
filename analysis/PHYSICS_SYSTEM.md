# Falcon 3.0 Physics System Deep Dive

**Version:** 1.0  
**Status:** Active Analysis  
**Last Updated:** 2026-11-11

## Executive Summary

The physics system implements the **flight model** - the core simulation of aircraft dynamics, aerodynamics, and forces. With 48 functions identified, it calculates how the F-16 responds to control inputs, airflow, gravity, and thrust.

**System Profile:**
- Functions: 48 identified
- Role: Flight dynamics simulation
- Update Rate: Every frame (~18 Hz in 1991)
- Complexity: High (realistic aerodynamics)
- Accuracy: Balance between realism and 1991 CPU constraints

**Analysis Progress:** 10% - Function count known, architecture to be discovered

## System Architecture

### Physics Update Loop

```
game_frame_pipeline_step (0x2D98F)
    ↓
[PHYSICS UPDATE - 48 functions]
    ↓
    1. READ INPUTS
       ↓ Control surfaces (stick, rudder, throttle)
       ↓ Trim settings
       ↓
    2. COMPUTE FORCES
       ↓ Lift, drag, thrust, weight
       ↓ Control surface effects
       ↓ Aerodynamic derivatives
       ↓
    3. INTEGRATE MOTION
       ↓ Linear acceleration → velocity → position
       ↓ Angular acceleration → angular velocity → orientation
       ↓
    4. UPDATE STATE
       ↓ Position, velocity, orientation
       ↓ G-forces, AoA, airspeed
    ↓
[Updated aircraft state]
    ↓
[Rendering, AI, weapons systems consume updated state]
```

### Integration Points

**Inputs:**
- Control inputs: pitch, roll, yaw, throttle
- Trim settings: pitch trim, rudder trim
- Gear/flaps position
- Environmental: wind, density altitude

**Outputs:**
- Position: (x, y, z) world coordinates
- Velocity: (vx, vy, vz) linear velocity
- Orientation: pitch, roll, heading (Euler angles or quaternion)
- Angular velocity: pitch rate, roll rate, yaw rate
- Derived values: airspeed, AoA, sideslip, G-force, Mach number

**Callers:**
- `game_frame_pipeline_step` - Main game loop

**Callees:**
- Math functions: sin, cos, atan2, sqrt
- Lookup tables: Lift/drag curves vs. AoA, Mach

## Core Functions (Expected)

### Status: NEEDS DISCOVERY

The 48 physics functions likely fall into these categories:

### 1. Force Calculation (~12 functions)

- **physics_compute_lift**: Lift force from wings
- **physics_compute_drag**: Drag force (parasitic + induced)
- **physics_compute_thrust**: Engine thrust based on throttle and Mach
- **physics_compute_weight**: Weight vector (gravity in body frame)
- **physics_compute_control_forces**: Forces from control surfaces (elevator, aileron, rudder)
- **physics_compute_ground_effect**: Increased lift near ground
- **physics_compute_compressibility**: Mach effects on lift/drag
- **physics_aero_coefficient_lift**: Lift coefficient CL(AoA, Mach, config)
- **physics_aero_coefficient_drag**: Drag coefficient CD(AoA, Mach, config)
- **physics_aero_coefficient_side**: Side force coefficient (sideslip)
- **physics_aero_coefficient_moment**: Pitching/rolling/yawing moments
- **physics_trim_forces**: Trim tab effects

### 2. Motion Integration (~8 functions)

- **physics_integrate_position**: Position += velocity * dt
- **physics_integrate_velocity**: Velocity += acceleration * dt
- **physics_integrate_orientation**: Orientation += angular_velocity * dt
- **physics_integrate_angular_velocity**: Angular_velocity += angular_accel * dt
- **physics_euler_step**: Simple Euler integration
- **physics_rk4_step**: Runge-Kutta 4th order (more accurate)
- **physics_quaternion_integrate**: Quaternion orientation integration
- **physics_normalize_quaternion**: Prevent drift

### 3. Coordinate Transformations (~6 functions)

- **physics_body_to_world**: Transform vector from body frame to world frame
- **physics_world_to_body**: Transform vector from world frame to body frame
- **physics_wind_to_body**: Transform from wind axes to body axes
- **physics_compute_dcm**: Direction cosine matrix from Euler angles
- **physics_dcm_to_euler**: Extract Euler angles from DCM
- **physics_quaternion_to_dcm**: Quaternion to direction cosine matrix

### 4. Derived Quantities (~8 functions)

- **physics_compute_airspeed**: True airspeed from velocity
- **physics_compute_aoa**: Angle of attack from velocity
- **physics_compute_sideslip**: Sideslip angle
- **physics_compute_dynamic_pressure**: q = 0.5 * rho * V^2
- **physics_compute_mach**: Mach number from airspeed and altitude
- **physics_compute_gforce**: G-force magnitude
- **physics_compute_load_factor**: Load factor (lift / weight)
- **physics_altitude_to_density**: Atmospheric density from altitude

### 5. Control Surface Effects (~6 functions)

- **physics_elevator_effect**: Pitching moment from elevator
- **physics_aileron_effect**: Rolling moment from ailerons
- **physics_rudder_effect**: Yawing moment from rudder
- **physics_flaps_effect**: Lift/drag change from flaps
- **physics_speedbrake_effect**: Drag from speed brakes
- **physics_gear_effect**: Drag from landing gear

### 6. Special Cases (~4 functions)

- **physics_ground_collision**: Detect and handle ground contact
- **physics_stall_model**: Stall behavior (loss of lift at high AoA)
- **physics_spin_model**: Spin dynamics
- **physics_departure_model**: Departure from controlled flight

### 7. Utility (~4 functions)

- **physics_init**: Initialize physics system
- **physics_reset**: Reset aircraft state
- **physics_update**: Main update function
- **physics_apply_damage**: Modify flight model for damage

## Flight Model Approaches

### Simplified Physics (Likely for 1991)

**Level of Detail:**
- Point mass model (aircraft as single point, no moment of inertia effects)
- Or: 6-DOF (6 degrees of freedom: 3 translational, 3 rotational)

**Aerodynamic Model:**
- Lookup tables for CL, CD vs. AoA
- Possibly Mach interpolation
- Control derivatives (CLδe, Cmδe, etc.) as constants or simple functions

**Fidelity Trade-offs:**
- Simplified to run at 18 FPS on 1991 hardware
- Probably NOT full CFD (Computational Fluid Dynamics)
- Balance between feel and realism

### Data-Driven vs. Analytical

**Data-Driven (Likely):**
- Lookup tables from F-16 flight manual data
- CL vs. AoA curve
- CD vs. AoA curve
- Possibly multi-dimensional: CL(AoA, Mach, flaps, gear)

**Analytical (Less Likely for Complex Aircraft):**
- Closed-form equations
- Suitable for simple models (Cessna, generic)
- Too limiting for F-16 with complex aerodynamics

## Data Structures

### Expected Structures (Need Verification)

```c
// Aircraft state
struct AircraftState {
    // Position and orientation
    int32_t x, y, z;              // World position (fixed-point or int)
    int16_t pitch, roll, heading; // Euler angles (degrees * scale)
    
    // Linear motion
    int16_t vx, vy, vz;           // Velocity (body frame or world frame)
    int16_t ax, ay, az;           // Acceleration
    
    // Angular motion
    int16_t pitch_rate;           // deg/s
    int16_t roll_rate;
    int16_t yaw_rate;
    int16_t pitch_accel;
    int16_t roll_accel;
    int16_t yaw_accel;
    
    // Derived quantities
    int16_t airspeed;             // knots
    int16_t aoa;                  // angle of attack (degrees * scale)
    int16_t sideslip;             // sideslip angle
    int16_t gforce;               // G-force * 10 (e.g., 35 = 3.5G)
    int16_t mach;                 // Mach * 100 (e.g., 90 = Mach 0.9)
    
    // Configuration
    uint8_t gear_position;        // 0=up, 1-100=transitioning, 100=down
    uint8_t flaps_position;
    uint8_t speedbrake_position;
};

// Control inputs
struct ControlInputs {
    int16_t pitch_input;      // -100 to +100 (stick forward/back)
    int16_t roll_input;       // -100 to +100 (stick left/right)
    int16_t yaw_input;        // -100 to +100 (rudder pedals)
    uint8_t throttle;         // 0-100% (or 0-150% with afterburner)
    int8_t pitch_trim;        // -50 to +50
    int8_t rudder_trim;
};

// Aerodynamic forces (computed each frame)
struct AeroForces {
    int16_t lift;
    int16_t drag;
    int16_t side_force;
    int16_t thrust;
    int16_t weight;
    
    int16_t pitching_moment;
    int16_t rolling_moment;
    int16_t yawing_moment;
};

// Lookup table for aerodynamics
struct AeroTable {
    int16_t aoa_values[20];      // AoA breakpoints (degrees * scale)
    int16_t cl_values[20];       // Lift coefficient at each AoA
    int16_t cd_values[20];       // Drag coefficient at each AoA
    uint8_t num_entries;
};
```

### Memory Locations (Need Discovery)

- Aircraft state: Unknown (likely in DGROUP, prominent location)
- Control inputs: Unknown
- Aero tables: Unknown (likely in code segment as const data)

## Physics Simulation Details

### Angle of Attack (AoA)

**Definition:** Angle between aircraft longitudinal axis and velocity vector

**Computation:**
```
AoA = atan2(vz, vx)  // In body frame
```

**Importance:**
- Primary driver of lift and drag
- Stall occurs at high AoA (~20-30° for F-16)
- Used to index aero lookup tables

### Lift Calculation

**Basic Formula:**
```
Lift = 0.5 * rho * V^2 * S * CL(AoA)
```

Where:
- rho = air density (from altitude)
- V = airspeed (true airspeed)
- S = wing area (constant)
- CL = lift coefficient (function of AoA, from table)

**Direction:** Perpendicular to velocity vector (in wind axes)

### Drag Calculation

**Basic Formula:**
```
Drag = 0.5 * rho * V^2 * S * CD(AoA)
```

**Components:**
- Parasitic drag: CD0 (constant, skin friction + form drag)
- Induced drag: CDi = CL^2 / (pi * AR * e) (from generating lift)
- Total: CD = CD0 + CDi

**Direction:** Opposite to velocity vector

### Thrust Calculation

**Jet Engine Model (Simplified):**
```
Thrust = f(throttle, Mach, altitude)
```

**Typical Approach:**
- Lookup table: Thrust vs. Mach at sea level
- Scale by density ratio for altitude
- Multiply by throttle position (0-100% or 0-150% with AB)

**F-16 Specifics:**
- Dry thrust: ~17,000 lbf
- Afterburner: ~29,000 lbf
- Thrust varies significantly with Mach (drop-off at transonic)

### Control Surface Effects

**Elevator (Pitch Control):**
```
Pitching_moment = Cmδe * elevator_deflection * q * S * c
```

Where:
- Cmδe = elevator effectiveness (derivative)
- q = dynamic pressure
- S = wing area
- c = mean aerodynamic chord

**Ailerons (Roll Control):**
```
Rolling_moment = Clδa * aileron_deflection * q * S * b
```

Where:
- Clδa = aileron effectiveness
- b = wingspan

**Rudder (Yaw Control):**
```
Yawing_moment = Cnδr * rudder_deflection * q * S * b
```

### Integration

**Simple Euler Integration (Likely for 1991):**
```
position(t+dt) = position(t) + velocity(t) * dt
velocity(t+dt) = velocity(t) + acceleration(t) * dt
```

**Acceleration from Forces:**
```
acceleration = Force_total / mass
angular_acceleration = Moment_total / inertia
```

**Time Step (dt):**
- Frame time: ~55ms (18 FPS)
- Possibly multiple sub-steps for stability

## Performance Characteristics

### Expected Timings (1991 Hardware)

**Physics Update Budget:** 5-10ms per frame (significant portion!)

**Per-Function Costs (estimated):**
- Lookup table interpolation: 50-100 µs
- Force calculation (lift/drag): 200-400 µs
- Coordinate transformation: 100-200 µs (trig functions)
- Integration step: 50-100 µs (simple math)
- Total: 5-10ms (includes all 48 functions)

**Optimization Strategies:**
- Lookup tables instead of equations (faster than computing from physics)
- Fixed-point math (avoid floating point if possible)
- Precomputed trig tables (sin/cos lookup)
- Simplified model (point mass vs. full 6-DOF)

## Integration with Other Systems

### Input System

**Physics consumes inputs:**
- Stick deflection → elevator/aileron
- Rudder pedals → rudder
- Throttle → engine thrust
- Gear/flaps controls → configuration

### HUD System

**HUD displays physics state:**
- Airspeed, altitude, VSI
- AoA, G-force
- Heading, pitch, roll

### Weapons System

**Physics affects weapons:**
- Aircraft velocity → initial bomb/missile velocity
- G-forces → weapon release constraints
- AoA → gun pointing accuracy

### AI System

**AI uses physics:**
- AI pilots also fly via physics simulation
- AI makes control inputs
- Physics updates AI aircraft state

### Terrain System

**Ground collision:**
- Physics checks altitude vs. terrain
- Ground effect near terrain
- Crash detection

## Discovery Status

### ✅ Completed

1. **Function Count:** 48 functions identified

### 🔄 In Progress

1. **Function List:** Need to extract actual physics function names
2. **Architecture:** Need to identify force calculation vs. integration functions
3. **Data Structures:** Need to find aircraft state structure

### 📋 Next Steps

1. **Search for Physics Functions:**
   - Pattern: "physics_*"
   - Pattern: "aero_*"
   - Pattern: "flight_*"
   - Pattern: functions with math (trig, sqrt)
   - Search for strings: "lift", "drag", "thrust", "aoa"

2. **Identify Main Update:**
   - Find physics update function
   - Trace call graph
   - Identify force calculation vs. integration

3. **Locate Aircraft State:**
   - Find position/velocity/orientation variables
   - Identify data structure
   - Map memory layout

4. **Analyze Aero Model:**
   - Find lift/drag lookup tables
   - Identify AoA calculation
   - Map control surface effects

5. **Profile Performance:**
   - Measure physics update cost
   - Identify expensive functions
   - Check for optimization opportunities

## Open Questions

### Architecture
1. **DOF:** Point mass or full 6-DOF (position + orientation)?
2. **Integration:** Euler or Runge-Kutta?
3. **Frame Rate:** Physics updated every frame or at fixed rate?
4. **Sub-steps:** Multiple integration steps per frame?

### Aerodynamics
5. **Aero Model:** Lookup tables or equations?
6. **Table Dimensions:** 1D (AoA only) or multi-dimensional (AoA, Mach, config)?
7. **Stall Model:** Sharp stall or progressive loss of lift?
8. **Compressibility:** Mach effects modeled?

### Performance
9. **Hotspot:** Which physics function costs the most CPU time?
10. **Math:** Fixed-point or floating-point?
11. **Bottleneck:** Is physics the frame-rate limiter?

### Data
12. **State Location:** Where is aircraft state in memory?
13. **Aero Tables:** Where are CL/CD lookup tables?
14. **Constants:** Where are mass, inertia, wing area, etc.?

## Next Steps

1. **Search for physics functions** - Build complete function list
2. **Analyze main update** - Understand physics update flow
3. **Locate aircraft state** - Find position/velocity/orientation data
4. **Map aero model** - Identify lookup tables and force calculations
5. **Profile execution** - Measure physics update cost
6. **Document key functions** - Complete analysis of force calc and integration
7. **Update ARCHITECTURE.md** - Add physics system details

## References

- **ARCHITECTURE.md**: Overall system structure
- **INPUT_SYSTEM.md**: Control inputs (upstream)
- **HUD_SYSTEM.md**: Display of flight data (downstream)
- **TERRAIN_SYSTEM.md**: Ground collision and ground effect
- **SYSTEM_MAP.md**: Initial discovery of 48 physics functions

---

**Analysis Status:** Stage 1 - Function count known, architecture to be discovered  
**Confidence:** Low-Medium (architecture assumptions based on typical flight sims)  
**Verification:** 10% (function count known, details need IDA analysis)
