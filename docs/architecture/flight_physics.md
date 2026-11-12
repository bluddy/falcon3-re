# Flight Physics & Aircraft System

---

## Architecture Overview

The flight simulation runs in a parallel chain to rendering:

```
main_frame_update_loop (FLIGHT PATH)
├── game_frame_update_chain     ← entity simulation + AI
│    ├── farobj_move_accumulate_step  ← entity motion
│    ├── aircraft_slot_cycle_step     ← per-aircraft cycling
│    ├── angle_matrix_far_invoke      ← build rotation matrix from aircraft heading
│    └── fixed_matrix_load_7b0e       ← load matrix into trig segment
└── game_frame_pipeline_step    ← rendering
     └── mode_frame_step_core   ← per-entity simulation step
```

---

## Flight Control Axes: `control_axes_read` (0x2234B, 211B)

Reads 4 flight control axes and normalizes to ±2048 (±0x800).

### Input Modes

**Joystick path** (cs_byte_test_zero returns nonzero):
```
joystick_axis_read_clamp → BX=axis0, AX=axis1, CX=axis2, DX=axis3
Store: cs:byte_22232+0/2/4/6 = BX, AX, CX, DX
```

**Keyboard path** (joystick absent):
```
test al, 1 → aileron left  key: cs:word_22242 += step
test al, 2 → aileron right key: cs:word_22244 += step
test al, 4 → elevator down: cs:word_2223E += step
test al, 8 → elevator up:   cs:word_22240 += step
...
Normalize: axis = raw × 0x800 / cs:word_2222C
Clamp to: -0x800 ≤ axis ≤ 0x800
Dead zone: if |raw| ≤ 9: shr bx,1; adc bx,0 (round toward zero)
```

### Output Axes

| CS address | Name | Hypothesis |
|---|---|---|
| `cs:byte_22232` | `axis_aileron` | Roll control (±2048) |
| `cs:byte_22232+2` | `axis_elevator` | Pitch control (±2048) |
| `cs:byte_22232+4` | `axis_throttle` | Throttle control (±2048) |
| `cs:byte_22232+6` | `axis_rudder` | Yaw/rudder control (±2048) |
| `cs:word_2222C` | `axis_sensitivity` | Scale divisor for normalization |

---

## Aircraft Kinematics Block (pos_step_chain_engine, 0x3B338)

Core position step function (459B, R05_2ACF). The aircraft kinematics are stored in a
**13-word (26B) flight state block** at `DS:[0x32]`.

### Position Step Formula

```
IF AX = 0: AX = 1 (minimum motion)
ELSE: AX = sign(AX) × 2 + 1   (via cwd; shl dx,1; inc dx; ax=dx)

ds:0xB0 = AX                   ; step coefficient
ds:0xB2 = AX × 0x3334          ; step in world units (13,108 = tile size)
ds:0xB4 = abs(AX)
```

Then copies 13 words (26 bytes) from `DS:[0x32]` to `DS:[0x66]` AND to `ES:0x7B0E:0x43BA`.

### Flight State Block (DS:[0x32], 26 bytes, layout HYPOTHESIS)

```c
struct FlightState {               // DS:[0x32..0x57]
    int16_t field_32;              // +0x00  heading or forward speed
    int16_t field_34;              // +0x02  unused or altitude rate
    int16_t field_36;              // +0x04  ...
    int16_t field_38;              // +0x06  cross-tile delta X
    int16_t field_3A;              // +0x08  cross-tile delta Y
    int16_t field_3C;              // +0x0A  position advance state
    int16_t field_3E;              // +0x0C  tile step remainder X
    int16_t field_40;              // +0x0E  tile step key (crossings)
    int16_t field_42;              // +0x10  ...
    int16_t field_44;              // +0x12  ...
    int16_t field_46;              // +0x14  ...
    int16_t field_48;              // +0x16  ...
    int16_t field_4A;              // +0x18  ...
};
// Size: 13 words = 26 bytes
```

Mirrored to:
- `DS:[0x66]` — previous frame state (for delta computation)
- `ES:0x7B0E:0x43BA` — trig segment copy (for matrix computation)

### Self-Modifying Code

`pos_step_chain_engine` patches inline constants each frame:
```asm
mov word ptr cs:loc_3B494+1, di  ; patch immediate operand at loc_3B494+1
mov word ptr cs:loc_3B3F7+1, ax  ; patch at loc_3B3F7+1
mov word ptr cs:loc_3B3DF+1, bx  ; ...
```

This avoids memory indirection for the matrix components, inline-patching the multiply
instructions with current values. Same technique as `farobj_rect_ratio_build`.

---

## Aircraft Slot Array (aircraft_slot_cycle_step, 0x49546)

40 × 24B aircraft/AI slot records at `DS:0x49AB:[0xC]`.

```c
struct AircraftSlot {           // stride 0x18 = 24 bytes
    uint8_t  flags;             // +0x00  0=inactive; bit 2=collision; bit 4=respawn
    uint16_t farobj_slot;       // +0x01  farobj main table index
    // ... 10 bytes unknown ...
    uint8_t  entity_type;       // +0x0D  entity type or weapon code
    // ... 2 bytes unknown ...
    uint16_t callback_offset;   // +0x14  far callback pointer offset
    uint16_t callback_seg;      // +0x16  far callback pointer segment
};
```

Iterated by `aircraft_slot_cycle_step`:
```
for si in [0xC, 0xC+24, 0xC+48, ...] (up to 40 entries):
    if [si] == 0: continue         ; inactive slot
    call sub_496D3                 ; some per-aircraft step
    entity_type = [si+0xD]
    farobj_slot = [si+1]
    farptr_table_get(farobj_slot) → ES:DI  ; get entity FarObj
    call sub_49A1F                 ; advance step
    if [si] & 4: inc byte ptr ES:[DI]       ; collision flag
    if [si] & 2: callback(ES:[DI])          ; callback via [si+14h]:[si+16h]
    [si] = 0                       ; deactivate slot
```

The counter `cs:word_49544` cycles 0..50 (0x33 max), stepped by `word_4A3E8` each frame.

---

## Entity Motion Table (farobj_move_accumulate_step, 0x4CD1D)

40-entry entity motion table at `DS:0x69FF:[4]`, stride 27B (0x1B per entry).

```c
struct EntityMotionEntry {      // stride 0x1B = 27 bytes
    // +0x00..+0x02  unknown
    uint8_t  entity_class;      // +0x03  entity type/class code
    // +0x04..+0x05  unknown
    uint16_t flags;             // +0x06  bit 0x200=skip; bit 0x1=active; bit 0x200=flags
    // ... more fields ...
    uint16_t slot_id;           // +0x21  slot identification (low word)
    uint16_t slot_seg;          // +0x23  slot identification (high word)
    uint16_t slot_id2;          // +0x25  second slot identification
};
```

Processing conditions:
```
IF flags & 0x200: skip entire entry
IF NOT (flags & 0x1): skip (not active)
IF slot_id == 0xFFFF AND slot_id2 == 0: skip (no slot assigned)
IF entity_class == 0xFF: use stride-table at DI
ELSE:
    di = 4 + entity_class × 0x1B  ; lookup entry for this class
    IF flag_at_di & 0x21: process motion accumulation
```

---

## Mode Frame Step Core (mode_frame_step_core, 0x3A3D6)

Per-entity simulation step (508B, R05_1F64). Called by `game_config_apply_init`
and `sub_30D5F` (which is called by terrain_state_reinit and view_terrain_frame_step).

### Entry Gates

```
IF ds:0x44C != 0 OR [si+0xCAh] & 0x100: set ds:0x4AC4=0, return early
```

The gate `ds:0x44C` = paused/frozen flag. `[si+0xCAh] & 0x100` = entity-level skip flag.

### Entity Record Access (DS:SI)

```c
// Entity simulation record at DS:SI (size ≥ 0xCA+2 = 204B)
struct EntitySimRecord {
    // ... many fields ...
    uint16_t mode_phase;        // +0xCAh  bits: 0x100=skip mode_step
};
```

### Processing Flow

1. Store entity pointer and tick rate
2. Load mode byte `ds:0x4A7Eh` → `cs_word_store`, `dispatch_220d8_via_24bba`
3. `far_cb_2`, `sub_263F6` (farobj_render_vtable dispatch)
4. `view_limits_load(SI=0x49C0)` — load view frustum
5. Check `ds:0x4AC2 >= 4` → phase-based routing
6. Check `ds:0x4A83` → `steerpoint_scan_update` (if entity has navigation)
7. `ds:0x4A89` countdown — `entity_table_walk_49a3` when expired
8. Farobj active gate: `ES:[bx+0x74] & 1` (checks scan list entry)

### Key Simulation Globals

| Global | Description |
|---|---|
| `DS:0x706h` | Simulation entity ptr (SI on entry) |
| `DS:0x4AC2h` | Mode phase counter (≥4 = alternate rendering path) |
| `DS:0x4AC4h` | Gate: 0 = paused/skipped |
| `DS:0x4A7Eh` | Current mode byte |
| `DS:0x4A83h` | Navigation active flag |
| `DS:0x4A89h` | AI step countdown (decremented by tick rate) |

---

## Steerpoint Navigation

`steerpoint_scan_update` (from mode_frame_step_core) handles navigation to waypoints.
Called when `ds:0x4A83 == 1` (navigation active) AND entity has not exceeded phase.

---

## Entity Counters: `entity_counters_update` (0x1CEA3, 453B, seg015)

Countdown timers at `ES:0x7772:0x506+N` (one byte per entity, up to N entities).
Called by `sub_17537` (10K dynamic calls, 0 static callers → called through function pointer).

```
for N = 0..entity_count-1:
    counter = ES:0x7772:[N + 0x506]
    if counter == 0: skip
    if counter > threshold: decrement
    else: decrement; set event flag ES:0x7894:0xD1Ah
```

Used for time-based events: weapons reload, missile motor burn time, damage recovery.
