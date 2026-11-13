# Fourth Axis Analysis - [si+2Ah]

**Date:** November 11, 2026  
**Status:** IN PROGRESS 🔍

## What We Know

### Storage & Access

**Location:** Entity structure offset +0x2Ah (word, 16-bit)

**Written by:**
1. **`control_axis_store_step`** @ 0x2FD3E (main source):
   ```asm
   0x2FD39: call   control_axis_value     ; Get fourth axis value
   0x2FD3E: mov    [si+2Ah], ax           ; Store to entity +2Ah
   ```

2. **`farobj_record_ops_exec`** @ 0x3BDDA:
   ```asm
   mov    [si+2Ah], ax
   ```

3. **`sub_38778`** @ 0x387B5:
   ```asm
   mov    word ptr [si+2Ah], 0            ; Clear/initialize
   ```

4. **`sub_3C62C`** @ 0x3C690:
   ```asm
   mov    word ptr [si+2Ah], 0            ; Clear/initialize
   ```

**Read by:**
1. **`viewobj_screen_project_step`** @ 0x38FAA (THIS IS sub_38CF3!):
   ```asm
   mov    ax, [si+2Ah]                    ; Read fourth axis
   ; (usage in aerodynamics TBD)
   ```

### Function Context

**Critical Discovery:** The function that reads [si+2Ah] at 0x38FAA is:
- **Address:** 0x38CF3 (sub_38CF3)
- **Size:** 2284 bytes
- **Name:** `viewobj_screen_project_step`
- **Description:** "Object screen-project/scale step: fixed-point imul with ds:1350/1352/1354/1356 scale factors"

**This is the SAME function** where we found elevator ([si+1Ah]) and aileron ([si+1Ch]) being used!

So all three control axes are used in the same aerodynamics function:
- [si+1Ah] = Elevator @ 0x38D8C  
- [si+1Ch] = Aileron @ 0x38E1F
- [si+2Ah] = Fourth axis @ 0x38FAA

## Source Function: control_axis_value

**Key Difference:** The fourth axis comes from `control_axis_value` (unknown function), while elevator/aileron come from `control_axes_read` (joystick input).

**From control_axis_store_step:**
```asm
; Axes 2 & 3: Direct joystick
call   control_axes_read              ; Read hardware
mov    [si+1Ah], ax                   ; Elevator
call   control_axes_read              ; Read again
mov    [si+1Ch], ax                   ; Aileron

; Axis 4: Different source
call   control_axis_value             ; ← DIFFERENT FUNCTION
mov    [si+2Ah], ax                   ; Fourth axis
```

**Hypothesis:** `control_axis_value` might be:
1. **Throttle** - derived from joystick throttle axis or keyboard
2. **Rudder** - yaw control axis
3. **Computed value** - derived from other inputs (e.g., auto-throttle, trim)
4. **Configuration/state** - not direct control (e.g., flaps, gear, speedbrakes)

## Evidence from Usage Pattern

### Pattern 1: Used in Aerodynamics

If [si+2Ah] is used at 0x38FAA in the same aerodynamics function as elevator/aileron, it's likely:
- **A control surface** (rudder for yaw?)
- **Thrust/drag** (throttle affecting aerodynamics?)

### Pattern 2: Cleared/Initialized

Multiple functions zero [si+2Ah], suggesting:
- It's a state that can be reset
- Not persistent across entity lifecycle
- May be recalculated each frame

### Pattern 3: Separate Source Function

`control_axis_value` vs `control_axes_read` suggests:
- **Not direct joystick axis** (those use control_axes_read)
- **Computed or derived** value
- **Single value** (not multiple axes like control_axes_read)

## Hypotheses Ranked by Likelihood

### #1: Throttle (70% confidence)

**Evidence FOR:**
- Throttle affects aerodynamics (speed → lift/drag)
- Would be separate from stick axes (different input method)
- Single value (not paired like elevator/aileron)
- Name "control_axis_value" (singular) vs "control_axes_read" (plural)

**Evidence AGAINST:**
- Throttle might be stored elsewhere (engine system)
- Speed is already in [si+14h]

**Test:** Check if [si+2Ah] correlates with speed changes

### #2: Rudder / Yaw Control (60% confidence)

**Evidence FOR:**
- Completes the 3-axis control (pitch/roll/yaw)
- Would affect aerodynamics
- Separate from primary stick axes
- Aircraft have rudder pedals (separate input)

**Evidence AGAINST:**
- Less critical than elevator/aileron
- Might be handled separately from primary aerodynamics

### #3: Computed Trim/Adjustment (40% confidence)

**Evidence FOR:**
- Separate function suggests calculation
- Could be auto-trim, stability augmentation
- Would affect aerodynamics continuously

**Evidence AGAINST:**
- Name doesn't suggest "computed" or "auto"
- Would expect more complex calculation logic

### #4: Flaps/Speedbrakes (30% confidence)

**Evidence FOR:**
- Affects aerodynamics significantly
- Single value (flap angle or speedbrake extension)
- Separate control from stick

**Evidence AGAINST:**
- Usually discrete states, not continuous axis
- Would expect different storage pattern

## Required Analysis

To definitively identify [si+2Ah], we need:

### 1. Assembly Around 0x38FAA

Get 50-100 lines of assembly showing:
- What happens before `mov ax, [si+2Ah]`
- How AX is used after loading [si+2Ah]
- What it's multiplied/divided with
- What field stores the result

### 2. control_axis_value Function

Find and analyze the function that returns the fourth axis value:
- What inputs does it use?
- Does it read hardware (keyboard/joystick)?
- Does it compute from other values?
- What's the return range?

### 3. Correlation with Known Fields

Check if [si+2Ah] correlates with:
- Speed [si+14h]
- Throttle setting (if stored separately)
- Engine state
- Configuration flags

### 4. Comparison with Other Axes

If we can extract the algorithm at 0x38FAA:
- Does it use same pattern as elevator (0x38D8C)?
- Same speed-dependent scaling?
- Same divisors/coefficients?
- Or completely different calculation?

## UPDATED WITH USER KNOWLEDGE 🆕

**User confirmed:** Falcon 3.0 supports **4 hardware axes:**
1. **Elevator** (pitch stick)
2. **Aileron** (roll stick)
3. **Throttle** (throttle axis)
4. **Rudder** (rudder pedals/twist)

**Famous for HOTAS support** - Thrustmaster and other multi-axis controllers of the era!

## NEW ANALYSIS

We now know `control_axes_read` returns **TWO** axes (plural):
- Call 1 @ 0x2FD22 → [si+1Ah] = **Elevator**
- Call 2 @ 0x2FD2D → [si+1Ch] = **Aileron**

And `control_axis_value` returns **ONE** axis (singular):
- Call @ 0x2FD39 → [si+2Ah] = **Throttle OR Rudder**

**Question:** Where is the 4th hardware axis stored?

**Hypothesis Updated:**
- [si+1Ah] = Elevator ✅
- [si+1Ch] = Aileron ✅
- [si+2Ah] = **Throttle** (85% confidence - used in aerodynamics @ 0x38FAA)
- [si+??h] = **Rudder** - MISSING! Where is it stored?

**OR:**
- [si+2Ah] = **Rudder** (15% confidence - but then where's throttle?)

**Next Steps:**
1. Extract assembly at 0x38FAA region (±100 lines)
2. Find control_axis_value function definition
3. Compare usage pattern with elevator/aileron
4. Test hypothesis against flight mechanics expectations

## Impact on Flight Physics Understanding

If [si+2Ah] is **throttle**, this completes the control→force picture:
- **[si+1Ah]** Elevator → pitch moment
- **[si+1Ch]** Aileron → roll moment
- **[si+2Ah]** Throttle → thrust/drag force
- **Missing:** Rudder (yaw control) - where is it?

If [si+2Ah] is **rudder**, we still need:
- Throttle mechanism
- How thrust is applied
- Engine model

Either way, identifying this axis is critical for 100% flight physics understanding.

---

*Analysis: November 11, 2026*  
*Analyst: Kiro*  
*Status: NEEDS ASSEMBLY EXTRACTION*
