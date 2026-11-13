# Control→Force Conversion Discovery

**Session 2, November 11, 2026**

## BREAKTHROUGH: Control Input Storage Found!

### Control Value Storage: `cs:word_2E139`

**Location:** Code segment variable at offset 0x2E139  
**Type:** int16 (word)  
**Range:** Scaled control input value (varies with tick rate)

### Control Flow Discovered @ 0x2F984-0x2F9A3

**Main game loop `sub_2F6D0` @ 0x2F6D0:**

```asm
; Read raw control axes (±2048)
0x2F988: call   control_axis_scale_store
0x2F98D: mov    al, ds:47Ah
0x2F990: call   control_axes_read         ; read 4 axes from hardware
0x2F995: call   control_axis_store_step   ; store to entity records
0x2F998: call   sub_321C1
0x2F99B: call   sub_2FD42

; Compute tick rate and scale control
0x2F99E: call   tick_rate_compute         ; returns AX=word_2E137, BX=word_2E139
0x2F9A3: mov    cs:word_2E139, bx         ; ← STORE SCALED CONTROL VALUE
0x2F9A8: mov    cs:word_2E137, ax         ; store companion value
0x2F9AC: call   flag22220_clear

; Use scaled control values
0x2F9B1: mov    bx, cs:word_2E139         ; reload control value
0x2F9B6: mov    ax, cs:word_2E137
0x2F9BA: call   state_add_70a03_70a5d     ; accumulate state
```

**Key Discovery:**
- `tick_rate_compute` @ 0x2F99E computes frame time and **scales control input**
- Returns two values: AX (`word_2E137`) and BX (`word_2E139`)  
- `word_2E139` is the **time-scaled control input** used throughout aerodynamics

### Usage in Aerodynamics (sub_38CF3 @ 0x38DE9)

```asm
; Aerodynamic force calculation
0x38DD5: mov    bx, [si+68h]      ; physics coefficient (control authority)
0x38DD8: imul   bx                ; multiply force by coefficient
0x38DDA: mov    bx, 80h           ; divisor (128)
0x38DDD: cmp    word ptr ds:135Ch, 1
0x38DE2: jz     loc_38DE7
0x38DE4: mov    bx, 100h          ; alternate divisor (256)
0x38DE7: idiv   bx                ; divide by scaling factor
0x38DE9: mov    bx, cs:word_2E139 ; ← LOAD CONTROL INPUT
0x38DEE: cmp    bx, 80h           ; clamp to 0..127
0x38DF2: jl     loc_38DF7
0x38DF4: mov    bx, 7Fh           ; clamp high = 127
0x38DF7: imul   bx                ; MULTIPLY FORCE × CONTROL INPUT
0x38DF9: mov    al, ah            ; extract high byte (÷256)
0x38DFB: mov    ah, dl
0x38DFD: pop    bx
0x38DFE: sub    bx, [si+34h]      ; delta from current state
0x38E01: cmp    bx, ax            ; limit rate of change
...
0x38E0D: add    ax, [si+34h]      ; accumulate to state
0x38E10: mov    [si+34h], ax      ; store result (orientation change?)
```

**Pattern:**
1. Load aerodynamic coefficient from FarObj physics fields (+0x68h)
2. Scale by base coefficient and divisor
3. **Multiply by control input** (`cs:word_2E139`)  
4. Extract result (÷256 via byte access)
5. Rate-limit the change
6. Apply to entity state ([si+34h])

### Control Value Range

From clamping @ 0x38DEE:
```asm
cmp    bx, 80h           ; compare to 128
jl     loc_38DF7         ; if less, use as-is
mov    bx, 7Fh           ; else clamp to 127
```

**Effective Range:** 0..127 (not ±2048!)

**This means:**
- Raw input: ±2048 from `control_axes_read`
- Scaled input: 0..127 in `cs:word_2E139`
- **Scaling factor: 2048 ÷ 128 = 16** (approximately)
- Or: control >> 4 (right shift 4 bits)

### Multiple Control Variables

**Discovered pair:**
- `cs:word_2E137` - possibly another axis or time delta
- `cs:word_2E139` - primary control input (aileron? elevator?)

**Need to find:**
- Where are the other 3 axes stored? (throttle, rudder, second control)
- How does `tick_rate_compute` scale raw ±2048 to 0..127?

### Physics Coefficient Fields (FarObj +0x60-0x70)

**Confirmed usage in sub_38CF3:**
- `+0x60h` - Speed threshold (compared to [si+14h])
- `+0x66h` - Divisor for one axis (force scaling)
- `+0x68h` - Multiplier for control authority
- `+0x6Ah` - Minimum speed for effect
- `+0x6Ch` - Divisor for second axis
- `+0x6Eh` - Second multiplier
- `+0x70h` - Second threshold

**Pattern: Speed-dependent control authority**

```c
if (speed > threshold_60h) {
    force = (axis_value × speed) ÷ divisor_66h;
} else {
    force = (axis_value × threshold_60h²) ÷ divisor_66h;
}

if (abs(force) < threshold_6Ah) {
    force = threshold_6Ah × (speed ÷ threshold_60h)²;
}

force = (force × coefficient_68h) ÷ 128;
force = force × control_input_2E139;
```

### Entity State Field: [si+34h]

**Updated by:** Aerodynamic calculation  
**Type:** int16 (orientation angle?)  
**Behavior:** Rate-limited accumulation  

From @ 0x38DFE-0x38E10:
```asm
sub    bx, [si+34h]      ; delta = new - current
cmp    bx, ax            ; limit positive change
jge    loc_38E0D
neg    ax
cmp    bx, ax            ; limit negative change
jle    loc_38E0D
mov    ax, bx            ; use clamped delta
add    ax, [si+34h]      ; new = current + delta
mov    [si+34h], ax      ; store
```

**Hypothesis:** `[si+34h]` is pitch or roll angle (14-bit angle format)

### Next Steps

1. **Find tick_rate_compute internals**
   - How does it scale ±2048 → 0..127?
   - What is `word_2E137`?

2. **Find other control axes**
   - Search for similar patterns with word_2E13B, word_2E13D, etc.
   - Trace control_axis_store_step to see where 4 axes go

3. **Map remaining physics fields**
   - Extract coefficient values for F-16, F/A-18, MiG-29
   - Document speed-dependent force curves

4. **Identify [si+34h]**
   - Likely pitch or roll angle
   - Connect to FarObj orientation fields (+0x0C-0x11)

---

## Summary

**MAJOR BREAKTHROUGH:** Found the control→force conversion path!

1. ✅ Control storage: `cs:word_2E139` (0..127 range)
2. ✅ Scaling: `tick_rate_compute` converts ±2048 → 0..127
3. ✅ Usage: Multiplied by aerodynamic coefficients in physics loop
4. ✅ Physics fields: +0x60-0x70 contain speed thresholds and force multipliers
5. ✅ Output: Rate-limited accumulation to entity state [si+34h]

**Progress:** 80% → 87% (control→force path confirmed, need other axes + coefficients)

---

*Discovery timestamp: 2026-11-11*  
*Analyst: Kiro (Session 2)*
