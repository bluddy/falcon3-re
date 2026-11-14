# Falcon 3.0 Reverse Engineering Workflow

**This document defines the standard workflow for all reverse engineering work on this project.**

## Core Principle

**Every function we discover must be renamed in IDA immediately, or we lose knowledge.**

## Standard Workflow: Learn → Document → Rename → Commit

### 1. Learn (Reverse Engineering)

When analyzing code:
- Use IDA Pro to disassemble and understand functions
- Trace execution paths
- Identify data structures
- Document findings in real-time

### 2. Document (Write Analysis)

**Location**: `docs/<system>/` for permanent documentation

**Format**: Markdown files with:
- System overview
- Function descriptions with addresses
- Data structure definitions
- Algorithm explanations
- Cross-references

**Example**:
```markdown
## Function: flight_control_axes_read_normalize

**Address**: 0x11450
**Size**: 114 bytes
**Purpose**: Reads 4 flight control axes and normalizes to ±2048 range

### Implementation
[detailed description]
```

### 3. Rename (Synchronize with IDA)

**Location**: `analysis/ida_scripts/apply_known_names.py`

**Immediately add discovered functions**:

```python
KNOWN_FUNCTIONS = {
    # System name in comment
    0x11450: "flight_control_axes_read_normalize",  # Description
}
```

**Naming convention**: `<system>_<component>_<action>_<detail>`

**Examples**:
- `dos_file_open` - DOS system file opening
- `ai_entity_behavior_dispatcher` - AI entity behavior routing
- `terrain_tile_heightmap_sample` - Terrain heightmap sampling
- `hud_readout_render_coordinator` - HUD rendering coordinator

**Run synchronization**:
```powershell
cd c:\Users\ybarnoy\projects\falcon3
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\apply_known_names.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

**Verify**: Check `analysis/ida_naming_report.json` for results

### 4. Commit (Version Control)

**Always commit together**:
```bash
git add docs/<system>/<file>.md
git add analysis/ida_scripts/apply_known_names.py
git add analysis/ida_naming_report.json
git commit -m "System: Added <function_name> - <one line description>"
```

**Commit message format**:
```
System: Brief description

- Function 1: purpose
- Function 2: purpose
- Analysis: what was learned

Results: X renamed, Y already correct
```

## Directory Structure

### Documentation (Permanent Knowledge)

```
docs/
├── architecture/        # System-level architecture docs
│   ├── ai.md           # AI system (permanent)
│   ├── flight_physics.md
│   ├── terrain.md
│   └── weapons.md
├── data_formats/       # File format specifications
│   ├── idx_dat.md      # .IDX/.DAT format
│   ├── isldat.md       # Island terrain data
│   └── arms_dat.md     # Weapons data
└── systems/            # Subsystem documentation
    ├── menu.md
    ├── hud.md
    └── file_io.md
```

### Analysis (Work in Progress)

```
analysis/
├── ida_scripts/        # IDA automation scripts
│   ├── apply_known_names.py      # MASTER: All function names
│   ├── extract_function.py       # Template for extraction
│   └── README.md                 # Quick reference
├── ida_falconcd/       # IDA database and exports
│   ├── FALCONCD.EXE.i64          # Main IDA database
│   └── batch*_*.json             # Exported data
├── ida_naming_report.json        # Latest sync results
├── sessions/           # Per-session notes (temporary)
│   ├── 2026-11-10/
│   └── 2026-11-11/
├── data_samples/       # Extracted game data
│   ├── isldat/         # Island terrain samples
│   ├── idx_dat/        # Menu graphics samples
│   └── weapons/        # Weapons data samples
└── tools/              # Analysis helper scripts
    ├── address_translator.py
    ├── segment_map.json
    └── data_extractors/
```

### Game Files (Read-Only Reference)

```
game/
├── FALCONCD.EXE        # Main executable
├── *.IDX / *.DAT       # Data files
├── *.ISL / *.DAT       # Terrain data
└── SQUAD*.CAM          # Campaign files
```

## When to Use Each Location

### Use `docs/<system>/`
- ✅ System architecture (complete understanding)
- ✅ Stable APIs and interfaces
- ✅ Data format specifications
- ✅ Permanent reference material

### Use `analysis/sessions/<date>/`
- ✅ Daily work notes
- ✅ Experimental findings
- ✅ Debugging traces
- ✅ Temporary hypotheses

### Use `analysis/ida_scripts/`
- ✅ IDA automation scripts
- ✅ Function name registry (apply_known_names.py)
- ✅ Reusable extraction templates

### Use `analysis/data_samples/`
- ✅ Extracted binary data
- ✅ File format examples
- ✅ Test data for tools

## Critical Rules

### 1. Never Skip Renaming

❌ **WRONG**:
```
"I discovered ai_target_tracking at 0x3D180"
[moves on without updating apply_known_names.py]
```

✅ **RIGHT**:
```
"I discovered ai_target_tracking at 0x3D180"
[immediately adds to apply_known_names.py]
[runs synchronization script]
[commits both documentation and script]
```

### 2. Keep Documentation and Code in Sync

❌ **WRONG**: Documentation says "flight_control_axes_read" but IDA has "sub_11450"

✅ **RIGHT**: Documentation, apply_known_names.py, and IDA all use "flight_control_axes_read_normalize"

### 3. Promote Session Notes to Permanent Docs

When analysis is complete:
- ✅ Move findings from `analysis/sessions/` to `docs/<system>/`
- ✅ Clean up and organize content
- ✅ Remove temporary hypotheses and dead ends
- ✅ Keep only confirmed, verified information

### 4. Clean Up Regularly

**Weekly**:
- Review session notes
- Promote complete findings to `docs/`
- Archive old session notes
- Verify IDA synchronization

**Monthly**:
- Review directory structure
- Consolidate documentation
- Update this workflow if needed

## Finding This Workflow

**For future agents**:

This file is located at the **repository root**: `WORKFLOW.md`

If you're working on this project and don't know the process, **read this file first**.

## IDA Automation Reference

### Running Synchronization

```powershell
cd c:\Users\ybarnoy\projects\falcon3
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\apply_known_names.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### Extracting a Function

```powershell
cd c:\Users\ybarnoy\projects\falcon3
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\extract_function.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### Verifying Results

Check `analysis/ida_naming_report.json`:
```json
{
  "total_functions": 63,
  "renamed": 56,
  "already_correct": 6,
  "failed": 1
}
```

## Common Mistakes to Avoid

### ❌ Documenting Without Renaming
**Problem**: Knowledge exists in markdown but not in IDA  
**Solution**: Always update apply_known_names.py

### ❌ Renaming Without Documenting
**Problem**: IDA has names but no explanation of what they do  
**Solution**: Always write docs with function descriptions

### ❌ Messy Session Notes Everywhere
**Problem**: Can't find anything, duplicate work  
**Solution**: Use `analysis/sessions/<date>/`, promote to `docs/` when done

### ❌ Inconsistent Naming
**Problem**: Some functions use `sub_XXXXX`, others use generic names  
**Solution**: Follow naming convention: `<system>_<component>_<action>_<detail>`

### ❌ Not Committing Together
**Problem**: Documentation and IDA database get out of sync  
**Solution**: Always commit docs + script + report together

## Questions?

If this workflow doesn't cover your situation:
1. Check `analysis/ida_scripts/README.md` for IDA-specific guidance
2. Check `docs/IDA_AUTOMATION_GUIDE.md` for detailed IDA automation
3. Update this file if you discover a gap in the workflow

---

**Remember**: Learn → Document → Rename → Commit

**Every. Single. Function.**

---

*Last updated: 2026-11-11*
