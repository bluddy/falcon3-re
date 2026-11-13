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

## BREAKTHROUGH: Configuration-Driven Dynamic Axis Mapping! 🎯

**User Knowledge:** Setup menu configures which hardware is active:
- Regular joystick: Only stick axes (elevator/aileron)
- HOTAS setup: Throttle axis enabled
- Rudder pedals: Rudder axis enabled
- Keyboard fallback: Any axis can use keyboard

**This explains:**
1. Why only 3 axes stored in entity - it's CONFIGURABLE!
2. Why `control_axis_value` is separate - it's DYNAMIC based on config
3. Why we couldn't find "the 4th axis" - it depends on player setup!

## NEW UNDERSTANDING

### Dynamic Axis Assignment

```c
// Configuration determines what control_axis_value returns:
int16_t control_axis_value() {
    if (config.has_throttle_axis) {
        return read_throttle_axis();      // Hardware throttle lever
    } else if (config.has_rudder_axis) {
        return read_rudder_axis();        // Hardware rudder pedals
    } else if (config.throttle_keyboard) {
        return read_keyboard_throttle();  // Keyboard throttle
    } else if (config.rudder_keyboard) {
        return read_keyboard_rudder();    // Keyboard rudder
    }
    // Fallback
    return 0;
}
```

### Entity Storage is Context-Dependent

```c
struct EntityControl {
    int16_t axis_calc;           // +0x18h  Calculated
    int16_t axis_elevator;       // +0x1Ah  Stick Y (always present)
    int16_t axis_aileron;        // +0x1Ch  Stick X (always present)
    // ...
    int16_t axis_auxiliary;      // +0x2Ah  DYNAMIC: throttle OR rudder OR other
                                 //         Depends on player configuration!
};
```

### Configuration Bytes

Remember from earlier: DS:8994h-899Ah config bytes!
- One byte probably: `control_mode` (simple/complex/hidef)
- Another byte: `auxiliary_axis_type` (0=none, 1=throttle, 2=rudder, 3=keyboard...)
- Hardware detection flags
- Input mapping configuration

### Usage at 0x38FAA

Now it makes sense why [si+2Ah] is in aerodynamics:
- **If throttle configured:** Affects thrust/drag aerodynamics
- **If rudder configured:** Affects yaw moment aerodynamics
- **If neither:** Zero value, no effect

The SAME code path handles EITHER input!

### Multiple Input Sources

The game must support:
1. **Joystick-only:** Stick X/Y, keyboard for throttle/rudder
2. **Joystick + Throttle:** Stick X/Y, throttle axis, keyboard rudder
3. **Joystick + Rudder:** Stick X/Y, keyboard throttle, rudder axis
4. **Full HOTAS:** Stick X/Y, throttle axis, rudder axis
5. **Keyboard-only:** All axes via keyboard

All configurations use the SAME entity structure and physics code!

## Implications

### [si+2Ah] Purpose

**IT DEPENDS ON CONFIGURATION!**

Could be:
- Throttle (most common HOTAS setup)
- Rudder (if pedals but no throttle axis)
- Trim setting (if neither hardware axis)
- Any auxiliary control player configured

### Why We Found 3 Reads Not 4

Because not everyone HAS 4 hardware axes!

**Minimum config (2-axis joystick):**
- control_axes_read x2 → Elevator, Aileron
- control_axis_value → 0 (no auxiliary hardware)
- Throttle/rudder via keyboard (different code path)

**Full HOTAS config:**
- control_axes_read x2 → Elevator, Aileron
- control_axis_value → Throttle
- Rudder via... where? Different call? Or ALSO through control_axis_value but different setup?

### The REAL Question

**How does the game handle BOTH throttle AND rudder with only ONE auxiliary storage location?**

**Possibility 1:** Only ONE can be a hardware axis
- Player chooses: throttle axis OR rudder axis (not both)
- The other uses keyboard
- This was common in 1991 (before 4+ axis controllers)

**Possibility 2:** Second auxiliary axis exists elsewhere
- [si+2Ah] = primary auxiliary (throttle usually)
- [si+??h] = secondary auxiliary (rudder usually)
- We haven't found it yet

**Possibility 3:** Rudder applied directly, not stored
- Throttle stored in [si+2Ah]
- Rudder applied immediately to heading without entity storage
- Different processing pipeline

## Config System Structure (Hypothesis)

```c
struct GameConfig {
    // Flight model
    uint8_t flight_model;        // 0=simple, 1=complex, 2=hidef
    
    // Hardware detection
    uint8_t joystick_present;    // 0=no, 1=yes
    uint8_t joystick_buttons;    // Number of buttons
    uint8_t joystick_axes;       // Number of axes (2, 3, 4...)
    
    // Axis mapping
    uint8_t axis0_function;      // PITCH (elevator)
    uint8_t axis1_function;      // ROLL (aileron)  
    uint8_t axis2_function;      // THROTTLE or RUDDER?
    uint8_t axis3_function;      // RUDDER or unused?
    
    // Keyboard fallbacks
    uint8_t throttle_input;      // 0=axis, 1=keyboard, 2=disabled
    uint8_t rudder_input;        // 0=axis, 1=keyboard, 2=disabled
    
    // Sound, AI, etc...
};
```

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
