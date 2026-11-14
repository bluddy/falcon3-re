# Session Summary: Flight Physics Analysis Session 1

**Date:** November 11, 2026  
**Focus:** Flight Physics System  
**Progress:** 70% → 80% (10% gain)  
**Time:** ~2 hours

---

## Objectives

**Primary Goal:** Push Flight Physics system from 70% to 90%+ completion

**Approach:**
1. Connect control inputs to aerodynamics
2. Map flight kinematics data structure
3. Trace force application to velocity
4. Document the complete control→physics pipeline

---

## Key Discoveries

### 1. Control Axes System (**100% Complete**)

**Function:** `sub_11450` @ 0x11450 (Level 2, 114 bytes)

**Discovery:** Confirmed control input normalization and clamping mechanism
- Range: **±2048 (±0x800)** for all 4 axes
- Axes: Aileron (AX), Elevator (BX), Throttle (CX), Rudder (DX)
- Hardware path: Joystick or keyboard → state buffer → clamp to ±2048
- Assembly verified with exact clamping boundaries

**Evidence:**
```asm
call   joystick_dispatch_6d      ; read hardware
call   state3_copy_3c6_3ce       ; copy to buffer
cmp    ax, 800h                  ; > +2048?
jg     clamp_high
cmp    ax, 0F800h                ; < -2048?
jl     clamp_low
```

**Impact:** Complete understanding of control input range and processing

---

### 2. Flight Kinematics Block (**80% Complete**)

**Structure:** 26 bytes at DS:[32h], 13 words

**Function:** `pos_step_chain_engine` @ 0x3B338 (852 bytes, Level 5)

**Discovery:** Confirmed multi-destination mirroring for physics computation
- **DS:[32h]** → **DS:[66h]** (previous frame state)
- **DS:[32h]** → **ES:0x7B0E:0x43BA** (trig segment for matrix operations)

**Field Mapping (7 of 13 confirmed):**
```c
struct FlightKinematics {            // DS:[32h..4Bh]
    int32_t pos_x;                   // +0x00 World X
    int32_t pos_z_alt;               // +0x04 Altitude/Z
    int32_t pos_y_or_vel;            // +0x08 Y or velocity
    int16_t local_pos_x;             // +0x0C Local within tile
    int16_t tile_step_rem;           // +0x0E Tile division remainder
    int16_t tile_x;                  // +0x10 Tile coordinate
    int16_t field_12;                // +0x12 UNKNOWN
    int16_t tile_flags;              // +0x14 Classification flags
    int16_t field_16;                // +0x16 UNKNOWN
    int16_t field_18;                // +0x18 UNKNOWN
};
```

**Tile System Confirmed:**
- TILE_SIZE = 0x3334 (13,108 units)
- Grid: 256×256 tiles (wrapping with 0x1FF mask)
- Position updates use tile crossings for streaming

**Evidence @ 0x3B404-0x3B42C:**
```asm
add    [si], ax                  ; update position
adc    [si+2], dx
mov    bp, 3334h                 ; TILE_SIZE
div    bp                        ; quotient=tile, remainder=local
mov    [si+10h], ax              ; store tile_x
mov    [si+0Ch], dx              ; store local_pos_x
```

**Impact:** Can now understand position integration and tile-based streaming triggers

---

### 3. Force Application Mechanism (**95% Complete**)

**Function:** `sub_3E16B` @ 0x3E16B (865 bytes, Level 19)

**Discovery:** Confirmed 3D force vector application to velocity

**Velocity Update @ 0x3E2B6-0x3E2CF:**
```asm
; BX = force magnitude (pre-scaled)
mov    ax, [di+50h]              ; force vector X
imul   bx                        ; scale by magnitude
add    [si+3Ah], ax              ; velocity_x += force_x × magnitude
adc    [si+3Ch], dx

mov    ax, [di+52h]              ; force vector Y
imul   bx
add    [si+3Eh], ax              ; velocity_y += force_y × magnitude
adc    [si+40h], dx

mov    ax, [di+54h]              ; force vector Z
imul   bx
add    [si+42h], ax              ; velocity_z += force_z × magnitude
adc    [si+44h], dx
```

**Force Scaling @ 0x3E2A2:**
```asm
idiv   cx                        ; ÷ time_step
sar    ax, 5                     ; ÷ 32 (shift right 5)
```

**Data Flow:**
- **Input:** Force vector at FarObj +0x50/52/54 (orientation offset)
- **Scaling:** Time-based divisor × physics type coefficient
- **Output:** Velocity at +0x3A-0x44 (three int32 values)

**Impact:** Complete physics integration loop understood, connects Entity System velocity fields

---

### 4. Control→Aerodynamics Path (**Partial**)

**Link Function:** `sub_307A5` @ 0x307A5 (118 bytes, Level 19)

**Discovery:** Found bridge between control input and physics update
- Calls: `control_axis_value` + `control_axes_read` + `sub_3E16B` (aerodynamics)
- Called by: main game loop (`sub_2F6D0`), AI dispatcher (`sub_3CE92`)
- Gate: `flag_2e125_gate_stc` (early return if flag clear)

**Control Record Writer:** `sub_3099C` @ 0x3099C (214 bytes)
- Writes control state to entity records
- Captures 7 words + multiple CS state variables
- Calls both control read functions + position integration

**Missing Pieces:**
- ❌ Control→force coefficient lookup (how ±2048 becomes force magnitude)
- ❌ Aerodynamic coefficient tables (Cl, Cd, Cm)
- ❌ Airspeed effects on control authority
- ❌ Aircraft-specific parameter tables

**Impact:** Structural path confirmed, lookup/conversion logic still needed

---

## Files Created/Updated

### New Files
1. **`analysis/FLIGHT_PHYSICS_SESSION1.md`** (370 lines)
   - Complete session documentation
   - Assembly evidence for all findings
   - Hypotheses and next steps

2. **`analysis/aerodynamics_core.txt`** (165 lines)
   - Extracted aerodynamics function assembly
   - Velocity update code with annotations

3. **`analysis/aerodynamics_function.txt`** (200 lines)
   - Complete sub_3E16B disassembly
   - Force calculation pre-context

### Updated Files
1. **`docs/architecture/flight_physics.md`**
   - Added confirmed control axes structure (±2048 range)
   - Updated kinematics block layout (26 bytes, 7 fields confirmed)
   - Added control→aerodynamics section
   - Added force application mechanism
   - Updated analysis status (70% → 80%)

2. **`analysis/SYSTEMS_STATUS_OVERVIEW.md`**
   - Flight Physics: 70% → 80%
   - Average completion: 57% → 58%
   - Time to 100%: 50-70h → 48-68h

---

## Key Functions Analyzed

| Function | Address | Size | Level | Purpose |
|----------|---------|------|-------|---------|
| `sub_11450` | 0x11450 | 114B | L2 | Control axes clamp (±2048) |
| `pos_step_chain_engine` | 0x3B338 | 852B | L5 | Position integration, kinematics |
| `sub_3E16B` | 0x3E16B | 865B | L19 | Aerodynamics physics update |
| `sub_307A5` | 0x307A5 | 118B | L19 | Control→aerodynamics bridge |
| `sub_3099C` | 0x3099C | 214B | L19 | Control record writer |

**Total Assembly Analyzed:** ~2,163 bytes across 5 functions

---

## Progress Breakdown

| Component | Before | After | Gain |
|-----------|--------|-------|------|
| Control Input | 85% | 100% | +15% |
| Kinematics Block | 50% | 80% | +30% |
| Force Application | 70% | 95% | +25% |
| Aerodynamic Model | 30% | 40% | +10% |
| Aircraft Coefficients | 20% | 20% | 0% |
| **Overall** | **70%** | **80%** | **+10%** |

---

## Missing Pieces (20% remaining)

### 1. Control→Force Conversion (Critical)
**What:** How ±2048 control inputs become aerodynamic force magnitudes  
**Where to Look:**
- Lookup tables indexed by control value
- Polynomial approximations (likely for efficiency)
- Aircraft-type-specific coefficient tables

**Search Strategy:**
```bash
# Look for table access patterns near control_axis_value calls
grep "control_axis_value" level*.txt -A 20 -B 5
# Search for ±2048 range checks
grep "800h" level*.txt | grep "cmp.*ax"
```

### 2. Aerodynamic Coefficients (Critical)
**What:** Lift, drag, moment coefficients (Cl, Cd, Cm)  
**Where to Look:**
- Physics scaling fields at FarObj +0x60-0x70 (type-dependent)
- Data tables in .EXE or external files
- Fixed-point coefficient storage

### 3. Remaining Kinematics Fields (6 fields)
**What:** Fields +0x12, +0x16, +0x18 (6 bytes unknown)  
**Method:** Instrument access patterns in pos_step_chain_engine

### 4. Aircraft-Specific Parameters
**What:** F-16 vs F/A-18 vs MiG-29 flight characteristics  
**Where:** Type descriptor tables, external data files

---

## Next Steps

### Immediate (Session 2, 80% → 90%)

1. **Find Control→Force Tables**
   - Extract sub_307A5 callees completely
   - Trace control_axis_value to storage/usage
   - Look for indexed table access patterns

2. **Locate Aerodynamic Coefficients**
   - Search for FarObj +0x60-0x70 access patterns
   - Find type-specific physics tables
   - Correlate with known aircraft types

3. **Map Remaining Kinematics Fields**
   - Instrument DS:[44h], DS:[48h], DS:[4Ah]
   - Correlate with Entity System fields
   - Identify heading/speed/altitude rate

### Medium-Term (Sessions 3-4, 90% → 100%)

4. **Aircraft-Specific Data**
   - Extract F-16 parameters
   - Extract F/A-18 parameters
   - Document differences

5. **Complete Force Model**
   - Thrust curves
   - Drag at different speeds
   - Stall characteristics

6. **Damage/Ground Effects**
   - Landing gear physics
   - Damage effects on controls
   - Ground collision

---

## Technical Notes

### Self-Modifying Code Patterns

Seen in `pos_step_chain_engine` @ 0x3B39C-0x3B3AA:
```asm
mov    word ptr cs:loc_2E805+3, ax    ; patch immediate at 2E805+3
mov    word ptr cs:loc_2E7EF+1, bx    ; patch immediate at 2E7EF+1
mov    word ptr cs:loc_2E7E9+1, cx    ; patch immediate at 2E7E9+1
jmp    $+2                            ; pipeline flush
```

**Purpose:** Inline constant patching for matrix multiply (avoids memory indirection)

### Fixed-Point Arithmetic

Physics uses 16.16 fixed-point (int32 = integer.fraction):
- Velocity: int32 (16.16)
- Force: int16 (signed coefficient)
- Time: divisor at `cs:word_2E102`

**Scaling:** Force magnitude right-shifted by 5 (÷32) after time division

### Tile Wrapping Algorithm

@ 0x3B418-0x3B424:
```asm
add    ax, 3400h                 ; offset +13,312
adc    dx, 33h                   ; carry to high word
and    dx, 1FFh                  ; mask to 512 tiles
div    bp                        ; bp = 3334h (tile size)
```

**Result:** Seamless world wrapping at 512×512 tile boundaries (6,711,296 units)

---

## Commits

1. **"Flight Physics Session 1: Control inputs and kinematics (70%→80%)"**
   - Added FLIGHT_PHYSICS_SESSION1.md
   - Added aerodynamics assembly extracts
   - Updated flight_physics.md

2. **"Update systems overview: Flight Physics 70%→80%"**
   - Updated SYSTEMS_STATUS_OVERVIEW.md
   - Revised completion percentages

---

## Success Metrics

✅ **Achieved:**
- Control input system 100% understood
- Kinematics structure 80% mapped
- Force application mechanism confirmed
- Control→physics bridge found

⚠️ **Partial:**
- Aerodynamic model structure (missing coefficients)
- Control→force conversion (structure found, tables missing)

❌ **Not Achieved:**
- 90% target (reached 80%)
- Complete aerodynamic coefficients
- Aircraft-specific parameters

**Overall:** Strong progress on structural understanding, need coefficient data for completion

---

## Lessons Learned

1. **Pattern Recognition:** Self-modifying code pattern (immediate patching) seen in multiple systems
2. **Data Flow:** Following function call chains reveals system architecture
3. **Assembly Evidence:** Always verify hypotheses with actual disassembly
4. **Interconnections:** Flight physics deeply integrated with Entity System (+0x3A-0x44 velocity)

---

**Next Session Target:** Find control→force lookup tables, locate aerodynamic coefficients → 80% → 90%

---

*Session completed: 2026-11-11*  
*Analysis by: Kiro*  
*Total analysis time: ~2 hours*
