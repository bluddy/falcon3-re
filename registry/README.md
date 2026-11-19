# Falcon 3.0 Registry — Single Source of Truth

This directory contains **machine-readable JSON files** that define all named functions, global variables, data structures, enums, and game knowledge for Falcon 3.0.

JSON is used as the single source of truth across all tools to eliminate fragile YAML parsing issues (such as unquoted colons, indentation errors, and external library dependencies).

## Registry Files (Active)

### `functions.json` (3,194 functions)
**The master function naming registry.**

Contains all function names with linear addresses, system classification, documentation, and sources. This file is read by `analysis/ida_scripts/apply_known_names.py` to synchronize with IDA Pro.

**Format:**
```json
{
  "address": 70736,
  "name": "flight_control_axes_read_normalize",
  "system": "flight_physics",
  "size": 114,
  "doc": "Reads 4 flight control axes and normalizes to ±2048 range",
  "source": "docs/architecture/flight_physics.md"
}
```

**Naming Convention:** `<system>_<component>_<action>_<detail>`

### `globals.json` (172 global variables)
**Global variable names and documentation.**

Contains all known global variables with DS-relative addresses, sizes, types, and documentation.

### `structs.json` (42 structures)
**Data structure definitions with exact field layouts.**

Contains comprehensive structure definitions with field offsets, types, sizes, and documentation. Synchronized directly into IDA Pro structures using `analysis/ida_scripts/sync_structs_to_ida.py`.

**Format:**
```json
{
  "name": "AIContext",
  "size": 24,
  "status": "confirmed",
  "source": "docs/architecture/ai.md",
  "fields": [
    {"offset": 0, "size": 2, "name": "entity_slot_idx", "type": "uint16", "comment": "Index to main entity slot table"},
    {"offset": 2, "size": 2, "name": "farobj_slot_idx", "type": "uint16", "comment": "Index to farobj main table"}
  ]
}
```

### `enums.json` (28 enums)
**Enumerations, state machine values, and bitflags.**

Contains named enums (e.g. `WeaponType`, `RadarModeState`, `EntityStatusFlags`) synchronized to IDA with `sync_structs_to_ida.py`.

### `game_knowledge.json`
**Game metadata and system knowledge.**

Contains architectural constants, memory model details, RTLink overlay directory specs, toolchain information, and system parameters.

---

## Workflow

### 1. Adding New Functions
Edit `registry/functions.json` and sync with IDA:
```powershell
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\apply_known_names.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### 2. Adding / Updating Structures
Edit `registry/structs.json` and sync with IDA:
```powershell
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\sync_structs_to_ida.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### 3. Applying Structure Offsets in Code (The 'T' Key)
When you identify a function using a struct via a base register:
Add the entry to `analysis/ida_scripts/struct_offset_targets.json` and run:
```powershell
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\apply_struct_offsets.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```
Or in IDA GUI: highlight the displacement operand (e.g., `[di+0xA]`), press **`T`**, and choose the struct.

---

## Archive Directory

`archive/` contains historical files from previous milestones (e.g. `naming.yaml`, `routines.yaml`). These are kept for reference and should not be modified.
