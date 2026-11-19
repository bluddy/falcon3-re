# Falcon 3.0 3D Graphics Pipeline & Model Format

**System**: `graphics_3d`  
**Binary**: `FALCONCD.EXE`  
**Primary Archive**: `game/OBJECTS`

---

## 1. Executive Summary

This document specifies the authentic 3D model storage format and rendering pipeline reversed from `FALCONCD.EXE` at `0x26B2E` (`object_3d_project_and_draw`). 

Falcon 3.0 models in `game/OBJECTS` do **not** use flat polygon streams. Instead, each LOD chunk defines:
1. A **signed 16-bit vertex array** ($X$: forward/aft, $Y$: lateral starboard/port, $Z$: vertical down/up in NED coordinates).
2. A **Visibility / BSP Tree pointer table** (`to` at offset `0x222`) containing 16-bit relative chunk offsets.
3. A contiguous **polygon definition block** where every face is explicitly defined with its color, vertex count $N$, and an $(N+1)$-word array of indices ($vi \times 16$).

---

## 2. Binary Data Structures

### `Object3DLODHeader` (10 bytes)
Located at `f16.find(b'\xFF\xFF\x00\x40') + 4`:
| Offset | Type | Field Name | Description |
| :--- | :--- | :--- | :--- |
| `+0x00` | `uint16_t` | `vertex_count` | Number of vertices $V$ in this LOD level |
| `+0x02` | `uint16_t` | `vertex_table_offset` | Byte offset `vo` from chunk start to vertex array |
| `+0x04` | `uint16_t` | `poly_table_offset` | Byte offset `to` from chunk start to BSP/visibility table |
| `+0x06` | `uint16_t` | `bounding_radius` | Bounding sphere radius |
| `+0x08` | `uint16_t` | `flags` | Rendering / LOD distance control flags |

### `ObjectPolygon` (Contiguous face record)
| Offset | Type | Field Name | Description |
| :--- | :--- | :--- | :--- |
| `+0x00` | `uint16_t` | `normal_or_flags` | Normal vector or visibility flags |
| `+0x02` | `uint16_t` | `render_mode` | `0` = standard flat, `1` = shaded / specular |
| `+0x04` | `uint16_t` | `color_index` | Palette color index (VGA 256-color DAC) |
| `+0x06` | `uint16_t` | `vertex_count` | Polygon vertex count $N$ |
| `+0x08` | `uint16_t[N+1]` | `vertex_indices` | Vertices stored as $vi \times 16$, closed with $v_0$ |

Total size of each polygon record: $(4 + N + 1) \times 2 = \mathbf{(N + 5) \times 2}$ bytes.

### `ObjectVisibilityNode` (BSP / View Angle Node)
| Offset | Type | Field Name | Description |
| :--- | :--- | :--- | :--- |
| `+0x00` | `uint16_t` | `marker` | `0xFFFF` indicates a group node |
| `+0x02` | `uint16_t[]` | `poly_offset_list` | Array of 16-bit byte offsets pointing to `ObjectPolygon` records, terminated with `0xFFFF` |

---

## 3. Reconstructed Pipeline in `FALCONCD.EXE`

```
object_3d_project_and_draw (0x26B2E)
  │
  ├── fixed_vec3_transform_es (0x26B64) ──> Multiplies vertices by 3x3 orientation matrix into buffer 0x441E (stride 16)
  │
  └── lodsw [si+4] (Traverses table at 'to')
        ├── Group Node (0xFFFF): Unpacks list of polygon offsets
        └── Polygon Node: Calls off_27974[0] (0x2978E: object_3d_poly_visibility_and_draw)
              ├── fixed_vec3_cross: Computes face normal from (v1 - v0) x (v2 - v1)
              ├── vec3_dot: Dot product with camera ray (0xF14)
              ├── jns culling: Backface culling
              └── object_3d_record_span_mask_rebuild (0x299D5): Builds scanline rasterizer spans
```

---

## 4. Key Functions Registered

| Linear Address | Name | Size | Purpose |
| :--- | :--- | :--- | :--- |
| `0x26B2E` | `object_3d_project_and_draw` | 148 B | Main 3D model transformation and traversal loop |
| `0x2978E` | `object_3d_poly_visibility_and_draw` | 128 B | Face normal cross product, dot product, backface culling |
| `0x28E50` | `object_3d_poly_rasterize_dispatch` | 117 B | Edge and span rasterization dispatcher |
| `0x299D5` | `object_3d_record_span_mask_rebuild` | 88 B | Transformed vertex loader (stride 16) and clip mask builder |
