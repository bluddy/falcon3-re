# CORRECT Control Discovery - Session 3

**Date:** November 11, 2026  
**Status:** VERIFIED ✅

## Control Input Storage: FOUND!

### Storage Locations (Entity Structure)

**After `control_axis_store_step` @ 0x2F995:**

```c
struct EntityControl {
    // ... earlier fields ...
    int16_t control_axis_1;      // +0x18h  (first control published)
    int16_t control_axis_2;      // +0x1Ah  ← USED IN AERODYNAMICS
    int16_t control_axis_3;      // +0x1Ch  ← USED IN AERODYNAMICS
    // ...
    int16_t control_axis_4;      // +0x2Ah  (fourth control published)
    // ...
};
```

**Evidence from function description:**
```
"control_axis_store_step"
"publishes the axis values at +18/+1A/+1C/+2A"
```

### Usage in Aerodynamics @ sub_38CF3

**Axis 1 ([si+1Ah]) @ 0x38D8C-0x38DAA:**
```asm
0x38D84: mov    ax, [si+60h]              ; speed_threshold
0x38D87: cmp    [si+14h], ax              ; compare current speed
0x38D8A: jg     loc_38D9B                 ; branch if high speed

; Low speed path
0x38D8C: mov    ax, [si+1Ah]              ; ← LOAD CONTROL AXIS 1
0x38D8F: mov    bx, [si+14h]              ; current speed
0x38D92: imul   bx                        ; axis × speed
0x38D94: mov    bx, [si+66h]              ; divisor
0x38D97: idiv   bx                        ; ÷ divisor
0x38D99: jmp    loc_38DAC

; High speed path
0x38D9B: imul   ax                        ; threshold²
0x38D9D: mov    bx, [si+66h]              ; divisor
0x38DA0: idiv   bx                        ; ÷ divisor
0x38DA2: mov    bx, [si+1Ah]              ; ← LOAD CONTROL AXIS 1
0x38DA5: imul   bx                        ; × axis
0x38DA7: mov    bx, [si+14h]              ; speed
0x38DAA: idiv   bx                        ; ÷ speed
```

**Axis 2 ([si+1Ch]) @ 0x38E1F-0x38E3D:**
```asm
0x38E17: mov    ax, [si+60h]              ; speed_threshold
0x38E1A: cmp    [si+14h], ax              ; compare current speed
0x38E1D: jg     loc_38E2E                 ; branch if high speed

; Low speed path
0x38E1F: mov    ax, [si+1Ch]              ; ← LOAD CONTROL AXIS 2
0x38E22: mov    bx, [si+14h]              ; current speed
0x38E25: imul   bx                        ; axis × speed
0x38E27: mov    bx, [si+6Ch]              ; divisor (different from axis 1!)
0x38E2A: idiv   bx                        ; ÷ divisor
0x38E2C: jmp    loc_38E3F

; High speed path
0x38E2E: imul   ax                        ; threshold²
0x38E30: mov    bx, [si+6Ch]              ; divisor
0x38E33: idiv   bx                        ; ÷ divisor
0x38E35: mov    bx, [si+1Ch]              ; ← LOAD CONTROL AXIS 2
0x38E38: imul   bx                        ; × axis
0x38E3A: mov    bx, [si+14h]              ; speed
0x38E3D: idiv   bx                        ; ÷ speed
```

### Key Observations

1. **Two Independent Control Axes:**
   - Axis 1 ([si+1Ah]) uses divisor at [si+66h]
   - Axis 2 ([si+1Ch]) uses divisor at [si+6Ch]
   - Different divisors = different control authorities

2. **Control Range:**
   - Still ±2048 from `control_axes_read` (sub_11450)
   - Stored directly without scaling
   - Scaling happens during force calculation

3. **No 0..127 Conversion:**
   - Previous assumption was WRONG
   - Control values stay as ±2048
   - word_2E139 (0x40 = 64) is TIME scaling, not control

4. **Axis Mapping (Updated):**
   - [si+18h] = Computed from [si+2Eh] via: `([si+2Eh] × 0x53F0) >> 16`
   - [si+1Ah] = Elevator (pitch) - first aerodynamic axis, from `control_axes_read`
   - [si+1Ch] = Aileron (roll) - second aerodynamic axis, from `control_axes_read`
   - [si+2Ah] = Fourth control axis, from `control_axis_value` (likely throttle/rudder)

### Complete Force Calculation (CORRECTED)

```c
int16_t aerodynamic_force(
    int16_t current_speed,       // [si+14h]
    int16_t control_input,       // [si+1Ah] or [si+1Ch] ← ACTUAL CONTROL (±2048)
    int16_t speed_threshold,     // [si+60h]
    int16_t force_divisor,       // [si+66h] or [si+6Ch]
    int16_t min_effect,          // [si+6Ah]
    int16_t control_authority,   // [si+68h]
    int16_t time_multiplier,     // cs:word_2E139 (typically 64)
    int16_t current_angle        // [si+34h]
) {
    int16_t force;
    
    // Speed-dependent base force
    if (current_speed > speed_threshold) {
        force = (speed_threshold * speed_threshold) / force_divisor;
        force = (force * control_input) / current_speed;        // ← CONTROL × FORCE
    } else {
        force = (control_input * current_speed) / force_divisor; // ← CONTROL × FORCE
    }
    
    // Apply minimum threshold
    if (abs(force) < min_effect) {
        force = min_effect * current_speed / speed_threshold;
        force = force * current_speed / speed_threshold;
    }
    
    // Scale by control authority
    force = (force * control_authority) / 128;
    
    // Scale by frame time
    force = (force * time_multiplier) / 256;                    // ← TIME SCALING
    
    // Rate limit
    int16_t delta = force - current_angle;
    // (clamping logic)
    
    return current_angle + delta;
}
```

### What word_2E139 Actually Does

**At 0x38DE9 (previously misidentified):**
```asm
0x38DD5: mov    bx, [si+68h]              ; control_authority
0x38DD8: imul   bx                        ; force × authority
0x38DDA: mov    bx, 80h                   ; divisor 128
0x38DE7: idiv   bx                        ; ÷ 128
0x38DE9: mov    bx, cs:word_2E139         ; ← LOAD TIME FACTOR (64)
0x38DEE: cmp    bx, 80h                   ; check if > 128
0x38DF2: jl     loc_38DF7
0x38DF4: mov    bx, 7Fh                   ; clamp to 127
0x38DF7: imul   bx                        ; force × time_factor
0x38DF9: mov    al, ah                    ; ÷ 256 (extract high byte)
```

**Purpose:** Scale force by frame time (normally 64 out of 256 = 25% = 0.25)

**Why 64?**
- Provides smooth physics across frame rate variations
- 64/256 = 0.25 = quarter-strength per frame
- Accumulates to full strength over 4 frames

## Summary

**CORRECT Understanding:**

1. ✅ Control inputs stored at [si+1Ah] and [si+1Ch]
2. ✅ Range: ±2048 (no 0..127 conversion)
3. ✅ Two independent axes with different divisors
4. ✅ cs:word_2E139 = time/frame scaling (64), NOT control
5. ✅ Force calculation multiplies control directly
6. ✅ Time scaling is SEPARATE from control scaling

**Progress:**
- Control storage: FOUND ✅
- Control→Force path: VERIFIED ✅
- Physics coefficients: 7/8 fields ✅
- Time scaling: UNDERSTOOD ✅

---

*Discovery: 2026-11-11, Session 3*  
*Analyst: Kiro*
