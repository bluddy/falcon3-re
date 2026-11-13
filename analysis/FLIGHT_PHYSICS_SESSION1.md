# Flight Physics Analysis - Session 1

**Goal:** Push Flight Physics from 70% → 90%+ by connecting control inputs to aerodynamics

## Key Findings

### 1. Control Axes System (COMPLETE)

**Function:** `sub_11450` @ 0x11450 (Level 2, 114B)
- Reads 4 control axes from joystick or keyboard
- Normalizes to **±2048 (±0x800)** range
- Clamps each axis independently

**Control Range:** -0x800 ≤ axis ≤ +0x800 (-2048 to +2048)

**Axis Clamping Logic:**
```asm
; For each axis (AX, BX, CX, DX):
cmp    ax, 800h
jg     clamp_high      ; if > +2048, clamp to +2048
cmp    ax, 0F800h      ; -2048 in two's complement
jl     clamp_low       ; if < -2048, clamp to -2048
; Repeat for BX, CX, DX
```

**Output Storage** (CS segment):
- `cs:byte_22232` - axis 0 (aileron - roll)
- `cs:byte_22232+2` - axis 1 (elevator - pitch)
- `cs:byte_22232+4` - axis 2 (throttle)
- `cs:byte_22232+6` - axis 3 (rudder - yaw)

### 2. Kinematics Block (DS:[32h], 26 bytes)

**Function:** `sub_3B338` @ 0x3B338 (pos_step_chain_engine, 852B)

**Block Layout:**
```
DS:[32h..4Bh] = 13 words = 26 bytes
```

**Initialization Pattern @ 0x3B357-0x3B360:**
```asm
mov    si, 32h        ; source = DS:[32h] (kinematics block)
mov    di, 66h        ; dest = DS:[66h] (previous frame copy)
mov    cx, 0Dh        ; 13 words
movsw                 ; copy 26 bytes
```

**Also mirrored to ES:0x7B0E:0x43BAh** (trig segment, @ 0x3B368-0x3B371):
```asm
mov    ax, 7B0Eh
mov    es, ax
mov    di, 43BAh      ; destination in trig segment
mov    si, 32h        ; source = kinematics block
mov    cx, 0Dh        ; 13 words
movsw                 ; copy to trig segment for matrix ops
```

**Step Coefficient @ 0x3B343:**
```asm
mov    ds:word_7B190, ax    ; store step coefficient
mov    dx, 3334h            ; TILE_SIZE = 13,108
imul   dx
mov    ds:word_7B192, ax    ; store step_in_world_units
```

**Cross-Tile Position Update @ 0x3B404-0x3B42C:**
```asm
mov    cx, ds:word_7B108        ; get current heading/speed?
call   loc_3B5DB                ; compute movement delta
add    [si], ax                 ; add to position X low
adc    [si+2], dx               ; add to position X high
mov    ax, [si]
mov    dx, [si+2]
mov    bp, 3334h                ; TILE_SIZE
add    ax, 3400h                ; offset for wrapping
adc    dx, 33h
and    dx, 1FFh                 ; mask to 512 tiles (256×256 grid)
div    bp                       ; quotient = tile, remainder = local pos
sub    ax, 1FFh
neg    ax
mov    [si+10h], ax             ; store tile coordinate
mov    [si+0Ch], dx             ; store local position within tile
```

**Field Hypotheses** (from access patterns in sub_3B338):
```c
struct FlightKinematics {        // DS:[32h..4Bh]
    int32_t pos_x;               // +0x00 [32h] world X position (int32)
    int32_t pos_z_alt;           // +0x04 [36h] altitude or Z (int32)
    int32_t pos_y_or_vel;        // +0x08 [3Ah] Y position or velocity (int32)
    int16_t local_pos_x;         // +0x0C [3Eh] local pos within tile
    int16_t tile_step_rem;       // +0x0E [40h] remainder from tile division
    int16_t tile_x;              // +0x10 [42h] tile coordinate X
    int16_t field_12;            // +0x12 [44h] unknown
    int16_t tile_flags;          // +0x14 [46h] tile classification flags (from sub_3B443)
    int16_t field_16;            // +0x16 [48h] unknown
    int16_t field_18;            // +0x18 [4Ah] unknown
};
// Total: 26 bytes
```

### 3. Aerodynamics Function (PARTIAL)

**Function:** `sub_3E16B` @ 0x3E16B (Level 19, 865B)
- **22 callees** including physics and AI functions
- Core physics update loop for entities

**Velocity Application @ 0x3E2B6-0x3E2CF:**
```asm
; Apply force vector [DI+50h/52h/54h] scaled by BX to velocity [SI+3Ah/3Ch/3Eh/40h/42h/44h]
mov    ax, [di+50h]        ; load force component X
imul   bx                  ; scale by BX (force magnitude)
add    [si+3Ah], ax        ; add to velocity X low word
adc    [si+3Ch], dx        ; add to velocity X high word

mov    ax, [di+52h]        ; load force component Y
imul   bx                  ; scale by BX
add    [si+3Eh], ax        ; add to velocity Y low word
adc    [si+40h], dx        ; add to velocity Y high word

mov    ax, [di+54h]        ; load force component Z
imul   bx                  ; scale by BX
add    [si+42h], ax        ; add to velocity Z low word
adc    [si+44h], dx        ; add to velocity Z high word
```

**Force Scaling @ 0x3E2A2-0x3E2A6:**
```asm
mov    cx, cs:word_2E102        ; get time divisor
idiv   cx                       ; divide by time step
mov    cl, 5
sar    ax, cl                   ; arithmetic right shift by 5 (÷32)
push   ax                       ; save scaled force magnitude → BX
```

**Connection Points:**
1. Force vector source: `[DI+50h/52h/54h]` (orientation offset vector from Entity System)
2. Force magnitude: computed from distance/time, scaled by type-specific physics divisor
3. Velocity target: `[SI+3Ah-44h]` (3D velocity vector from Entity System)

### 4. Control Flow (HYPOTHESIS)

```
main_frame_update_loop
├── control_axes_read (sub_11450)           ← Read joystick/keyboard (±2048)
│   └── Store to cs:byte_22232+N            ← 4 axes stored
│
├── pos_step_chain_engine (sub_3B338)       ← Position integration
│   ├── Copy DS:[32h] → DS:[66h]            ← Save previous frame
│   ├── Copy DS:[32h] → ES:7B0E:43BAh       ← To trig segment for matrix
│   ├── Compute tile crossing               ← Update world position
│   └── Tile classification                 ← Spatial partitioning
│
├── angle_matrix_far_invoke                 ← Build rotation matrix
│   └── fixed_matrix_load_7b0e              ← Load matrix from trig segment
│
├── sub_3E16B (aerodynamics dispatcher)     ← Physics update
│   ├── Read control axes                   ← [MISSING LINK]
│   ├── Compute aerodynamic forces          ← [MISSING LINK]
│   ├── Apply forces to velocity            ← @ 0x3E2B6 (FOUND)
│   └── Update entity state                 ← Multiple subsystems
│
└── farobj_move_accumulate_step             ← Entity motion accumulation
```

## Missing Links

1. **Control → Force Conversion:**
   - Where do control axes (±2048) connect to force calculations?
   - Need to find function that reads `cs:byte_22232+N` and applies to aerodynamics
   - Likely: lookup table or polynomial conversion (control_input → force_coefficient)

2. **Aerodynamic Force Model:**
   - How does airspeed affect control authority?
   - Where are aircraft-specific coefficients (Cl, Cd, Cm)?
   - Drag, lift, thrust calculations

3. **Orientation Integration:**
   - How do forces at +0x50/52/54 relate to aircraft orientation (+0x0C-0x11)?
   - Angular velocity → orientation update path

## Next Steps

1. **Find Control Input Path:**
   ```bash
   grep "cs:byte_22232\|cs:22232h" level*.txt
   grep "cs:.*22232" level*.txt  # Look for computed access
   ```

2. **Trace Force Computation:**
   - Find callees of sub_3E16B that compute BX (force magnitude)
   - Look for physics coefficient tables
   - Search for "angle_matrix" + velocity interactions

3. **Map Kinematics Fields:**
   - Instrument sub_3B338 access patterns
   - Correlate with Entity System velocity fields
   - Identify heading, speed, altitude rate in 26-byte block

4. **Aircraft Coefficients:**
   - Search for F-16/F/A-18 specific data tables
   - Find Cl/Cd/Cm lookup tables or polynomials
   - Locate thrust/drag curves

## Assembly Evidence

### Control Axes Clamp (sub_11450 @ 0x11458-0x114B5)
```asm
call   joystick_dispatch_6d
call   state3_copy_3c6_3ce
cmp    ax, 800h           ; AX = axis 0
jg     loc_1146A          ; if > 2048, clamp
cmp    ax, 0F800h         ; if < -2048, clamp
jl     loc_1146F
; ... (repeats for BX, CX, DX)
mov    ax, 800h           ; clamp high
mov    ax, 0F800h         ; clamp low
```

### Position Step (sub_3B338 @ 0x3B338-0x3B343)
```asm
push   ax
or     ax, ax
jz     loc_3B343          ; if AX == 0
cwd                       ; sign-extend AX → DX
shl    dx, 1              ; DX = sign(AX) × 2
inc    dx                 ; DX = sign(AX) × 2 + 1
mov    ax, dx
loc_3B343:
mov    ds:word_7B190, ax  ; step coefficient
mov    dx, 3334h          ; TILE_SIZE
imul   dx
mov    ds:word_7B192, ax  ; world_step = coef × TILE_SIZE
```

### Velocity Update (sub_3E16B @ 0x3E2B6-0x3E2CF)
```asm
pop    bx                 ; BX = force magnitude
mov    ax, [di+50h]       ; force vector X
imul   bx
add    [si+3Ah], ax       ; velocity X += force_x × magnitude
adc    [si+3Ch], dx
mov    ax, [di+52h]       ; force vector Y
imul   bx
add    [si+3Eh], ax       ; velocity Y += force_y × magnitude
adc    [si+40h], dx
mov    ax, [di+54h]       ; force vector Z
imul   bx
add    [si+42h], ax       ; velocity Z += force_z × magnitude
adc    [si+44h], dx
```

## Status

- **Control Input System:** 100% (±2048 range, 4 axes, clamping confirmed)
- **Kinematics Block:** 60% (structure found, 7/13 fields hypothesized)
- **Force Application:** 90% (velocity update confirmed, magnitude source unclear)
- **Aerodynamic Model:** 30% (force vectors identified, coefficients not found)

**Overall Flight Physics: 70% → 80%**

## Files to Update

1. `docs/architecture/flight_physics.md` - Add control system details
2. `docs/architecture/farobj.md` - Cross-reference velocity and force fields
3. Create `docs/architecture/kinematics.md` - Document 26-byte block in detail

---
*Analysis date: 2026-11-11*
*Analyst: Kiro (Session 1)*
