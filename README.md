# Falcon 3.0 Reverse Engineering Project

**Two parallel tracks for understanding Falcon 3.0**

## Quick Start

**For reverse engineering work** (documenting the original code):
1. Read `WORKFLOW.md` - standard reverse engineering process
2. Check `docs/` - system documentation
3. Use `analysis/ida_scripts/apply_known_names.py` - function name registry
4. Follow: Learn → Document → Rename → Commit

**For the OCaml rebuild** (Track E - formal decompilation):
1. Read `status.md` - detailed project state
2. Read `plan.md` - Track E formal plan
3. Check `registry/` - formal function ledger
4. Check `docs/findings_log.md` - append-only research log

## Project Structure

### Two Complementary Approaches

#### 1. Reverse Engineering Documentation (What We're Doing)
**Goal**: Understand and document how Falcon 3.0 works

**Workflow**: `WORKFLOW.md` (repository root)
- Learn by reverse engineering in IDA
- Document systems in `docs/architecture/`
- Rename functions in `analysis/ida_scripts/apply_known_names.py`
- Commit docs + script + report together

**Status**: See current progress below

#### 2. Track E OCaml Rebuild (Formal Decompilation)
**Goal**: Build a native 64-bit OCaml application that behaves like Falcon 3.0

**Plan**: `plan.md` (detailed formal plan)
**Status**: `status.md` (comprehensive state tracking)
**Knowledge Base**: `registry/` (formal ledgers, YAML)
**Research Log**: `docs/findings_log.md` (append-only, findings 1-204)

**Current Phase**: IDB stabilization (S1c in progress)

## Directory Guide

```
falcon3/
├── README.md           # This file - project overview
├── WORKFLOW.md         # Reverse engineering workflow (for docs/ work)
├── plan.md            # Track E formal decompilation plan
├── status.md          # Track E detailed status (entry point for formal work)
│
├── docs/              # Documentation (both tracks)
│   ├── architecture/  # System-level docs (RE track output)
│   ├── data_formats/  # File format specs
│   ├── workflow/      # Track E procedures
│   ├── findings_log.md # Track E append-only research log
│   └── ...            # Track E detailed docs
│
├── analysis/          # RE track work area
│   ├── ida_scripts/   # IDA automation (critical!)
│   │   └── apply_known_names.py  # Function name registry (RE track)
│   ├── ida_falconcd/  # IDA database
│   ├── sessions/      # Temporary work notes
│   ├── data_samples/  # Extracted data
│   ├── tools/         # Analysis helper scripts
│   └── archive/       # Historical files
│
├── registry/          # Track E formal ledgers (YAML)
│   ├── naming.yaml    # Function name ledger (Track E)
│   ├── structs.yaml   # Data structures
│   └── ...            # Other formal registries
│
├── tools/             # Track E IDA scripts and build tools
│   ├── naming.py      # Track E naming gate
│   ├── verify_rebuild.py  # Track E integrity gate
│   └── ...            # 500+ scripts (many temporary)
│
├── game/              # Original game files (gitignored)
├── rebuild/           # Track E OCaml port (future)
└── src/               # Track E C port work (in progress)
```

## Current Status

### Reverse Engineering Track (Documentation)

**Systems Documented** (as of 2026-11-11):
- ✅ HUD System (100% complete)
- ✅ Terrain System (100% complete)
- 🟢 AI System (90% complete)
- 🟢 Flight Physics (90% complete)
- 🟡 Weapons System (70% complete)
- 🟡 Menu System (60% complete)
- 🟡 File I/O (80% complete)

**Functions Named**: 63 functions with proper descriptive names
- Naming convention: `<system>_<component>_<action>_<detail>`
- Synchronized with IDA: 98.4% success rate
- Location: `analysis/ida_scripts/apply_known_names.py`

**Documentation Quality**: Professional ✅
- Clear system architecture docs
- Data format specifications
- Comprehensive analysis
- Organized directory structure

### Track E (Formal Decompilation)

**Phase**: IDB Stabilization S1c (in progress)
**Functions**: 4,127 total (from IDA analysis)
**Named**: 2,034 in formal ledger (`registry/naming.yaml`)
**Completion**: Level-0 campaign complete (66 functions)

**Current Work**: 
- S1c-7 boundary repairs (split merged functions)
- P1-P6 classification and cleanup
- Function table integrity maintenance

See `status.md` for detailed state.

## Key Differences Between Tracks

| Aspect | RE Documentation Track | Track E Formal Track |
|--------|----------------------|---------------------|
| **Goal** | Understand & document | Rebuild in OCaml |
| **Function Names** | `analysis/ida_scripts/apply_known_names.py` (63) | `registry/naming.yaml` (2,034) |
| **Workflow** | `WORKFLOW.md` | `docs/workflow/` + `status.md` |
| **Output** | `docs/architecture/` markdown | `registry/` YAML + `rebuild/` code |
| **Process** | Learn → Doc → Rename → Commit | Formal convergence gates |
| **Status** | Above summary | `status.md` (comprehensive) |

**Both tracks share**:
- IDA database (`analysis/ida_falconcd/FALCONCD.EXE.i64`)
- Game files (`game/`)
- Some documentation (`docs/`)

## Which Track Should I Use?

### Use RE Documentation Track If:
- ✅ Want to understand a specific system
- ✅ Need to document findings quickly
- ✅ Working on architecture or behavior
- ✅ Adding function names as you discover them
- ✅ Creating system-level documentation

→ Follow `WORKFLOW.md`, update `analysis/ida_scripts/apply_known_names.py`

### Use Track E If:
- ✅ Working on formal decompilation
- ✅ Need byte-level precision
- ✅ Maintaining function ledgers
- ✅ Building the OCaml port
- ✅ Following formal convergence process

→ Follow `status.md` and `plan.md`, update `registry/naming.yaml`

## Getting Started

### For New Contributors (RE Track)
1. Read `WORKFLOW.md` (standard process)
2. Check `analysis/README.md` (directory guide)
3. Review `docs/architecture/` (what's documented)
4. Start with `analysis/ida_scripts/apply_known_names.py` (what we know)

### For Track E Work
1. Read `status.md` (entry point, comprehensive state)
2. Read `plan.md` (formal plan)
3. Check `docs/findings_log.md` (research history)
4. Review `registry/` (formal ledgers)

## Tools Reference

### IDA Automation (RE Track)
```powershell
# Synchronize function names with IDA
cd c:\Users\ybarnoy\projects\falcon3
& "C:\Program Files\IDA Professional 9.1\idat.exe" -A `
  -S"analysis\ida_scripts\apply_known_names.py" `
  "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### Track E Tools
```powershell
# Verify naming ledger
python tools/naming.py check

# Verify IDB integrity
python tools/verify_rebuild.py

# Apply function boundaries
python tools/apply_orphan_funcs.py
```

## Contributing

**Before making changes**:
1. Decide which track you're working in
2. Follow that track's workflow
3. Keep the two tracks' artifacts separate
4. Don't mix naming registries

**Commit standards**:
- RE Track: Commit `docs/ + analysis/ida_scripts/ + report` together
- Track E: Follow formal convergence gates in `status.md`

## Questions?

**General Questions**:
- Check this README first
- Then check the appropriate workflow doc

**RE Track Questions**:
- `WORKFLOW.md` - process
- `analysis/README.md` - directory structure
- `docs/architecture/<system>.md` - system docs

**Track E Questions**:
- `status.md` - current state
- `plan.md` - formal plan
- `docs/workflow/` - detailed procedures
- `docs/findings_log.md` - research history

## Project Philosophy

**RE Track**: Document as we learn, rename immediately, commit together
**Track E**: Formal convergence with gates, ledgers, and byte-level precision

Both approaches are valid and complementary. Use the right tool for the job.

---

*Last updated: 2026-11-11*
