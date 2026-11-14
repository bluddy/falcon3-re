# Tools Directory

**Track E IDA scripts and build tools**

## Overview

This directory contains 500+ Python scripts for Track E (formal decompilation). Most are **one-off scripts** for specific analysis tasks during IDB stabilization.

## File Organization

### Production Tools (No `_` prefix)
**Reusable, maintained scripts**

These are the core tools used regularly:
- `naming.py` - Track E naming ledger gate (verifies `registry/naming.yaml`)
- `verify_rebuild.py` - Track E IDB integrity gate
- `verify_idb.py` - IDB semantic verification
- `apply_orphan_funcs.py` - Apply function boundary fixes
- `export_*.py` - Export data from IDA for analysis
- `parse_*.py` - Parse game file formats
- `plot_*.py` - Generate visualizations

**Total**: ~210 production scripts

### Temporary/One-Off Tools (`_` prefix)
**Session-specific or experimental scripts**

These were created for specific analysis tasks and may not be reusable:
- `_append_naming*.py` - One-off naming batch scripts (80+ files)
- `_append_routines*.py` - One-off routine batch scripts (80+ files)
- `_derive_*.py` - Level derivation scripts (50+ files)
- `_docs*.py` - Documentation generation scripts (40+ files)
- `_diag_*.py` - Diagnostic/debugging scripts
- `_probe_*.py` - Exploratory analysis scripts
- Other single-use analysis scripts

**Total**: ~285 temporary scripts

## Which Tools Should I Use?

### For RE Documentation Track
**You probably don't need these tools** - use `analysis/tools/` instead.

Track E tools are for formal decompilation work (IDB stabilization, ledger maintenance, byte-level verification).

**Exception**: File format parsers (`parse_*.py`) may be useful.

### For Track E Work
1. **Gates** (run these regularly):
   - `naming.py check` - Verify naming ledger
   - `verify_rebuild.py` - Verify IDB integrity
   - `verify_idb.py` - Semantic IDB check

2. **IDB Mutation** (apply fixes):
   - `apply_orphan_funcs.py` - Apply function boundaries
   - `apply_*.py` - Various IDB fix applicators

3. **Analysis** (extract data):
   - `export_*.py` - Export IDA data
   - `parse_*.py` - Parse game files
   - `analyze_*.py` - Analyze extracted data

4. **Visualization**:
   - `plot_*.py` - Generate SVG visualizations
   - Mostly for ISLDAT terrain data

## Temporary Files Status

### Should Temporary Files Be Deleted?

**NO** - they are historical record:
- ✅ Show how analysis progressed
- ✅ May be needed to reproduce findings
- ✅ Git history preserves them anyway
- ✅ Not causing harm (just clutter)

### But They're Hard to Navigate!

**Solution**: Ignore `_*.py` files when browsing:
- They're one-off scripts
- Check production tools first
- Only look at `_` files if reproducing historical work

## Production Tool Categories

### 1. Gates (Quality Control)
**Run these to verify state**:
- `naming.py check` - Naming ledger consistency
- `verify_rebuild.py` - IDB integrity vs. ground truth
- `verify_idb.py` - Semantic IDB verification

### 2. IDB Mutation (Apply Fixes)
**Scripts that modify the IDA database**:
- `apply_orphan_funcs.py` - Function boundary fixes
- `apply_fixups_ida.py` - Overlay fixup application
- `apply_flow_fixes.py` - Control flow repairs
- `apply_rebase_fixes.py` - Address rebase fixes
- `apply_variant_selectors.py` - Variant disambiguation
- `add_*.py` - Various IDB additions

### 3. IDB Export (Extract Data)
**Scripts that read IDA and export data**:
- `export_callrefs.py` - Call graph extraction
- `export_ds_facts.py` - Data segment facts
- `export_segments_simple.py` - Segment map
- `export_farcalls.py` - Far call sites
- `export_epilogues.py` - Function epilogues

### 4. Analysis (Process Extracted Data)
**Scripts that analyze exported data**:
- `analyze_*.py` - Various analysis tasks
- `callgraph_bottomup.py` - Build call graph
- `classify_*.py` - Classification tasks
- `mine_traces.py` - Process runtime traces

### 5. Game File Parsing
**Scripts that parse original game files**:
- `parse_isldat.py` - Island terrain data parser
- `parse_fixup_tables.py` - Overlay fixup tables
- `mzparse.py` - DOS MZ executable parser

### 6. Visualization
**Scripts that generate SVG visualizations**:
- `plot_isldat_*.py` - Terrain visualizations (many versions)
- `extract_isldat_coast_edges.py` - Coastline extraction
- Various terrain rendering scripts

### 7. Build Tools
**Tools for C/OCaml compilation**:
- `compile_msc51.py` - Microsoft C 5.1 compiler wrapper
- `compile_msc6_ref.py` - MSC 6.0 reference
- `splice.py` - Splice compiled code into original EXE

### 8. RTLink/Overlay Tools
**Tools for overlay system analysis**:
- `rtlink_scan.py` - RTLink directory scanner
- `map_overlays.py` - Overlay mapping
- `rebuild_overlay_segments.py` - Overlay segment builder
- Various fixup and thunk tools

## Common Workflows

### Verify Project State (Track E)
```bash
cd tools
python naming.py check          # Verify naming ledger
python verify_rebuild.py        # Verify IDB integrity
python verify_idb.py            # Semantic check
```

### Extract Call Graph
```bash
# In IDA (headless)
python export_callrefs.py

# Process extracted data
cd tools
python callgraph_bottomup.py
```

### Parse Game Files
```bash
cd tools
python parse_isldat.py ../game/ISLDAT.ISR  # Parse terrain
python mzparse.py ../game/FALCONCD.EXE     # Parse executable
```

### Generate Visualization
```bash
cd tools
python plot_isldat_final_v7.py  # Generate terrain SVG
```

## Tool Dependencies

Most tools use only Python standard library. Some require:
- **IDA Pro**: Scripts with `ida*` imports (run in IDA)
- **numpy/matplotlib**: Visualization scripts
- **yaml**: Ledger manipulation scripts

## Historical Context

### Why So Many Temporary Files?

Track E follows a **formal convergence process** with many small, verifiable steps:
- Each finding (204 total) may need custom scripts
- Batches (Level-0 through Level-21) each have custom tools
- IDB stabilization phases (S1a-S1c-7, etc.) each need scripts
- Diagnostic scripts for investigating specific issues

This is **intentional and correct** - each step is isolated and reproducible.

### File Naming Convention

**Production**: `verb_noun.py` (e.g., `export_callrefs.py`)
**Temporary**: `_context_description.py` (e.g., `_append_naming_l1a.py`)

The `_` prefix signals "this was for a specific task, don't expect it to work in other contexts".

## Future Cleanup

**When Track E is complete**:
1. Archive temporary scripts to `tools/archive/`
2. Keep production tools in `tools/`
3. Document the 20-30 most important tools
4. Create a "greatest hits" guide

**For now**: Leave as-is, they're not causing problems.

## Questions?

**For RE Track**: Use `analysis/tools/` instead
**For Track E**: Read `status.md` and `docs/workflow/`
**For specific tools**: Check script docstring or ask

---

*Note: This directory is for Track E (formal decompilation). For reverse engineering documentation work, see `analysis/tools/`.*

---

*Last updated: 2026-11-11*
