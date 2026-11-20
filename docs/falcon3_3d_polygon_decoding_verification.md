# Falcon 3.0 — 3D Polygon & Geometry Decoding Verification

## 1. Executive Summary

We have identified and resolved the exact root cause of the polygon distortion observed in [f-16_problem.png](file:///C:/Users/yotam/projects/falcon3/f-16_problem.png).

By tracing the 3D rendering pipeline in `FALCONCD.EXE` (`0x26B2E` $\to$ `0x28CA1` $\to$ `0x2978E` $\to$ `0x29917`), we decoded the fixed-point geometry structures and polygon record stream.

![F-16 4-View Turnaround Verification](file:///C:/Users/yotam/projects/falcon3/analysis/f16_perfect_turnaround.png)

---

## 2. Root Cause Analysis of the Polygon Glitch

Four distinct issues caused the pink crossing triangles and distorted shapes seen in [f-16_problem.png](file:///C:/Users/yotam/projects/falcon3/f-16_problem.png):

### Root Cause 1: Heuristic Byte Scanning vs. Sequential LOD Stream
In the earlier extractor script, faces were found by scanning every 2 bytes looking for coincidental byte pairs matching `(1 <= col <= 255 and 3 <= cnt <= 8)`. This picked up:
- Transform matrices and orientation angles
- Visibility display lists and aspect-angle tables
- Trailing control words and boundary markers

### Root Cause 2: Cross-LOD Polygon Pollution
Falcon 3.0 models in `game/OBJECTS` contain up to 4 Levels of Detail (LOD 0 through LOD 3) in a single byte stream:
- **LOD 0**: 74 vertices (full detail mesh)
- **LOD 1**: 53 vertices (medium distance mesh)
- **LOD 2**: 19 vertices (distant silhouette)
- **LOD 3**: 8 vertices (extreme range box)

The heuristic scanner scanned beyond the boundary of LOD 0 into LOD 1 and LOD 2, assigning polygons meant for 19-vertex and 53-vertex models to LOD 0's 74-vertex table, creating giant stretched triangles crossing the cockpit and wings.

### Root Cause 3: 2-Byte Stream Desynchronization (Closed Loops)
In Falcon 3.0 polygon records, the vertex index list contains $N + 1$ words rather than $N$ words, where the closing vertex repeats the first vertex:
$$\text{Vertices} = [v_0, v_1, v_2, \dots, v_{N-1}, v_0]$$

Reading only $N$ words caused a 2-byte alignment shift. The next polygon's color was read from the closing vertex, its vertex count was read from the trailing flag, and all vertex indices were offset by 1, corrupting every subsequent face in the model.

### Root Cause 4: Aviation Body Frame (NED) vs. OpenGL Coordinates
Falcon 3.0 stores all coordinates as fixed-point integers in the standard aerospace **North-East-Down (NED)** coordinate convention:
- $X_{\text{falcon}}$: Longitudinal forward axis (nose = $+X$, tail = $-X$)
- $Y_{\text{falcon}}$: Lateral axis (starboard wing = $+Y$, port wing = $-Y$)
- $Z_{\text{falcon}}$: Vertical axis (down = $+Z$, up = $-Z$)

Feeding these raw coordinates directly into OpenGL caused the aircraft to lie on its side with wings oriented vertically and the nose pointing sideways. Converting to standard graphics space:
$$X_{\text{gl}} = Y_{\text{falcon}} \quad (\text{Right})$$
$$Y_{\text{gl}} = -Z_{\text{falcon}} \quad (\text{Up})$$
$$Z_{\text{gl}} = -X_{\text{falcon}} \quad (\text{Depth / Forward})$$

---

## 3. Disassembly Verification in `FALCONCD.EXE`

Tracing the disassembly in `FALCONCD.EXE` confirmed the exact format:

### Object Projection Dispatcher (`0x26B2E`)
```assembly
026b5d: mov cx, word ptr [si]      ; [si + 0] = vertex_count
026b5f: mov si, word ptr [si + 2]  ; [si + 2] = vertex_table_offset
026b7b: call 0x28ca1               ; Transform vertices into buffer 441Eh (stride 16)
026b90: mov si, word ptr [si + 4]  ; [si + 4] = subrecord / display list offset
026b93: lodsw                      ; Load next subrecord pointer until 0xFFFF
```

### Polygon Record Format (`0x2978E` & `0x29917`)
Each polygon record in the model stream has the exact layout:
| Offset | Type | Description |
| :--- | :--- | :--- |
| `+0` | `uint16` | Palette Color Index (1..255, indexed into `game/ALTPAL.ISR`) |
| `+2` | `uint16` | Vertex Count $N$ ($3 \le N \le 8$) |
| `+4` | `uint16[N+1]` | Vertex Offsets ($v_i \times 16$), where $v_N = v_0$ (closed perimeter) |
| `+4 + (N+1)*2` | `uint16` | Trailing normal flag / plane constant |

Total record byte length: $(N + 4) \times 2$ bytes.

---

## 4. Updates & Verification

1. **Asset Pipeline Updated**:
   - [extract_all_3d_assets.py](file:///C:/Users/yotam/projects/falcon3/scripts/extract_all_3d_assets.py): Rewrote `decode_objects_archive` and `decode_aircraft_bin` to use exact subrecord bounds, closed polygon loops, and NED coordinate mapping.
   - Master database regenerated at [assets_database.json](file:///C:/Users/yotam/projects/falcon3/analysis/viewer/assets_database.json).
2. **F-16 Geometry Cleaned**:
   - LOD 0 now has **74 vertices and 57 clean closed polygons** with zero crossing triangles and zero pink stretched planes.
3. **Qt6 3D Viewer Enhanced**:
   - [falcon3_viewer_qt.py](file:///C:/Users/yotam/projects/falcon3/scripts/falcon3_viewer_qt.py): Added two-sided lighting (`GL_LIGHT_MODEL_TWO_SIDE`), polygon offset fill (`GL_POLYGON_OFFSET_FILL`) to eliminate Z-fighting between filled faces and cyan wireframes, and dynamic face normal calculation.
