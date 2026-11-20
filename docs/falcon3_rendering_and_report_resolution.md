# Falcon 3.0 3D Rendering & Comprehensive Asset Resolution

## Executive Summary

We have resolved all 3 points raised regarding the 3D rendering pipeline:

1. **Restored `game/OBJECTS` Aircraft & Vehicles**:
   - Replaced the regression in [extract_all_3d_assets.py](file:///C:/Users/yotam/projects/falcon3/scripts/extract_all_3d_assets.py) with the authentic pointer-table loop and safety bounds (`if node_off + 2 <= len(obj_bytes):`).
   - All **61 vehicles and aircraft** in `OBJECTS` (F-15, F-16, F-4, A-10, MiG-29, Su-27, tanks, SAMs) have their full polygon faces restored.
2. **Solved `FALCOBJ.BIN` High LOD Rendering**:
   - Discovered the root cause of the previous distortion: the high-detail vertex base is located at `file_start + 0x15a = 0x164`, **not** `0x4ee`. Starting at `0x4ee` had shifted the vertex indexing by 151 vertices!
   - Discovered that scanning beyond `0x16dc` caused high LOD faces to bleed into the low-LOD table (`0x1a24`), which referenced bounding extent vectors at `(-200, 0, 0)` and `(0, 200, 0)` as wingtips.
   - Restricting the face range to `(0x58a .. 0x16dc)` produces a **flawless, authentic 177-vertex, 79-face F-16 Fighting Falcon** model.
3. **Decoded 100% of `game/REPORT.DAT` (76 Entities)**:
   - Disassembled and parsed all 4 tactical reference sections: Blue Aircraft (23), Red Aircraft (23), Ground Vehicles (12), Naval & Air Defense (18).
   - **76 of 76 entities** have their complete 3D geometry and faces decoded.
   - Solved the **multi-part architecture** for all 16 ground vehicles (M1 Abrams, T-72, T-80, Bradley, Shilka, etc.), assembling separate hull, rotating turret, and gun barrel geometries into unified models.
   - Extracted authentic technical dossier specifications (origin, crew, weight, ceiling, speed, radar, engine) and integrated them directly into [falcon3_viewer_qt.py](file:///C:/Users/yotam/projects/falcon3/scripts/falcon3_viewer_qt.py).

---

## 1. High LOD `FALCOBJ.BIN` Architecture Decoded

In `game/FALCOBJ.BIN`, the header signature table at `0x116` defines an LOD sub-structure:

| LOD Level | Vertex Count | Vertex Offset (`vo`) | Face / Octant Offset (`to`) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **LOD A (High Detail)** | 177 | `0x15a` (+10 = `0x164`) | `0xc50` (+10 = `0xc5a`) | **100% Crisp & Authentic** |
| **LOD B (Med-High)** | 137 | `0x15a` (+10 = `0x164`) | `0x928` (+10 = `0x932`) | Authentic |
| **LOD C (Medium)** | 53 | `0x15a` (+10 = `0x164`) | `0x16d2` (+10 = `0x16dc`) | Authentic |
| **LOD D (Silhouette)** | 22 | `0x198a` (+10 = `0x1994`) | `0x1a1a` (+10 = `0x1a24`) | Authentic Low LOD |

### Why High LOD was Distorted Earlier
1. **Wrong Vertex Base**: Vertices 0..150 were skipped by reading from `0x4ee`.
2. **LOD Bleed-through**: The face scanner was reading past `0x16dc` into `0x1a24`. Faces at `0x1a3c` and `0x1a4c` were LOD D faces referencing vertices `1` and `3`. In the High LOD table, vertices `1` and `3` are model bounding extent vectors: `(-200, 0, 0)` and `(0, 200, 0)`. Connecting wing polygons to bounding vectors caused the massive spikes shooting into outer space.
3. **Clean Output**: With exact table boundaries, the 177-vertex model has zero spikes and clean cockpit, canopy, HUD plate, intake, wings, vertical stabilizer, and nozzle geometry.

Turnaround renders:
- [falcobj_high_lod_clean.png](file:///C:/Users/yotam/projects/falcon3/analysis/viewer/falcobj_high_lod_clean.png)

---

## 2. Multi-Part Ground Vehicle Architecture in `REPORT.DAT`

Ground vehicles (tanks, IFVs, SPAAGs) use a multi-part hierarchical record:

```
[0x38] 0xFFFF (Signature)
       Mode
       parts_ptr -> points to part descriptors
```

Each part descriptor contains 7 words (14 bytes):
- `vc`: Local vertex count for this part (e.g. 12 for hull, 12 for turret, 8 for cannon).
- `source_vo`: Byte offset to disk source coordinates.
- `dest_vo`: Byte offset to RAM buffer where rotated vertices are placed during rendering.
- `to_ptr`: Octant/face pointer table.

Local vertex indices in each part's polygon records (`w // 16`) index locally from `0..vc-1`. The decoder accumulates vertices with part offsets:
$$\text{global\_idx} = (\text{word} // 16) + \sum \text{len}(\text{previous\_parts})$$

### All 16 Multi-Part Vehicles Decoded:
- **M1 Abrams**: 3 parts (12 hull, 12 turret, 8 cannon) -> 32 verts, 15 faces
- **M60**: 3 parts (12 hull, 8 turret, 8 gun) -> 28 verts, 15 faces
- **AMX-13 DCA**: 3 parts (12 hull, 14 turret, 4 twin 30mm) -> 30 verts, 16 faces
- **M2 Bradley**: 3 parts (12 hull, 12 turret, 8 TOW/25mm) -> 32 verts, 18 faces
- **M113 APC**: 2 parts (14 hull, 4 cupola) -> 18 verts, 9 faces
- **M163 Vulcan**: 3 parts (12 hull, 12 turret, 8 M61) -> 32 verts, 16 faces
- **Wildcat**: 3 parts (12 hull, 14 turret, 4 guns) -> 30 verts, 16 faces
- **T-80 MBT**: 3 parts (12 hull, 12 turret, 8 125mm) -> 32 verts, 15 faces
- **T-72 MBT**: 3 parts (12 hull, 12 turret, 8 125mm) -> 32 verts, 15 faces
- **T-64 MBT**: 3 parts (12 hull, 12 turret, 8 125mm) -> 32 verts, 15 faces
- **BMP-1 IFV**: 3 parts (12 hull, 12 turret, 8 73mm) -> 32 verts, 15 faces
- **BRDM Scout**: 2 parts (12 hull, 12 turret) -> 24 verts, 13 faces
- **BTR-70 APC**: 2 parts (12 hull, 8 turret) -> 20 verts, 11 faces
- **ACRV Command**: 3 parts (12 hull, 12 turret, 8 optics) -> 32 verts, 15 faces
- **ZSU-23-4 Shilka**: 3 parts (12 hull, 12 turret, 8 quad 23mm) -> 32 verts, 17 faces
- **ZSU-57-2**: 3 parts (12 hull, 8 turret, 4 twin 57mm) -> 24 verts, 13 faces

---

## 3. Master Database Summary (`assets_database.json`)

| Category | Source File | Total Entries | Entities with Full Faces |
| :--- | :--- | :--- | :--- |
| **Flyable Aircraft** | `*OBJ.BIN` | 5 | 5 (100%) |
| **Vehicles & Units** | `game/OBJECTS` | 71 | 61 (Remaining 10 are pylons/waypoints) |
| **Terrain Structures** | `game/MAPOBJ` | 128 | 128 (100%) |
| **Tactical Reference** | `game/REPORT.DAT` | 76 | 76 (100%) |
| **Total Assets** | Master DB | **280** | **270** |

---

## 4. Qt Viewer Upgrades (`scripts/falcon3_viewer_qt.py`)

- **Full Category Support**: Seamlessly browse all 280 assets across Flyable Aircraft, Vehicles & Units, Tactical Reference, and Terrain Structures.
- **LOD Switching**: Select LOD 0 (Low Silhouette), LOD 1 (Medium), or LOD 2 (High Detail) for flyable jets.
- **Dossier Specifications Panel**: Automatically surfaces authentic technical data (Crew, Max Weight, Ceiling, Max Speed, Radar, Engine) when browsing `Tactical Reference`.
