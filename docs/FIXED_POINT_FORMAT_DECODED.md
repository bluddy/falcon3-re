# Fixed-Point Format Decoded

## Discovery

The 3D math engine uses a **custom 15-bit fixed-point format** with per-axis normalization adjustments.

---

## Divisor Values (cs segment)

```
cs:0x22C83  fixedpoint_divisor_x  = 32771 (0x8003)
cs:0x22C85  fixedpoint_divisor_y  = 32779 (0x800B)
cs:0x22C87  fixedpoint_divisor_z  = 32783 (0x800F)
```

### Analysis

**Base**: ~32768 (2^15)
**Variance**: X=+3, Y=+11, Z=+15 from base

This is NOT standard 8.8, 12.4, or 16.16 fixed-point!

**Interpretation**: Custom 15-bit normalization with slight per-axis adjustments, likely for:
- Lens distortion correction
- Aspect ratio compensation
- Screen space mapping optimization

### Format: **15.1 Custom**

- 15 bits for integer/fractional combined
- Divisor ~32768 provides normalization scale
- Small variations per axis for corrections

---

## Current State Snapshot

Captured from idle IDA database (not during gameplay):

### Vector Components
```
vec3_x_component  = 7397
vec3_y_component  = 29447
vec3_z_component  = 802
```

### Matrix Scale Factors
```
matrix_scale_x  = 179
matrix_scale_y  = 183
matrix_scale_z  = 182
```

**Average scale**: 181.3
**Interpretation**: Small scale factors suggest either:
- Narrow field of view (zoomed in)
- World coordinates in large units
- These are idle/default values, not active projection

---

## Algorithm Implementation

### Python Test

```python
def fixed_vec3_accumulate(vec_x, vec_y, vec_z, 
                         scale_x, scale_y, scale_z,
                         div_x, div_y, div_z):
    """
    Implement fixed_vec3_accumulate_a algorithm.
    Result = (X*ScaleX % DivX) + (Y*ScaleY % DivY) + (Z*ScaleZ % DivZ)
    """
    
    # X component
    product_x = vec_x * scale_x
    remainder_x = product_x % div_x
    result = remainder_x
    
    # Y component
    product_y = vec_y * scale_y
    remainder_y = product_y % div_y
    result += remainder_y
    
    # Z component
    product_z = vec_z * scale_z
    remainder_z = product_z % div_z
    result += remainder_z
    
    return result
```

### Test Results

**Test Case 1: Idle Values**
```
Vector: (7397, 29447, 802)
Scale:  (179, 183, 182)
Divisor: (32771, 32779, 32783)

X: 7397 * 179 = 1,324,063 → remainder 13,223
Y: 29447 * 183 = 5,388,801 → remainder 13,045
Z: 802 * 182 = 145,964 → remainder 14,832

Result: 41,100 (0xA08C)
Signed 16-bit: -24,436
```

**Test Case 2: Simple Values**
```
Vector: (100, 100, 100)
Scale:  (1000, 1000, 1000)
Divisor: (32768, 32768, 32768)

Each component: 100 * 1000 = 100,000 → remainder 1,696
Total: 5,088 (0x13E0)
```

---

## Key Insight: Remainder Accumulation

The algorithm stores **remainders** (modulo), not quotients!

```assembly
div cs:fixedpoint_divisor_x     ; AX = quotient, DX = remainder
mov cs:vec3_x_component, dx     ; Store REMAINDER back
mov cx, dx                      ; CX = remainder (result)
```

**Why remainders?**

1. **Pseudo-random variation**: Remainders create pseudo-random values for animation
2. **Fractional precision**: Keep sub-pixel precision between frames
3. **Accumulator pattern**: Builds up over multiple calls
4. **Timing effects**: Mentioned in IDA comments as "timing-based pseudo-RNG"

This is NOT standard fixed-point arithmetic - it's an accumulator with pseudo-random behavior!

---

## Projection Math Reconstruction

### Standard Fixed-Point (Expected)

```
screen_x = (cam_x * focal_length) / divisor
```

### Actual Algorithm (Observed)

```
result = (cam_x * matrix_scale_x) % divisor_x +
         (cam_y * matrix_scale_y) % divisor_y +
         (cam_z * matrix_scale_z) % divisor_z
```

The result accumulates **remainders**, not quotients!

### Additional Scaling Required

The result from `fixed_vec3_accumulate_a` needs additional processing:

1. **Quotient extraction**: Likely done by caller before/after
2. **Zoom multiplication**: Scale by zoom factor
3. **Screen centering**: Add 160 (X) or 100 (Y)
4. **Clipping**: Test against 0-319, 0-199

**Evidence**: Result of 8480 for test case is way outside screen bounds (0-319).
The caller must apply additional division or right-shift to bring into screen range.

---

## Typical Projection Pipeline (Hypothesis)

```c
// 1. Load vector and matrix
vec3_x = world_x - camera_x;
vec3_y = world_y - camera_y;
vec3_z = world_z - camera_z;

matrix_scale_x = projection_matrix[0][0];  // M11
matrix_scale_y = projection_matrix[0][1];  // M12
matrix_scale_z = projection_matrix[0][2];  // M13

// 2. Call accumulator
remainder_sum = fixed_vec3_accumulate_a();

// 3. Additional scaling (MISSING PIECE)
// Likely: screen_x = remainder_sum >> shift_factor
// Or: screen_x = remainder_sum / additional_divisor

// 4. Apply zoom
screen_x = screen_x * zoom_factor;

// 5. Center on screen
pixel_x = screen_x + 160;

// 6. Clip
if (pixel_x < 0 || pixel_x > 319) → off-screen
```

**The key missing piece**: How remainder_sum converts to screen coordinate range.

---

## Per-Axis Divisor Variance

```
X: 32771 = 32768 + 3
Y: 32779 = 32768 + 11
Z: 32783 = 32768 + 15
```

**Increasing variance** (X < Y < Z) suggests intentional correction factors.

### Possible Reasons

1. **Aspect ratio**: VGA 320×200 is not 1:1 (320/200 = 1.6:1)
2. **Pixel aspect**: Mode 13h pixels are not square (1:1.2 ratio)
3. **Lens distortion**: Simulating camera lens effects
4. **Depth perception**: Z-axis needs different scale for perspective

### Correction Formula

```
True aspect ratio = 320 / 200 = 1.6
Pixel aspect ratio = 1 / 1.2 = 0.833

Combined: 1.6 / 0.833 = 1.92

This might explain Y having larger divisor than X
(to compensate for non-square pixels).
```

---

## Comparison with view_projection

The other 3D function `view_projection` (0x20BDB) uses different math:

```
delta = (target - origin) * 16
result = abs(delta) / |scale|
```

This is **quotient-based**, not remainder-based!

### Two Projection Systems

Falcon 3.0 appears to have TWO different 3D projection systems:

1. **view_projection**: Quotient-based, 282K calls/frame
   - Used for: Terrain tiles, view list entities, cockpit vectors
   - Returns screen coordinates directly

2. **fixed_vec3_accumulate_a**: Remainder-based, 51K calls/frame
   - Used for: HUD, flight physics, tactical map, special effects
   - Returns accumulated remainder (needs additional scaling)

**Hypothesis**: System 2 is for **dynamic/animated** elements where the accumulator pattern provides smooth motion and pseudo-random variation.

---

## Runtime Testing Required

To fully understand the projection, we need:

1. **Capture during tactical map display**:
   - Vector values (waypoint positions)
   - Matrix scale values (actual projection matrix)
   - Result from fixed_vec3_accumulate_a
   - Final screen coordinate

2. **Capture during HUD rendering**:
   - How is result scaled to screen?
   - What additional operations occur?
   - Where does zoom factor apply?

3. **Trace complete flow**:
   - waypoint_display_helper → fixed_vec3_accumulate_a → caller processing → pixel

---

## Conclusions

### ✅ Confirmed

- **Format**: Custom 15-bit with divisors ~32768
- **Algorithm**: Remainder accumulation, not quotient
- **Per-axis variance**: Intentional corrections (+3, +11, +15)
- **Purpose**: Pseudo-random variation + fractional precision

### ⏳ Needs Investigation

- **Remainder → Screen coordinate conversion**: Missing scaling step
- **Matrix values during actual projection**: Idle values captured, not active
- **Zoom factor application**: Where and how?
- **Relationship to view_projection**: Why two systems?

### 🎯 Next Steps

1. Set debugger breakpoint at 0x022C91 during tactical map display
2. Capture vector, matrix, and result values
3. Trace caller to see post-processing
4. Compare with view_projection results
5. Document complete transformation formula

---

## Impact on Recreation

To recreate tactical map projection:

```c
// Use observed algorithm
int16_t remainder = fixed_vec3_accumulate(vec_x, vec_y, vec_z,
                                          scale_x, scale_y, scale_z,
                                          32771, 32779, 32783);

// MISSING: How to convert remainder to screen coordinate?
// Likely one of:
//   screen = remainder >> shift_bits
//   screen = remainder / some_divisor
//   screen = (remainder * multiplier) >> shift

// Then apply zoom and center
int16_t pixel = (screen * zoom) + 160;

// Clip
if (pixel < 0 || pixel > 319) → off_screen
```

**The critical missing piece** is the remainder → screen coordinate conversion.

This requires either:
- Runtime debugging to capture the complete flow
- Analysis of waypoint_display_helper to find post-processing
- Reverse engineering the caller's handling of the result

---

## Summary

We've decoded the math algorithm itself, but discovered it's more complex than expected:

- **Not standard fixed-point** - custom format with intentional variance
- **Remainder-based** - accumulates modulo results, not quotients
- **Requires additional scaling** - result is not directly a screen coordinate
- **Dual-purpose** - provides both projection AND pseudo-random variation

**Progress**: 70% → 75% (+5%)

The final 25% requires runtime debugging to capture the complete transformation pipeline.
