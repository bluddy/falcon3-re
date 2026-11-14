# Analysis Directory Reorganization Plan

## Current Problem

The analysis directory has 200+ files with no clear organization:
- Session notes mixed with permanent findings
- Multiple versions of the same document
- ISLDAT visualization files scattered everywhere
- Python scripts mixed with markdown
- No clear separation between work-in-progress and completed analysis

## New Structure

```
analysis/
├── ida_scripts/              # IDA automation (KEEP AS-IS)
│   ├── apply_known_names.py
│   ├── extract_function.py
│   └── README.md
│
├── ida_falconcd/            # IDA database and exports (KEEP AS-IS)
│   └── FALCONCD.EXE.i64
│
├── sessions/                # Per-session work notes (NEW)
│   ├── 2026-11-10_ai/
│   ├── 2026-11-10_terrain/
│   ├── 2026-11-11_hud/
│   └── README.md           # "Session notes are temporary, promote to docs/ when done"
│
├── data_samples/           # Extracted game data (NEW)
│   ├── isldat/            # All ISLDAT visualization files
│   │   ├── coast_edges/
│   │   ├── clean_coasts/
│   │   ├── rivers/
│   │   ├── tiles/
│   │   └── svgs/
│   ├── ai_contexts/       # AI memory dumps
│   ├── mission_files/     # Parsed mission data
│   └── README.md
│
├── tools/                  # Analysis scripts (NEW)
│   ├── address_translator.py
│   ├── segment_map.json
│   ├── data_parsers/      # All parse_*.py and decode_*.py
│   ├── data_extractors/   # All extract_*.py and analyze_*.py
│   └── README.md
│
├── archive/               # Superseded documents (NEW)
│   ├── old_sessions/      # Old session summaries
│   ├── old_analyses/      # Superseded analysis docs
│   └── README.md         # "These are historical, check docs/ for current"
│
├── ida_naming_report.json # Latest IDA sync (KEEP)
├── CLEANUP_TASK.md       # Future work (KEEP)
└── README.md             # Directory guide (NEW)
```

## Files to Move

### Session Notes → sessions/
All `SESSION_*.md`, `*_SESSION*.md` files

### ISLDAT Data → data_samples/isldat/
- All `isldat_*` directories
- All `isldat_*.svg` files
- `ISLDAT_*.md` → docs/data_formats/ (specs stay in docs)

### AI Data → data_samples/ai_contexts/
- `ai_contexts_*.bin`
- Memory dump files

### Tools → tools/
- All `parse_*.py`
- All `decode_*.py`
- All `extract_*.py`
- All `analyze_*.py`
- All `find_*.py`
- `segment_map.json`, `address_translator.py`

### Archive → archive/
- Duplicate analysis files (keep latest only)
- Old session summaries (superseded)
- Experimental findings (not confirmed)

### Keep in docs/
- System-level permanent docs (AI, weapons, terrain, etc.)
- Data format specifications
- Architecture documents

## Files Status

### Keep in analysis/ root:
- ✅ `ida_naming_report.json` - latest sync results
- ✅ `CLEANUP_TASK.md` - future work tracker

### Move to docs/systems/:
- ✅ All `*_SYSTEM*.md` files (if final)
- ✅ All `*_COMPLETE*.md` files
- ✅ All `*_ANALYSIS.md` files (if final)

### Move to sessions/:
- ✅ All `SESSION_*.md`
- ✅ All `*_SESSION*.md`
- ✅ Work-in-progress notes

### Move to archive/:
- ✅ Duplicate/old versions
- ✅ `.txt` output files
- ✅ `.log` files

## Execution Steps

1. Create new directory structure
2. Move ISLDAT data samples
3. Move AI data samples
4. Move tools/scripts
5. Move session notes
6. Archive old/duplicate files
7. Create README.md files
8. Update WORKFLOW.md if needed
9. Commit reorganization

## Benefits

✅ **Findability**: Clear location for each type of file  
✅ **Clarity**: Separation of temporary vs. permanent  
✅ **Maintainability**: Easy to clean up sessions  
✅ **Professionalism**: Organized project structure  
✅ **Efficiency**: Don't waste time searching for files  

---

*Plan created: 2026-11-11*
