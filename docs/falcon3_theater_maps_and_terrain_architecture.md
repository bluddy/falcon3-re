# Falcon 3.0 — Complete Multi-Theater Map & Terrain Architecture Report

## Executive Summary

To test the absolute limits of our understanding of Falcon 3.0's world and terrain systems, we executed a complete reverse-engineering and visual rendering pipeline across **all 8 battle theaters**:
- **Israel & Sinai** (`ISR`)
- **Korea** (`KOR`)
- **Kuwait & Iraq** (`IRQ`)
- **Bosnia-Herzegovina** (`BOS`)
- **Hokkaido / Japan** (`HOK`)
- **Panama** (`PAN`)
- **Nellis Red Flag** (`NEL`)
- **Pakistan / India** (`PAK`)

The experiment was an **unqualified success**: we successfully extracted and rendered both the 240 × 200 strategic elevation/hydrography raster matrices (`*.MAP`) with their native VGA palettes (`ALTPAL.*`), and the vector geographical features from `ISLDAT.*` (coastlines, rivers, lakes, and international boundaries), resolving the longstanding local-to-world coordinate transform mystery (Finding 118).

---

## Master Overview: The Eight Battle Theaters

Below is the master composite sheet generated directly from the binary assets of all 8 theaters in Falcon 3.0:

![Falcon 3.0 Multi-Theater Overview](C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/all_theaters_overview.png)

---

## Architectural Decoding: How the Terrain Works

Falcon 3.0 employs a tripartite terrain representation that cleanly separates 2D strategic tactical planning, 2D vector boundaries, and 3D flight rendering:

```mermaid
flowchart TD
    subgraph Assets ["Game Binary Assets (per theater)"]
        MAP["*.MAP (48,004 bytes)<br/>240 × 200 Tile Matrix"]
        PAL["ALTPAL.* (840 bytes)<br/>280-Color VGA DAC Palette"]
        ISL["ISLDAT.* (1.3 - 8.0 KB)<br/>Spatial Quadtree + Convex Rings"]
        OBJ["MAPOBJ.* (56 - 252 KB)<br/>12-byte 3D Point Vertices"]
    end

    subgraph R2D ["2D Strategic & Tactical Engine"]
        MAP -->|Tile IDs 32..85| RAST["Raster Elevation & Depth Renderer"]
        PAL -->|6-bit DAC (0..63) × 4| RAST
        ISL -->|Centroid tx, ty + px/2000.0| VEC["Vector Polyline Engine<br/>Coasts, Rivers, Lakes, Borders"]
        RAST --> SCREEN["Tactical Planning Screen<br/>& Mission Editor (R29/R55/R57)"]
        VEC --> SCREEN
    end

    subgraph R3D ["3D Real-Time Flight Engine"]
        ISL -->|Spatial Index Lookup| CULL["pos_neighbor_norm_scan (0x14B4F)<br/>O(1) Grid Visibility Culling"]
        OBJ -->|Int32 X, Y, Z Points| PROJ["3D View Projection & Bresenham Line Drawing"]
        CULL --> PROJ
    end
```

---

## Decoded File Specifications

### 1. Strategic Elevation Matrix (`*.MAP`)
- **File size**: Exactly $48,004$ bytes across all theaters.
- **Header**: 4 bytes little-endian:
  - `uint16_t width` = $240$ (`0x00F0`)
  - `uint16_t height` = $200$ (`0x00C8`)
- **Body**: $240 \times 200 = 48,000$ bytes of 8-bit tile indices.
- **Tile ID Semantics**:
  - `32..39`: **Bathymetric Depth Levels** (8 graduated sea/water tiers).
  - `40..85+`: **Hypsometric Land Elevation Levels** (46+ altitude steps and surface textures).

### 2. VGA Color Palette (`ALTPAL.*`)
- **File size**: $840$ bytes $= 280 \times 3$ bytes.
- **Format**: Standard 6-bit VGA DAC entries ($0..63$).
- **Color Conversion**: To convert to standard 24-bit RGB ($0..255$):
  $$\text{RGB}_8 = \text{round}\left( \text{DAC}_6 \times \frac{255}{63} \right) \approx \text{DAC}_6 \times 4 + \lfloor \text{DAC}_6 / 16 \rfloor$$
- **Color Bands**:
  - Palette entries `32..39` contain graduated sea blues.
  - Entries `40..60` contain coastal lowlands, plains, and valley greens/tans.
  - Entries `61..85` contain mountain elevations, highlands, and peaks.

### 3. Vector Spatial Index & Geometry (`ISLDAT.*`)
- **Header (18 bytes)**:
  - `+0x00`: `uint16_t data_size`
  - `+0x02`: `uint16_t coastline_grid_offset`
  - `+0x04`: `uint16_t river_grid_offset`
  - `+0x06`: `uint16_t pointer_table_offset`
  - `+0x08`: `uint8_t swap_flag` (indicates coordinate system swap for theaters like `HOK`, `KOR`, `PAN`)
- **Feature Record Header**:
  - Centroids `tx` and `ty` in signed 16.16 fixed-point nautical miles:
    $$\text{tx} = \frac{\text{raw\_x}}{65536.0}, \quad \text{ty} = \frac{\text{raw\_y}}{65536.0}$$
  - Attribute tag (`+0x20`):
    - `0x14` (20): **Coastline** (Deep Blue `#1E88E5`)
    - `0x32` (50): **River / Canal** (Emerald `#00BFA5`)
    - `0x64` (100): **Lake** (Indigo `#3949AB`)
    - `0xC8` (200): **International Border** (Crimson `#E53935`)
- **Solved Local-to-World Transform (Finding 118 Resolution)**:
  Local point offsets $\{px, 0, pz\}$ have bounding boxes of approx $\pm 5109$ units per tile (~5.12 nm). The scale divisor to nautical miles is **2000.0**:
  $$\text{world\_x} = \text{tx} + \frac{px}{2000.0}$$
  $$\text{world\_y} = \text{ty} + \frac{pz}{2000.0}$$
  Adjacent tile boundary vertices across neighboring records stitch together with $< 0.01\text{ nm}$ error.

---

## Multi-Theater Census & Statistics

All 8 theaters inspected, parsed, and verified:

| Theater | Code | MAP File | Tile Range | ISLDAT File | Records | Features / Polylines | Points | Coord Bounding Box (X, Y nm) | MAPOBJ Size |
|---------|------|----------|------------|-------------|---------|---------------------|--------|------------------------------|-------------|
| **Bosnia** | `BOS` | `BOSNIA.MAP` | `[40..77]` | `ISLDAT.BOS` | 21 | 24 (Coasts, Lakes, Borders) | 403 | `[-60.4..15.4, -44.6.. 9.4]` | 188,998 B |
| **Hokkaido** | `HOK` | `JAPAN.MAP` | `[33..65]` | `ISLDAT.HOK` | 29 | 51 (Coasts, Rivers, Lakes, Borders) | 401 | `[-57.6..39.4, -29.9..39.3]` | 104,226 B |
| **Kuwait / Iraq** | `IRQ` | `KUWAIT.MAP` | `[34..85]` | `ISLDAT.IRQ` | 28 | 43 (Coasts, Rivers) | 281 | `[-48.0..31.0, -19.2..77.2]` | 252,053 B |
| **Israel** | `ISR` | `ISRAEL.MAP` | `[32..85]` | `ISLDAT.ISR` | 32 | 37 (Coasts, Rivers) | 206 | `[-47.5..29.1, -56.5..13.8]` | 108,401 B |
| **Korea** | `KOR` | `KOREA.MAP` | `[32..83]` | `ISLDAT.KOR` | 29 | 29 (Coasts, Lakes) | 346 | `[-22.0..71.8, -46.1..28.6]` | 134,245 B |
| **Nellis** | `NEL` | `NELLIS.MAP` | `[32..85]` | `ISLDAT.NEL` | 2 | 4 (Lakes / Salt Flats) | 56 | `[ -1.5..-0.2,  -7.4.. 0.2]` | 63,505 B |
| **Pakistan / India**| `PAK` | `INDIA.MAP` | `[32..87]` | `ISLDAT.PAK` | 0 | 0 (Pure Raster Theater) | 0 | *None* | 187,670 B |
| **Panama** | `PAN` | `PANAMA.MAP` | `[32..85]` | `ISLDAT.PAN` | 31 | 61 (Coasts, Canal/Rivers) | 381 | `[-40.3..38.9, -40.9..42.9]` | 56,299 B |

---

## Detailed Theater Comparisons: Raster vs Vector

````carousel
![Israel Raster Map](C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/ISR_raster_map.png)
<!-- slide -->
![Israel Vector Map](C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/ISR_vector_map.png)
<!-- slide -->
![Korea Raster Map](C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/KOR_raster_map.png)
<!-- slide -->
![Korea Vector Map](C:/Users/yotam/.gemini/antigravity-cli/brain/55de3f9f-195f-4620-9a3d-ce8463e4c888/KOR_vector_map.png)
````

---

## Generated Artifacts & Codebase Deliverables

1. **Renderer Script**:
   - [scripts/render_all_theater_maps.py](file:///C:/Users/yotam/projects/falcon3/scripts/render_all_theater_maps.py): Standalone production script for rendering raster maps, vector SVGs, vector PNGs, and composite comparison sheets for all 8 theaters.
2. **Architecture Documentation**:
   - [docs/architecture/terrain.md](file:///C:/Users/yotam/projects/falcon3/docs/architecture/terrain.md): Formally updated with the 240 × 200 `.MAP` format, the `ALTPAL` DAC color conversion, the solved `px / 2000.0` coordinate transform, and the complete multi-theater census.
3. **High-Resolution Render Outputs**:
   - Located in [analysis/theater_maps/](file:///C:/Users/yotam/projects/falcon3/analysis/theater_maps/):
     - `all_theaters_overview.png` (Master 8-theater sheet)
     - `BOS_raster_map.png`, `BOS_vector_map.svg`, `BOS_vector_map.png`
     - `HOK_raster_map.png`, `HOK_vector_map.svg`, `HOK_vector_map.png`
     - `IRQ_raster_map.png`, `IRQ_vector_map.svg`, `IRQ_vector_map.png`
     - `ISR_raster_map.png`, `ISR_vector_map.svg`, `ISR_vector_map.png`
     - `KOR_raster_map.png`, `KOR_vector_map.svg`, `KOR_vector_map.png`
     - `NEL_raster_map.png`, `NEL_vector_map.svg`, `NEL_vector_map.png`
     - `PAK_raster_map.png`
     - `PAN_raster_map.png`, `PAN_vector_map.svg`, `PAN_vector_map.png`
