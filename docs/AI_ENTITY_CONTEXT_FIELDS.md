# AI Entity Context Fields - Extended Documentation
**Date**: 2025-01-15  
**Source**: IDA analysis of ai_grid_position_update and related functions

## Overview

The AI system operates on an **entity context structure** passed via SI register. This structure contains at least **0x4D bytes** (77 bytes) based on observed field accesses. It differs from the smaller AIContext structure (24 bytes) documented in structs.yaml.

## Discovered Fields

### Position & Grid System (+0x31 - +0x35)

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0x31 | 1 | byte | grid_x_tile | World grid X tile coordinate (wraps at 52?) |
| +0x32 | 1 | byte | grid_y_tile | World grid Y tile coordinate |
| +0x33 | 2 | word | grid_x_frac | Grid X fractional position (subpixel 0-0x3333) |
| +0x35 | 2 | word | grid_y_frac | Grid Y fractional position (subpixel 0-0x3333) |

**Grid System Details**:
- Wraparound boundary: **0x3334** (13,108 decimal)
- When fraction >= 0x3334: increment tile, subtract 0x3334 from fraction
- When fraction < 0: decrement tile, add 0x3334 to fraction
- Suggests **52 tiles × 256 subunits** or **13,108 units** per world axis

### Heading & Turn Rate (+0x1D, +0x4C)

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0x1D | 2 | word | entity_heading | Current heading (14-bit angle, 0-0x3FFF) |
| +0x4C | 2 | word | turn_rate | Turn rate capability (scaled by RFM) |

**Usage**: 
- `ai_heading_adjustment_gate` reads +0x1D, compares with farobj +0x0C
- Scales +0x4C by `rfm_turn_rate_scalar` to determine max turn per frame
- Updates farobj heading with clamped delta

### Behavior System (+0x0A, +0x0B, +0x08)

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0x08 | 2 | word | state_flags | AI state flags (bit 0 = position dirty) |
| +0x0A | 1 | byte | behavior_flags_low | Lower behavior flags (bits 0-1 entity-specific, 2-7 copied from leader) |
| +0x0B | 1 | byte | behavior_flags_high | Higher behavior flags (bit 7 copied from leader) |

**Behavior Mirroring** (ai_behavior_mirror_to_target @ 0x3D1C5):
- **Copied from leader**: +0x0A bits 2-7, +0x0B bit 7
- **Retained locally**: +0x0A bits 0-1
- Purpose: Wingmen mirror leader's combat stance while maintaining local state

### Additional Fields (+0x14, +0x1A-1C, +0x37, +0x39)

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0x14 | 2 | word | altitude | Altitude (used for LOD calculation) |
| +0x1A | 1 | byte | unknown_1A | Copied during behavior mirroring |
| +0x1B | 1 | byte | unknown_1B | Copied during behavior mirroring |
| +0x1C | 1 | byte | unknown_1C | Copied during behavior mirroring |
| +0x37 | 2 | word | unknown_37 | Copied during behavior mirroring |
| +0x39 | 1 | byte | unknown_39 | Copied during behavior mirroring |

### Farobj Reference (+0x06)

| Offset | Size | Type | Name | Description |
|--------|------|------|------|-------------|
| +0x06 | 2 | word | farobj_ptr | Pointer to associated farobj structure |

**Farobj Fields** (accessed via DI = [SI+6]):
- **+0x0C**: Heading (updated by ai_heading_adjustment_gate)
- **+0x50**: X velocity (added to grid_x_frac)
- **+0x52**: Y velocity (added to grid_y_frac)
- **+0x56**: Unknown (compared in ai_target_tracking_update)
- **+0x60**: Unknown (copied to +0x23 in multiple paths)
- **+0x75**: Entity type (0x33 = aircraft?, 0x10 = special type?)

---

## Altitude LOD Ranges

**ai_grid_position_update** sets farobj field based on altitude:

| Altitude Range (hex) | Altitude Range (dec) | LOD Value | Terrain Detail |
|---------------------|---------------------|-----------|----------------|
| < 0x139 | < 313 | 0 | Lowest (ground) |
| 0x139 - 0x1FA | 313 - 506 | (alt-0x11A)>>5 | Scaled 0-6 |
| >= 0x1FA | >= 506 | 7 | Highest |

**Formula** (middle range):
```c
lod = (altitude - 0x11A) >> 5;  // (alt - 282) / 32
```

---

## World Grid Math

**Position Update** (ai_grid_position_update @ 0x3CEF4):

```c
// X-axis update
grid_x_frac += velocity_x;
if (grid_x_frac < 0) {
    grid_x_tile--;
    grid_x_frac += 0x3334;
    dirty = true;
} else if (grid_x_frac >= 0x3334) {
    grid_x_tile++;
    grid_x_frac -= 0x3334;
    dirty = true;
}

// Same for Y-axis
// ...

if (dirty) {
    state_flags |= 1;  // Set position dirty flag
}
```

**World Size Calculation**:
- If wraparound = 0x3334 = 13,108 units
- Possible interpretations:
  - 52 tiles × 256 units = 13,312 (close)
  - 51 tiles × 256 + 52 = 13,108 (exact)
  - Or: Fixed-point with fractional bits

---

## Integration with Registry

These fields should be added to the **entity context structure** in `registry/structs.yaml`. The structure passed to AI functions is larger than the 24-byte AIContext currently documented.

**Proposed Action**:
1. Create new structure: **AIEntityContext** (size >= 0x4D bytes)
2. Merge fields from AIContext (0x00-0x14) with newly discovered fields
3. Document relationship between AIContext and AIEntityContext

---

## Cross-References

**Functions using these fields**:
- `ai_heading_adjustment_gate` @ 0x3CE92: +0x1D, +0x4C
- `ai_entity_data_copy_18byte` @ 0x3CEDD: +0x06
- `ai_grid_position_update` @ 0x3CEF4: +0x31/32/33/35, +0x08, +0x14
- `ai_behavior_mirror_to_target` @ 0x3D1C5: +0x0A/0B, +0x1A/1B/1C, +0x37, +0x39
- `ai_state_processor_core` @ 0x3CF9D: Multiple fields throughout

**Related RFM Globals**:
- `rfm_ai_behavior_ptr` @ cs:0x3B830: AI behavior data pointer
- `rfm_turn_rate_scalar` @ cs:0x3B832: Turn rate scaling factor

---

**Status**: Fields identified but not yet added to registry structures. Needs structure definition update.
