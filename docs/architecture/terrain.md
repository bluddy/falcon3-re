# World / Terrain System

---

## Coordinate System

| Property | Value | Certainty |
|---|---|---|
| World space | Signed int32 per axis (FarObj lo:hi word pairs) | STRONG |
| Tile size | **0x3334 (13,108) world units** per tile side | STRONG |
| World grid | **512 × 512 tiles** | STRONG |
| Total world | ~6,712,320 × 6,712,320 world units | STRONG |
| Tile count | 0x200 × 0x200 = 262,144 tiles | STRONG |

---

## World → Tile Conversion

```
// From farobj_tile_copy_resolve (0x14EAE):
cx = 0x3334  ; tile divisor

// X axis:
dx:ax = world_x + 0x003400    ; add bias
dx &= 0x1FF                   ; keep lower 9 bits of high word (512 tiles)
dx:ax / cx                    ; quotient = tile index (0..0x1FF)
tile_x = 0x1FF - quotient     ; invert (world increases opposite to tile index)

// Y axis: same formula with world_y
```

The bias 0x003400 centers the tile grid so that world coordinate 0 maps to tile ~0x1FF/2.

**Valid tile type range**: 0x00..0x5F (95 valid terrain types). `tile_index_resolve` returns 0x60+ for invalid/out-of-bounds.

---

## Core Tile Functions

### farobj_tile_copy_resolve (0x14EAE, 470B, seg005)

**397K dynamic calls per session, 44 callers** — the most-used tile function.

```
Input:  DS:SI = 8-byte struct {world_x int32, world_y int32}
        (also cs:byte_11C88 = out-of-range gate)

If cs:byte_11C88 == 0xFF: return AX=0, DX=0 (skip)
Else:
  cs:byte_11C7D = 1 (working flag)
  tile_x = 0x1FF - ((world_x + 0x3400) & 0x1FF0000) / 0x3334
  tile_y = same for world_y
  cs:word_11C1C = tile_x, cs:word_11C1E = tile_y
  cs:byte_11C7D = 0 (success)
  tile_type = tile_index_resolve(tile_x, tile_y)
  if valid (≤ 0x5F):
    cs:byte_11C5D = tile_type
    also resolve (tile_x+1, tile_y) → cs:byte_11C5B
    also resolve (tile_x+1, tile_y-1) → cs:byte_11C59
    ... (more neighbor lookups)
Return: AX = tile_type, DX = dl=cs:byte_11C7D
```

Called by: `entity_setup_step`, `farobj_entity_step_near`, `farobj_rect_ratio_build`,
`sub_14BE0`, rendering pipeline.

### tile_world_index_3334 (0x142DA, 124B, seg005)

Converts DS:SI {world_x int32, world_y int32} to tile indices and resolves tile type.
Checks 4 neighbor tiles (AX,BX), (AX+1,BX), (AX,BX-1), (AX+1,BX-1) and returns
`BP = max(tile_type)` across all 4 neighbors (AH=AL packing).

### tile_index_clamp_5f (0x1656F, 10B, seg005)

```
call tile_index_resolve(AX=tile_x, BX=tile_y)
if AL > 0x5F: AL = 0   ; clamp out-of-bounds to 0
retf
```

---

## Terrain Frame Update: terrain_frame_update_driver (0x153A5, 113B, seg005)

Called each flight frame by `game_frame_pipeline_step` (11K dynamic calls, Level-14).

```
DS = ES = 0x71C1  ; terrain/map segment

pos_neighbor_norm_scan              ; scan neighbor tile positions
if cs:byte_11CF3 != 0:              ; terrain mode flag
    record_script_exec_quad          ; execute quad-resolution terrain scripts
    record_script_exec_main          ; execute main terrain scripts
    cs:byte_11C89 = 0xFF
    tile_base_opcode_interpreter     ; interpret tile opcodes
    cs:byte_11C89 = 0
    if cs:byte_11C69 & 3:
        terrain_attr_walk_13110      ; walk terrain attribute stream
    return
else:
    if cs:byte_11C88 == 0:
        fixed_matrix_scale_shift_7e900  ; scale/shift the view matrix
        state_cursor_advance_11c94      ; advance cursor
        cs:byte_11C69 = 4
        terrain_attr_scan_draw_b        ; scan and draw terrain attributes
        if dx >= 0x40: cs:byte_11C69 = 0; goto loc_153A2
        ... position advance ...
    record_script_exec_lite          ; lightweight terrain script execution
    terrain_attr_walk_13110
```

### Record Scripts

Three variants of terrain script execution (from most to least expensive):
- `record_script_exec_main`: full script execution (CS-local quad records)
- `record_script_exec_quad`: quad-resolution execution
- `record_script_exec_lite`: lightweight single-pass

The "record script" appears to be a small bytecode for terrain event processing
(weather changes, day/night transitions, etc.).

---

## Terrain Segment (0x71C1)

The primary terrain/map data segment. Many terrain functions set DS = ES = 0x71C1.

**Key offsets** (from `entity_setup_step`):
- `0x71C1:0x774F3+0x1EA` = entity X position (int32 relative to terrain)
- `0x71C1:0x774F3+0x1EE` = entity Y position (int32)
- `0x71C1:0x774F3+0x1F2` = accumulated X (int32)
- `0x71C1:0x774F3+0x1F6` = heading
- `0x71C1:0x774F3+0x1F8` = pitch (angle_fold via stub_to_24988)

Scale factor: `× 0x96 (150)` applied to convert heading units.

---

## Self-Modifying Code: farobj_rect_ratio_build (0x14CC6, 396B, seg005)

The projection matrix builder for the tile renderer uses INLINE CODE PATCHING:

```asm
; Set up with trig lookup (bx=0x3868):
stub_to_249d8(bx=0x3868)   ; lookup sine/cosine
ax = ds:word_7E94A          ; view matrix element
cs:word_14D43 = ax          ; ← PATCHES inline mov ax, 0xABCD at 14D43
cs:word_14D4C = ax          ; ← PATCHES inline mov ax, 0xABCD at 14D4C
...                         ; (more patches at 14D68, 14D71, 14D7A, 14D83, 14D9F)
```

After patching, the code at 0x14D3B executes 6 inline multiply operations with the
just-patched constants, avoiding memory reads for each multiply. This achieves maximum
speed for the per-tile matrix computation.

The placeholders at compile time are 0xABCD. At runtime they become the current
view matrix values. Same optimization as `pos_step_chain_engine`.

---

## Tile Opcodes: tile_base_opcode_interpreter

A bytecode interpreter for tile-based operations. Called when `cs:byte_11C89 = 0xFF`
is set during terrain update. Likely handles: collision detection, event triggers,
terrain type transitions (water/land boundaries for naval entities).

---

## Unknown: Terrain Struct at 0x71C1

The terrain segment at 0x71C1 holds:
- Entity positions relative to tile grid
- Terrain attribute cache
- Map window state (slot2/slot3 windows)
- DS:0xC55h = current view mode/attribute index (read by coord_point_group_project)
- DS:0x7EAh..0x7F0h = world position offsets (written by coord_point_group_project)
- DS:0x102h..0x10Ah = temporary view record (for view_projection calls)

The exact layout of this segment's fields is not fully mapped.
