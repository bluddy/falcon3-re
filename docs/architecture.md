# Falcon 3.0 — Runtime Architecture

*Last updated 2026-11-12 (findings 1–179, S4 Level-0/1 analysis).*
*Certainty keys: **PROVEN** (byte-level), **STRONG** (multi-signal), **HYPOTHESIS** (plausible single-signal).*

---

## 1. Binary & Toolchain

| Fact | Value | Certainty |
|---|---|---|
| Compiler (C modules) | Borland C++ 2.0 (`bcc -c -ml -1 -O`) | PROVEN (finding 22) |
| ASM modules | Hand-written x86 real-mode ASM, mixed with C | STRONG |
| Linker | RTLink/Plus overlay linker | PROVEN |
| Compression library | PKWARE DCL 1.11 (Patent 5,051,745) linked in | PROVEN (strings) |
| Compressed tail format | UNKNOWN — no PK signatures found in EXE | UNKNOWN (finding 31) |
| Memory model | DOS real mode, far/large (CS≠DS≠SS possible) | PROVEN |
| CRT | No standard CRT — custom asm startup | PROVEN |
| Binary size | 1,375,101 B total: 118,609 B resident + 1,243,798 B tail | PROVEN |

### File Layout

```
Offset       Size      Description
0x000000     0x2C00    MZ header (704 paragraphs) + 2,717 relocations
0x002C00     0x1CF51   Load image (resident code + data = 118,609 B)
0x01FB51     ...       RTLink tail: overlay records + asset data
0x01FB61     204 B     4-byte directory (51 entries: initial overlay load list)
0x01E24F     ...       18-byte RTLink directory (70 records × 18 B)
```

---

## 2. Memory Model

### Address Space (DOS real mode)

```
Paragraph  Linear (IDA)   Segment name       Description
0x0000     0x00000        BIOS/DOS           BDA at 0x0000:0x0417 (keyboard flags)
0x1000     0x10000        load base          MZ image loaded here by DOS
0x1AA3     0x1AA30        resident base      Entry, thunk table, overlay dir, loader
...        0x2B19C        entry point        0x1AA3:0x076C = startup
...        0x2BAFF        thunk table        0x1AA3:0x157F (86 entries × 10 B)
...        0x2CF60        OVL_1CF6           Core overlay stubs
0x7A32     0x7A320        DGROUP             DS=SS=DGROUP throughout (finding 121)
0x85AE0    (runtime heap) VGRAPH             Graphics driver (40-slot entry table)
...        runtime        R05_1E10..R05_xxx  Game overlays loaded at runtime
```

**DGROUP (0x7A32 / linear 0x7A320)** is the global data segment. DS is set to 0x7A32 at startup and preserved. `SS = DS = DGROUP`. Key DGROUP globals below.

### Segments in IDB (post-finding 120, 47 object segments in R05)

The resident image has ~23 segments. The 70 RTLink overlay records expand to 68+ IDA segments (R05 split into 47 CS-true object segments; R29 similarly split). Total: ~115 segments.

---

## 3. Overlay System (RTLink/Plus)

**PROVEN.** RTLink/Plus manages ~1.2 MB of overlays loaded on demand.

### Thunk Table (0x1AA3:0x157F)

86 entries × 10 bytes each. Each entry is:
```
E8 disp16   CALL rel16 -> overlay loader (0x1AA3:0x058D / linear 0x1DBBD)
EA off seg  LJMP far -> overlay function target
word        record_id (RTLink directory index)
```

When a thunk is called: loader checks if the target overlay is resident; if not, evicts and loads from disk, patches the LJMP, then JMPs to target. The thunk EA is the stable callable address; the LJMP destination changes after every load.

### Overlay Records

70 × 18-byte directory entries at linear 0x2E24F (0x1AA3:0x0C1F). Each entry records the overlay segment paragraph, file offset of the fixup table, size, group ID (`C` field), and record ID. Groups:
- `C=0xFFFF`: core/startup overlays (always resident or early-load)
- `C=5`: primary game overlays (R05 family — largest, 40 KB)
- `C=0xD/0x10/0x12`: graphics/sound/input overlays

---

## 4. Calling Conventions

Borland C++ large model uses **far calls** between modules. Within a module: `push cs; call rel16` (near, same CS). Common patterns:

| Pattern | Description |
|---|---|
| `push cs; call near ptr fn` | Near intra-segment call (most common) |
| `call far ptr fn` | Far inter-segment call |
| `push es; push cs; call near ptr fn; pop es; retf` | Far-callable wrapper for near leaf |
| `retf` | Return from far function |
| `retn` | Return from near function |

**Argument passing**: stack (cdecl, caller cleans: `add sp, N` after far call). Parameters pushed right-to-left. Return value: AX (16-bit), DX:AX (32-bit or far ptr), ES:DI (far pointer).

**Register conventions in hand-ASM leaves**: AX=param0/return, BX=param1, CX=param2, DX=param3, SI/DI=pointers, DS=DGROUP (preserved), ES=scratch (often saved/restored via stack).

**14-bit angles**: heading/pitch/roll stored as 14-bit values in uint16. Helpers:
- `fixed_angle_mask_3fff` (0x24980): `ax &= 0x3FFF` — unsigned 14-bit wrap
- `fixed_angle_fold_e000` (0x24988): maps 14-bit to signed range [-8192..8191]

---

## 5. Main Frame Loop

**STRONG** (main_frame_update_loop disassembly fully traced, 2026-11-12).

### Top-Level Loop: `main_frame_update_loop` (0x31319, 257B, R05_1F64)

Dispatches on `word_54D2B` (the game mode indicator):
- `<= 14` or `== 26`: **MENU PATH** — keyboard-only: `bda_kb_flag_get`, `flag_bits_dispatch`, loop if flag set
- `word_54EFA == 0x0D`: **EXIT** game loop
- else: **FLIGHT PATH** — full per-frame simulation:

```
1. farobj_slot_update_driver       farobj state update
2. range_cb_dispatch_loop
3. hud_state_rowtable_step  }
4. hud_panel_transform_step }   HUD
5. hud_readout_timer_render }
6. farobj_move_accumulate_step     move all accumulating entities (CX=0x52 entries)
7. aircraft_slot_cycle_step
8. tile_object_interpreter, farobj_tile_key_cache
9. farobj_slot_step_spawn, farobj_sweep_all
10. game_frame_pipeline_step       ← main per-frame rendering pipeline
11. viewport_rect_state_store
12. tick_rate_compute               compute frame timing
13. flag22220_clear                 reset tick counter
14. view_terrain_frame_step
15. hud_data_panel_draw, vga_dac_palette_upload
16. flag_bits_dispatch (second pass)
17. → back to loop start
```

### `game_frame_pipeline_step` (0x2FD42, 387B, Level-18)

Called once per FLIGHT frame. Steps: `fn_table_dispatch` (view mode), `farobj_pos_wrap_update`, `pos_clamp_40`, `entity_update_batch`, `view_pos_cache_update`, terrain VM gating, `entity_state_load`, `terrain_frame_update_driver`, `viewlist_project_flagged`, `farobj_scan_74_timer_c`, `farobj_scan_74_gate_a`, `farobj_sort_and_step`. `ds:4EAh` = view mode flags.

### `flag_bits_dispatch` (0x24FB9) — 88-event input dispatcher

Scans CS:0x5762 (11 bytes = 88 event bits), calls `key_event_table_dispatch` for each active bit. Called twice per FLIGHT frame. 21K dynamic calls.

---

## 6. FarObj System — Central Game Object Architecture

**STRONG/HYPOTHESIS.** The most important runtime architecture discovery (S4).

### Overview

`FarObj` is the central game object instance record. All aircraft, vehicles, terrain objects, and other game entities use this structure. Objects are stored in a **main slot table** at `R05_400C:0x34`, accessed by slot index via:

```asm
; farptr_table_get(AX=slot_index) → ES:DI = FarObj*
mov     di, seg R05_400C
mov     es, di
shl     ax, 1 ; ax *= 4
shl     ax, 1
add     ax, 34h    ; table starts at offset 0x34
mov     di, ax
les     di, es:[di] ; ES:DI = far pointer to FarObj instance
retf
```

78 static callers, 210K+ dynamic calls. This is the most-called non-leaf function.

### Global Tables

| Address | Name | Description |
|---|---|---|
| `R05_400C:0x34` | `farobj_main_table` | Main slot table: `far_ptr[N]`, 4B/entry. `farptr_table_get(index)` loads ES:DI from here. |
| `0x54AF:0x1734` | `farobj_scan_list` | 16-entry active-object scan list. Iterated by `farobj_scan_74_*` each frame. |
| `0x54AF:0x4ED` | `entity_accum_table` | Motion sweep: up to 40 × 14-byte `EntityAccumEntry` records (periodic motion commands). |
| `0x7B0E:0x3052` | `farobj_typedesc_table` | Type descriptor table: `far_ptr[N]`, indexed by `FarObj.object_kind × 4`. |

### FarObj Struct Layout (hypothesis, minimum 210 bytes)

```c
struct FarObj {
    // 3D world position — three int32 as lo:hi word pairs
    int16_t world_x_lo;     // +0x00
    int16_t world_x_hi;     // +0x02  — int32 X = (hi<<16)|lo
    int16_t world_y_lo;     // +0x04
    int16_t world_y_hi;     // +0x06
    int16_t world_z_lo;     // +0x08
    int16_t world_z_hi;     // +0x0A

    // 3D orientation — 14-bit angles
    uint16_t angle_heading; // +0x0C  masked with 0x3FFF; 0xFFFF = uninitialized
    int16_t  angle_pitch;   // +0x0E  signed 14-bit, fold-normalized
    uint16_t angle_roll;    // +0x10  14-bit

    // Type / category
    uint8_t  render_flags;  // +0x12  HUD/render bits
    uint8_t  type_flags;    // +0x13  bits include range-visibility (bit 6)
    uint8_t  entity_class;  // +0x14  entity type code (see §6.4)
    uint8_t  entity_class_hi;//+0x15  high byte of entity class word

    // Type-derived attributes (from FarObjTypeDesc at farobj_typedesc_table)
    int16_t  attr_a;        // +0x16  raw attribute A (type descriptor +0x0E)
    int16_t  attr_b;        // +0x18  scaled attribute B (type descriptor +0x0C)
    int16_t  attr_c;        // +0x1A  scaled attribute C (type descriptor +0x10)
    uint16_t field_1C;      // +0x1C  unknown

    // Per-frame state
    uint16_t frame_timer;   // +0x1E  animation counter mod 8 (driven by scan_74_timer_c)
    uint16_t cmd_field;     // +0x20  command/state ID (farptr_table_field_store/_get)
    uint16_t object_kind;   // +0x22  index into farobj_typedesc_table (decoded by farobj_type_field_get → 0/1/2/3)
    uint16_t state_flags;   // +0x24  bit 0x0040=has_ext_slot; bit 0x8000=scan gate set;
                            //         bits 0xF1FF=timer phase (animation frame 0-7)

    // Slot identity
    uint8_t  slot_flags;    // +0x26  bits 0-5 slot state; bits 6-7 cleared by kind_slot_reset
    uint8_t  slot_id;       // +0x27  0xFF = unassigned; entity slot index

    // Type-dependent data (layout varies by FarObj.object_kind subtype)
    uint16_t type_ext_0;    // +0x28
    uint16_t type_base;     // +0x2A  written by farobj_field_set for subtype 1 & 3
    uint16_t type_ext_A;    // +0x2C  written for subtype 2

    // ... unknown fields 0x2E..0x73 ...

    uint8_t  active;        // +0x74  bit 0 = slot occupied/active (checked by scan_74 functions)

    // ... unknown fields 0x75..0x79 ...

    uint16_t self_slot_idx; // +0x7A  this object's index in farobj_main_table

    // ... unknown fields 0x7C..0xD0 ...

    uint8_t  timer_active;  // +0xD1  bit 0: include in scan_74_timer_c animation update
};
```

### Type Descriptor System (FarObjTypeDesc)

`FarObj.object_kind` indexes into `farobj_typedesc_table` (a table of far pointers). Each entry points to a `FarObjTypeDesc` record:

```c
struct FarObjTypeDesc {
    uint8_t  type_category; // +0x00  0 or 1 = simple; >1 = complex (has subtype)
    uint8_t  subtype;       // +0x01  subtype code 1/2/3 (returned by farobj_type_field_get)
    // ...
    int16_t  scale_attr_b;  // +0x0C  → FarObj.attr_b (shifted by DS:0x19B7 scale factor)
    int16_t  raw_attr_a;    // +0x0E  → FarObj.attr_a
    int16_t  scale_attr_c;  // +0x10  → FarObj.attr_c (shifted)
};
```

`farobj_type_field_get(AX=object_kind)` returns the subtype code (0–3), used by callers to select variant-specific field layouts.

### Entity Class Codes (FarObj.entity_class)

Known from `farobj_type_gate_test` (0x4BF8B) comparisons:

| Code | Entity type |
|---|---|
| 0x12 | HYPOTHESIS: aircraft/player entity |
| 0x14 | HYPOTHESIS: unknown (possibly vehicle) |
| 0x33 | HYPOTHESIS: unknown |
| 0x38 | HYPOTHESIS: unknown |

### Key FarObj Operations

| Function | EA | Description |
|---|---|---|
| `farptr_table_get` | 0x2703F | Load ES:DI from farobj_main_table[AX]; 78 callers |
| `farobj_type_field_get` | 0x2647E | Decode object_kind to subtype 0–3 via type descriptor table |
| `farptr_table_accum_fields` | 0x2E896 | Add int32 XYZ deltas to FarObj position (int32 ADC pattern) |
| `farptr_table_offset_apply` | 0x2E8BE | Apply 14-bit angle deltas to FarObj orientation |
| `farptr_table_field_store` | 0x2E902 | Write BX to FarObj.cmd_field [+0x20] |
| `farptr_table_field20_get` | 0x2E8F4 | Read FarObj.cmd_field [+0x20] into BX |
| `farptr_table_field22_store` | 0x2E910 | Write BX to FarObj.object_kind [+0x22] |
| `farobj_scan_74_gate_a` | 0x3415F | Frame scan: set bit 0x8000 in state_flags for visible active objects |
| `farobj_scan_74_clear_b` | 0x34193 | Frame scan: clear bit 0x8000 in state_flags |
| `farobj_scan_74_timer_c` | 0x341C0 | Frame scan: advance animation timer mod 8 |
| `farobj_entity_attr_setup` | 0x44352 | Initialize FarObj fields from type descriptor (entity spawn) |
| `entity_slot_create` | 0x2EBCD | Allocate memory and register a new farobj slot |
| `farobj_entity_accum_sweep` | 0x2E48C | Per-frame: apply EntityAccumEntry motion commands to farobj positions |

### Two-Tier Object Lists

Objects exist in two overlapping lists:
1. **Main table** (`R05_400C:0x34`, N slots): all registered objects; `farptr_table_get` indexed.
2. **Scan list** (`0x54AF:0x1734`, 16 entries): a subset of active objects that need per-frame scanning. Each scan-list entry points to a FarObj; the FarObj's `self_slot_idx` [+0x7A] is its index in the main table.

---

## 7. Render/Dispatch System (Opcode Handlers)

**HYPOTHESIS** (from function naming and disassembly patterns).

A set of **CS-relative far pointer slots** at addresses around 0x2200x acts as the render pipeline dispatch table:

| CS offset | Proposed name | Description |
|---|---|---|
| `dword_220A0` | - | `dispatch_220a0_stub` calls this |
| `dword_220C8` | `clip_handler` | Clip/skip path (called by `clip_or_draw_dispatch` when AX < 0) |
| `cs:opcode_handler_1` | - | `far_cb_0` calls this |
| `cs:opcode_handler_2` | - | `far_cb_1` calls this |
| `cs:opcode_handler_5` | `draw_handler` | Draw path (called by `clip_or_draw_dispatch` when AX ≥ 0) |
| `dword_220D0` | - | `dispatch_220d0_stub` calls this (terrain strip) |
| `dword_220D4` | - | `dispatch_220d4_stub` calls this (HUD draw) |
| `dword_220E0` | `frame_cb_ptr` | Main frame callback (`far_cb_with_args` invokes this + ES=0x834A, BP=word_24BB8) |
| `dword_220E4` | `view_limits_cb_ptr` | View/frustum limits callback (`view_limits_wrap` entry 1 calls this) |
| `dword_220EC` | - | `dispatch_220ec_invoke(BX,DI,DS:SI)` |

Also from Level-1 analysis:
- `dword_220E4` = `view_limits_cb_ptr` (view/frustum limits mode callback)
- `fn_table_dispatch` uses `cs:word_22D28` as the current view mode index (0–14)
- `op_dispatch` = 17-slot DOS/memory operation shim (allocate/free/read/write/seek); see §13 for details

### Rendering Pipeline (STRONG)

The 3D rendering pipeline, traced from `main_frame_update_loop`:

```
main_frame_update_loop
└── game_frame_pipeline_step (once per flight frame)
     ├── fn_table_dispatch → sets view projection constants
     ├── farobj_batch_build_project  ← TERRAIN TILE RENDERER
     │    └── coord_point_group_project (per-tile patch)
     │         └── view_projection (THE 3D projection, 282K calls/session)
     ├── sub_256A3 → view_projection (fixed reference point)
     ├── viewlist_project_flagged (per-entity object list)
     │    └── view_projection (each flagged 16B view record)
     ├── viewmode3_vector_project (mode 3 cockpit vectors)
     │    └── view_projection
     └── farobj_sort_and_step → farobj_record_lookup_step

Additional projection paths (per-farobj):
     viewobj_project_select
     ├── viewobj_project_advance → view_projection
     └── viewobj_project_advance_mark → view_projection (also sets state_flags bit 5)
```

**`view_projection` (0x20BDB, 1076B)** — the core 3D projection:
- Input: ES:BX = view origin (world XY int32), DS:DI = object to project
- Algorithm: `screen = (world_x - view_x) × 16 / |FarObj.cmd_field[+0x20]|`
- FarObj.cmd_field [+0x20] must be NEGATIVE for projection to proceed (negated to get scale)
- Also uses `cs:word_1F6E6` as a secondary scale factor
- FarObj.object_kind [+0x22] doubles as an **LOD accumulator** (incremented by viewobj_project_advance)
- FarObj.state_flags [+0x24] bit 0x80 = skip projection gate

**`farobj_batch_build_project` (0x13CB0)** — terrain tile batch renderer:
- Computes XY view offsets: `offset = (cs:word_11BCC - 0x7FF) × (−0xCCD) / 0x400`
- Processes a stream of tile drawing commands from DS:SI
- Each tile patch projected via `coord_point_group_project`
- Callers: `farobj_tile_stream_build`, `tile_base_batch_build`

**Distance-based LOD** in terrain object renderer (sub_4DDB4): 3 tiers based on projected distance (thresholds 0x3A98 and 0x7530), selecting BX = 0x809 (close), 0x80B (medium), 0x80D (far).

### farobj_render_vtable (0x26400)

A table of 14 far pointers embedded at 0x26400 (after the `dispatch_220d0_stub` retf):

```
object_quad_proj_draw       — project & draw quad-mesh objects
object_init_flag_draw       — initialize draw flags
object_rot_proj_draw        — rotate-and-project draw
object_view_matrix_build    — build view matrix
object_frame_advance_step   — advance one animation frame
farobj_render_draw_1f712    — draw via type 0x1F712 handler
object_type_field_step      — step by type field
object_proj_draw_dispatch   — projection draw dispatch
farobj_render_prep_1f712    — prep draw
object_scale_gather_draw    — scaled gather draw
object_record_stream_step   — step via record stream
object_type3_table_step     — type-3 table step
anim_line_object_draw       — animated line object draw
flag_1f733_gate             — flag gate
```

---

## 8. Hardware / OS Interface

### Timer (IRQ0) — `timer_tick_isr` (0x22AFF)

DOS IRQ0 fires at ~18.2 Hz. The ISR:
- Increments `tick_counter` (`cs:word_22220`) each tick if `timer_gate_flag` (`cs:byte_2224B`) ≠ 1
- Maintains `timer_divider` (`cs:word_22222`); on every 4th tick (`& 3 == 0`): chains to BIOS timer ISR (or sends EOI and returns)
- Gates joystick polling via `joystick_timer_flag` (`cs:byte_22246`)

### Mouse (INT 33h) — `mouse_int33_dispatch` (0x1018F)

Far function registered as an INT 33h mouse event callback. Receives a pointer (DS:SI) to a mouse event record: `[SI+0]` = event type (9, 0xC, 0x10, 0x14, 0x16–0x19, 0x1F–0x21), `[SI+2]` = buttons, `[SI+4]` = delta. 337K dynamic calls — the most-called function in the game.

### Keyboard — `bda_kb_flag_get` (0x24E5D)

Reads BDA `0x0000:0x0417` = keyboard status flags byte (Shift/Alt/Ctrl/CapsLock/NumLock/ScrollLock/Insert states). Returns in AX (zero-extended). Called by game init and main loop.

Previously misnamed `bda_equipment_flag_get` — **PROVEN** correction: address 0x417 is the keyboard flags register, not the equipment flags register (0x410).

### Joystick — `joystick_poll` (0x1122A)

111-byte far function. Reads from game I/O port 0x201 (or INT 15h AH=0x84 for AT joystick). Counts high bits over 8 iterations to get button state. Updates `cs:word_11168` (button latch) and `cs:word_11102` (input status word). Called from the timer ISR chain every 4 ticks.

### Input State — `input_status_pack` (0x112A1)

Packs the joystick/mouse button latch (`cs:word_11102`) into a single byte returned in AL. Called by `mouse_buttons_get` family.

---

## 9. Audio (OPL/FM) — `opl_reg_write` (0x16F10)

**PROVEN.** The OPL base port is **0x388** (confirmed: `sound_device_init` calls `adlib_device_init(0x388)` for device type 2).

**Sound device type codes** (from `sound_device_init`, 0x1740D):

| AX | Mode | Initialization |
|---|---|---|
| 1 | PC speaker | `always_true` (no-op) |
| 2 | **AdLib/OPL2 at port 0x388** | `adlib_device_init(0x388)` — **PROVEN** |
| 3 | SoundBlaster | `sbi_port_discover_aa` (auto-detect) |
| 4 | SBI verify | `sbi_reset_verify` |

**OPL register write** (`opl_reg_write`, 0x16F10):
OUT port, reg_addr       ; write register address
IN al, port (×6)         ; delay loop
OUT port+1, reg_data     ; write data byte
IN al, port (×18)        ; delay loop
```

The read-loop delays satisfy OPL2/OPL3 register-write timing requirements (address: ≥3.3 µs, data: ≥23 µs). Called only from `opl_addr_data_init_60_80` family during sound card initialization.

---

## 10. Graphics (VGRAPH Driver)

**STRONG** (finding 176, S2).

A 12 KB runtime-loaded graphics driver is loaded into a heap block at linear `0x85AE0` (IDA segment `VGRAPH`). It has a **40-entry function pointer table** at offset 0 (the EXE `game\VGRAPH` file). The driver handles all low-level graphics output (tile blitting, pixel writes, line drawing, palette operations).

Key metrics:
- 76 functions registered (40 entry table + 36 from traced IPs)
- Slot 1: 127K dynamic calls (most-called VGRAPH slot)
- Slot 39: second most called
- ~10% of all runtime far calls go to VGRAPH

Companion variants: `VGRAPHH` (Harrier, 47.7% identical, shifted entry IPs) and `VGRAPHM` (Mig-29, 97.8% identical) — analyzed separately in their own executables.

---

## 11. 3D Coordinate System and Math

**HYPOTHESIS** (from `farptr_table_accum_fields`, `farptr_table_offset_apply`, Level-0/1 math functions).

- **World coordinates**: signed int32 per axis (stored as lo:hi word pairs in FarObj)
- **Angles**: 14-bit fixed-point, range 0–16383 for heading/roll (via `fixed_angle_mask_3fff`), signed –8192..8191 for pitch (via `fixed_angle_fold_e000`)
- **Angle struct** (3-word array at DS:SI): [+0]=heading, [+2]=pitch, [+4]=roll; `angle_wrap` (0x24992) normalizes pitch and re-wraps heading/roll
- **Vector operations**: `fixed_vec3_accumulate_a/b` for per-frame position stepping (3-component int16 delta accumulation with 32-bit carry)
- **Matrix math**: `fixed_matrix_mul` (0x23D2B) performs 16.16 fixed-point multiply-accumulate using trig table values from `0x7B0E:0x3868`. Rounding pattern: `add ax, 0x4000; adc dx, 0; shl ax, 1; rcl dx, 1`.
- **Trig table**: at `0x7B0E:0x3868` (hypothesis: sine table, possibly also cosine and atan). Accessed via `trig_table_lookup` (near, at 0x249D8) and its far stubs (`stub_to_249d8`=0x260AF, `stub_to_trig_lookup`).
- **Matrix segment `0x7B0E`**: also contains the view rotation matrix at `0x7B0E:0x7E948` (4 × int16 = 2×2 matrix) and projection output words at `0x7B0E:0x7E966/7E968`.
- **View mode dispatch**: `fn_table_dispatch` (0x231F0) selects one of 15 view/projection modes via `cs:fn_table_dispatch_table[cs:word_22D28]`. After dispatch, rebuilds angle matrix and returns projection values.
- **Projection**: `segment_clip_test` (0x25F93, 262B, 42K calls) — 2D segment clip against viewport bounds stored in `cs:word_2547C/0/2/4` (xmin/xmax/ymin/ymax)
- **Screen coordinates**: signed int16; negative = off-screen/clipped (basis of `clip_or_draw_dispatch`)
- **View limits**: `view_limits_wrap` (0x25F64) calls either `cs:dword_220E4` (a per-mode view-limits callback) or `view_limits_load` from stack args

---

## 12. Mode / State Machine

**STRONG** (from main_frame_update_loop, game_frame_update_chain analysis).

### Game Mode (word_54D2B)

Controls which update path runs each frame:
- `<= 14` or `= 26`: menu path (keyboard-only)
- `> 14` and `≠ 26`: flight simulation path

### Per-Frame Update Architecture

Two parallel frame chains run during flight:

**`main_frame_update_loop`** dispatches (top level):
1. `game_frame_update_chain` — entity simulation + AI + HUD
2. `game_frame_pipeline_step` — rendering + terrain + projection

**`game_frame_update_chain` (0x2FEF2, R05_1F64)** — the entity update chain:
```
farobj_slot_update_driver       → 16 slot records
farobj_move_accumulate_step     → 40-entry entity motion (CX=82 max)
entity_timer_row_scan           → countdown timers
aircraft_slot_cycle_step        → 40 aircraft/AI slots
mode_strip_frame_step, tile_object_interpreter, farobj_tile_key_cache
farobj_slot_step_spawn, farobj_sweep_all
HUD: hud_state_rowtable_step, hud_panel_transform_step, hud_readout_timer_render
entity_proj_depth_class         → depth classification for drawing order
angle_matrix_far_invoke(DS:0x48BA+0xC) → build rotation matrix from aircraft heading
fixed_matrix_load_7b0e(0x430C)  → load matrix into trig segment
```

`DS:0x48BAh` = current aircraft entity pointer; `DS:0x44AAh` = aircraft index (0–2).

### Mode Frame Step Core: `mode_frame_step_core` (0x3A3D6, 508B)

Per-entity flight simulation step. Checks gates (paused/active), processes:
- `steerpoint_scan_update` — navigation
- `entity_table_walk_49a3` — entity AI processing
- Farobj active gate ([bx+0x74] from scan list)
- Mode phase counter `ds:0x4AC2` (when ≥ 4 → alternate rendering)
- Render dispatch callbacks

---

## 13. Flight Physics and Aircraft System

**STRONG** (from pos_step_chain_engine, control_axes_read, aircraft_slot_cycle_step).

### Flight Control Axes (`control_axes_read`, 0x2234B)

Reads 4 flight control axes, normalized to ±2048 (±0x800). Two input modes:
- **Joystick**: `joystick_axis_read_clamp` → BX/AX/CX/DX = aileron/elevator/throttle/rudder
- **Keyboard**: accumulated key presses from CS:word_22242/44/3E/40 (with dead zone ≤ 9)

Normalized: `axis = raw × 0x800 / cs:word_2222C`. Stored to `cs:byte_22232+0/2/4/6`.

### Aircraft Kinematics Block (`pos_step_chain_engine`, 0x3B338)

Core position step function. The aircraft kinematics are stored in a **13-word (26B) flight state block** at `DS:[0x32]` (also mirrored to `DS:[0x66]` and `ES:0x7B0E:0x43BA`):
- Likely: heading, speed, altitude, roll, pitch, and XY/Z position deltas
- Step formula: `delta = speed_coeff × 0x3334` (tile units = 13,108 per tile)
- Uses **self-modifying code** (patches inline constants each frame for speed)

### Aircraft Slot Array (`aircraft_slot_cycle_step`, 0x49546)

40 × 24B aircraft/AI slot records at `DS:0x49AB:[0xC]`:

| Offset | Field |
|---|---|
| [+0] | flags (0 = inactive) |
| [+1] | farobj slot index |
| [+D] | entity type |
| [+14/16] | far callback pointer |

Cycled each frame; deactivates entries after processing (sets [+0] = 0). Handles AI aircraft, missiles, explosions. Counter cycles 0–50 (0x33) with step `word_4A3E8`.

### Entity Motion Table (`farobj_move_accumulate_step`, 0x4CD1D)

40-entry entity motion table at `DS:0x69FF:[4]` (stride 27B = 0x1B per entry):

| Offset | Field |
|---|---|
| [+3] | entity_class |
| [+6] | flags (bit 0x200=skip, bit 0x1=active) |
| [+21h, +25h] | slot identification |

Processes up to 82 active entities per frame, applying motion accumulation from physics step.

---

## 13. DOS Services / Resource Management (`op_dispatch`)

**PROVEN.** The `op_dispatch` function (0x2257B, 29B) is the central DOS services shim with 16 operations, dispatched via `call cs:op_dispatch_table[BX]` where BX is a **byte offset** into a table at CS:0x22060 (seg020 base = 0x1F6C0):

| BX | Function | DOS operation |
|---|---|---|
| 0x00 | `dos_mem_alloc` | INT 21h AH=48h: allocate paragraph block |
| 0x02 | `dos_mem_free`  | INT 21h AH=49h: free paragraph block |
| 0x04 | `file_create`   | INT 21h AH=3Ch: create file |
| 0x06 | `file_open`     | INT 21h AH=3Dh: open (AX=0/1/2=r/w/rw) |
| 0x08 | `file_close`    | INT 21h AH=3Eh: close handle |
| 0x0A | `file_read`     | INT 21h AH=3Fh: read (also gates timer ISR) |
| 0x0C | `file_write`    | INT 21h AH=40h: write |
| 0x0E | `file_lseek`    | INT 21h AH=42h: seek (CH=method) |
| 0x10 | `file_find_first`| INT 21h AH=4Eh: find first file |
| 0x12 | `file_find_next` | INT 21h AH=4Fh: find next |
| 0x14 | `file_get_dta`  | INT 21h AH=2Fh: get DTA address |
| 0x16 | `mem_copy_fwd`  | REP MOVSW+MOVSB: copy CX bytes DS:SI→ES:DI |
| 0x18 | `mem_store_fwd` | REP STOSW+STOSB: fill CX bytes at ES:DI |
| 0x1A | `dos_print_str` | INT 21h AH=9: print DS:SI string |
| 0x1C | `file_delete`   | INT 21h AH=41h: delete file |
| 0x1E | `file_size`     | lseek to end+start to get file size |

**Entity loading pattern**: `entity_slot_create` (0x2EBCD) uses BX=6 (file_open) to open entity data files, BX=0xA (file_read) to load records, BX=0xE (file_lseek) to seek, and BX=8 (file_close) to release. FarObj entity instances are **loaded from disk at creation time**.

### op_dispatch Calling Variants

| Function | EA | Description |
|---|---|---|
| `op_dispatch` | 0x2257B | Register-based (AX=handle, BX=op, CX=count, DX=buf) |
| `op_dispatch_far_entry` | 0x22598 | Far-callable with DS from stack; **54 callers** (kb subsystem) |
| `op_dispatch_far_wide` | 0x225B6 | Far wrapper with CH=seek_method override |

### Streaming Buffer API

A multi-level file streaming API manages budget-limited reads from large data files:

- `cs:word_27476` = current open file handle
- `cs:word_2747A` = bytes remaining (stream budget)
- `cs:word_27480/27482` = source copy pointer
- **`far_op_execute` (0x27703)**: opens file → reads 768B → dispatches via callbacks → closes. The high-level file executor.
- **`far_op_execute_farptr` (0x276E9)**: far wrapper; called by `ui_loadout_menu_enter` for loadout data files.
- **`buffer_budget_entry_block` (0x275D8)**: reads up to `stream_budget` bytes from file; decrements budget.
- **`buffer_callback_api_block` (0x274E6)**: multi-entry method dispatch table for buffer state management.

---

## 14. World / Terrain System

**STRONG** (from `farobj_tile_copy_resolve`, `tile_world_index_3334`, Level-2 analysis).

- **World space**: signed int32 per axis (FarObj lo:hi word pairs)
- **Tile grid**: 512×512 tiles, each **0x3334 (13,108) world units** per side → ~6.7M world units total
- **World→tile**: `tile = 0x1FF - ((world + 0x003400) & 0x1FF0000) / 0x3334`
- **Valid tile types**: 0x00..0x5F (returned by `tile_index_resolve`; > 0x5F = out-of-bounds)
- **Core function**: `farobj_tile_copy_resolve` (0x14EAE, 470B, 397K calls, 44 callers) — converts FarObj world_x/y to tile indices, looks up terrain type. Called by entity step, rendering, terrain queries.
- **Self-modifying code**: `farobj_rect_ratio_build` (0x14CC6) patches inline matrix operands (placeholder `0xABCD`) with live trig values — avoids memory indirection in the hot path.

---

## 15. Audio Architecture

**STRONG** (from `channel_release`, `channel_volume_store`, `opl_reg_write`, Level-2).

- **Channels**: handles are byte offsets into channel data tables; `[handle - 0x519E]` = key control, `[handle - 0x5186]` = volume, `[handle - 0x517A]` = active/key-on flag
- **OPL mode**: `ds:0xAF90` = 0 → OPL2/AdLib (channels 0-8); nonzero → SoundBlaster (channels 6-9 use different registers)
- **OPL key-on**: writing byte 0x20 to `[handle - 0x517A]` triggers key-on; `hw_reg_write_pair` writes OPL 0xB0+channel register
- **Volume table**: at DS:0x99A7 (OPL mode) or 0x99B9 (SB mode) — maps channel to OPL register index
- **Subsystem**: seg007 overlay — `sbi_channel_event_dispatch`, `channel_release`, `channel_volume_store`, `channel_note_seq_write`, `sbi_level_write_6`

---

## 16. Entity / World Management

**STRONG** (from farobj system analysis, main loop disassembly).

### Entity Data Layers

The entity system uses four distinct data structures updated each flight frame:

| Structure | Location | Description |
|---|---|---|
| Main farobj table | `R05_400C:0x34` (N×4B) | Primary state: position, orientation, type, LOD |
| Entity slot records | `0x54AF:0x386F` (16×92B) | Per-frame update state; [+0xA] bit 0 = active |
| Event/timer state | `0x7772:0x506+N` (byte/N) | Countdown timers (weapons reload, state changes) |
| Spawn queue | `0x6B58:0x33` (10×6B) | Pending entity creation queue |

### Per-Frame Entity Update Sequence

Each FLIGHT frame in `main_frame_update_loop`:
1. `farobj_slot_update_driver` — 3-pass update of 16 entity slot records at `0x54AF:0x386F`
2. `farobj_move_accumulate_step` — apply EntityAccumEntry motion (CX=0x52 entries max)
3. `aircraft_slot_cycle_step` — cycle aircraft slot states
4. `farobj_slot_step_spawn` — process spawn queue (up to 10 pending spawns)
5. `farobj_sweep_all` — three sweeps: slot sweep + cmd sweep + entity accum sweep
6. `game_frame_pipeline_step` → includes `farobj_sort_and_step` (depth sort + per-entity step via `farobj_record_lookup_step`)

### Entity Class Codes (FarObj.entity_class [+0x14])

Set by `farobj_entity_attr_setup` from type table B at DS:0x16F4 (R05_33AE overlay).
Used by `farobj_type_gate_test` (gate: only process certain entity types):

| Code | Hypothesis |
|---|---|
| 0x12 (18) | Player / allied aircraft |
| 0x14 (20) | Enemy aircraft |
| 0x33 (51) | Ground target / vehicle |
| 0x38 (56) | Naval / other entity |

### Entity Step State Machine

`farobj_record_lookup_step` (called each frame per projected entity) uses:
- `FarObj.object_kind` [+0x22] × 4 + 0x3052 → type descriptor stream index at `0x7B0E:0x3052`
- Advances through the stream to find the right record (8-byte entries, 0xFFFF = end)
- Executes the per-type step logic

### Entity Creation

`entity_slot_pair_create` creates linked entity pairs (e.g., aircraft + wingman):
calls `entity_slot_create` twice with BX=0 and BX=1.
`farobj_slot_step_spawn` handles spawn queue; uses `fixed_vec3_accumulate_b` with jitter (±3)
for position variation on spawned entities.

### Map Tile Position

`map_tile_pos_get` (0x128A1, corrected from `state_farptr_get`) returns current tile X/Y
from CS globals `map_pos_x` / `map_pos_y`.

---

## 17. Key Global Variables (DGROUP 0x7A32)

| CS/DS offset | Proposed name | Type | Description |
|---|---|---|---|
| `cs:word_22210` | `active_farptr_offset` | uint16 | Current 3D context far pointer — offset half |
| `cs:word_22212` | `active_farptr_seg` | uint16 | Current 3D context far pointer — segment half |
| `cs:word_22214` | `saved_farptr_offset` | uint16 | Saved context pointer — offset half |
| `cs:word_22216` | `saved_farptr_seg` | uint16 | Saved context pointer — segment half |
| `cs:byte_2224B` | `timer_gate_flag` | uint8 | 1 = suppress tick_counter increment |
| `cs:word_22220` | `tick_counter` | uint16 | Gated tick counter (increments every IRQ0 when gate=0) |
| `cs:word_22222` | `timer_divider` | uint16 | Ungated counter; AND 3 == 0 triggers BIOS chain |
| `cs:byte_22246` | `joystick_timer_flag` | uint8 | Enables joystick polling via timer ISR |
| `cs:word_22C71/73/75` | `vec3_accum_x/y/z` | int16 | Per-frame 3D step accumulator components |
| `cs:word_22C7D/7F/81` | `vec3_scale_x/y/z` | int16 | Accumulator scale numerators |
| `cs:word_22C83/85/87` | `vec3_div_x/y/z` | int16 | Accumulator scale denominators |
| `cs:byte_1F734` | `batch_active_flag` | uint8 | Render batch active (set/cleared by `farobj_batch_build_project`) |
| `cs:byte_1F733` | `batch_mode_bits` | uint8 | Bit 0 drives `batch_active_flag` |
| `cs:byte_1F743` | `render_batch_flag` | uint8 | Read by `flag_byte_get`; checked by render pipeline stages |
| `cs:word_24BB8` | `frame_cb_arg` | uint16 | BP argument passed to `dword_220E0` frame callback |
| `cs:dword_220E0` | `frame_cb_ptr` | far_ptr | Current frame update callback (set per mode) |
| `cs:word_2547C/80/7E/82` | `viewport_x/y_min/max` | int16 | Clipping viewport bounds for `segment_clip_test` |
| `cs:word_27476` | `file_handle` | uint16 | Current open file handle (set by `far_op_execute`) |
| `cs:word_2747A` | `stream_budget` | uint16 | Bytes remaining in streaming read budget |
| `cs:word_2748A/27488` | `stream_buf_ptr` | far_ptr | Buffer pointer for streaming file reads |
| `cs:0x5762` | `input_flag_bytes` | flags8[11] | 88-bit keyboard/button event flag bitmap |
| `word_54D2B` | `game_mode` | uint16 | Game mode: ≤14 or =26 = menus; else = in-flight |
| `word_54EFA` | `quit_flag` | uint16 | 13 = exit game loop |
| `0x7A32:0xAD50` | `opl_base_port` | uint16 | OPL I/O base port address (hypothesis: 0x388) |
| `0x54AF:0x1734` | `farobj_scan_list` | far_ptr[16] | 16-entry active-object scan list |
| `0x54AF:0x4ED` | `entity_accum_table` | EntityAccumEntry[40] | Motion sweep entries |

---

## 18. Known Subsystem Map (Overlay Segments)

Based on naming analysis and function organization (HYPOTHESIS unless noted):

| Overlay(s) | Primary content |
|---|---|
| Resident (seg000–seg020) | Core game loop, IRQ0, mouse, joystick, BDA, DGROUP state, farobj dispatch primitives, 3D math, viewport clip |
| R05_1E10 | Main game object system: farobj entity management, sweep, field ops |
| R05_1EFE / R05_1F64 | 3D projection pipeline, viewport transforms, rendering primitives |
| R05_2ACF / R05_2B83 | Terrain sampling, tile rendering, sprite projection |
| R05_2B83+ | HUD readout, flight data, cockpit instruments |
| R05_3xxx | Flight physics, state machines, aircraft motion |
| R05_4xxx | Entity behavior, farobj slot management, entity spawn/update |
| R06_xxx | Unknown (small overlay — possibly menu/UI) |
| R12_xxx | R12 overlay: state record entries, farptr helper |
| R14_5E0B | R14 overlay: stream read, farptr call gate |
| R15_5E8F | R15 overlay: flag/sequence dispatch |
| R17_5E8F | R17 overlay: UI event loop, dispatch |
| R19_5F6C | R19 overlay: farptr dispatch entry |
| R30_569F | R30 overlay: loadout menu, record fields, heap layout |
| R36_xxx | Module slot index |
| R53_569Fs | Unknown |

---

## 19. What We Don't Know Yet

- Exact entity_class codes (0x12/0x14/0x33/0x38 → see §16 hypothesis; type table in R05_33AE not correctly read yet)
- Asset format (PKWARE DCL compression — UNKNOWN, never exercised)
- Full FarObj struct layout (fields 0x2E–0x73 and 0x7C–0xD0)
- Full 13-word flight state block at DS:[0x32] layout (heading, speed, altitude, roll, pitch ordering)
- Aircraft flight model details: lift, drag, gravity equations inside pos_step_chain_engine
- The event_state_machine (0x1AB34) full 17-case breakdown
- How the HUD overlays onto the 3D scene (record_queue_push → renderer chain)
- Campaign and mission state management (above Level-18 of callgraph)
- The 15-slot fn_table_dispatch view mode functions (sub_23235..sub_235BB)
- Asset format (PKWARE DCL compression — UNKNOWN, never exercised)
- Full FarObj struct layout (fields 0x2E–0x73 and 0x7C–0xD0); struct at 0x54AF:0x386F [+0xC0/0xC1] = possibly hit points/fuel (30 = 0x1E initial)
- How view_projection maps to actual screen pixel coordinates (complete math beyond the formula)
- The aircraft flight physics (sub_3A003 → mode_frame_step_core chain)
- The event_state_machine (0x1AB34) full 17-case breakdown
- What the 16-entry type descriptor stream format looks like in detail
- The 15-slot fn_table_dispatch (0x231F0) table contents (view mode functions)
- How the HUD overlays onto the 3D scene (record_queue_push → renderer)
- Campaign and mission state management (above Level-18)

---

## 20. Key Runtime Segments

| Segment | Hypothesis | Evidence |
|---|---|---|
| DGROUP 0x7A32 | Main data/stack segment (DS=SS throughout) | PROVEN finding 121 |
| 0x71C1 | Terrain/map data: entity positions relative to tile grid, slot data | STRONG (entity_update_batch, entity_state_load) |
| 0x7772 | Event/sound/hardware state (sound card mode, event counters, IRQ state) | STRONG (event_state_machine, irq_unmask_and_query, state_mode_check) |
| 0x7894 | Game entity state: slot index table, entity counters | HYPOTHESIS (entity_counters_update, mode_slot_index_build) |
| 0x7B0E | Trig/projection math: sine table, view matrix, farobj sort arrays | STRONG (fixed_matrix_mul, farobj_sort_and_step, farobj_type_field_get) |
| 0x834A | Frame callback ES segment (preset in far_cb_with_args) | HYPOTHESIS |
| 0x5982 | Entity sweep / game-state table area | HYPOTHESIS (farobj_entity_accum_sweep) |

---

*Evidence sources: `registry/game_knowledge.yaml`, `registry/structs.yaml`, `registry/functions.yaml`, `registry/naming.yaml`, `docs/structures.md`, `analysis/s4/farobj_callers.log`, `analysis/s4/toplevel_disasm.log`, findings 1–179.*
