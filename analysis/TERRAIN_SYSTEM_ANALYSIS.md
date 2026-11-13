# Falcon 3.0 Terrain Rendering System - Initial Analysis

## Executive Summary

**Status**: Initial Discovery Phase (15% complete)

The Terrain rendering system is responsible for drawing the 3D landscape visible in external/chase camera views. It consists of **89 functions** organized into 7 major subsystems:

1. **Height Lookup** (6 functions) - Terrain elevation queries
2. **Tile Management** (34 functions) - World tile streaming and caching
3. **Attribute System** (18 functions) - Terrain properties (texture, color, type)
4. **Rendering** (3 functions) - Drawing terrain to screen
5. **VM System** (8 functions) - Virtual memory/terrain streaming  
6. **Grid System** (2 functions) - Spatial partitioning
7. **Frame Update** (8 functions) - Per-frame coordination

## System Architecture

### Main Coordinator

**Function**: `view_terrain_frame_step` at 0x31CA1 (460 bytes)

**Called by**:
- `main_frame_update_loop` - Every frame during flight
- `game_config_apply_init` - Initial setup

**Key Responsibilities**:
- Calls `view_limits_install_step` (2x) - Sets up external view rendering mode
- Calls `terrain_menu_triple_step` - Menu/UI overlay
- Calls `terrain_grid_cb_dispatch` - Spatial grid processing
- Calls `map_view_entity_project` - Projects entities onto terrain

**Total Calls**: 16 function calls per frame

**Connection to HUD System**: 
- Calls `view_limits_install_step` which installs external view renderers
- This connects terrain system to the HUD rendering pipeline we analyzed

### Subsystem Breakdown

#### 1. Height Lookup System (6 functions)

**Purpose**: Query terrain elevation at any world position

**Key Functions**:
- `terrain_height_lookup_11cc8` at 0x11D40 (142 bytes, 3 callers)
  - Primary height query function
  - Takes world X,Y coordinates, returns Z (elevation)
  
- `terrain_attr_lookup_3840` at 0x12F27 (157 bytes, 4 callers)
  - Looks up terrain attributes at a position
  - Returns texture, color, terrain type
  
- `terrain_lookup_gated_b` at 0x13162 (21 bytes, 1 caller)
  - Gated/cached lookup with bounds checking
  
- `farobj_height_gate_wrap` at 0x399A2 (80 bytes, 2 callers)
  - Height lookup for distant objects
  - Likely uses lower LOD data

**Usage**:
- Collision detection (aircraft/ground)
- Object placement (buildings, trees, vehicles)
- Line-of-sight calculations
- Shadow rendering

#### 2. Tile Management System (34 functions - largest subsystem)

**Purpose**: Stream and manage world terrain tiles

**Falcon 3's world is divided into tiles** - square chunks of terrain data loaded on-demand as the player moves through the world.

**Key Functions**:

**Tile Streaming**:
- `farobj_tile_stream_build` at 0x1318C (234 bytes)
  - Builds streaming queue for tiles
  - Loads tiles ahead of player movement

- `tile_base_set_stream` at 0x120EA (45 bytes)
  - Sets active tile base for streaming

- `farobj_tile_copy_resolve` at 0x14EAE (470 bytes, 47 callers!)
  - Resolves tile references
  - Most-called tile function - critical path

**Tile Lookup**:
- `tile_record_search_bl` at 0x12696 (109 bytes, 4 callers)
  - Searches for tile record by ID
  
- `map_tile_pos_get` at 0x128A1 (10 bytes, 6 callers)
  - Gets tile position from map coordinates
  
- `tile_base_search_11caa` at 0x123E9 (47 bytes)
  - Searches tile database

**Tile Processing**:
- `tile_base_opcode_interpreter` at 0x1575E (421 bytes)
  - Interprets tile command stream
  - Likely processes compressed tile data
  
- `slot3_tile_record_load` at 0x13870 (483 bytes, 15 callers)
  - Loads tile record into memory slot 3
  - Slot-based caching system

**Tile Rendering**:
- `tile_strip_sample_draw` at 0x16060 (126 bytes)
  - Draws a strip of tile samples
  
- `tile_strip_project_draw` at 0x361FC (331 bytes)
  - Projects and draws tile strip (3D → 2D)

- `tile_sprite_strip_project` at 0x39748 (179 bytes, 2 callers)
  - Projects sprite strips (roads, rivers?)

**Tile Classification**:
- `tile_quad_classify` at 0x3B6BB (39 bytes)
  - Classifies tile quadrant (flat, sloped, cliff?)
  
- `tile_quad_sample` at 0x14956 (114 bytes, 5 callers)
  - Samples tile quadrant for rendering
  
- `tile_quad_sample_group` at 0x13C3F (113 bytes)
  - Samples multiple quadrants together

**Objects on Tiles**:
- `entity_spawn_from_tile` at 0x49AB4 (335 bytes)
  - Spawns entities (buildings, vehicles) from tile data
  
- `tile_object_interpreter` at 0x4B68D (46 bytes, 2 callers)
  - Interprets tile object opcodes
  
- `tile_object_init_opstream` at 0x4BDD0 (386 bytes)
  - Initializes object command stream

#### 3. Attribute System (18 functions)

**Purpose**: Manage terrain surface properties

**Terrain attributes include**:
- Surface texture (grass, sand, rock, water, snow)
- Surface color/tint
- Surface type (land, water, runway)
- Traversability flags
- Radar signature

**Key Functions**:

**Attribute Lookup**:
- `terrain_attr_default_60` at 0x12F1D (10 bytes, 5 callers)
  - Returns default terrain attributes
  
- `terrain_attr_walk_13110` at 0x13110 (82 bytes, 4 callers)
  - Walks terrain attribute tree/table

**Attribute Storage**:
- `terrain_attr_store_11c8e` at 0x144AC (146 bytes)
- `terrain_attr_store_11c8e_b` at 0x145CF (143 bytes)
- `terrain_attr_store_11c8e_c` at 0x1441C (144 bytes)
- `terrain_attr_store_11c8e_d` at 0x1453E (145 bytes)
  - Four variants - likely for different quadrants or LOD levels

**Attribute Unpacking**:
- `terrain_attr_unpack_11c2c` at 0x14356 (129 bytes)
  - Unpacks compressed attribute data

**Attribute Scanning**:
- `terrain_attr_block_scan` at 0x14870 (156 bytes, 2 callers)
- `terrain_attr_block_scan_inc` at 0x1469A (157 bytes, 2 callers)
- `terrain_attr_block_scan_dec` at 0x147D4 (156 bytes, 2 callers)
- `terrain_attr_block_scan_axdec` at 0x14737 (157 bytes, 2 callers)
  - Scan terrain blocks in different directions
  - Used for collision detection, pathfinding?

**Attribute Dispatch**:
- `terrain_attr_quadrant_dispatch` at 0x143D7 (69 bytes)
- `terrain_attr_quadrant_dispatch_b` at 0x1465E (60 bytes)
  - Dispatches attribute operations by quadrant

#### 4. Rendering System (3 functions)

**Purpose**: Draw terrain to screen

Surprisingly **only 3 dedicated rendering functions**! This suggests terrain rendering piggybacks on the HUD rendering system we already analyzed.

**Key Functions**:

- `hud_terrain_strip_render` at 0x3718D (988 bytes - largest function!)
  - **Main terrain renderer**
  - Called once per frame
  - Renders horizontal strips of terrain
  - 988 bytes = complex algorithm
  
- `terrain_point_label_draw` at 0x36347 (112 bytes)
  - Draws labels on terrain points (cities, bases, waypoints)
  - Uses HUD text rendering (connects to font system)
  
- `terrain_point_project_store` at 0x36437 (45 bytes, 2 callers)
  - Projects 3D terrain point to 2D screen
  - Stores result for drawing

**Rendering Algorithm** (preliminary analysis):

```
hud_terrain_strip_render (988 bytes)
    ↓
For each horizontal strip on screen:
    ├─ tile_strip_project_draw (331 bytes)
    │   ├─ Get visible tiles in strip
    │   ├─ Project 3D coordinates to 2D
    │   └─ Call drawing primitives
    │
    ├─ tile_strip_sample_draw (126 bytes)
    │   └─ Sample and draw tile strip
    │
    └─ terrain_point_label_draw (112 bytes)
        └─ Draw labels/markers
```

**Connection to HUD System**:
- Uses `far_cb_with_args` (external primary renderer)
- Uses HUD font system for labels
- Uses same pixel plotting gateway

#### 5. VM (Virtual Memory) System (8 functions)

**Purpose**: Stream terrain data on-demand to fit in limited memory

**Challenge**: Falcon 3's world is huge, but 1990 PCs had only 640KB RAM. Solution: **streaming virtual memory** system that loads/unloads terrain as needed.

**Key Functions**:

**Streaming**:
- `terrain_stream_pos_update` at 0x310B7 (66 bytes, 2 callers)
  - Updates terrain streaming position
  - Triggered by player movement
  
- `terrain_stream_counter_step` at 0x310F9 (38 bytes)
  - Steps streaming counter
  - Rate-limits streaming operations

**Buffering**:
- `terrain_vm_buffer_decay` at 0x4F3EC (188 bytes, 4 callers)
  - Marks old terrain buffers for unloading
  - LRU cache eviction?
  
- `terrain_vm_blend_gate` at 0x38C91 (26 bytes)
- `terrain_vm_blend_apply` at 0x4F7B8 (56 bytes)
  - Blends terrain LOD transitions
  - Prevents popping artifacts

**Sweeping**:
- `terrain_vm_sweep_sample` at 0x2F400 (309 bytes)
  - Samples terrain during sweep
  - Horizon calculation?
  
- `terrain_vm_sweep_kick` at 0x4FCBE (38 bytes, 6 callers)
  - Kicks off terrain sweep operation
  
**Lookup**:
- `terrain_vm_entry_lookup` at 0x4FE02 (44 bytes)
  - Looks up terrain VM entry
  - Maps world position → memory buffer

**Flags**:
- `terrain_vm_flag_gate` at 0x4F8BC (168 bytes)
  - Gates operations based on VM flags
  - Prevents access to unloaded data

#### 6. Grid System (2 functions)

**Purpose**: Spatial partitioning for efficient queries

**Falcon 3 likely uses a grid/quadtree** to avoid checking every object against every other object.

**Key Functions**:

- `terrain_pos_grid_build` at 0x163AD (429 bytes, 2 callers)
  - Builds spatial grid from terrain positions
  - Large function = complex algorithm
  - Likely quadtree or uniform grid construction
  
- `terrain_grid_cb_dispatch` at 0x3AB59 (37 bytes)
  - Dispatches callback for grid cells
  - Called from `view_terrain_frame_step`
  - Iterates visible grid cells, calls renderer

**Usage**:
- Frustum culling (don't render offscreen terrain)
- Collision detection optimization
- Entity queries (find nearby objects)

#### 7. Frame Update System (8 functions)

**Purpose**: Per-frame terrain state updates

**Key Functions**:

- `terrain_frame_update_driver` at 0x153A5 (113 bytes, 4 callers)
  - Drives per-frame terrain updates
  - Coordinates subsystem updates
  
- `terrain_menu_triple_step` at 0x31E6D (82 bytes)
  - Updates terrain menu/UI overlay
  - Called from `view_terrain_frame_step`
  
- `terrain_angle_time_step` at 0x37818 (145 bytes)
  - Updates terrain angles over time
  - Animated terrain (waves, vegetation)?
  
- `terrain_ratio_wrap_step` at 0x38405 (203 bytes)
  - Steps terrain ratio with wrapping
  - FOV or LOD ratio?

- `terrain_ratio_select` at 0x4E0B9 (80 bytes)
  - Selects terrain detail ratio
  - LOD selection based on distance
  
- `terrain_field_sample_step` at 0x38537 (118 bytes)
  - Steps terrain field sampling
  - Horizon/visibility calculation?
  
- `farobj_step_terrain_clamp` at 0x47787 (234 bytes, 5 callers)
  - Clamps far object to terrain
  - Prevents objects from floating/sinking
  
- `cmd_terrain_decay_step` at 0x67974 (24 bytes)
  - Steps terrain decay (damaged runways?)

### Supporting Functions

**Terrain Advancement**:
- `terrain_advance_gated` at 0x11DCE (444 bytes, 3 callers)
  - Advances terrain state
  - Large function = main update loop

- `terrain_dot_advance_11cf8` at 0x11F8A (121 bytes)
  - Advances terrain dot product (lighting?)

- `terrain_matrix_advance_11d04` at 0x1293B (188 bytes)
  - Advances terrain transformation matrix
  - View matrix updates

**Terrain Initialization**:
- `terrain_state_reinit` at 0x31138 (481 bytes)
  - Reinitializes terrain state
  - Mission start, respawn?

**Terrain Projection**:
- `terrain_attr_project_point` at 0x3601B (81 bytes, 3 callers)
  - Projects terrain attribute point to screen

- `terrain_attr_scan_clamp` at 0x3606C (400 bytes)
  - Scans terrain attributes with clamping
  - Large function, likely complex visibility algorithm

**EMS Integration**:
- `ems_terrain_pos_gate` at 0x37C73 (135 bytes)
  - Gates terrain position through EMS (Expanded Memory)
  - Terrain data stored in EMS for > 640KB?

## Data Flow

### Frame Rendering Flow

```
main_frame_update_loop
    ↓
view_terrain_frame_step (460 bytes)
    ├─ view_limits_install_step
    │   └─ Sets up external view rendering mode
    │       ├─ cs:dword_35924 → far_cb_with_args (primary renderer)
    │       └─ cs:dword_35920 → dispatch_220d4_stub (secondary renderer)
    │
    ├─ terrain_grid_cb_dispatch
    │   └─ Iterate visible grid cells
    │       └─ Call renderers for each cell
    │
    ├─ hud_terrain_strip_render (988 bytes)
    │   └─ For each horizontal strip:
    │       ├─ tile_strip_project_draw (331 bytes)
    │       │   ├─ Load visible tiles
    │       │   ├─ Project 3D → 2D
    │       │   └─ Call drawing primitives
    │       │
    │       ├─ tile_strip_sample_draw (126 bytes)
    │       │   └─ Sample and draw pixels
    │       │
    │       └─ terrain_point_label_draw (112 bytes)
    │           └─ Draw labels using HUD font system
    │
    └─ map_view_entity_project
        └─ Project entities onto terrain view
```

### Tile Loading Flow

```
Player moves
    ↓
terrain_stream_pos_update
    ↓
farobj_tile_stream_build
    ├─ Calculate needed tiles based on position/heading
    └─ Build streaming queue
    ↓
tile_base_opcode_interpreter (421 bytes)
    ├─ Read compressed tile commands
    ├─ Decompress tile data
    └─ Load into memory slot
    ↓
slot3_tile_record_load (483 bytes)
    ├─ Allocate slot 3
    ├─ Load tile record
    └─ Cache for rendering
    ↓
farobj_tile_copy_resolve (470 bytes, 47 callers!)
    └─ Resolve tile references for rendering
```

### Height Lookup Flow

```
Query: Get terrain height at (X, Y)
    ↓
terrain_height_lookup_11cc8 (142 bytes)
    ├─ Calculate which tile contains (X, Y)
    ├─ map_tile_pos_get → tile coordinates
    ├─ Load tile if not cached
    │   └─ slot3_tile_record_load
    ├─ Sample height from tile heightmap
    └─ Return Z elevation
```

## Performance Estimates

Based on function sizes and call counts:

**Per-Frame Terrain Rendering**:
- `view_terrain_frame_step`: 460 bytes, ~2,000 instructions
- `hud_terrain_strip_render`: 988 bytes, ~4,000 instructions
- `tile_strip_project_draw`: 331 bytes × ~20 strips = ~3,000 instructions
- Supporting functions: ~5,000 instructions
- **Total: ~14,000 instructions per frame**

**At 8MHz 8086**:
- Average 10 cycles per instruction
- 14,000 × 10 = 140,000 cycles
- @ 8MHz = ~17.5ms per frame

**Frame Budget**: 55ms @ 18 FPS
**Terrain Rendering**: ~17.5ms (32% of budget)

This is **significantly higher** than HUD rendering (2-4%), which makes sense - terrain is the most expensive subsystem.

## Key Insights

### 1. Strip-Based Rendering

Terrain is rendered in **horizontal strips** across the screen, not polygon-by-polygon. This is a classic early-90s optimization:

- Coherent memory access (cache-friendly)
- Simple scanline algorithm
- Easy clipping against horizon
- Works well with 2D frame buffer

### 2. Tile-Based Streaming

The world is divided into **tiles** that stream in/out as needed:

- Huge world fits in limited memory
- Predictive loading (based on heading)
- Slot-based caching (slot 3 explicitly mentioned)
- Opcode interpreter for compressed data

### 3. LOD System

Multiple functions mention "ratio" and distance-based selection:

- `terrain_ratio_select` - Chooses detail level
- `terrain_ratio_wrap_step` - Updates LOD ratio
- VM blend functions - Smooth LOD transitions

### 4. Attribute-Based System

Terrain attributes are separate from geometry:

- Heights are in one system (heightmap)
- Attributes are in another (texture/color)
- Allows compression (many tiles share attributes)

### 5. Grid-Based Culling

Spatial grid (`terrain_grid_cb_dispatch`) enables:

- Frustum culling (don't render offscreen)
- Early rejection (skip distant tiles)
- O(visible_cells) instead of O(all_tiles)

### 6. EMS Integration

`ems_terrain_pos_gate` suggests terrain data is stored in **Expanded Memory Specification (EMS)**:

- Breaks 640KB DOS limit
- Paging terrain data in/out
- Common technique for large datasets in DOS

## Next Steps

To reach 100% understanding of the terrain system:

### Phase 1: Core Rendering (Priority: High)

1. **Analyze `hud_terrain_strip_render`** (988 bytes)
   - Understand strip rendering algorithm
   - Identify projection math
   - Map connections to tile system

2. **Analyze `tile_strip_project_draw`** (331 bytes)
   - 3D projection algorithm
   - Clipping strategy
   - Drawing primitive calls

3. **Analyze `tile_strip_sample_draw`** (126 bytes)
   - Sampling algorithm
   - Pixel output

### Phase 2: Tile System (Priority: High)

4. **Analyze `farobj_tile_copy_resolve`** (470 bytes, 47 callers!)
   - Most-called function
   - Critical path performance
   - Tile reference resolution

5. **Analyze `tile_base_opcode_interpreter`** (421 bytes)
   - Compressed data format
   - Opcode instruction set
   - Decompression algorithm

6. **Analyze `slot3_tile_record_load`** (483 bytes, 15 callers)
   - Tile caching strategy
   - Slot management
   - Memory layout

### Phase 3: Height/Attribute System (Priority: Medium)

7. **Analyze `terrain_height_lookup_11cc8`** (142 bytes)
   - Heightmap sampling
   - Interpolation algorithm
   - Tile coordinate mapping

8. **Analyze `terrain_attr_lookup_3840`** (157 bytes)
   - Attribute storage format
   - Lookup algorithm
   - Default attribute handling

### Phase 4: VM/Streaming (Priority: Medium)

9. **Analyze `terrain_vm_sweep_sample`** (309 bytes)
   - Streaming strategy
   - Horizon calculation?
   - Visibility determination

10. **Analyze `terrain_stream_pos_update`** (66 bytes)
    - Streaming triggers
    - Position tracking
    - Predictive loading

### Phase 5: Grid/Culling (Priority: Low)

11. **Analyze `terrain_pos_grid_build`** (429 bytes)
    - Spatial data structure
    - Grid cell size
    - Quadtree or uniform grid?

12. **Analyze `terrain_grid_cb_dispatch`** (37 bytes)
    - Callback interface
    - Cell iteration order
    - Visibility testing

## Summary

The Terrain system is **substantially larger and more complex** than the HUD system:

| Metric | HUD System | Terrain System |
|--------|-----------|---------------|
| Functions | 60+ | 89 |
| Subsystems | 4 layers | 7 subsystems |
| Main Coordinator | 908 bytes | 460 bytes |
| Primary Renderer | varies | 988 bytes |
| Frame Budget | 2-4% (~1-2ms) | ~32% (~17.5ms) |
| Complexity | Medium | High |

**Terrain is the most performance-critical subsystem**, consuming nearly 1/3 of the frame budget. This makes sense - realistic terrain rendering was a key selling point of Falcon 3.0 and a major technical achievement for 1991.

The system shows sophisticated engineering:
- ✅ Streaming to handle huge worlds in limited RAM
- ✅ LOD system to maintain performance at distance
- ✅ Spatial culling to skip invisible geometry
- ✅ EMS integration to break 640KB barrier
- ✅ Strip-based rendering for cache efficiency
- ✅ Compressed tile data to save memory

---

**Analysis Status**: Initial Discovery (15% complete)  
**Date**: 2026-11-11  
**Analyst**: Kiro AI  
**Next**: Analyze core rendering functions (`hud_terrain_strip_render`, `tile_strip_project_draw`)
