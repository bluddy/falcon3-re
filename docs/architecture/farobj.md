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
    uint16_t cmd_field;     // +0x20  command/state ID; also used as projection scale!
                            //         farptr_table_field_store/_get access this
                            //         MUST BE NEGATIVE for view_projection to proceed
    uint16_t object_kind;   // +0x22  index into farobj_typedesc_table (kind × 4)
                            //         decoded by farobj_type_field_get → subtype 0/1/2/3
                            //         ALSO used as LOD accumulator by viewobj_project_advance
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
    uint16_t type_ext_A;    // +0x2C  written for subtype 2

    // === UNKNOWN (0x2E-0x73) ===
    // 70 bytes not yet mapped

    // === Active/Scan (0x74-0x7B) ===
    uint8_t  active;        // +0x74  bit 0 = slot active/occupied (checked by scan_74 functions)
    // 5 bytes unknown
    uint16_t self_slot_idx; // +0x7A  this object's index in farobj_main_table

    // === UNKNOWN (0x7C-0xD0) ===
    // 85 bytes not yet mapped

    uint8_t  timer_active;  // +0xD1  bit 0 = include in scan_74_timer_c animation update
};
// Minimum confirmed size: 0xD2 = 210 bytes
```

### Key Field Notes

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

Set by `farobj_entity_attr_setup` (0x44352) from type table B at `DS:0x16F4` (R05_33AE).
Used by `farobj_type_gate_test` (0x4BF8B) for entity-type filtering.

| Code | Hypothesis | Evidence |
|---|---|---|
| 0x12 (18) | Player / allied aircraft | HYPOTHESIS |
| 0x14 (20) | Enemy aircraft | HYPOTHESIS |
| 0x33 (51) | Ground target / vehicle | HYPOTHESIS |
| 0x38 (56) | Naval / other entity | HYPOTHESIS |

`farobj_type_gate_test`: returns CF=0 if [DI+14h] ∈ {0x12, 0x14, 0x33, 0x38}; CF=1 otherwise.

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
