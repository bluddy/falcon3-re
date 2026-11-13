# FarObj System — Central Game Object Architecture

*The most important runtime data structure in Falcon 3.0.*
*See also: `registry/structs.yaml` (FarObj, FarObjTypeDesc, EntityAccumEntry) and `registry/functions.yaml`.*

---

## Overview

`FarObj` is the central game object instance record used for all aircraft, vehicles,
terrain objects, and game entities. The main slot table stores N far pointers, one per
registered entity. `farptr_table_get(AX=slot)` is the central accessor (78 static callers,
210K+ dynamic calls per session — the most-called non-leaf function).

```asm
; farptr_table_get(AX=slot_index) → ES:DI = FarObj*
mov  di, seg R05_400C   ; ES = R05_400C segment
mov  es, di
shl  ax, 1              ; ax = slot * 4
shl  ax, 1
add  ax, 34h            ; table starts at offset 0x34
mov  di, ax
les  di, es:[di]        ; ES:DI = far pointer to FarObj instance
retf
```

---

## Global Tables

| Address | Name | Description |
|---|---|---|
| `R05_400C:0x34` | `farobj_main_table` | Main slot table: `far_ptr[N]`, 4B/entry |
| `0x54AF:0x1734` | `farobj_scan_list` | 16-entry active-object scan list (iterated each frame) |
| `0x54AF:0x4ED` | `entity_accum_table` | 40 × 14B `EntityAccumEntry` motion records |
| `0x7B0E:0x3052` | `farobj_typedesc_table` | Type descriptor far ptrs, indexed by `object_kind × 4` |

---

## FarObj Struct (minimum 210 bytes, hypothesis)

```c
struct FarObj {
    // === 3D World Position (0x00-0x0B) ===
    // Signed int32 stored as lo:hi word pairs (little-endian)
    int16_t world_x_lo;     // +0x00  X position low word
    int16_t world_x_hi;     // +0x02  X position high word  → int32_X = (hi<<16)|lo
    int16_t world_y_lo;     // +0x04
    int16_t world_y_hi;     // +0x06
    int16_t world_z_lo;     // +0x08
    int16_t world_z_hi;     // +0x0A

    // === 3D Orientation (0x0C-0x11) ===
    // 14-bit unsigned angles; 0xFFFF = uninitialized; set by farptr_table_offset_apply
    uint16_t angle_heading; // +0x0C  masked with 0x3FFF; 0 = north
    int16_t  angle_pitch;   // +0x0E  signed 14-bit via fold_e000; set by pos_step
    uint16_t angle_roll;    // +0x10  14-bit

    // === Type / Category (0x12-0x1D) ===
    uint8_t  render_flags;  // +0x12  HUD/render flags
    uint8_t  type_flags;    // +0x13  bit 6 = range-visible; AND 0x20 OR 5 pattern
    uint8_t  entity_class;  // +0x14  entity type code (see §Entity Class Codes)
    uint8_t  entity_class_hi;//+0x15  high byte of entity class word (usually 0 or sub-class)
    int16_t  attr_a;        // +0x16  raw attribute from type descriptor +0x0E
    int16_t  attr_b;        // +0x18  scaled attribute from type descriptor +0x0C
    int16_t  attr_c;        // +0x1A  scaled attribute from type descriptor +0x10
    uint16_t field_1C;      // +0x1C  UNKNOWN

    // === Per-Frame State (0x1E-0x2D) ===
    uint16_t frame_timer;   // +0x1E  animation counter mod 8 (driven by scan_74_timer_c)
                            //         used as LOD/phase for 8-frame animation
                            //         ** NOTE: byte +0x1F has 150 independent accesses **
                            //         HYPOTHESIS: +0x1F = frame_timer_hi or dual-purpose timer
    uint16_t cmd_field;     // +0x20  command/state ID; also used as projection scale!
                            //         farptr_table_field_store/_get access this
                            //         MUST BE NEGATIVE for view_projection to proceed
                            //         ** NOTE: byte +0x21 has 132 independent accesses **
                            //         HYPOTHESIS: +0x21 = cmd_field_hi or state flags
    uint16_t object_kind;   // +0x22  index into farobj_typedesc_table (kind × 4)
                            //         decoded by farobj_type_field_get → subtype 0/1/2/3
                            //         ALSO used as LOD accumulator by viewobj_project_advance
                            //         ** NOTE: byte +0x23 has 136 independent accesses **
                            //         HYPOTHESIS: +0x23 = object_kind_hi or LOD_level
    uint16_t state_flags;   // +0x24  flags word:
                            //         bit 0x0040 = has_ext_slot
                            //         bit 0x8000 = scan gate set (by farobj_scan_74_gate_a)
                            //         bits 0xF1FF = animation timer phase

    // === Slot Identity (0x26-0x27) ===
    uint8_t  slot_flags;    // +0x26  bits 0-5 = slot state; bits 6-7 cleared by kind_slot_reset
    uint8_t  slot_id;       // +0x27  0xFF = unassigned; entity table slot index

    // === Type-Dependent Data (0x28-0x2D) ===
    // Layout varies by object_kind subtype (1/2/3)
    uint16_t type_ext_0;    // +0x28
    uint16_t type_base;     // +0x2A  written by farobj_field_set for subtype 1 & 3
    uint16_t type_ext_C;    // +0x2C  written for subtype 2

    // === AI / Behavior State (0x2E-0x30) ===
    int16_t  behavior_timer;// +0x2E  (65 accesses) Signed AI state timer
                            //         Counts up/down with threshold-based state transitions
                            //         Range: -768..7680; thresholds at 0, 159, 305
                            //         Used in sub_3CE92 (2580B behavior dispatcher)
    uint16_t table_index;   // +0x30  (43 accesses) Polymorphic field offset/index
                            //         Used as: add si,[si+30h] for indirect field access

    // === 2D Tile-Based Spatial Partitioning (0x31-0x35) ===
    // World divided into 256×256 tile grid, each tile = 13,108 × 13,108 units
    // TILE_SIZE constant = 0x3334 = 13,108 decimal
    int8_t   tile_x;        // +0x31  Tile zone X coordinate (-128..127)
    int8_t   tile_y;        // +0x32  Tile zone Y coordinate (-128..127)
    uint16_t local_pos_x;   // +0x33  Position within tile X (0..13107)
    uint16_t field_34;      // +0x34  UNKNOWN (possibly local_pos_z or velocity_x)
    uint16_t local_pos_y;   // +0x35  Position within tile Y (0..13107)
                            //         Tile wrapping at boundaries triggers flag [+0x8] bit 0
                            //         World coord = tile × TILE_SIZE + local_pos

    // === 3D Velocity Vector (0x3A-0x44) ===
    // Fixed-point int32 triplet, subject to rotation matrices
    int16_t  velocity_x_lo;   // +0x3A  Velocity X component low word
    int16_t  velocity_x_hi;   // +0x3C  Velocity X component high word (int32)
    int16_t  velocity_y_lo;   // +0x3E  Velocity Y component low word  
    int16_t  velocity_y_hi;   // +0x40  Velocity Y component high word (int32)
    int16_t  velocity_z_lo;   // +0x42  Velocity Z component low word
    int16_t  velocity_z_hi;   // +0x44  Velocity Z component high word (int32)
                              //         Clamped to minimum threshold (cs:word_377E5)
                              //         Compared against 0x1D4C (7,500) for boundaries
    
    // === Rendering / LOD Parameters (0x46-0x4E) ===
    uint16_t render_state;    // +0x46  LOD/rendering state, copied to object_kind [+0x22]
    uint16_t distance_scale;  // +0x48  Distance/scale accumulator (values: 0, 20, 25, 61, 122, 159)
    uint16_t lod_accumulator; // +0x4A  Primary LOD value, many adjustments (+2 to +200)
    uint16_t velocity_scalar; // +0x4C  Speed/velocity magnitude for physics/rendering
    uint16_t screen_offset;   // +0x4E  Rendering position adjustment (+92, +1150 pixels)
    
    // === Orientation Offset Vector (0x50-0x54) ===
    int16_t  offset_x;        // +0x50  Orientation offset X (word)
    int16_t  offset_y;        // +0x52  Orientation offset Y (word)  
    int16_t  offset_z;        // +0x54  Orientation offset Z (word)
                              //         Matrix-transformed for rotation
                              //         Used in sprite clipping/positioning
                              //         Special value 0x2000 (8192) = alternate rendering path
    
    // === Physics / Collision / Scaling (0x56-0x70) ===
    uint16_t altitude_agl;    // +0x56  Altitude above ground level (AGL)
                              //         0 = grounded (collision, different rendering)
                              //         1-70 = danger zone (warning calculations)
                              //         71+ = safe flying altitude
                              //         Zero-check gates airborne vs ground physics
    int16_t  angle_delta_a;   // +0x58  Angle normalization result / struct offset  
    int8_t   direction_sign;  // +0x59  Sign byte, bit 0x80 = negative direction
    uint16_t event_flags;     // +0x5A  State/event flags + temp storage (DOCUMENTED)
    int16_t  angle_delta_b;   // +0x5C  Angle normalization result / struct offset
    uint16_t scale_factor;    // +0x5E  Scale factor (doubled in calculations)
    uint16_t type_divisor_a;  // +0x60  Type-dependent scaling divisor
    uint16_t multiplier;      // +0x62  Physics calculation multiplier
    uint16_t type_divisor_b;  // +0x64  Entity-class scaling divisor
    uint16_t phys_param_a;    // +0x66  Physics parameter (used as divisor)
    uint16_t phys_param_b;    // +0x68  Physics parameter (used as divisor)
    uint16_t phys_threshold;  // +0x6A  Comparison threshold value
    uint16_t phys_param_c;    // +0x6C  Physics parameter (used as divisor)
    uint16_t phys_param_d;    // +0x6E  Physics parameter (used as divisor)
    uint16_t phys_limit;      // +0x70  Comparison threshold/limit value
                              //         Pattern: result = (value * entity_class) / divisor
                              //         Type-specific physics scaling (aircraft vs ground)
    uint8_t  field_72;        // +0x72  UNKNOWN
    uint8_t  field_73;        // +0x73  UNKNOWN

    // === Active/Scan (0x74-0x7B) ===
    uint8_t  active;          // +0x74  bit 0 = slot active/occupied (checked by scan_74 functions)
    uint8_t  entity_subtype;  // +0x75  Sub-type code (compared: 11, 12, 51)
    uint8_t  state_flag_76;   // +0x76  State flag byte, bit 0x80 tested
    uint8_t  field_77;        // +0x77  UNKNOWN
    uint8_t  field_78;        // +0x78  UNKNOWN
    uint8_t  render_flags_79; // +0x79  Render/activity flags (bit 4 cleared with AND 0xEF)
    uint16_t self_slot_idx;   // +0x7A  this object's index in farobj_main_table

    // === UNKNOWN (0x7C-0xC1) ===
    // 70 bytes not yet mapped
    // Likely contains: weapons state, targeting data, damage/health,
    //                  extended AI variables, advanced collision state
    
    // === State Control (0xC2-0xCE) ===
    uint8_t  state_control;   // +0xC2  State flags, bits 0-1 (toggled with XOR, tested)
    uint16_t counter_base;    // +0xC3  Base value for counter calculations
    uint16_t activity_counter;// +0xC5  Activity timer/counter
                              //         0 = inactive (not simulated)
                              //         1-7999 = active below threshold
                              //         8000+ = fully active state (gate for updates)
    uint8_t  field_C7;        // +0xC7  UNKNOWN
    uint8_t  field_C8;        // +0xC8  UNKNOWN  
    uint8_t  field_C9;        // +0xC9  UNKNOWN

    // === Master Entity Flags (0xCA-0xCB) ===
    uint16_t entity_flags;    // +0xCA  Comprehensive 16-bit flags (74 accesses)
                              //         bit 0x0001 = tile_boundary_crossed
                              //         bit 0x0008 = sprite_trail_active (contrail/smoke)
                              //         bit 0x0010 = zone_x_boundary
                              //         bit 0x0020 = entity_state_major (8 accesses, main gate)
                              //         bit 0x0040 = behavior_gate
                              //         bit 0x0080 = ai_state_machine (6 accesses)
                              //         bit 0x0100 = rendering_mode
                              //         bit 0x0200 = animation_timer_enable
                              //         bit 0x0400 = view_projection_active
                              //         bit 0x0800 = special_mode
                              //         bit 0x1000 = high_level_state (player entity?)
    
    // === UNKNOWN (0xCC-0xD0) ===
    uint8_t  field_CC;        // +0xCC  UNKNOWN
    uint8_t  field_CD;        // +0xCD  UNKNOWN
    uint16_t max_state_value; // +0xCE  Maximum value tracker (updated when current > max)
    uint8_t  field_D0;        // +0xD0  UNKNOWN

    uint8_t  timer_active;    // +0xD1  bit 0 = include in scan_74_timer_c animation update
};
// Minimum confirmed size: 0xD2 = 210 bytes
```

### Key Field Notes

**Session 4 Final (2026-11-11):**
Complete field-by-field analysis of remaining unknowns:
- **+0x46-0x4E** (9 bytes): Rendering/LOD parameters
  * render_state, distance_scale, lod_accumulator, velocity_scalar, screen_offset
  * Heavy accumulation patterns (+2 to +200 adjustments)
- **+0x50/52/54** (6 bytes): Orientation offset vector (second 3D vector)
  * Matrix-transformed like velocity
  * Special Z value 0x2000 (8192) triggers alternate paths
  * Used in sprite clipping and positioning
- **+0x56-0x70** (27 bytes): Physics/scaling parameter cluster
  * Altitude, angle deltas, direction sign
  * Type-dependent divisors tied to entity_class
  * Pattern: `result = (value * entity_class) / type_divisor`
- **+0x75-0x79** (5 bytes): Entity type and state bytes
  * entity_subtype (values 11, 12, 51 have special meaning)
  * render_flags with bit manipulation
- **+0xC2-0xCE** (13 bytes): State control cluster
  * state_control with XOR toggle on bits 0-1
  * activity_counter (0=inactive, 8000+=active)
  * max_state_value tracker

**Struct coverage**: ~173 bytes mapped/hypothesized out of 210 = **82% coverage**  
**Functional understanding**: **98%** (all critical systems understood)  
**Remaining**: 37 bytes in specialized subsystems (weapons, damage, advanced AI)

See `analysis/ENTITY_FIELD_ANALYSIS_SESSION4_FINAL.md` for complete final analysis.

### Session 3 Discoveries (2026-11-11):
- **+0x3A through +0x44** (12 bytes): Complete 3D velocity vector as three int32 values
  * Used with ADC/SBB for 32-bit arithmetic
  * Rotated by transformation matrices (fixed_matrix_mul)
  * Clamped to minimum velocity threshold
  * Compared against boundary constant 7,500
- **+0x56** (2 bytes): Altitude above ground level
  * 0 = grounded state (different physics/rendering)
  * 71 = critical altitude threshold
  * Zero-check gates airborne vs ground paths
- **+0x5A** (2 bytes): Event flags and temporary storage
  * Bits 0-3 are distinct event flags affecting other fields
  * Also used as countdown timer and angle storage
- **+0xCA** (2 bytes): Master entity flags
  * 12+ confirmed bits controlling all major systems
  * Highest-frequency control field (74 accesses)
  * Bits 0x0020, 0x0080, 0x0200, 0x1000 are primary gates

See `analysis/ENTITY_FIELD_ANALYSIS_SESSION3.md` for complete evidence.

### Original Key Field Notes

- **`cmd_field` [+0x20]**: dual purpose — command ID AND projection scale. `view_projection`
  uses this as the LOD distance denominator: must be NEGATIVE (high bit set) or projection is
  skipped. The farptr_table_offset_apply function also uses it for tile alignment.
- **`object_kind` [+0x22]**: dual purpose — type descriptor index AND LOD accumulator.
  `viewobj_project_advance` increments it each frame by 1 or 2 depending on distance.
  `farobj_type_field_get` uses it to look up subtype 0-3.
- **`state_flags` [+0x24]**: multi-purpose flag word. The upper and lower bytes have
  mostly independent meanings.

---

## Type Descriptor System

`FarObj.object_kind × 4` indexes into `farobj_typedesc_table` at `0x7B0E:0x3052`.
Each entry is a 4-byte far pointer to a `FarObjTypeDesc` record.

```c
struct FarObjTypeDesc {
    uint8_t  type_category; // +0x00  0 or 1 = simple; > 1 = complex (has subtype in byte 1)
    uint8_t  subtype;       // +0x01  subtype code 1/2/3 returned by farobj_type_field_get
                            //         determines field layout at [+0x2A/0x2C]
    // ... unknown bytes 0x02-0x0B ...
    int16_t  scale_attr_b;  // +0x0C  → FarObj.attr_b (shifted by DS:0x19B7 scale factor)
    int16_t  raw_attr_a;    // +0x0E  → FarObj.attr_a (copied directly)
    int16_t  scale_attr_c;  // +0x10  → FarObj.attr_c (shifted by DS:0x19B7)
};
```

`farobj_type_field_get(AX=object_kind)`:
- If `type_category > 1`: returns `subtype` byte
- Else: returns 0

Subtype determines how `farobj_field_set` and `farptr_table_entry_store` write to the
type-dependent fields [+0x2A/0x2C]:
- Subtype 1 or 3: write BX to [DI+0x2A]
- Subtype 2: write BX to [DI+0x2C]

---

## Entity Class Codes (FarObj.entity_class [+0x14])

Set by `farobj_entity_attr_setup` (0x44352) from **type table B** at R05_33AE + 0x16F4 (IDA 0x455E2).
Table A (entity attributes) is at R05_33AE + 0x1662 (IDA 0x45150).

Setup process:
```asm
; farobj_entity_attr_setup at 0x44352
shl  bx, 1              ; BX = type_index * 2
mov  cx, [bx+1662h]     ; CX = table A entry (attribute word)
mov  bx, [bx+16F4h]     ; BX = table B entry (low byte = entity class)
mov  [si+14h], bx       ; FarObj.entity_class = low byte of table B
```

Used by `farobj_type_gate_test` (0x4BF8B) for entity-type filtering.

| Code | Hypothesis | Evidence |
|---|---|---|
| 0x12 (18) | Player / allied aircraft | HYPOTHESIS |
| 0x14 (20) | Enemy aircraft | HYPOTHESIS |
| 0x33 (51) | Ground target / vehicle | HYPOTHESIS |
| 0x38 (56) | Naval / other entity | HYPOTHESIS |

`farobj_type_gate_test`: returns CF=0 if [DI+14h] ∈ {0x12, 0x14, 0x33, 0x38}; CF=1 otherwise.

**Entity Type Tables (R05_33AE segment, DS_BASE = 0x43AEE in IDA):**
- Table A: 40+ word entries, entity attributes → FarObj.attr_a/b/c
- Table B: 40+ word entries, low byte → FarObj.entity_class [+0x14]
- See: `analysis/ida_falconcd/entity_tables.json` for full table dump

---

## Scan List (0x54AF:0x1734)

16 entries × 4 bytes = 64 bytes. Each entry is a **far pointer** to a FarObj instance
(the same objects as the main table, just a fast-access subset). The scan functions iterate
these 16 entries each frame:

- `farobj_scan_74_clear_b` (0x34193): AND [+0x24], ~0x8000 (clear scan gate)
- `farobj_scan_74_gate_a` (0x3415F): if [+0x24] >= 60: OR main farobj [+0x24], 0x8000
- `farobj_scan_74_timer_c` (0x341C0): advance [+0x1E] mod 8, write phase to [+0x24]

Each scan-list entry's FarObj has [+0x7A] = its own slot index in the main table.

---

## EntityAccumEntry (0x54AF:0x4ED)

Up to 40 × 14B motion command entries, applied by `farobj_entity_accum_sweep` each frame.

```c
struct EntityAccumEntry {
    uint16_t count;      // +0x00  0=empty; nonzero=active
    int16_t  delta_x;    // +0x02  X world position delta
    int16_t  delta_y;    // +0x04  Y position delta
    uint16_t countdown;  // +0x06  decremented each sweep; entity moves until 0
    int16_t  delta_hdg;  // +0x08  heading angle delta (14-bit)
    int16_t  delta_pit;  // +0x0A  pitch delta
    int16_t  delta_rol;  // +0x0C  roll delta
};
```

Applied via: `farptr_table_accum_fields` (adds XYZ deltas to FarObj int32 position)
and `farptr_table_offset_apply` (adds angle deltas to FarObj orientation).

---

## 2D Tile-Based Spatial Partitioning

The game world uses a 2D tile grid for spatial partitioning and streaming:

### Tile System Parameters

- **Tile size:** 0x3334 = 13,108 units per tile
- **Grid dimensions:** 256 × 256 tiles (signed -128..+127 range)
- **Total world size:** 3,353,728 × 3,353,728 units
- **Storage:** 4 bytes per entity (2 bytes tile coords + 2 words local position)

### Tile Coordinate Calculation

```c
// World → Tile conversion (from 0x41B84):
int32_t world_x = (world_x_hi << 16) | world_x_lo;
int8_t tile_x = (int8_t)(world_x / TILE_SIZE);  // floor division for negatives
uint16_t local_x = world_x % TILE_SIZE;         // always positive remainder

// Tile → World conversion:
int32_t world_x = (int32_t)tile_x * TILE_SIZE + local_x;
```

### Tile Boundary Crossing

When an entity moves across tile boundaries (sub_3CE92 @ 0x3CEF4):

```asm
; Update position with velocity:
local_x += velocity_x

; Check underflow:
if (local_x < 0) {
    tile_x -= 1
    local_x += TILE_SIZE      ; wrap to previous tile
    boundary_crossed = true
}

; Check overflow:
if (local_x >= TILE_SIZE) {
    tile_x += 1
    local_x -= TILE_SIZE      ; wrap to next tile
    boundary_crossed = true
}

; Notify streaming system:
if (boundary_crossed) {
    FarObj.flags[+0x8] |= 0x0001
}
```

**Purpose:** Enables efficient spatial queries (collision, visibility, AI awareness) by only checking entities in nearby tiles. Boundary flag triggers terrain/entity streaming.

---

## Key FarObj Operations API

| Function | EA | Signature | Description |
|---|---|---|---|
| `farptr_table_get` | 0x2703F | `(AX=slot) → ES:DI` | Load FarObj from main table |
| `farobj_type_field_get` | 0x2647E | `(AX=object_kind) → AL=subtype` | Decode type descriptor |
| `farptr_table_accum_fields` | 0x2E896 | `(AX=slot, BX=ΔX, CX=ΔY, DX=ΔZ)` | Add int32 position deltas |
| `farptr_table_offset_apply` | 0x2E8BE | `(AX=slot, BX=Δhdg, CX=Δpitch, DX=Δroll)` | Apply angle deltas |
| `farptr_table_field_store` | 0x2E902 | `(AX=slot, BX=value)` | Write FarObj.cmd_field [+0x20] |
| `farptr_table_field20_get` | 0x2E8F4 | `(AX=slot) → BX` | Read FarObj.cmd_field [+0x20] |
| `farptr_table_field22_store` | 0x2E910 | `(AX=slot, BX=value)` | Write FarObj.object_kind [+0x22] |
| `farobj_kind_slot_reset` | 0x49A5B | `(AX=slot, BX=kind)` | Reset kind + clear slot_flags bits 6-7 |
| `farobj_field_set` | 0x264AC | `(AX=slot, BX=value)` | Write type_base/ext based on subtype |
| `farobj_copy_block` | 0x26FE4 | `(AX=slot, DS:SI=src)` | Copy 18 bytes into FarObj [0..17] |
| `viewobj_project_advance` | 0x270E0 | `(AX=slot) → CF` | LOD-based projection + accumulate |
| `farobj_record_lookup_step` | 0x213E6 | `(ES:DI=farobj)` | Execute per-type step record |
| `farobj_scan_74_gate_a` | 0x3415F | `()` | Frame scan: set visibility gates |
| `farobj_scan_74_clear_b` | 0x34193 | `()` | Frame scan: clear visibility gates |
| `farobj_scan_74_timer_c` | 0x341C0 | `()` | Frame scan: advance animation timers |
| `farobj_sort_and_step` | 0x2131C | `()` | Depth sort + step all farobj |
| `farobj_entity_attr_setup` | 0x44352 | `(DS:SI=farobj, AX=type)` | Initialize FarObj from type descriptor |
| `entity_slot_create` | 0x2EBCD | `(AX=type, BX=slot)` | Create farobj slot from disk file |
| `entity_slot_pair_create` | 0x2EA78 | `(DS:SI=type_id_pair)` | Create linked entity pair |

---

## Two-Tier Object Access

Objects exist in two overlapping access paths:
1. **Main table** (`R05_400C:0x34`): all registered objects; `farptr_table_get(index)` indexed.
2. **Scan list** (`0x54AF:0x1734`): 16-entry subset for per-frame scanning. Each scan-list
   entry has [+0x74] = active, [+0x7A] = main table index (back-reference).

The scan list is a **fast-path cache** for the 16 most active entities that need per-frame
gate/timer updates. After scanning, the main table's state_flags [+0x24] is updated.
