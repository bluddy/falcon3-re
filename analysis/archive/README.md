# Archive

**Historical and superseded files**

## Purpose

This directory contains files that are no longer current but kept for historical reference:
- Old session notes
- Superseded analysis documents
- Output files from old tool runs
- Legacy work directories

## Structure

```
archive/
├── old_sessions/       # Historical session notes
├── old_analyses/       # Superseded analysis documents
├── output_files/       # Old .txt and .log output
├── dgroup/            # Legacy analysis directory
├── memdump/           # Old memory dumps
├── traces/            # Old debug traces
├── s1/, s4/           # Legacy segment analysis
├── segsplit/          # Old segment splitting work
└── README.md (this file)
```

## What's Archived

### `old_sessions/`
Session notes that have been completed and promoted to permanent documentation in `docs/`:
- `SESSION_*.md` files
- `*_SESSION*.md` files
- Per-session work logs

**Check these for**: Historical context, how understanding evolved

### `old_analyses/`
Analysis documents that have been superseded by newer, more complete documentation:
- `*_INITIAL.md` - Early findings (now incorporated into system docs)
- `*_PROGRESS*.md` - Progress reports (now complete)
- `*_DISCOVERED.md` - Discovery notes (now documented)
- `*_FINDINGS.md` - Preliminary findings (now verified)

**Check these for**: How analysis progressed, dead ends, alternative approaches

### `output_files/`
Text and log output from old tool runs:
- `*.txt` - Text output from analysis scripts
- `*.log` - Debug and trace logs
- Assembly dumps, hex dumps

**Check these for**: Raw data that might still be useful

### Legacy Directories

#### `dgroup/`
Early analysis of data group segment, exploring startup and data structures.

#### `memdump/`
Memory dumps from running game for dynamic analysis.

#### `traces/`
Debug traces and execution logs.

#### `s1/`, `s4/`
Segment-specific analysis directories from early project phases.

#### `segsplit/`
Early work on splitting executable into segments.

## When to Check Archives

✅ **Check archives when**:
- Need historical context for current work
- Want to see how understanding evolved
- Looking for alternative approaches that might work now
- Need old data or output that might still be relevant

❌ **Don't check archives for**:
- Current system documentation → use `docs/`
- Current function names → use `ida_scripts/apply_known_names.py`
- Current data samples → use `data_samples/`
- Current tools → use `tools/`

## Archive Policy

### What to Archive
- Session notes older than 2 weeks (if promoted to docs)
- Analysis documents superseded by better docs
- Output files from completed work
- Legacy directories no longer actively used

### What NOT to Archive
- Current work-in-progress
- IDA database (always keep current)
- Master function name registry
- Current documentation

### When to Archive
- **Weekly**: Archive session notes that have been promoted
- **Monthly**: Archive superseded analyses
- **Quarterly**: Review and clean up old output files

## Archive Maintenance

### Yearly Review
1. Check if archived files are still useful
2. Consider compressing old directories
3. Remove truly obsolete files (with git history backup)

### Git History
Remember: Even deleted files remain in git history, so:
- ✅ Safe to delete files if truly obsolete
- ✅ Git log shows what was there
- ✅ Can always `git checkout` old versions

## Finding Things in Archives

### By Date
Session notes are dated: `YYYY-MM-DD` format

### By Topic
Look for topic keywords in filenames:
- AI system: `AI_*`, `*_AI_*`
- Terrain: `TERRAIN_*`, `*_TERRAIN_*`
- Weapons: `WEAPONS_*`, `*_WEAPONS_*`

### By Type
- Sessions: `SESSION_*`, `*_SESSION*`
- Progress: `*_PROGRESS*`, `*_STATUS*`
- Initial: `*_INITIAL*`, `*_DISCOVERED*`

## Restoring from Archive

If you find something in archive that's still useful:
1. **Copy** (don't move) to active location
2. **Update** to current standards
3. **Integrate** with current documentation
4. **Keep** original in archive for history

## Archive vs. Git History

**Archive**: Quick access to recent old files  
**Git History**: Permanent record of everything

Use archive for files you might need to reference in near future. For older history, use git log and checkout.

## Questions?

- **Need current docs?** → Check `docs/`
- **Need current tools?** → Check `tools/`
- **Need function names?** → Check `ida_scripts/apply_known_names.py`
- **Can't find something?** → Try `git log` and `git checkout`

---

**Remember**: Archives are historical. For current work, check `docs/` and active analysis directories.

---

*Last updated: 2026-11-11*
