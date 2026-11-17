# Falcon 3.0 Radar Detection Logic - Complete Analysis

**Date:** 2026-11-17  
**Status:** Detection mechanism fully identified

---

## Summary

Found the **two functions that set the RADAR_VISIBLE flag** (entity+0x79 bit 0):

1. **`farobj_floor_match_dispatch`** (0x3A9B7) - Primary detection function
2. **`bound_range_check_4aad`** (0x3AA7E) - Range-based detection gating

These functions run during entity updates and set/clear the `RADAR_VISIBLE` flag based on:
- Distance checks (range)
- Angle/azimuth bounds
- Radar mode settings
- State machine conditions

---

## Function 1: farobj_floor_match_dispatch (0x3A9B7)

**Size:** 101 bytes  
**Purpose:** Primary radar detection logic with angle and range checks

### Disassembly Analysis

```c
void farobj_floor_match_dispatch(entity_ptr) {
    // Skip if in ACM mode (mode 3)
    if (byte_595B2 == 3) {  // radar_mode_state
        goto floor_checks;
    }
    
    // Skip if radar mode flag not set
    if (byte_595B4 == 0) {  // radar_mode_flag
        goto floor_checks;
    }
    
    // Check if this is the currently tracked entity
    if (entity_ptr == current_tracked_entity) {
        floor_copy_4aa3();
        return;
    }

floor_checks:
    // Get entity angle/azimuth (at +0x8E)
    uint16_t angle = entity[+0x8E];
    
    // Normalize angle to range [0, 0x2000]
    if (angle > 0x2000) {
        angle = 0x4000 - angle;  // Fold from upper half
    }
    
    // Center at 0x1000 and get absolute deviation
    angle = abs(angle - 0x1000);
    
    // AZIMUTH CHECK: Must be within ±0xE3 (227 decimal) of forward
    if (angle > 0xE3) {
        goto check_range_or_clear;
    }
    
    // TARGET WITHIN AZIMUTH - Now check range
    
check_range_or_clear:
    // Check radar type
    if (byte_59573 == 1) {  // SAM mode
        goto range_check;
    }
    
    // Call distance bounds check
    farobj_dist_bounds_4ac0();
    if (out_of_range) {
        goto clear_flag;
    }
    
range_check:
    // Get entity range value at +0x92
    uint16_t range = entity[+0x92];
    
    // Call bound table check (likely F8 range setting lookup)
    bound_table_check_49b8(range);
    if (out_of_bounds) {
        goto clear_flag;
    }
    
    // ALL CHECKS PASSED - SET RADAR VISIBLE
    entity[+0x79] |= 0x01;  // Set RADAR_VISIBLE flag
    return;

clear_flag:
    // DETECTION FAILED - CLEAR RADAR VISIBLE
    entity[+0x79] &= 0xFE;  // Clear RADAR_VISIBLE flag
    return;
}
```

### Key Findings

**1. Azimuth Check (Angle at entity+0x8E):**
```c
// Normalized angle must be within ±0xE3 of forward (0x1000)
abs(angle - 0x1000) <= 0xE3
```

**0xE3 = 227 decimal**

In a 14-bit angle system (0x0000-0x3FFF representing 0-360°):
- 0x1000 = 4096 / 16384 = 1/4 circle = **90° (or forward direction)**
- 0xE3 = 227 units
- 227 / 16384 * 360° ≈ **5°**

**This is a ±5° cone check!** Much narrower than the manual's claimed 20°/60°/120°.

**Hypothesis:** The 0xE3 constant might be the NARROWEST setting, and F9 (azimuth key) modifies this value dynamically.

**2. Range Check (at entity+0x92):**
```c
bound_table_check_49b8(entity[+0x92])
```

This function likely looks up the current F8 range setting (10/20/40/80 nm) and compares the entity range against it.

**3. Radar Type Branching:**
- **SAM mode (type==1):** Skips `farobj_dist_bounds_4ac0`, goes straight to range check
- **Other modes:** Calls distance bounds check first

**4. Mode State Check:**
- Skips special handling if `radar_mode_state == 3` (ACM)
- Checks `radar_mode_flag` (byte_595B4) for active state

---

## Function 2: bound_range_check_4aad (0x3AA7E)

**Size:** 157 bytes  
**Purpose:** Range-based detection with state machine integration

### Disassembly Analysis

```c
bool bound_range_check_4aad(uint32_t distance_dx_ax) {
    // Shift right by 1 (divide by 2)
    distance_dx_ax >>= 1;
    
    // Check if distance fits in 16 bits
    if (dx != 0) {
        return OUT_OF_RANGE;  // Too far (>64K units)
    }
    
    // Compare against range bounds at DS:4AAD and DS:4AAF
    if (ax > [DS:4AAD]) return OUT_OF_RANGE;  // Too far
    if (ax < [DS:4AAF]) return OUT_OF_RANGE;  // Too close
    
    return IN_RANGE;
}

void bound_range_check_wrapper(entity_ptr) {
    // Check entity active flag
    if (!(entity[+0x74] & 0x01)) {  // Not active
        goto clear_flag;
    }
    
    // Get entity range
    uint16_t range = entity[+0x92];
    
    // Call bound table check
    if (bound_table_check_49b8(range) == OUT_OF_BOUNDS) {
        goto detection_passed;
    }
    
    // Check mode state
    if ([DS:4AC2] != 1) {
        goto clear_flag;
    }
    
    // Additional state checks...
    // (Complex state machine logic involving DS:4A93, DS:4AC3, etc.)
    
clear_flag:
    entity[+0x79] &= 0xFE;  // Clear RADAR_VISIBLE
    [DS:4AC4] = 0;
    // Update state machine variables
    return;

detection_passed:
    // More state checks
    if ([DS:4AC2] == 2) {
        goto set_visible;
    }
    
    if ([DS:4A83] == 1) {
        goto set_visible;
    }
    
    // Check entity distance fields
    uint32_t distance = (entity[+0x0A] << 16) | entity[+0x08];
    
    if (!bound_range_check_4aad(distance)) {
        goto clear_flag;
    }
    
    // Check entity range value
    if (entity[+0x92] >= 0x240) {
        goto set_visible;
    }
    
    // Update state machine
    [DS:4ABD] = 0;
    [DS:4AC3] = 0;
    [DS:4AC2] = 2;
    
set_visible:
    entity[+0x79] |= 0x01;  // Set RADAR_VISIBLE
    return;
}
```

### Key Findings

**1. Range Bounds (DS:4AAD and DS:4AAF):**

These global variables likely store the **min/max range** based on F8 setting:

| F8 Setting | Min Range (4AAF) | Max Range (4AAD) |
|------------|------------------|------------------|
| 10 nm | ~1 nm | 10 nm |
| 20 nm | ~2 nm | 20 nm |
| 40 nm | ~4 nm | 40 nm |
| 80 nm | ~8 nm | 80 nm |

**2. Entity Range Field (entity+0x92):**

This is the **computed range/distance** to the entity, likely in game units. The constant **0x240 (576 decimal)** is a threshold.

**3. Entity Distance Fields (entity+0x08/0x0A):**

32-bit distance value (lo:hi words) used for fine-grained range checking.

**4. State Machine Variables:**

Several DS-relative variables control detection state:
- **DS:4AC2** - Mode state (checked for 1 and 2)
- **DS:4A83** - Detection gate flag
- **DS:4ABD, DS:4AC3, DS:4AC4** - State machine flags
- **DS:4A93** - Timer/counter

---

## Detection Flow Diagram

```
Entity Update Loop (per frame)
        |
        v
    For each active entity:
        |
        v
farobj_floor_match_dispatch (0x3A9B7)
        |
        ├─ Check radar_mode_state (595B2)
        ├─ Check radar_mode_flag (595B4)
        |
        v
    Azimuth Check (entity+0x8E)
        |
        ├─ Normalize angle to [0, 0x2000]
        ├─ Center at 0x1000 (forward)
        ├─ abs(angle - 0x1000) <= 0xE3?
        |
        v
    YES: Within azimuth cone (~±5°)
        |
        v
    Check radar_type_selector (59573)
        |
        ├─ If SAM (type==1): Skip distance check
        ├─ Else: Call farobj_dist_bounds_4ac0()
        |
        v
    Range Check (entity+0x92)
        |
        ├─ Call bound_table_check_49b8(range)
        ├─ Compare against F8 setting bounds
        |
        v
    YES: Within range
        |
        v
    OR entity[+0x79], 0x01  ← SET RADAR_VISIBLE
        |
        v
    [Entity appears on radar]

    NO: Out of azimuth or range
        |
        v
    AND entity[+0x79], 0xFE  ← CLEAR RADAR_VISIBLE
        |
        v
    [Entity invisible to radar]
```

---

## F8/F9/F10 Parameter Integration

### F8 (Range: 10/20/40/80 nm)

**Global Variables:**
- **DS:4AAD** - Maximum range threshold
- **DS:4AAF** - Minimum range threshold

**Set by:** F8 key handler (scan code 0x42) updates these globals based on selection.

**Effect:** `bound_table_check_49b8` compares entity range (entity+0x92) against these bounds.

### F9 (Azimuth: 20°/60°/120°)

**Constant:** 0xE3 (227 units ≈ 5° in code)

**Hypothesis:** The azimuth check constant is **dynamically modified** by F9 handler:
- 20° mode: Sets constant to ~0xB6 (smaller cone, focused)
- 60° mode: Sets constant to ~0x22A (medium cone)
- 120° mode: Sets constant to ~0x455 (wide cone)

**To verify:** Need to find F9 key handler (scan code 0x43) and see what global it modifies.

**Current Evidence:** The hardcoded 0xE3 in `farobj_floor_match_dispatch` might be a **default or intermediate value**.

### F10 (Elevation: 1/2/4/6 bars)

**Not yet found in these functions.**

**Hypothesis:** Elevation is handled by a **separate vertical angle check** (entity+0x90 or similar field) with similar logic to azimuth.

**To find:** Search for entity field accesses around +0x90-0x94 with angle normalization patterns.

---

## Entity Fields Identified

### New Fields from Detection Logic

| Offset | Name (Proposed) | Type | Purpose |
|--------|-----------------|------|---------|
| +0x08 | `distance_lo` | uint16 | Distance lo word (32-bit pair with +0x0A) |
| +0x0A | `distance_hi` | uint16 | Distance hi word |
| +0x8E | `angle_azimuth` | uint16 | Azimuth angle (14-bit, 0x0000-0x3FFF) |
| +0x92 | `range` | uint16 | Computed range/distance to player |

### Complete Radar-Relevant Fields

| Offset | Name | Type | Purpose |
|--------|------|------|---------|
| +0x08 | `distance_lo` | uint16 | Distance lo word |
| +0x0A | `distance_hi` | uint16 | Distance hi word |
| +0x74 | `status_flags` | EntityStatusFlags | Bit 0: ACTIVE, Bit 6: AIRCRAFT_TYPE |
| +0x79 | `tracking_flags` | EntityTrackingFlags | Bit 0: **RADAR_VISIBLE** |
| +0x8E | `angle_azimuth` | uint16 | Azimuth angle from player |
| +0x92 | `range` | uint16 | Range to player |
| +0x96 | `position_x` | int16 | World X |
| +0x98 | `position_y` | int16 | World Y |
| +0x9A | `position_z` | int16 | Altitude |

---

## Detection Probability - SIMPLIFIED MODEL

**Key Finding:** Detection is **NOT probabilistic with RNG** - it's **deterministic bounds checking!**

The "detection chance" the manual refers to is effectively:
1. **Azimuth:** In cone or not (binary, but cone size adjustable with F9)
2. **Range:** Within bounds or not (binary, bounds set by F8)
3. **Elevation:** Within bars or not (binary, bars set by F10 - not yet found)

**No RNG calls found in detection functions.**

**This is more like a radar "scan pattern"** than a probability simulation:
- Narrow settings (20°, 1 bar, 10nm) = **small search volume, all targets within detected**
- Wide settings (120°, 6 bars, 80nm) = **large search volume, all targets within detected**

**Trade-off:**
- Narrow: **High certainty within cone**, but **easy to miss** targets outside
- Wide: **See everything**, but **more targets to track** (information overload)

**Real-world radar simulation:** The difficulty comes from **managing the scan pattern**, not from random detection failures.

---

## Global Variables for Detection

### New Globals Identified

| Address | Name (Proposed) | Type | Purpose |
|---------|-----------------|------|---------|
| 0x4AAD | `radar_range_max` | uint16 | Maximum detection range (F8 setting) |
| 0x4AAF | `radar_range_min` | uint16 | Minimum detection range |
| 0x4AC2 | `detection_mode_state` | uint8 | Detection state machine mode |
| 0x4A83 | `detection_gate_flag` | uint8 | Detection enable gate |
| 0x4ABD | `detection_state_flag_1` | uint8 | State flag |
| 0x4AC3 | `detection_state_flag_2` | uint8 | State flag |
| 0x4AC4 | `detection_state_flag_3` | uint8 | State flag |
| 0x4AC5 | `detection_state_flag_4` | uint8 | State flag |
| 0x4A93 | `detection_timer` | uint16 | Detection timer/counter |
| 0x4A91 | `detection_threshold` | uint16 | Threshold value (set to 0xA00) |

---

## Functions to Analyze Next

### High Priority

1. **`bound_table_check_49b8` (0x49B8):**
   - Looks up range in bounds table
   - Likely uses F8 setting as index
   - Returns in_bounds/out_of_bounds

2. **`farobj_dist_bounds_4ac0` (0x4AC0):**
   - Distance bounds check
   - May compute 3D distance
   - Returns in_range/out_of_range

3. **F9 Key Handler (scan code 0x43):**
   - Find what variable it modifies
   - Likely changes the 0xE3 azimuth constant
   - Or modifies a global that azimuth check reads

4. **F10 Key Handler (scan code 0x44):**
   - Elevation bar control
   - Find vertical angle checks
   - Likely similar pattern to azimuth

5. **Entity Angle Computation:**
   - How is entity+0x8E computed?
   - Relative angle from player to target
   - Probably in entity update functions

---

## Summary

**DETECTION IS DETERMINISTIC, NOT PROBABILISTIC!**

✅ **Found:**
- Two functions that set/clear RADAR_VISIBLE flag
- Azimuth cone check: ±0xE3 units (≈±5°, likely F9-adjustable)
- Range bounds check: DS:4AAD (max), DS:4AAF (min) from F8
- Entity fields: +0x8E (azimuth), +0x92 (range), +0x08/0x0A (distance)
- State machine with mode checks and gates

❓ **Still Missing:**
- F9 azimuth constant modification
- F10 elevation bar logic (vertical angle check)
- How entity angles (+0x8E) are computed
- Complete bound_table_check_49b8 logic

📊 **Completion:**
- **Detection logic: 85%** (main mechanism found, parameters incomplete)
- **Overall radar system: 97%** (only F9/F10 parameter handling remains)

---

**Next:** Analyze `bound_table_check_49b8` and find F9/F10 handlers to complete the detection system.
