# Falcon 3.0 Reverse Engineering Project

**Understanding Falcon 3.0 through practical reverse engineering**

## Quick Start

1. Read `WORKFLOW.md` - standard reverse engineering process
2. Check `docs/` - system documentation  
3. Review `analysis/ida_scripts/apply_known_names.py` - what we know
4. Follow: **Learn → Document → Rename → Commit**

## Our Approach

**Pragmatic reverse engineering that gets results:**
- Analyze systems in IDA as we encounter them
- Document understanding immediately in markdown
- Rename functions with descriptive names as we learn them
- Commit documentation + names together to never lose knowledge

**This informal approach has successfully documented:**
- HUD system (100%)
- Terrain system (100%)  
- AI system (90%)
- Flight physics (90%)
- And 6+ other major systems

**Why this works:** We document what we understand when we understand it, rather than trying to achieve byte-perfect formal correctness before documenting anything

## Directory Structure

```
falcon3/
├── README.md           # This file - project overview
├── WORKFLOW.md         # Standard reverse engineering workflow
│
├── docs/              # Documentation
│   ├── architecture/  # System-level architecture docs
│   │   ├── ai.md           # AI system (90% complete)
│   │   ├── flight_physics.md  # Flight physics (90% complete)
│   │   └── ...
│   ├── data_formats/  # File format specifications
│   └── systems/       # Subsystem documentation
│
├── analysis/          # Work area
│   ├── ida_scripts/   # IDA automation (CRITICAL!)
│   │   └── apply_known_names.py  # Master function name registry
│   ├── ida_falconcd/  # IDA database (source of truth)
│   ├── sessions/      # Temporary work notes
│   ├── data_samples/  # Extracted game data
│   ├── tools/         # Analysis helper scripts
│   └── archive/       # Historical files
│
├── tools/             # Legacy IDA automation scripts
│   └── (mostly historical, use analysis/ida_scripts instead)
│
├── game/              # Original game files (gitignored)
└── manual/            # Original game manual scans
```

## Current Status (2026-11-11)

### Systems Documented

| System | Completion | Documentation |
|--------|-----------|---------------|
| **HUD System** | 100% ✅ | `docs/architecture/hud.md`, Complete rendering pipeline |
| **Terrain System** | 100% ✅ | `docs/architecture/terrain.md`, Full heightmap & rendering |
| **AI System** | 90% 🟢 | `docs/architecture/ai.md`, Behavior system complete |
| **Flight Physics** | 90% 🟢 | `docs/architecture/flight_physics.md`, Controls & aerodynamics |
| **Weapons System** | 70% 🟡 | Damage model, spawn system, effects |
| **Menu System** | 60% 🟡 | UI state machine, data formats |
| **File I/O** | 80% 🟢 | DOS wrappers, .IDX/.DAT loaders |
| **Audio System** | 30% 🟠 | Basic understanding |
| **Mission System** | 40% 🟠 | File formats partially decoded |

### Functions Named

**63 functions** with proper descriptive names (98.4% success rate)
- Location: `analysis/ida_scripts/apply_known_names.py`
- Naming convention: `<system>_<component>_<action>_<detail>`
- Examples:
  - `flight_control_axes_read_normalize` - Read 4 flight control axes, normalize to ±2048
  - `hud_readout_render_coordinator` - Main HUD rendering coordinator
  - `terrain_tile_heightmap_sample` - Bilinear heightmap sampling
  - `ai_entity_behavior_dispatcher` - Master AI behavior routing

### Data Formats Decoded

- ✅ `.IDX/.DAT` - Menu graphics pairs (offset tables + data)
- ✅ `.ISL/.DAT` - Island terrain data (quadtrees, vectors, heightmaps)
- ✅ Mission waypoints - Campaign mission structure
- 🟡 Save game format - Partially understood
- 🟡 Weapon data tables - Structure known, values documented

## Workflow

**Our standard process** (see `WORKFLOW.md` for details):

```
1. Learn
   ↓ Reverse engineer in IDA, trace execution, identify patterns

2. Document  
   ↓ Write findings in docs/architecture/<system>.md

3. Rename
   ↓ Add functions to analysis/ida_scripts/apply_known_names.py

4. Commit
   ↓ Git commit docs + script + report together
```

**Critical rule:** Every discovered function MUST be renamed in IDA immediately, or we lose knowledge.

### Running IDA Synchronization

```powershell
cd c:\Users\ybarnoy\projects\falcon3
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A `
  -S"analysis\ida_scripts\apply_known_names.py" `
  "analysis\ida_falconcd\FALCONCD.EXE.i64"

# Check results
cat analysis\ida_naming_report.json
```

## Getting Started

### For New Contributors

1. **Understand the workflow** - Read `WORKFLOW.md`
2. **See what's documented** - Browse `docs/architecture/`
3. **Check what we know** - Review `analysis/ida_scripts/apply_known_names.py`
4. **Pick a system** - Choose something interesting (menu, audio, mission, etc.)
5. **Start reverse engineering** - Follow the Learn → Document → Rename → Commit process

### For Continuing Work

1. **Check current state** - Review relevant `docs/architecture/<system>.md`
2. **Open IDA** - Load `analysis/ida_falconcd/FALCONCD.EXE.i64`
3. **Analyze** - Trace functions, understand behavior
4. **Document** - Update markdown docs as you learn
5. **Rename** - Add to `apply_known_names.py` immediately
6. **Synchronize** - Run IDA script to apply names
7. **Commit** - Git commit docs + script + report together

## Key Files and Their Purpose

| File/Directory | Purpose |
|----------------|---------|
| `WORKFLOW.md` | Standard reverse engineering process - read this first |
| `analysis/ida_scripts/apply_known_names.py` | Master function name registry - THE source of truth |
| `analysis/ida_falconcd/FALCONCD.EXE.i64` | IDA database - contains all analysis |
| `analysis/ida_naming_report.json` | Latest synchronization results |
| `docs/architecture/` | System documentation - HUD, terrain, AI, etc. |
| `docs/data_formats/` | File format specifications |
| `analysis/sessions/` | Temporary work notes (promote to docs when done) |
| `analysis/tools/` | Helper scripts for parsing and analysis |

## Next Steps

### High-Priority Systems
1. **Menu System** (60% → 80%) - Complete state machine
2. **Weapons System** (70% → 90%) - Finish damage model
3. **Mission System** (40% → 70%) - Complete file formats

### Medium-Priority
4. **Audio System** (30% → 60%) - Sound effects and music
5. **Input System** (40% → 70%) - Beyond flight controls
6. **Campaign System** (30% → 60%) - State progression

### Lower-Priority (Nice to Have)
7. Network/Multiplayer system
8. Complete graphics rendering pipeline
9. Save game format completion

## Questions?

- **How do I...?** → Check `WORKFLOW.md`
- **Where is...?** → Check `analysis/README.md`  
- **What does X do?** → Check `docs/architecture/<system>.md`
- **What have we learned?** → Check `analysis/ida_scripts/apply_known_names.py`

## Project Philosophy

> **"Every function we discover must be renamed in IDA immediately, or we lose knowledge."**

This project follows a pragmatic, results-oriented approach:
- ✅ Document understanding as we gain it
- ✅ Rename functions with descriptive names immediately
- ✅ Commit documentation and names together
- ✅ Don't wait for perfection before documenting
- ✅ Focus on understanding systems, not byte-perfect reconstruction

**This approach has successfully documented 9+ major systems with 100% and 90% completion rates.**

---

*Last updated: 2026-11-11*
