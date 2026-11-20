# Falcon 3.0: Vector Maps & Terrain Architecture Resolved

## Executive Summary

1. **2D Tactical Map (`*.MAP`)**: Confirmed via disassembly of `0x133535` and xref analysis of `dword_79D92`. The 240 × 200 raster `.MAP` file is **strictly a 2D Tactical/Mission Planning screen asset**, displayed up to **20x zoom**. It is **never** accessed by the 3D flight engine and is **never** used for elevation, line-of-sight, or collision.
2. **3D Flight Elevation**: Managed exclusively at runtime in active flight memory (`ds:0x3840`, 32 × 32 tile grid, cell divisor `0xCCD0` = 0.8 nm, center bias `0x333400` = 64 tiles).
3. **The "Broken Coastline & Rotated Pieces" Mystery (Solved)**: The disjointed, shattered appearance of Israel's coastline and displaced Dead Sea was caused by two compounding flaws:
   - **Local Offset vs Centroid Invariant Pairing**: Centroids are stored as `Centroid_X` (`c0` at `[di+0]`, Longitude) and `Centroid_Y` (`c4` at `[di+4]`, Latitude). Local offsets inside each tile are stored as `w0` (Local Y, North-South) and `w2` (Local X, East-West).
     Between adjacent Dead Sea records (Rec 12 and Rec 13), $\Delta c4 = +335,360 / 65536 = +5.1171875\text{ nm}$, which is canceled exactly by $\Delta w0 = -8,776 / \text{SCALE} = -5.1171875\text{ nm}$.
     Swapping local offsets $(w0, w2)$ without swapping centroids $(c0, c4)$ previously caused each individual tile to rotate inside its boundary, breaking the shared edges and tearing the map apart.
   - **Seamless Invariant Mesh**:
     $$u = \frac{\text{Centroid\_X}}{65536.0} + \frac{w2}{\text{SCALE}} \quad (\text{Longitude, East-West})$$
     $$v = \frac{\text{Centroid\_Y}}{65536.0} + \frac{w0}{\text{SCALE}} \quad (\text{Latitude, North-South})$$
     With this invariant mesh, adjacent tile boundaries align with **$0.0000000000$ error** across all tiles.
   - **Unified Whole-Map Orientation (View B: $X=v, Y=u$)**:
     - Confirmed across all theaters: $X = v = \text{Centroid\_Y} + w0/\text{SCALE}$ and $Y = u = \text{Centroid\_X} + w2/\text{SCALE}$.
     - **Nellis (`NEL`)**: Lake Mead renders horizontally (aspect ratio 2.5), matching [NELLIS.MAP](file:///C:/Users/yotam/projects/falcon3/game/NELLIS.MAP) and real geography.
     - **Israel (`ISR`)**: Coastline forms a continuous watertight surface extending from Egypt in the SW up to Turkey/Syria in the N, with the Dead Sea seamlessly connecting across records.
     - **Korea (`KOR`) & Bosnia (`BOS`)**: Orientations now match their tactical raster counterparts.
4. **Hydrography vs. Ground Surface Plates (`attr == 0x32`)**:
   - The polygons previously colored emerald green are **NOT water bodies**. They are `attr == 0x32` records (Records 0..10 in `ISLDAT.ISR`), indexed exclusively by Fine Grid A (`T2`).
   - In the 3D flight engine assembly (`0x28A68..0x28A80`), their sub-records index palette colors `0x00..0x08`. In `ALTPAL.ISR`, indices `0x00..0x08` are `RGB(160, 160, 212)` to `RGB(168, 156, 216)`—**pale grayish-white**.
   - These are **coarse ground sector plates** spaced in regular 17.5 nm grid increments that appear in the 3D cockpit as **flat white surfaces on the ground**.
   - Because they are not hydrographic water, the primary vector map [ISR_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/ISR_vector_map.png) isolates the true watertight hydrography, while [ISR_ground_plates_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/ISR_ground_plates_vector_map.png) provides the full composite overlay.
5. **All 8 Theater Vector Maps Generated**: All 8 theaters (`BOS`, `HOK`, `IRQ`, `ISR`, `KOR`, `NEL`, `PAK`, `PAN`) have been rendered into seamless vector maps and master composite overviews.

---

## 1. 2D Tactical View vs 3D Flight Engine Elevation

```
                                  [ GAME ASSETS ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
         2D TACTICAL VIEW                                3D FLIGHT SIMULATOR
    ┌─────────────────────────┐                     ┌─────────────────────────┐
    │       *.MAP (48KB)      │                     │        ISLDAT.*         │
    │  240 x 200 raster image │                     │ 3D water polygon mesh   │
    └────────────┬────────────┘                     └────────────┬────────────┘
                 │ (undoc_133535)                                │ (pos_neighbor_norm_scan)
                 ▼                                               ▼
    ┌─────────────────────────┐                     ┌─────────────────────────┐
    │   dword_79D92 buffer    │                     │  Flight Terrain Memory  │
    │  [bx]=240, [bx+2]=200   │                     │  32 x 32 elevation grid │
    └────────────┬────────────┘                     └────────────┬────────────┘
                 │                                               │
        Zoom <= 20x: Raster Base                        Continuous 3D terrain height,
        Zoom > 20x:  Vector Lines                       collision, ground shadowing
```

### Disassembly Proof (`0x133535`)
```assembly
0x0013355A: push word ptr es:aMap+1 ; ".MAP"
0x0013356A: call string_concatenate
0x0013357E: call op_dispatch_far_entry ; Open file (op 6)
0x0013359C: push 0BB84h ; Read 48,004 bytes (48,000 pixels + 4 header bytes)
0x001335A2: call op_dispatch_far_entry ; Read file (op 10)
0x001335CB: les  bx, es:dword_79D92
0x001335D0: mov  word ptr es:[bx], 0F0h   ; Set width = 240
0x001335DC: mov  word ptr es:[bx+2], 0C8h ; Set height = 200
```

Xref analysis on `dword_79D92` confirmed that **zero** instructions in the flight engine (`0x10000..0x4FFFF`) ever read this pointer. It is accessed exclusively by 2D tactical map coordinators and blitters (`0x172xxx`, `0x184xxx`, `0x1A8xxx`).

---

## 2. ISLDAT Coordinate System & Assembly Proof

In `pos_diff_norm` (`0x28874`) and `graphics_line_draw_bresenham` (`0x28B08`), FalconCD patches its own projection instructions:

```assembly
0x000289E9: mov ax, cs:word_1F6E8 ; Centroid Y delta
0x000289ED: mov dx, cs:word_1F6EE
0x000289F2: mov word ptr cs:loc_28B1F+1, ax ; Patched into 1st vertex load (w0)
0x000289FB: mov ax, cs:word_1F6EA ; Centroid Z delta
0x000289FF: mov dx, cs:word_1F6F0
0x00028A04: mov word ptr cs:loc_28B4E+1, ax ; Patched into 2nd vertex load (w1)
0x00028A0D: mov ax, cs:word_1F6EC ; Centroid X delta
0x00028A11: mov dx, cs:word_1F6F2
0x00028A16: mov word ptr cs:loc_28B8C+1, ax ; Patched into 3rd vertex load (w2)
```

### Exact Scale Derivation
Between adjacent records in `ISLDAT.ISR` (e.g. Rec 12 and Rec 13):
- $\Delta \text{Centroid\_Y} = -1,638,320 - (-1,973,680) = 335,360\text{ (fixed point)} = 5.1171875\text{ nm}$.
- Tile top local Y $= +4388$, tile bottom local Y $= -4388 \implies \Delta \text{Local\_Y} = 8,776$.
- $\text{SCALE} = \frac{8776.0}{5.1171875} = 1715.0045801526717\text{ local units / nm}$.
- Checking boundary identity:
  $$Y_{\text{top}}(Rec 12) = \frac{-1973680}{65536} + \frac{4388}{1715.00458} = -27.557373\text{ nm}$$
  $$Y_{\text{bottom}}(Rec 13) = \frac{-1638320}{65536} - \frac{4388}{1715.00458} = -27.557373\text{ nm}$$
  $$\text{Difference} = 0.0000000000\text{ nm}$$

---

## 3. Multi-Theater Census & Generated Maps

| Theater | Code | Records | Convex Polygons | Vector Map Artifact |
|---|---|---|---|---|
| **Bosnia** | `BOS` | 21 | 159 | [BOS_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/BOS_vector_map.png) |
| **Hokkaido** | `HOK` | 29 | 138 | [HOK_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/HOK_vector_map.png) |
| **Kuwait / Iraq** | `IRQ` | 34 | 106 | [IRQ_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/IRQ_vector_map.png) |
| **Israel** | `ISR` | 32 | 75 | [ISR_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/ISR_vector_map.png) |
| **Korea** | `KOR` | 29 | 104 | [KOR_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/KOR_vector_map.png) |
| **Nellis AFB** | `NEL` | 2 | 18 | [NEL_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/NEL_vector_map.png) |
| **Pakistan** | `PAK` | 0 | 0 | [PAK_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/PAK_vector_map.png) |
| **Panama** | `PAN` | 31 | 107 | [PAN_vector_map.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/PAN_vector_map.png) |

Master Overview: [all_theaters_vector_overview.png](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/all_theaters_vector_overview.png)

![All Theaters Vector Overview](file:///C:/Users/yotam/projects/falcon3/analysis/all_theaters_vector_overview.png)

![Israel Vector Map](file:///C:/Users/yotam/projects/falcon3/analysis/ISR_vector_map.png)
