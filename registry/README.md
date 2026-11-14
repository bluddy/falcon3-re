# Falcon 3.0 Registry — Single Source of Truth

This directory contains **machine-readable YAML files** that define all named functions, global variables, data structures, and game knowledge for Falcon 3.0.

## Registry Files (Active)

### `functions.yaml` (1,892 functions)
**The master function naming registry.**

Contains all function names with addresses, system classification, documentation, and sources. This file is read by `analysis/ida_scripts/apply_known_names.py` to synchronize with IDA Pro.

**Format:**
```yaml
functions:
  - address: 0x011450
    name: flight_control_axes_read_normalize
    system: flight_physics
    size: 114
    doc: Reads 4 flight control axes and normalizes to ±2048 range
    source: docs/architecture/flight_physics.md
```

**Naming Convention:** `<system>_<component>_<action>_<detail>`

**Examples:**
- `dos_file_open` - DOS system file opening
- `ai_entity_behavior_dispatcher` - AI entity behavior routing
- `terrain_tile_heightmap_sample` - Terrain heightmap sampling
- `hud_readout_render_coordinator` - HUD rendering coordinator

### `globals.yaml` (32 global variables)
**Global variable names and documentation.**

Contains all known global variables with DS-relative addresses, sizes, types, and documentation.

**Format:**
```yaml
globals:
  - address: 0x3840
    name: terrain_heightmap_31x31
    size: 1922
    type: array[31x31]
    doc: 31×31 height samples for terrain tile rendering
    source: TERRAIN_SYSTEM_100_PERCENT_COMPLETE.md
```

### `structs.yaml` (20+ structures)
**Data structure definitions.**

Contains comprehensive structure definitions with field layouts, offsets, types, and documentation.

**Format:**
```yaml
structs:
  - name: AIContext
    size: 24
    status: confirmed
    source: docs/architecture/ai.md
    fields:
      - {offset: 0x00, size: 2, name: entity_slot_idx, type: uint16, comment: "..."}
      - {offset: 0x02, size: 2, name: farobj_slot_idx, type: uint16, comment: "..."}
```

**Key Structures:**
- `MZHeader` - DOS MZ executable header
- `RTLinkDirEntry` - Overlay directory record (18 bytes)
- `RTLinkThunkEntry` - Overlay call stub (10 bytes)
- `FarObj` - Main game object instance (≥210 bytes)
- `AIContext` - AI entity context (24 bytes, 40 slots)
- `FlightKinematics` - Flight state block (26 bytes)
- `AircraftSlot` - Aircraft slot record (24 bytes, 40 slots)
- `EntitySlotRecord` - Active entity slot (92 bytes, 16 slots)
- `IsldatHeader` - Terrain file header (9 bytes)
- `IsldatRecord` - Terrain feature record (54+ bytes)
- `ObjectModelHeader` - 3D model file header

### `game_knowledge.yaml`
**Game metadata and system knowledge.**

Contains high-level game information: memory model, load base, resident image, overlay segments, thunk tables, and architectural facts.

Not typically edited — serves as reference documentation.

## Archive Directory

`archive/` contains old registry files from the Track E formal decompilation approach:
- `naming.yaml` (945KB) - Old registry we merged from
- `routines.yaml` (1.1MB) - Old routines data  
- `functions_original_70.yaml` (16KB) - Backup before merge
- `FALCONCD.EXE.yaml`, `OVL_1E10.yaml` - Old overlay data
- `*_expected.json` - Track E IDA fix metadata

These files are **archived for historical reference** and should not be edited.

## Workflow

### Adding New Functions

1. **Edit `functions.yaml`** (NOT the Python script!)
   ```yaml
   - address: 0x012345
     name: system_component_action
     system: system_name
     size: 123
     doc: What the function does
     source: docs/architecture/system_name.md
   ```

2. **Run IDA synchronization:**
   ```powershell
   & "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\apply_known_names.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
   ```

3. **Verify results:**
   - Check `analysis/ida_naming_report.json`
   - Verify IDA database has new names

4. **Commit:**
   ```bash
   git add registry/functions.yaml analysis/ida_naming_report.json
   git commit -m "Added <function_name> - <description>"
   ```

### Adding New Globals

Edit `globals.yaml`:
```yaml
- address: 0x1234
  name: system_variable_name
  size: 16
  type: struct
  doc: What it stores
  source: where_you_learned_it.md
```

### Adding New Structures

Edit `structs.yaml`:
```yaml
- name: StructName
  size: 42
  status: confirmed | hypothesis
  source: docs/architecture/system.md
  fields:
    - {offset: 0x00, size: 2, name: field1, type: uint16, comment: "description"}
    - {offset: 0x02, size: 4, name: field2, type: int32,  comment: "description"}
```

## Critical Rules

1. **YAML is the source of truth** - Edit YAML, not Python scripts
2. **Always sync after editing** - Run `apply_known_names.py` after changes
3. **Commit registry + report together** - Keep them in sync
4. **Follow naming conventions** - `system_component_action_detail`
5. **Document sources** - Always note where information came from

## Statistics

**As of 2026-11-15:**
- **1,892 functions** named
- **32 global variables** documented
- **20+ structures** defined
- **9 major systems** documented (100%)
- **YAML-based** single source of truth

---

**For detailed workflow:** See `WORKFLOW.md` at repository root  
**For system documentation:** See `docs/architecture/`  
**For IDA automation:** See `analysis/ida_scripts/README.md`
