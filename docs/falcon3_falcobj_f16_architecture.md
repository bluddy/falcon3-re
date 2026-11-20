# Falcon 3.0 Authentic F-16 3D Architecture: `FALCOBJ.BIN` vs `OBJECTS`

## 1. Why `OBJECTS` Chunk 3 Looked Like an F-16 (and Why It Had Glitches)

You asked:
> *"how did we get data that looked like an f-16 at all though. I'm so confused."*

Here is the exact explanation of how the game's asset pipeline works:

1. **Two Different F-16 Models Exist in the Game**:
   - **`game/OBJECTS` (Chunk 3)**: The **Tactical / AI Aircraft Model**. This model is stored in the master archive alongside all 71 other vehicles (MiG-29, Su-27, SAMs, tanks). It was authored for distant AI flights and radar targets.
   - **`game/FALCOBJ.BIN`**: The **Player Aircraft Model**. This is a standalone, dedicated model loaded specifically for the player's aircraft in external and flight views.

2. **Why `OBJECTS` Chunk 3 Looked Like an F-16**:
   `OBJECTS` Chunk 3 **is an authentic F-16 model**. Its coordinates really describe an F-16 airframe (canopy, wings, ventral fins, afterburner ring). That is why the nose, wings, and tail were recognizable.

3. **Why `OBJECTS` Chunk 3 Had the "Front-to-Back" Glitches**:
   In `OBJECTS` Chunk 3, the polygon list is organized as an **8-Octant View-Dependent BSP Tree**:
   - The game never rendered all 58 polygons at once.
   - Depending on whether the camera was viewing from the front, rear, top, or bottom, the game engine selected **one specific octant list** (via `object_quad_proj_draw` at `0x286CE`).
   - Within that octant, polygons with flag `0xFFFF` or bit `0x4000` were skipped, and backfacing polygons were culled in screen space.
   - When our extraction script parsed the file, it extracted **every single face across all 8 octants simultaneously without the engine's view-angle culling**. Internal occlusion planes and directional geometry (e.g. connecting tail nozzle `v70` to nose `v45` for backface culling checks) became visible as giant cross-fuselage polygons.

---

## 2. The Discovery in `MEMDUMP7_flight_outside_view.BIN`

When we examined the DOS memory dump taken during active flight outside view:
- **`OBJECTS` Chunk 3 is completely absent from RAM**: searching the entire 1 MB address space found zero instances of its vertices or octants.
- **`FALCOBJ.BIN` is loaded directly into RAM**:
  - Allocated by DOS MCB `0x9095` into memory segment **`0x9096`** (`phys 0x090960`).
  - The simulator's active 3D model pointer table at physical address **`0x070080`** points directly to the 4 LODs of `FALCOBJ.BIN`:
    - LOD 0: `0x9096:0x0000`
    - LOD 1: `0x9096:0x008C`
    - LOD 2: `0x9096:0x00CA`
    - LOD 3: `0x9096:0x1AAA`

`FALCOBJ.BIN` is the actual F-16 being rendered when flying outside view.

---

## 3. Rendering `FALCOBJ.BIN`

Why didn't we see `FALCOBJ.BIN` earlier? In [extract_all_3d_assets.py](file:///C:/Users/yotam/projects/falcon3/scripts/extract_all_3d_assets.py#L35-L69), `decode_aircraft_bin()` was hardcoded to `'face_count': 0, 'faces': []` because it was assumed to be only a wireframe.

When we decode the authentic polygon table from `FALCOBJ.BIN` (`to = 0x0020`), every polygon is **clean, planar, and symmetric**:

| Polygon ID | Name | Vertex Indices | Description |
| :--- | :--- | :--- | :--- |
| **Poly 0** | **Wing Delta** | `[14, 18, 19, 12, 11, 13]` | Symmetrical wing delta on $Y = 0$: $(+124, 0, 13) \to (+124, 0, -13) \to (-124, 0, -13) \to (-124, 0, 13)$ |
| **Poly 1** | **Tail Elevators** | `[16, 0, 15, 10, 1, 17]` | Horizontal tail surfaces from $(+86, +7, -115)$ to $(-86, +7, -115)$ |
| **Poly 2** | **Canopy & Fuselage** | `[21, 8, 11, 10, 15, 13, 9]` | Master top surface starting at nose tip `v21` $(0, 0, +250)$ through canopy to wingroots |
| **Poly 3** | **Lower Intake Nose** | `[3, 13, 11]` | Symmetric triangle on ventral intake |
| **Poly 4** | **Upper Canopy Nose** | `[4, 13, 11]` | Symmetric triangle on dorsal nose |
| **Poly 5** | **Centerline Spine** | `[2, 4, 21, 3, 7, 5]` | Exact vertical spine (all $X = 0$) |
| **Poly 6** | **Ventral Keel** | `[7, 6, 20, 5]` | Lower vertical stabilizer / keel |

### Multi-View Render of `FALCOBJ.BIN`

![Authentic Falcon 3.0 Player F-16 (FALCOBJ.BIN)](/C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/f16_falcobj_rendered.png)

### Native Qt 3D Asset Inspector Verification

![Qt 3D Inspector - FALCOBJ.BIN](/C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/inspector_falcobj_test.png)

Every polygon is planar, clean, and symmetrical, with zero cross-fuselage distortion.
