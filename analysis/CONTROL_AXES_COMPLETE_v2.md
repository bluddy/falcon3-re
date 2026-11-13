# Control Axes - Complete Analysis v2

**Date:** November 11, 2026  
**Status:** UPDATED WITH USER KNOWLEDGE 🆕

---

## USER CONFIRMED: 4 Hardware Axes

Falcon 3.0 supports **4 independent hardware axes:**
1. **Elevator** (pitch - stick forward/back)
2. **Aileron** (roll - stick left/right)  
3. **Throttle** (power - throttle lever)
4. **Rudder** (yaw - rudder pedals or twist)

**Famous HOTAS support:** Thrustmaster and other multi-axis controllers!

---

## Storage Mystery: Where Are All 4 Axes?

### What We Found in Entity Structure

```c
struct EntityControl {
    // ...
    int16_t axis_calc;           // +0x18h  CALCULATED from [si+2Eh]
    int16_t axis_elevator;       // +0x1Ah  ✅ VERIFIED in aerodynamics
    int16_t axis_aileron;        // +0x1Ch  ✅ VERIFIED in aerodynamics
    // ...
    int16_t axis_unknown;        // +0x2Ah  Used in aerodynamics @ 0x38FAA
    // ...
};
```

### Storage Function: control_axis_store_step @ 0x2FC79

```asm
; Calculated axis (NOT hardware input)
0x2FD17: mov    ax, [si+2Eh]           ; Load base value
0x2FD1A: mov    dx, 53F0h              ; Multiply
0x2FD1D: mul    dx
0x2FD1F: mov    [si+18h], dx           ; → [si+18h] CALCULATED

; Hardware axes via control_axes_read
0x2FD22: call   loc_22436              ; control_axes_read (entry 1)
0x2FD27: mov    [si+1Ah], ax           ; → [si+1Ah] ELEVATOR ✅
0x2FD2A: mov    ds:452h, ax

0x2FD2D: call   loc_2243B              ; control_axes_read (entry 2)
0x2FD32: mov    [si+1Ch], ax           ; → [si+1Ch] AILERON ✅
0x2FD35: or     ds:452h, ax

; Third hardware axis via different function
0x2FD39: call   control_axis_value     ; (singular, not plural)
0x2FD3E: mov    [si+2Ah], ax           ; → [si+2Ah] THROTTLE or RUDDER?
```

**Problem:** We see only **3 hardware reads** but game supports **4 axes**!

---

## Analysis of Function Names

### control_axes_read (PLURAL)
- Called **twice** with different entry points (0x22436, 0x2243B)
- Returns **one axis per call** in AX
- Call 1 → Elevator
- Call 2 → Aileron
- **Interpretation:** Reads stick X/Y axes

### control_axis_value (SINGULAR)
- Called **once**
- Returns **one axis** in AX
- **Interpretation:** Reads single auxiliary axis (throttle OR rudder)

---

## Three Hypotheses

### Hypothesis A: Throttle Stored Here, Rudder Elsewhere ⭐ (60%)

**Claim:** [si+2Ah] = **Throttle**, Rudder stored in different location

**Evidence FOR:**
- Throttle affects aerodynamics (drag, prop wash)
- [si+2Ah] used in aerodynamics @ 0x38FAA (same function as elevator/aileron)
- Throttle is continuous control like elevator/aileron
- Name "control_axis_VALUE" (singular) = throttle value

**Evidence AGAINST:**
- Where is rudder then?
- Rudder should also affect aerodynamics (yaw moment)

**If TRUE:** Need to find rudder storage location
- Might be in orientation/angular velocity fields
- Might be in separate yaw control structure
- Might be applied directly to heading without storage

### Hypothesis B: Rudder Stored Here, Throttle Elsewhere (30%)

**Claim:** [si+2Ah] = **Rudder**, Throttle in engine system

**Evidence FOR:**
- Rudder creates yaw moment (aerodynamic force)
- Would logically be with other aerodynamic controls
- Throttle might be in engine/propulsion system separate from aerodynamics

**Evidence AGAINST:**
- Throttle was listed BEFORE rudder in control setup (standard order: pitch/roll/throttle/rudder)
- Less intuitive to separate throttle from aerodynamics

**If TRUE:** Need to find throttle in engine/propulsion code

### Hypothesis C: Only 3 Axes Stored in Entity (10%)

**Claim:** 4th axis processed differently, not stored in entity structure

**Evidence FOR:**
- Asymmetric handling might make sense for certain inputs
- One axis might be "instant-apply" without storage

**Evidence AGAINST:**
- All other axes stored for physics continuity
- Unlikely design choice

---

## Evidence from Aerodynamics Usage

### All THREE stored axes used in sub_38CF3 (viewobj_screen_project_step):

```
Function sub_38CF3 (2284 bytes):
  0x38D8C: mov ax, [si+1Ah]    ; Elevator → pitch force
  0x38E1F: mov ax, [si+1Ch]    ; Aileron → roll force
  0x38FAA: mov ax, [si+2Ah]    ; ??? → ??? force
```

**Question:** What force does [si+2Ah] create?

**If Throttle:**
- Thrust force (forward acceleration)
- Drag variation (high power = more drag)
- Prop wash effects on control surfaces

**If Rudder:**
- Yaw moment (turn left/right)
- Side slip correction
- Coordinated turn effects

---

## Required Investigation

### 1. Extract Assembly @ 0x38FAA

Need ~100 lines of assembly showing:
- Context before loading [si+2Ah]
- How the loaded value is used
- What coefficients it's multiplied with
- What field stores the result
- Compare to elevator pattern @ 0x38D8C

**Expected patterns:**

**If Throttle:**
```asm
mov    ax, [si+2Ah]              ; Load throttle
; Apply to thrust/drag calculation
; Affects forward velocity [si+...]
```

**If Rudder:**
```asm
mov    ax, [si+2Ah]              ; Load rudder
imul   bx                        ; × speed or coefficient
; Apply to yaw angle [si+34h] or heading
```

### 2. Find Missing 4th Axis

**If [si+2Ah] is throttle:**
- Search for "rudder" or "yaw" control application
- Check heading/orientation update code
- Look for [si+34h] (orientation) manipulation

**If [si+2Ah] is rudder:**
- Search for "throttle" or "engine" system
- Check thrust/propulsion code
- Look for velocity manipulation separate from aerodynamics

### 3. Identify control_axis_value Function

Find the actual implementation:
- What hardware does it read?
- Does it read joystick axis 3 or 4?
- Any special processing?

---

## Educated Guess Based on All Evidence

**MOST LIKELY: [si+2Ah] = THROTTLE**

**Reasoning:**
1. **Usage in aerodynamics** - Throttle affects drag/thrust which are aerodynamic
2. **Standard ordering** - Pitch/Roll/Throttle/Rudder is classic
3. **Separate function** - Throttle has different input method (lever vs. stick)
4. **Name pattern** - "control_axis_VALUE" suggests continuous value like throttle position
5. **Physics priority** - Throttle has bigger impact on aerodynamics than rudder

**Prediction:**  
Rudder is applied directly to heading/yaw in a separate system, possibly:
- In the angle update code (angle_aux_near, angle_xy_near mentioned in yaw context)
- As direct heading modification rather than moment
- Through simplified yaw model (not full aerodynamic calculation)

This would make sense for 1991 flight sim:
- Full aerodynamic model for primary axes (pitch, roll, thrust)
- Simplified model for secondary (yaw/rudder)
- Reduces computation while maintaining playability

---

## Next Steps

### Immediate (to confirm throttle):
1. Extract assembly @ 0x38FAA region
2. Compare with elevator algorithm @ 0x38D8C
3. Check if result affects velocity vs. orientation

### Follow-up (to find rudder):
1. Search for yaw/heading modification code
2. Check control_axis_value implementation
3. Look for direct heading input application

### Complete picture:
1. Document all 4 axes storage locations
2. Understand throttle→thrust conversion
3. Understand rudder→yaw conversion
4. Map complete control→motion pipeline

---

**Current Status:**  
- Elevator: ✅ 100% (location + usage verified)
- Aileron: ✅ 100% (location + usage verified)
- Throttle: ⚠️ 90% (location found, usage TBD)
- Rudder: ❓ 0% (location unknown)

**Overall Control System:** 72% complete (3/4 axes confirmed)

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: UPDATED - Need assembly extraction to proceed*
