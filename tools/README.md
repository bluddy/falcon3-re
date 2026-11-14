# Tools Directory (Legacy)

**Historical IDA scripts from earlier project phase**

## Status: Legacy

This directory contains 500+ Python scripts from an earlier, more formal phase of the project. **Most of these are now superseded by the simpler approach in `analysis/ida_scripts/`**.

## Current Tools

**For active reverse engineering work, use:**
- `analysis/ida_scripts/apply_known_names.py` - Master function registry (use this!)
- `analysis/tools/` - Helper scripts for parsing and analysis

**This directory is kept for:**
- Historical reference
- File format parsers that may still be useful
- Understanding how we got here

## What's Here

### Production Tools (~210 files, no `_` prefix)
Scripts that were actively used and may still be useful:
- `parse_*.py` - Game file format parsers (some still useful)
- `export_*.py` - IDA data exporters
- `plot_*.py` - Visualization generators (mostly ISLDAT terrain)

### Temporary Tools (~285 files, `_` prefix)
One-off scripts for specific analysis tasks:
- `_append_naming*.py` - Batch naming scripts (80+ files)
- `_derive_*.py` - Level derivation scripts (50+ files)  
- `_docs*.py` - Documentation generators (40+ files)
- Various diagnostic and probe scripts

## Why Keep These?

1. **Historical record** - Shows how analysis progressed
2. **File format parsers** - Some are still the best way to parse certain formats
3. **Techniques** - Examples of how to extract data from IDA
4. **Git history** - Already committed, not worth removing

## Should I Use These?

**Probably not.** The current workflow is simpler and more effective:
- Use `analysis/ida_scripts/apply_known_names.py` for function naming
- Use `analysis/tools/` for parsing and extraction
- Write new simple scripts instead of trying to understand these

## Historical Context

These tools were created during an attempt at formal, byte-perfect decompilation with:
- Formal convergence gates
- Function ledgers in YAML
- Integrity verification at each step
- 204 numbered findings with custom tools for each

**That approach was abandoned in favor of the current pragmatic approach**, which has successfully documented 9+ major systems.

## Useful Parsers

If you need to parse game files, these may still be helpful:
- `parse_isldat.py` - Island terrain data (fully working)
- `mzparse.py` - DOS executable parser
- File format parsers in general

For everything else, prefer simpler new scripts in `analysis/tools/`.

---

*This directory is legacy. Use `analysis/ida_scripts/` and `analysis/tools/` for current work.*
