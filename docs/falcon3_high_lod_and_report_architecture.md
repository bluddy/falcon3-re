# Falcon 3.0 High-LOD Aircraft & Tactical Reference Architecture

## Executive Summary

Following the discovery in `MEMDUMP8_f16_model_viewer.BIN` that Falcon 3.0 houses distinct 3D representations across in-flight models (`*OBJ.BIN`) and technical dossiers (`REPORT.DAT` / `VGRAPH`), we successfully decoded the **High Level-of-Detail (LOD 2)** authentic geometry for the player's aircraft.

All data has been integrated into the master assets pipeline:
- [scripts/extract_all_3d_assets.py](file:///C:/Users/yotam/projects/falcon3/scripts/extract_all_3d_assets.py) updated to extract both Low and High LODs for all flyable aircraft, plus 23 tactical reference models from `REPORT.DAT`.
- [analysis/viewer/assets_database.json](file:///C:/Users/yotam/projects/falcon3/analysis/viewer/assets_database.json) regenerated (914.8 KB).
- [scripts/falcon3_viewer_qt.py](file:///C:/Users/yotam/projects/falcon3/scripts/falcon3_viewer_qt.py) updated to support interactive LOD switching (LOD 0 vs LOD 2) and Tactical Reference browsing.
- Wavefront OBJ models exported to [analysis/3d_models/](file:///C:/Users/yotam/projects/falcon3/analysis/3d_models/) (`FALCOBJ_High.obj`, `FALCOBJ_Low.obj`, `HORNOBJ_High.obj`, `FULCOBJ_High.obj`, etc.).

---

## 1. High-LOD F-16 Turnaround Verification

The High-LOD F-16 (`LOD 2` in `FALCOBJ.BIN`) features **182 authentic vertices** and **91 unique planar polygons**, detailing the bubble canopy curvature, radome, engine intake ducting, wing strakes, flaperons, and vertical stabilizer with zero front-to-back distortion.

![High-LOD F-16 Turnaround](file:///C:/Users/yotam/projects/falcon3/analysis/f16_falcobj_high_lod_turnaround.png)

---

## 2. Interactive LOD Comparison in Qt 3D Inspector

````carousel
![F-16 High LOD (182 vertices, 91 faces)](file:///C:/Users/yotam/projects/falcon3/analysis/inspector_falcobj_high_lod.png)
<!-- slide -->
![F-16 Low LOD (22 vertices, 7 faces)](file:///C:/Users/yotam/projects/falcon3/analysis/inspector_falcobj_low_lod.png)
<!-- slide -->
![Original In-Game Model Viewer Framebuffer](file:///C:/Users/yotam/projects/falcon3/analysis/memdump8_vga_screen.png)
````

---

## 3. Flyable Aircraft Fleet: Decoded LOD Specifications

Every flyable aircraft file in `game/` packages both a clean mid-range silhouette (LOD 0) and an ultra-detailed close-up model (LOD 2):

| File | Aircraft | Low LOD (LOD 0) | High LOD (LOD 2) | Wavefront OBJ Files |
| :--- | :--- | :--- | :--- | :--- |
| **`FALCOBJ.BIN`** | F-16 Fighting Falcon | 22 verts, 7 faces | **182 verts, 91 faces** | `FALCOBJ_High.obj`, `FALCOBJ_Low.obj` |
| **`HORNOBJ.BIN`** | F/A-18 Hornet | 38 verts, 14 faces | **376 verts, 132 faces** | `HORNOBJ_High.obj`, `HORNOBJ_Low.obj` |
| **`FULCOBJ.BIN`** | MiG-29 Fulcrum | 27 verts, 12 faces | **90 verts, 65 faces** | `FULCOBJ_High.obj`, `FULCOBJ_Low.obj` |
| **`FSXOBJ.BIN`** | FSX Enhanced F-16 | 22 verts, 7 faces | **182 verts, 88 faces** | `FSXOBJ_High.obj`, `FSXOBJ_Low.obj` |
| **`JFULCOBJ.BIN`**| Japanese MiG-29 | 27 verts, 12 faces | **90 verts, 65 faces** | `JFULCOBJ_High.obj`, `JFULCOBJ_Low.obj` |

---

## 4. Technical Architecture: `REPORT.DAT` & `VGRAPH`

Memory dump `MEMDUMP8` proved that Falcon 3.0's built-in **Tactical Reference / Threat Viewer** does not load `OBJECTS` or `FALCOBJ.BIN`. Instead, it allocates:

```mermaid
graph TD
    A["Falcon 3.0 Main Engine (MCB 0x192)"] --> B["VGRAPH (MCB 0x7750, 12 KB)"]
    A --> C["REPORT.DAT Entry (MCB 0x7a40, 65 KB)"]
    
    subgraph "REPORT.DAT Record"
        C1["Specifications Text (0x0006 - 0x0127)"]
        C2["2D HUD / Layout Data (0x0127 - 0x16AE)"]
        C3["Dedicated 3D Model (0x16AE - End, 3,040 bytes)"]
    end
    
    C --> C1
    C --> C2
    C --> C3
    
    B -->|"int 10h 3D Vector Projection"| D["VGA Screen (0xA0000, 320x200 Mode 13h)"]
    C3 -->|"Feeds Geometry"| B
```

- **Shared Heritage**: The 3D model inside `REPORT.DAT` shares 1,350 consecutive bytes of polygon indexing directly with `FALCOBJ.BIN` LOD 2, proving that both were authored from the same master CAD models at Spectrum HoloByte.
- **23 Threat Dossiers**: `REPORT.DAT` contains dossiers for 23 distinct aircraft (F-16, F-15, F-14, F-117A, F-4, A-10, B-52, C-130, E-3, AH-64, Tornado, Mirage III/5, etc.), all now cataloged in `assets_database.json`.
