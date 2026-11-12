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

**HYPOTHESIS** (inferred from call graph, not fully traced).

The top-level frame pipeline is driven by `game_frame_pipeline_step` (resident, Level-6+). Each frame:
1. `timer_tick_isr` (IRQ0 ~18.2 Hz) updates tick counters and optionally polls joystick
2. `game_frame_update_chain` → `mode_frame_step_core` drives the per-frame update
3. `game_frame_pipeline_step` calls:
   - `farobj_scan_74_clear_b` — reset scan gate bits for 16 active objects
   - `farobj_scan_74_gate_a` — set scan gate if visible/active condition met
   - `farobj_scan_74_timer_c` — advance 8-frame animation timer
   - `hud_terrain_strip_render` / `hud_draw_chain_step` — HUD and terrain strips
4. `mode_frame_step_core` calls the registered frame callback via `cs:dword_220E0` (the opcode handler system below)
5. `game_config_apply_init` (1,123B) is the top-level game initialization: sets mode, IRQ, joystick, entities, terrain.

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
| `dword_220EC` | - | `dispatch_220ec_invoke(BX,DI,DS:SI)` |

These pointers are set by the mode system (e.g. `game_config_apply_init`, `mode_frame_step_core`) and swapped out when transitioning between game states (cockpit view, map view, debrief, etc.).

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

**STRONG.** Far function that writes one (register, data) pair to the OPL FM synthesis chip.

```
Port = [0x7A32:0xAD50]  ; OPL base I/O port (hypothesis: 0x388 for AdLib/SB)
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

**HYPOTHESIS** (from `farptr_table_accum_fields`, `farptr_table_offset_apply`, Level-0 math functions).

- **World coordinates**: signed int32 per axis (stored as lo:hi word pairs in FarObj)
- **Angles**: 14-bit fixed-point, range 0–16383 for heading/roll (via `fixed_angle_mask_3fff`), signed –8192..8191 for pitch (via `fixed_angle_fold_e000`)
- **Vector operations**: `fixed_vec3_accumulate_a/b` for per-frame position stepping (3-component int16 delta accumulation with 32-bit carry)
- **Projection**: `segment_clip_test` (0x25F93, 262B, 42K calls) — 2D segment clip against viewport bounds stored in `cs:word_2547C/0/2/4` (xmin/xmax/ymin/ymax)
- **Screen coordinates**: signed int16; negative = off-screen/clipped (basis of `clip_or_draw_dispatch`)
- **View transform**: `fn_table_dispatch` (0x231F0) — 15-mode indexed dispatch via `cs:off_22D2A[BX]`

---

## 12. Mode / State Machine

**HYPOTHESIS** (from function naming, `mode_frame_step_core`, `game_config_apply_init`).

Falcon 3.0 has multiple game modes:
- Cockpit view, map view, debrief, loadout, main menu, campaign screen
- Mode transitions managed by `mode_frame_step_core` / `mode_phase_apply_core` / `mode_flags_apply`
- Current mode stored in globals at DGROUP

The farobj opcode handler pointers (`dword_220D0` family) are **per-mode** — set during mode transitions to point to appropriate rendering/update functions. `dispatch_220d0_stub` etc. are thin wrappers that call through these pointers.

The `mode_session_state_reset` chain (findings 168-169) resets game state between sessions. The `mode_axis_state_select` (1,929B, Level-2+) handles joystick axis selection and dispatch for view/map mode.

---

## 13. Entity / World Management

**HYPOTHESIS** (from function naming, S4 analysis).

### Entity Sweep

`entity_accum_table` at `0x54AF:0x4ED` holds up to 40 `EntityAccumEntry` records (14B each):
- `count` (uint16): 0 = empty; nonzero = active
- `delta_x/y` (int16): position deltas per sweep
- `countdown` (uint16): timer (decremented; entity moves until 0)
- `delta_hdg/pit/rol` (int16): angle deltas per sweep

`farobj_entity_accum_sweep` (0x2E48C) iterates all 40 entries each frame, applying deltas to the linked farobj's position and orientation via `farptr_table_accum_fields` and `farptr_table_offset_apply`.

### Entity Slots

Entity creation (`entity_slot_create` 0x2EBCD, 463B) calls `op_dispatch` to allocate memory segments, then initializes FarObj fields. The entity slot index is stored in `FarObj.slot_id` [+0x27]. The slot flags at [+0x26] track extended-slot state.

### Map / Tile System

`map_tile_pos_get` (0x128A1, previously misnamed `state_farptr_get`) returns tile coordinates:
- AX = `cs:map_pos_y` (Y tile index)
- BX = `cs:map_pos_x` (X tile index)

Called by `tile_object_interpreter`, `farobj_tile_key_cache`, R12 state entry records.

---

## 14. Key Global Variables (DGROUP 0x7A32)

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
| `0x7A32:0xAD50` | `opl_base_port` | uint16 | OPL I/O base port address (hypothesis: 0x388) |
| `0x54AF:0x1734` | `farobj_scan_list` | far_ptr[16] | 16-entry active-object scan list |
| `0x54AF:0x4ED` | `entity_accum_table` | EntityAccumEntry[40] | Motion sweep entries |

---

## 15. Known Subsystem Map (Overlay Segments)

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

## 16. What We Don't Know Yet

- Exact entity_class codes (0x12/0x14/0x33/0x38 → aircraft/vehicle/ground/naval?)
- Asset format (PKWARE DCL compression — UNKNOWN, never exercised)
- Full FarObj struct layout (fields 0x2E–0x73 and 0x7C–0xD0)
- Full render pipeline (how objects go from FarObj to screen)
- Sound/music beyond OPL register writes
- EMS/XMS overlay swapping details
- Campaign state machine (session, mission, debrief)
- Network/multiplayer support (if any)
- The 15-slot `fn_table_dispatch` (0x231F0) table contents
- The `op_dispatch` (0x2257B) 17-slot operation table targets

---

*Evidence sources: `registry/game_knowledge.yaml`, `registry/structs.yaml`, `registry/functions.yaml`, `registry/naming.yaml`, `docs/structures.md`, `analysis/s4/farobj_callers.log`, findings 1–179.*
