# Rendering System — 3D Projection Pipeline

*See also: `docs/architecture/farobj.md` for FarObj struct.*
*See also: `docs/TACTICAL_MAP_COMPLETE_SUMMARY.md` for tactical map 3D system.*

---

## Overview

The 3D rendering pipeline runs entirely within `game_frame_pipeline_step` each flight frame.
The core function `view_projection` (0x20BDB, 1076B) is the most-called non-trivial function:
**282K dynamic calls per session** — roughly 15K calls per second at 18Hz.

**MAJOR DISCOVERY (2024)**: The tactical map display uses the same 3D projection engine via
`fixed_vec3_accumulate_a` (0x22C91, 68B) which performs **51,000+ calls per frame** across
all rendering contexts (HUD, cockpit, external view, tactical map).

---

## Core 3D Math Engine ⭐

### fixed_vec3_accumulate_a (0x22C91, 68 bytes)

**THE mathematical heart of all 3D rendering in Falcon 3.0.**

**Performance**: 51,000+ calls/frame, ~150-300 cycles/call, <0.5ms total

**Purpose**: Fixed-point 3D vector dot product for projection

**Formula**: `Result = (X×ScaleX÷DivX) + (Y×ScaleY÷DivY) + (Z×ScaleZ÷DivZ)`

**State Variables** (cs segment):
```
cs:0x22C71  vec3_x_component        ; 3D vector X (16-bit fixed-point)
cs:0x22C73  vec3_y_component        ; 3D vector Y
cs:0x22C75  vec3_z_component        ; 3D vector Z

cs:0x22C7D  matrix_scale_x          ; Transform matrix element M11
cs:0x22C7F  matrix_scale_y          ; Transform matrix element M12
cs:0x22C81  matrix_scale_z          ; Transform matrix element M13

cs:0x22C83  fixedpoint_divisor_x    ; Normalization divisor
cs:0x22C85  fixedpoint_divisor_y    ; (determines fixed-point format:
cs:0x22C87  fixedpoint_divisor_z    ;  256=8.8, 4096=12.4, 65536=16.16)
```

**Algorithm**:
```assembly
; X component
mov ax, cs:vec3_x_component
mul cs:matrix_scale_x
div cs:fixedpoint_divisor_x
mov cx, dx                      ; CX = X contribution

; Y component
mov ax, cs:vec3_y_component
mul cs:matrix_scale_y
div cs:fixedpoint_divisor_y
add cx, dx                      ; CX += Y contribution

; Z component
mov ax, cs:vec3_z_component
mul cs:matrix_scale_z
div cs:fixedpoint_divisor_z
add cx, dx                      ; CX += Z contribution

retf                            ; Return CX = projected coordinate
```

**Used By**:
- HUD targeting system (~30,000 calls/frame)
- 3D object projection (~15,000 calls/frame)
- Flight physics visualization (~5,000 calls/frame)
- **Tactical map display** (~100 calls/frame via waypoint_display_helper)
- Loadout menu F-16 model
- External view rendering

**Wrapper**: `farobj_vec3_accum_b_ret` (0x022C89, 8B) - calls fixed_vec3_accumulate_a and returns result in AX

---

## Tactical Map 3D Projection

**Discovery**: The tactical map is NOT a simple 2D overlay. It uses full 3D projection with perspective.

### Pipeline

```
Mission Waypoints (X, Y, Altitude)
    ↓
Camera State (position, zoom, angles)
    ↓
waypoint_display_helper (0x1A163A, 2048B)
    ├─ Transform world → camera space
    ├─ Call farobj_vec3_accum_b_ret (2×)
    │   └─ fixed_vec3_accumulate_a
    │       └─ Compute screen_x, screen_y
    └─ Output: pixel coordinates
    ↓
waypoint_coordinate_processor (0x1A2441, 871B)
    └─ Marshal data structures (21B → 18B → 6B)
    ↓
draw_from_struct (0x02245A, 104B)
    ├─ 5-word struct: [x1, y1, x2, y2, attr]
    └─ Dispatch via cs:0x22084 table
    ↓
graphics_line_draw_bresenham (0x028B08, 409B)
    └─ Bresenham line algorithm → VGA 0xA000
```

### Key Functions

| Function | Address | Size | Purpose |
|----------|---------|------|---------|
| tactical_screen_coordinator | 0x12DB6A | 1,031 | UI coordinator |
| waypoint_display_processor | 0x1A0F10 | 2,090 | Buffer initialization |
| waypoint_display_helper | 0x1A163A | 2,048 | 3D projection (calls vec3_accum) |
| waypoint_coordinate_processor | 0x1A2441 | 871 | Data marshaling |

### Display State (segment 0x7894)

```
0x7A2EA/E8  display_data_ptr        ; Main display data (far pointer)
0x7A2F6/F4  waypoint_array_ptr      ; Points to 0x4FC2:0x168
0x7A2F2     display_buffer_handle   ; Buffer handle
0x7A2DA/D8  display_buffer2         ; Secondary buffer
0x7A2E6/E4  display_buffer3         ; Tertiary buffer
0x7A2FA/F8  display_buffer4         ; Fourth buffer
```

### Waypoint Data (segment 0x4FC2)

```
0x13E168    Waypoint array base     ; 21-byte records
0x13E002-   Camera/map state        ; Position, zoom, view mode
0x13E168    (area before waypoints)
```

---

## Pipeline Architecture

```
game_frame_pipeline_step
├── fn_table_dispatch          → select view mode (15 modes), get projection constants
├── farobj_batch_build_project → TERRAIN TILE RENDERER
│    └── coord_point_group_project (per tile patch)
│         └─→ EITHER view_projection OR fixed_vec3_accumulate_a
├── sub_256A3                  → project fixed reference point (DS:0x7B0E:0x4287)
│    └── view_projection
├── viewlist_project_flagged   → per-entity view list (16B-entry records)
│    └── view_projection (each flagged entry)
├── viewmode3_vector_project   → mode 3 cockpit view vectors (DS:0x62D4)
│    └── view_projection (each vector entry)
└── farobj_sort_and_step       → depth sort + step all farobj
     └── farobj_record_lookup_step (per entity, executes type step logic)

Additional per-farobj projection:
viewobj_project_select (each registered farobj, 59K dyn calls)
├── viewobj_project_advance        → LOD-based projection
│    └── view_projection
└── viewobj_project_advance_mark   → same + sets state_flags bit 5 (marked)
     └── view_projection

Tactical Map Rendering (separate pipeline):
tactical_screen_coordinator
└── waypoint_display_processor
    └── waypoint_display_helper
        └── farobj_vec3_accum_b_ret (via fixed_vec3_accumulate_a)
```

---

## Core Projection: `view_projection` (0x20BDB, 1076B)

**282K dynamic calls/session. THE most performance-critical function.**

### Inputs

| Register | Description |
|---|---|
| `ES:BX` | View origin position (FarObj-like struct: [BX+0,2]=X int32, [BX+4,6]=Y int32) |
| `DS:DI` | Target object to project (FarObj-like struct) |
| `CS:word_1F6E6` | Secondary scale factor (CX on entry) |

Saved on entry: `CS:word_1F71C = ES`, `CS:word_1F71E = BX`.

### Skip Conditions (returns immediately)

```
IF FarObj.state_flags [DI+0x24] & 0x80: skip (gate set)
IF FarObj.cmd_field   [DI+0x20] >= 0:   skip (SI must be negative = projection scale)
```

`cmd_field` [+0x20] MUST be negative (bit 15 set) for projection to proceed.
SI = `-cmd_field` (negated to get positive scale factor).

### Projection Formula

```
delta_x = ([DI+0] - ES:[BX+0]) × 16     ; shift left 4 (integer multiply by 16)
           with carry-propagation on int32
delta_div = abs(delta_x) / |SI|          ; divide by scale factor
```

For each axis (X then Y):
1. Compute int32 delta (target - view_origin)
2. Scale × 16 via 4× shl/rcl
3. Take abs (negate if negative)
4. Divide by |SI| (the negated cmd_field)
5. Apply CX (secondary scale) if != 0

The result is a screen-space coordinate (signed int16). Negative = off-screen/clipped.

### LOD Accumulator (FarObj.object_kind [+0x22])

`viewobj_project_advance` increments `object_kind` by 1 or 2 each frame based on
`state_flags` bits:
- Bit pattern of [+0x26] rotated 2: 0=skip, 1=inc by 1 if [+0x27] bit 0x20, 2/3=inc by 1 or 2

This creates distance-based LOD: nearby objects accumulate faster, reaching higher
object_kind values → different rendering modes via `farobj_type_field_get`.

---

## Terrain Tile Renderer: `farobj_batch_build_project` (0x13CB0, 346B, seg005)

Processes a **tile drawing command stream** from DS:SI, projecting each tile patch.

### View Offset Computation

```
offset_x = (cs:word_11BCC - 0x7FF) × (-0xCCD) / 0x400
offset_y = (cs:word_11BCA - 0x400) × (-0xCCD) / 0x400
```

Stored to `cs:word_11BD6/BD8` (X) and `cs:word_11BD2/BD4` (Y).
These offsets convert tile-space to world-space for the projection.

### Command Stream Format (HYPOTHESIS)

DS:SI points to a stream of variable-length drawing commands:
```
lodsb                   ; read command byte
test al, 80h            ; bit 7 = special command type?
lodsw; and bp, 0xC000   ; read next word; test top 2 bits
  cmp bp, 0xC000: skip  ; if both bits set: skip this group
  else: call coord_point_group_project
```

Each tile patch has: a command byte, a type word (top 2 bits = 0xC000 = skip), and
point group data. The exact format is not fully decoded.

### Callers

- `farobj_tile_stream_build` — builds the stream for current view
- `tile_base_batch_build` — entry for tile-based batch

---

## View Object List: `viewlist_project_flagged` (0x2F590, 65B, R05_1F59)

Iterates CX entries of a view object list, projecting each flagged entry.

### View Record Format (16 bytes)

```c
struct ViewRecord {
    uint16_t flags;       // +0x00  bit 15 = needs projection; lower 15 = slot index
    int16_t  world_x;     // +0x02  world X (lo word, written to DS:0x102)
    int16_t  world_x_hi;  // +0x04  world X hi word (→ DS:0x104)
    int16_t  world_y;     // +0x06  → DS:0x106
    int16_t  world_y_hi;  // +0x08  → DS:0x108
    int16_t  field_A;     // +0x0A  → DS:0x10A
    uint16_t pad[2];      // +0x0C  padding to 16 bytes total
};
```

For each record where `flags & 0x8000`: strip the flag, copy 5 words to DS:0x102..0x10A,
set DI=0x102 (the view record block), call `view_projection`.

The view origin comes from `CS:word_1F71C/1F71E` (saved at view_projection entry).

---

## Mode 3 Cockpit Vectors: `viewmode3_vector_project` (0x2F535, 91B, R05_1F40)

Only active when `state_word_44d3d_get()` returns 3.
Iterates `DS:0x62D4:word_62D6A` entries of 6-byte angle vectors at DS:[0x66]:

```
for each entry in DS:0x62D4:[0x66]:
    DS:[0x2E+2]  = vector[0]   ; copy to view struct
    DS:[0x2E+6]  = vector[2]
    DS:[0x2E+0xA] = vector[4]
    ES = 0x54AF, BX = 0x20     ; view origin in R05_1F5F segment
    view_projection(ES:BX, DS:DI=0x2E)
    SI += 6
```

This renders the cockpit's forward/up/right vectors (3 × 2B = 6B per vector) for the
mode 3 (cockpit HUD overlay?) view.

---

## View Mode Dispatch: `fn_table_dispatch` (0x231F0, 58B)

15-entry function table at `CS:fn_table_dispatch_table[CS:word_22D28]`.
Called each frame to select the view/projection mode.

After dispatch: rebuilds angle matrix (`angle_matrix_build_neg` from ES:0x7B0E:0x3884),
copies matrix constants, returns:
- BX = `ES:word_7E968` (projection Z offset)
- CX = `ES:word_7E966` (projection Z scale)
- DX = `ES:word_7E94C+18h`

**The 15 View Mode Functions:**

| Index | Address | Name | Description |
|---|---|---|---|
| 0 | 0x23235 | `view_proj_default` | Conditional: if cs:byte_2322A==0 → copy 3 words DS:SI → ES:DI=3884h |
| 1 | 0x2325E | `view_proj_preset_1` | ES:3884=0x0555, ES:3886=0x0199, ES:3888=0 |
| 2 | 0x2327B | `view_proj_preset_2` | ES:3884=0xFAAB (−0x555), ES:3886=0x0199, ES:3888=0 |
| 3 | 0x23298 | `view_proj_preset_4` | ES:3884=0x1000, ES:3886=0, ES:3888=0 |
| 4 | 0x232B2 | `view_proj_preset_5` | ES:3884=0xF000 (−0x1000), ES:3886=0, ES:3888=0 |
| 5 | 0x232CC | `view_proj_preset_3` | ES:3884=0xE000, ES:3886=0, ES:3888=0 |
| 6 | 0x232E6 | `view_matrix_build` | ES:3884=ES:3896, ES:3886=ES:3898, ES:3888=0; matrix build chain |
| 7 | 0x23316 | `view_proj_preset_6` | ES:3884=0, ES:3886=0xF000 (−0x1000), ES:3888=0 |
| 8 | 0x23330 | `view_proj_preset_7` | ES:3884=0, ES:3886=0x1000, ES:3888=0 |
| 9 | 0x2334A | `view_proj_offset_accum` | Load ES:3884=CS:22D22, ES:3886=CS:22D24; matrix multiply |
| 10 | 0x23394 | `view_proj_load_3896` | Read 3 words at 7B0E:3896 → globals |
| 11 | 0x233D6 | `view_proj_ring_shift` | Barrel shift: DX:AX = BX << CL |
| 12 | 0x233FD | `view_proj_ring_push` | Copy 3 words → ES:3884; push into 0x12-byte ring buffer |
| 13 | 0x2350A | `view_angles_from_struct` | Copy 6 words CS:22DC0:22DBE → 7B0E:38AC; angle transformation |
| 14 | 0x235BB | `view_proj_preset_offset` | Read 7B0E:3896 (3 words); optional CS:22D22/22D24 offset |

All functions write to the 3-vector at ES:7B0E:0x3884/3886/3888 (unit scale 0x1000 = 1.0).
Presets 1-7 are fixed camera orientations. Modes 9-14 perform dynamic view transformations.

---

## Opcode Handler Dispatch (CS: 0x220xx Family)

A family of CS-relative far-pointer slots for per-mode rendering callbacks:

| CS offset | Name | Description |
|---|---|---|
| `dword_220A0` | — | dispatch_220a0_stub |
| `dword_220C8` | `clip_handler` | Clip/skip path (AX < 0 from clip_or_draw_dispatch) |
| `opcode_handler_1` | — | far_cb_0 target |
| `opcode_handler_2` | — | far_cb_1 target |
| `opcode_handler_5` | `draw_handler` | Draw path (AX ≥ 0 from clip_or_draw_dispatch) |
| `dword_220D0` | — | dispatch_220d0_stub (terrain strip rendering) |
| `dword_220D4` | — | dispatch_220d4_stub (HUD draw chain) |
| `dword_220E0` | `frame_cb_ptr` | Main frame callback via far_cb_with_args (ES=0x834A) |
| `dword_220E4` | `view_limits_cb_ptr` | View frustum limits (view_limits_wrap entry 1) |
| `dword_220EC` | — | dispatch_220ec_invoke(BX, DI, DS:SI) |

---

## farobj_render_vtable (0x26400, 14 entries)

Embedded far-pointer table after `dispatch_220d0_stub` retf. Called by mode dispatch.

| Index | Name | Description |
|---|---|---|
| 0 | `object_quad_proj_draw` | Project & draw quad-mesh objects |
| 1 | `object_init_flag_draw` | Initialize draw flags |
| 2 | `object_rot_proj_draw` | Rotate-and-project draw |
| 3 | `object_view_matrix_build` | Build view matrix |
| 4 | `object_frame_advance_step` | Advance animation frame |
| 5 | `farobj_render_draw_1f712` | Draw via type 0x1F712 handler |
| 6 | `object_type_field_step` | Step by type field |
| 7 | `object_proj_draw_dispatch` | Projection draw dispatch |
| 8 | `farobj_render_prep_1f712` | Prep draw |
| 9 | `object_scale_gather_draw` | Scaled gather draw |
| 10 | `object_record_stream_step` | Step via record stream |
| 11 | `object_type3_table_step` | Type-3 table step |
| 12 | `anim_line_object_draw` | Animated line object draw |
| 13 | `flag_1f733_gate` | Flag gate |

---

## VGRAPH Driver (0x85AE0)

A 12KB runtime-loaded graphics driver (file `game\VGRAPH`). Handles all pixel-level output.

- **40-entry function table** at offset 0 (40 × 4B far pointers)
- 76 functions total (40 table + 36 from traced IPs)
- Slot 1: 127K dynamic calls (most-called slot)
- ~10% of all runtime far calls
- Variants: VGRAPHM (Mig-29, 97.8% identical), VGRAPHH (Harrier, 47.7% identical)

---

## VGA Graphics System

### Mode 13h - 320×200 256-Color

**Specification**:
- Resolution: 320×200 pixels
- Colors: 256 (1 byte per pixel)
- Segment: 0xA000:0000
- Total size: 64,000 bytes
- Addressing: Linear (offset = Y × 320 + X)

### Graphics Primitives

| Function | Address | Size | Purpose |
|----------|---------|------|---------|
| draw_from_struct | 0x02245A | 104 | Main dispatcher (649 calls/codebase) |
| draw_struct_args_dispatch | 0x0224C2 | 17 | Load 5-word struct, dispatch via cs:0x22084 |
| graphics_line_draw_bresenham | 0x028B08 | 409 | Bresenham line algorithm |
| graphics_rect_fill_tiled | 0x014200 | 106 | Rectangle fill with 8×8 tiles |
| font_glyph_bitmap_render | 0x011AE7 | 62 | Bitmap font rendering |
| line_record_draw_loop | 0x028E50 | 136 | Line stream walker |
| terrain_anim_line_object_draw | 0x027A20 | 442 | Animated lines (tracers, missiles) |
| clip_or_draw_dispatch | 0x026099 | — | Viewport clipping dispatcher |

### Draw Struct Format (5 words)

```c
struct DrawParams {
    uint16_t x1;    // Start X or position
    uint16_t y1;    // Start Y or position
    uint16_t x2;    // End X or width
    uint16_t y2;    // End Y or height
    uint16_t attr;  // Attributes (color, style, flags)
};
```

**Usage Pattern**:
```assembly
mov si, offset draw_params    ; Point to 5-word struct
call draw_from_struct         ; Dispatcher handles the rest
```

**Dispatch Table**: cs:0x22084 routes to specific primitives:
- Type 0: Point/pixel
- Type 1: Line → graphics_line_draw_bresenham
- Type 2: Rectangle → graphics_rect_fill_tiled
- Type 3: Sprite/blit
- Type N: Custom handlers

### Bresenham Line Algorithm

**graphics_line_draw_bresenham** (0x028B08, 409 bytes):
- Classic Bresenham rasterization
- Handles all 8 octants
- Direct VGA segment 0xA000 writes
- Pixel offset calculation: Y × 320 + X

**Pattern**:
```assembly
mov es, 0xA000          ; VGA segment
mov ax, y               ; Y coordinate
mov cx, 320
imul cx                 ; AX = Y × 320
add ax, x               ; AX = Y × 320 + X
mov di, ax              ; DI = pixel offset
mov al, color           ; Color value (0-255)
mov es:[di], al         ; Write to VGA memory
```

---

## 3D Coordinate System

| Property | Value | Certainty |
|---|---|---|
| World space | Signed int32 per axis (lo:hi word pairs in FarObj) | STRONG |
| Heading/roll | 14-bit unsigned [0, 16383] | STRONG |
| Pitch | 14-bit signed [−8192, 8191] | STRONG |
| Angle struct | [+0]=heading, [+2]=pitch, [+4]=roll (3 words) | HYPOTHESIS |
| Matrix math | 16.16 fixed-point multiply-accumulate (0x4000 rounding bias) | PROVEN |
| Trig table | Sine at 0x7B0E:0x3868; accessed via `stub_to_249d8` | STRONG |
| View matrix | 2×2 int16 at 0x7B0E:0x7E948 | STRONG |
| Proj constants | Z scale at 0x7B0E:0x7E966, Z offset at 0x7B0E:0x7E968 | HYPOTHESIS |

### Clip System

`segment_clip_test` (0x25F93, 262B, 42K calls): 2D segment clip against viewport.
Viewport bounds at `cs:word_2547C/0/2/4` = xmin/xmax/ymin/ymax.
Result in DX:BP = outcode bitmask (0=inside, nonzero=clipped).

`clip_or_draw_dispatch` (0x26099, 16B): `if AX >= 0: opcode_handler_5; else: dword_220C8`.
Dispatches to draw or clip path based on sign of projected screen coordinate.
