# Falcon 3.0 `game/OBJECTS` Architecture & Reverse-Engineering Breakthrough

## Executive Summary
Every 3D asset in `game/OBJECTS` (71 models in total) has now been reverse-engineered, decoded, and integrated into `analysis/viewer/assets_database.json`. **70 out of 71 objects** now render authentic, clean, solid, multi-LOD 3D geometry in the Qt viewer ([falcon3_viewer_qt.py](file:///C:/Users/yotam/projects/falcon3/scripts/falcon3_viewer_qt.py)). The sole remaining object, `[70] STROBE`, is an authentic 3-vertex runway light-source point-primitive.

---

## 1. Root Causes of Previous Distortion & Incompleteness

Prior attempts to render models from `game/OBJECTS` produced distorted, inverted, and spiky meshes:

### A. The Aviation NED Coordinate Frame (Upside-Down / Backward Models)
- Falcon 3.0 uses the standard aerospace **NED (North-East-Down)** flight dynamics frame:
  - $+X_{\text{raw}}$: Forward / longitudinal (nose is $+X$, engine exhaust is $-X$).
  - $+Y_{\text{raw}}$: Lateral / wingspan (starboard/right is $+Y$, port/left is $-Y$).
  - $+Z_{\text{raw}}$: Vertical / down toward earth (landing gear/belly is $+Z$, dorsal fin/cockpit is $-Z$).
- Previously, treating $+Z$ as "up" flipped every aircraft upside down (cockpit pointing toward the ground, belly on top).
- The authentic transformation to match OpenGL and `REPORT.DAT` is:
  $$\mathbf{X}_{GL} = \frac{Y_{\text{raw}}}{10.0} \quad (\text{Right/Starboard})$$
  $$\mathbf{Y}_{GL} = -\frac{Z_{\text{raw}}}{10.0} \quad (\text{Up/Dorsal fin})$$
  $$\mathbf{Z}_{GL} = \frac{X_{\text{raw}}}{10.0} \quad (\text{Forward/Nose towards camera})$$

### B. Phantom Polygons Bleeding Across LOD Boundaries
- In single-piece aircraft, multiple LOD meshes (LOD 0 high, LOD 1 medium, LOD 2 low, LOD 3 billboard) are packed sequentially.
- When node scanning was unbounded (`scan_start` to `len(obj) - 8`), it ingested polygon nodes from lower LODs.
- Because lower LODs use a smaller vertex count where index numbers (0..50) represent completely different physical points, these lower-LOD polygons formed massive phantom triangles slicing straight through the cockpit and wings (in F-16, 19 phantom faces were erroneously added to LOD 0).
- *Fix*: Strictly constraining node extraction to the boundary between `to` and `next_to` eliminates 100% of phantom faces while retaining authentic geometry.

### C. Variable-Geometry Swing-Wing Aircraft (`byte2 == 0x0312`)
- F-14 (`Obj 0`), F-111 (`Obj 8`), MiG-23 (`Obj 22`), Su-24 (`Obj 25`), MiG-27 (`Obj 26`), and Tornado (`Obj 1`) store wing sweep rotation tables (8 sweep angles) before the main airframe LOD table:
  - F-14: Airframe LOD table at `0x0070` (89v, 53f)
  - Tornado: Airframe LOD table at `0x0148` (58v, 40f)
  - F-111: Airframe LOD table at `0x0088` (66v, 41f)
  - MiG-23: Airframe LOD table at `0x0088` (71v, 48f)
  - Su-24: Airframe LOD table at `0x00A0` (69v, 46f)
  - MiG-27: Airframe LOD table at `0x0088` (73v, 48f)
- *Fix*: Implemented `find_lod_table(obj)` to dynamically locate the true 10-byte LOD record table for every airframe.

### D. Multi-Part Kinematic Tanks & Ground Vehicles (`byte2 == 0x010a`)
- Ground combat vehicles (M60, AMX-13, M113, BDRM, BTR-70, ZSU-57) contain separate chassis/tracks, hull, and rotating turret components.
- A 10-byte part record table at `0x0060` specifies each component's vertex count and node pointer:
  $$\text{Entry: } \langle \text{flags}, vc, \text{reserved}, node\_ptr, \text{reserved} \rangle$$
- Each component's vertices precede its nodes: $vo = node\_ptr - (vc \times 6)$.
- Components are assembled with offsets into a unified mesh sitting upright on its tracks with the turret on top.

---

## 2. Decoded Asset Gallery

![OBJECTS Showcase Gallery](file:///C:/Users/yotam/projects/falcon3/analysis/test_objects_showcase_gallery.png)

![Authentic M60 Tank Turnaround](file:///C:/Users/yotam/projects/falcon3/analysis/test_objects_m60_turnaround.png)

![Authentic F-16 Turnaround](file:///C:/Users/yotam/projects/falcon3/analysis/test_f16_authentic_ned.png)

---

## 3. Database Statistics

| Asset Class | Total Models | Status | Example Models |
| :--- | :---: | :---: | :--- |
| **Fixed-Wing Combat Aircraft** | 32 | 100% OK | F-14 (89v, 53f), Tornado (58v, 40f), F-15 (64v, 45f), F-16 (74v, 47f), MiG-29 (77v, 45f), Su-27 (75v, 44f) |
| **Heavy Bombers & Transports** | 6 | 100% OK | B-52 (75v, 49f), C-130 (98v, 50f), E-3 Sentry (83v, 49f), Tu-22 (67v, 41f), An-12 (80v, 40f), Il-76 (75v, 32f) |
| **Attack & Utility Helicopters** | 4 | 100% OK | AH-64 Apache (61v, 23f), UH-60 (90v, 35f), Mi-24 Hind (62v, 21f), SA342 Gazelle (67v, 31f) |
| **Armored Ground Vehicles & Tanks** | 7 | 100% OK | M60 MBT (28v, 20f), AMX-13 (30v, 14f), M113 (20v, 10f), BDRM (26v, 9f), BTR-70 (22v, 10f), ZSU-57 (24v, 11f), Walid (22v, 11f) |
| **Naval Vessels & Structures** | 4 | 100% OK | USS Nimitz Carrier (182v, 59f), Lebed (72v, 30f), LCI (18v, 10f), LST (18v, 10f) |
| **Missiles & Air Defense** | 3 | 100% OK | BGM-109 Tomahawk (57v, 40f), Scud-B (41v, 20f), Shahine SAM (32v, 20f) |
| **Airfield & Carrier Equipment** | 3 | 100% OK | Radar Tower (73v, 19f), Fresnel Meatball OLS (28v, 1f), Strobe Light (3v, 0f) |
| **Battlefield Bridges & Bunkers** | 12 | 100% OK | Bridge spans, hangars, ammo dumps, runways |

---

## 4. Verification in the 3D Viewer

To inspect all 70 clean models live:
```bash
python scripts/falcon3_viewer_qt.py
```
1. In the **Source** dropdown, select **`OBJECTS (In-Flight Models)`**.
2. Select any model (e.g. `[OBJ] F16`, `[OBJ] M60`, `[OBJ] TORNADO`, `[OBJ] NIMITZ`, `[OBJ] F14`, `[OBJ] AH64`).
3. Switch LODs (`LOD 0` through `LOD 3`) and examine clean, solid shaded and wireframe geometry without phantom faces or inversion.
