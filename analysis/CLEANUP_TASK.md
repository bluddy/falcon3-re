# Project Cleanup Task - FUTURE WORK

**Priority**: MEDIUM  
**Estimated Time**: 4-6 hours  
**Status**: NOT STARTED

---

## Problem

We have accumulated many scripts, tools, and analysis files across multiple directories. While they were useful for discovery, they now create confusion:

- **analysis/** - 300+ files, many one-off scripts
- **analysis/s4/** - 200+ files from session 4
- **analysis/ida_scripts/** - Starting to accumulate
- **analysis/dgroup/** - Probing scripts
- Multiple Python scripts at analysis root level

**Result**: Hard to find what you need, unclear what's current vs obsolete.

---

## Goal

Create a clean, organized structure where:
- Current/verified tools are easy to find
- Obsolete/experimental code is archived
- Documentation points to the right files
- Future agents know what to use

---

## Cleanup Tasks

### Phase 1: Inventory (1 hour)
- [ ] List all Python scripts in analysis/
- [ ] List all Python scripts in analysis/s4/
- [ ] Categorize by: Active Tool, Archive, Delete
- [ ] Document what each verified tool does

### Phase 2: Reorganize (2 hours)
- [ ] Create **analysis/tools/** for active, verified tools
- [ ] Create **analysis/archive/** for historical/experimental work
- [ ] Move scripts to appropriate locations
- [ ] Update all documentation to reference new paths

### Phase 3: Consolidate (2 hours)
- [ ] Merge duplicate scripts (e.g., multiple address translators?)
- [ ] Create **analysis/tools/README.md** with tool catalog
- [ ] Remove true obsolete code (commented out, broken, superseded)
- [ ] Update .gitignore if needed

### Phase 4: Verify (1 hour)
- [ ] Test that all documented tools still work
- [ ] Update IDA_AUTOMATION_GUIDE.md with new paths
- [ ] Update ADDRESS_TRANSLATION_GUIDE.md with new paths
- [ ] Commit with clear "reorganization" commit message

---

## Proposed Structure

```
analysis/
├── tools/                    # Active, verified tools
│   ├── README.md            # Tool catalog
│   ├── address_translator.py
│   ├── ida/                 # IDA automation
│   │   ├── README.md
│   │   └── *.py scripts
│   └── data/                # Data analysis tools
│       └── *.py scripts
│
├── docs/                    # Current analysis docs
│   ├── *.md (architecture, systems)
│   └── guides/
│       └── *.md (how-to guides)
│
├── archive/                 # Historical work
│   ├── session_4/          # s4/ contents
│   ├── probes/             # dgroup/, other probes
│   └── experiments/        # One-off scripts
│
└── ida_falconcd/           # IDA database (unchanged)
    └── FALCONCD.EXE.i64
```

---

## What to Keep Active

### Definitely Keep in tools/:
- `address_translator.py` - Critical for IDA work
- `segment_map.json` - Complete segment/function map
- IDA scripts that work (extract_idx_dat_loader.py, etc.)

### Archive to archive/:
- One-off analysis scripts (analyze_*.py unless actively used)
- Probe scripts (*_probe.py)
- Experimental/superseded code
- Session-specific work (s4/)

### Delete:
- Truly broken/obsolete scripts
- Duplicate functionality
- Abandoned experiments clearly marked as such

---

## Why Not Now?

**Current Priority**: Keep IDA database synchronized with our knowledge

We need to rename functions/structs in IDA as we learn them, or we'll lose our knowledge. This cleanup can wait - synchronization cannot.

**Rationale**:
- Cleanup is about organization (nice to have)
- IDA sync is about preserving knowledge (critical)
- We can navigate the mess for now
- We cannot recover lost function names later

---

## Trigger Conditions

Do this cleanup when:
- [ ] We finish a major analysis phase (e.g., complete menu system)
- [ ] We start getting confused about what tools to use
- [ ] A new agent joins and can't navigate the structure
- [ ] We have 4+ hours of low-priority time

---

## Success Criteria

After cleanup:
- Any agent can find the address translator in < 30 seconds
- Clear distinction between "use this" and "historical archive"
- Documentation references are all correct
- Git history is preserved (no force pushes)
- All verified tools still work

---

## Notes

- Don't prematurely delete - we might need to reference old work
- Preserve git history - archive, don't delete
- Update docs AFTER moving files, not before
- Test tools after moving to catch broken imports

