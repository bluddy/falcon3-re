---
inclusion: auto
name: project-workflow-rules
description: Core workflow rules for Falcon 3.0 reverse engineering project
---

# Falcon 3.0 Project Workflow Rules

**Purpose:** Establish consistent workflow for reverse engineering, renaming, documentation, and synchronization.

**Apply:** Every time code analysis is performed, functions are discovered, or understanding is improved.

---

## Rule 1: IDA Automation Knowledge

**Learn from:** `docs/IDA_AUTOMATION_GUIDE.md` and related documentation

**Before using IDA automation:**
1. Read `docs/IDA_AUTOMATION_GUIDE.md` to understand proper workflows
2. Use Python scripts (NOT IDC) for all automation
3. Always use batch mode: `idat.exe -A -S"script.py" "database.i64"`
4. Always call `idaapi.auto_wait()` at script start
5. Always call `idc.qexit(0)` at script end
6. Save results to JSON files for later analysis
7. Check exit codes and log files to verify success

**Never:**
- Skip `idaapi.auto_wait()` (causes incomplete analysis)
- Skip `idc.qexit(0)` (IDA hangs)
- Use interactive mode for batch operations
- Assume operations succeeded without checking logs

---

## Rule 2: Rename Everything You Learn

**When you discover a function's purpose, immediately rename it in IDA.**

### Renaming Criteria

**Rename if:**
- Function purpose is understood (even partially)
- Current name is generic (sub_XXXXX, undoc_XXXXX)
- Better name reflects actual behavior
- Name would help future analysis

**Don't rename if:**
- Purpose is still completely unclear
- Current name is already descriptive and accurate
- Name is a placeholder waiting for better understanding

### Naming Conventions

**Functions:**
- Use descriptive snake_case: `squadron_mission_file_loader`
- Include subsystem prefix when clear: `input_device_calibration_init`
- Include key behavior: `string_concatenate`, `int_to_string_converter`
- For coordinators/dispatchers: `menu_dispatcher_19ops`, `game_mode_r48_main_coordinator`

**Globals:**
- Use descriptive names with type suffix: `mission_slot_array`, `graphics_mode_flag`
- Include segment if relevant: `dword_79D3E` → `mission_slots_far_ptr`

**Structs:**
- Use PascalCase: `MissionSlot`, `TaskRecord`, `SquadronFile`
- Include size in comment: `MissionSlot // 20 bytes`

### Renaming Process

1. **Read actual disassembly first** (never rename based on patterns alone!)
2. Create IDA Python script: `rename_XXXXXX.py`
3. Use `idc.set_name(addr, new_name, idc.SN_CHECK)`
4. Add function comment with `idc.set_func_cmt(addr, comment, False)`
5. Add inline comments at key locations with `idc.set_cmt(addr, comment, False)`
6. Run script in batch mode
7. Verify success in log file (exit code 0)

---

## Rule 3: Always Update Registry and Sync with IDA

**Registry is the source of truth for all discovered knowledge.**

### After Every Analysis Session

**Update registry/functions.yaml:**
```yaml
- address: 0xXXXXXX
  name: descriptive_function_name
  system: subsystem_name
  size: bytes
  callers: count
  rank: N  # if from top-100 analysis
  doc: 'Detailed description of purpose, behavior, patterns, key findings.'
  source: 'Analysis document reference'
```

**Update registry/structs.yaml** (when structures are discovered):
```yaml
- name: StructureName
  size: bytes
  offset: 0xXXXXXX  # if at known address
  doc: 'Structure purpose and layout'
  fields:
    - offset: 0x00
      name: field_name
      type: uint8_t
      doc: 'Field purpose'
```

### Synchronization Checklist

After analysis session, verify:
- [ ] All renamed functions added to `registry/functions.yaml`
- [ ] All renamed globals added to `registry/globals.yaml` (if exists)
- [ ] All discovered structs added to `registry/structs.yaml`
- [ ] IDA database updated with renames and comments
- [ ] IDA operations verified in log files
- [ ] Documentation updated (see Rule 4)

**Create sync status document** after major sessions:
- `analysis/SYNC_STATUS_YYYY-MM-DD.md`
- Lists all IDA operations
- Lists all registry updates
- Lists all documentation updates
- Verification checklist

---

## Rule 4: Keep Documentation Complete and Current

**docs/architecture/ must reflect complete understanding of the codebase.**

### Documentation Structure

**Core architecture documents:**
- `docs/architecture/index.md` - Quick reference, key addresses, sub-document index
- `docs/architecture/*.md` - Subsystem-specific documentation (binary, game_loop, entity, etc.)

**Analysis documents:**
- `analysis/*.md` - Detailed analysis of specific functions or systems
- `analysis/TOP_100_PROGRESS.md` - Progress tracking for systematic analysis

### Update Triggers

**Update docs/architecture/index.md when:**
- New key addresses discovered
- New subsystems identified
- Major architectural patterns found

**Update subsystem docs when:**
- Function purposes clarified
- Data structures decoded
- Control flow understood
- File formats discovered

**Create new analysis docs when:**
- Deep diving into specific function (e.g., `SQUADRON_MISSION_FILE_LOADER_ANALYSIS.md`)
- Investigating related function group (e.g., `CALLEE_ANALYSIS_FINDINGS.md`)
- Documenting discovery process

### Documentation Quality Standards

**Every doc must have:**
1. **Status header**: PROVEN / STRONG / HYPOTHESIS / UNKNOWN certainty levels
2. **Date stamp**: Last updated date
3. **Cross-references**: Link to related docs, IDA addresses, registry entries
4. **Evidence**: Quote disassembly, reference files, show proof
5. **Next steps**: Clear action items for further investigation

**When updating existing docs:**
- Update "Last updated" date
- Update status/certainty if new evidence found
- Add new sections rather than deleting old ones (show progression)
- Update progress percentages if specified

### Key Addresses Tracking

**Always add to docs/architecture/index.md "Key Addresses" table:**
```markdown
| Address | Name | Description |
|---------|------|-------------|
| 0xXXXXXX | function_name | Brief description (size, callers, key behavior) |
```

---

## Rule 5: Workflow for Each Analysis Session

**Standard workflow to follow every time:**

### 1. Preparation
- Read relevant docs/architecture/*.md to understand current knowledge
- Check `analysis/TOP_100_PROGRESS.md` for next function to analyze
- Review IDA database for function's current name and state

### 2. Analysis
- Extract disassembly using IDA Python script
- Read ACTUAL code (never guess based on size/callers alone!)
- Document findings in analysis/*.md
- Identify callees and their purposes
- Discover data structures, globals, patterns

### 3. Naming
- Choose descriptive names for functions, globals, structs
- Create IDA Python rename script
- Add function comments and inline comments
- Run script and verify success

### 4. Registry Update
- Add all new discoveries to registry/functions.yaml
- Add structs to registry/structs.yaml
- Include: address, name, system, size, callers, doc, source

### 5. Documentation Update
- Update relevant docs/architecture/*.md files
- Add key addresses to docs/architecture/index.md
- Create detailed analysis doc if deep dive
- Update progress tracking

### 6. Synchronization Verification
- Create SYNC_STATUS_YYYY-MM-DD.md for major sessions
- Verify IDA database, registry, and docs all match
- Check all rename operations succeeded
- Confirm all comments added

### 7. Next Steps
- Document what to investigate next
- Identify gaps in understanding
- Note dependencies on other analysis

---

## Rule 6: Never Rename Without Reading Code

**CRITICAL LESSON from Rank #9 analysis:**

**WRONG approach:**
- Look at function size, caller count, name pattern
- Guess purpose based on similar functions
- Rename without reading actual disassembly
- Result: Completely incorrect name (r03_screen_coordinator ≠ input_device_calibration_init)

**CORRECT approach:**
1. Extract actual disassembly via IDA script
2. Read the assembly code line by line
3. Identify callees, string references, data accesses
4. Count actual callees (not estimated from size)
5. Understand control flow and purpose
6. THEN choose appropriate name
7. Document the evidence in analysis doc

**If you cannot read the actual code:**
- Do NOT rename the function
- Mark it as pending investigation
- Come back when you can extract disassembly

---

## Rule 7: Deep Dive on Important Functions

**When to do a deep dive:**
- High caller count (top 100)
- Central coordinator/dispatcher functions
- File I/O operations
- Exclusive helpers (0 other callers - reveals tight coupling)
- Large functions with complex behavior

**Deep dive process:**
1. Extract full disassembly (all lines)
2. Analyze all callees (not just the function itself)
3. Map control flow branches
4. Document data structures accessed
5. Identify memory segments used
6. Reconstruct C pseudocode
7. Create comprehensive analysis document (5,000+ words)
8. Update all related documentation

**Callee analysis reveals:**
- Exclusive helpers show tight coupling
- High-traffic callees show central APIs
- Call hierarchy shows architecture layers

---

## Rule 8: Track Progress Systematically

**Use analysis/TOP_100_PROGRESS.md for systematic coverage:**

**Update after each function:**
- Mark function as ✅ Completed
- Update percentage (X/100)
- Add one-line summary
- Note if deep dive performed

**Milestones:**
- 25/100 (25%) - Quarter complete
- 50/100 (50%) - Half complete (current target)
- 75/100 (75%) - Three quarters
- 100/100 (100%) - Full coverage

**Track patterns:**
- Phase 1 vs Phase 2 functions
- Mega-coordinators vs specialized handlers
- Transition points
- Architecture insights

---

## Rule 9: Handle Errors and Failures

**When IDA script fails:**
1. Check `ida_*.log` file for error message
2. Common issues:
   - Missing `import idautils` (add it)
   - Missing `idaapi.auto_wait()` (add it)
   - Missing `idc.qexit(0)` (add it)
   - Wrong field names (check IDA API docs)
3. Fix script and re-run
4. Never proceed without verifying success

**When rename fails:**
- Check if name already exists
- Check if name has invalid characters
- Try alternate name
- Document why original name didn't work

**When analysis is blocked:**
- Document what's blocking (missing data, unclear code)
- Mark function as partially analyzed
- Move to next function
- Come back when more context available

---

## Rule 10: Maintain Certainty Levels

**Always mark findings with certainty:**

- **PROVEN**: Byte-level verification, confirmed in multiple sources
- **STRONG**: Multi-signal evidence, high confidence
- **HYPOTHESIS**: Single-signal, logical inference, needs verification
- **UNKNOWN**: No current understanding

**Update certainty as evidence accumulates:**
- HYPOTHESIS → STRONG when second source confirms
- STRONG → PROVEN when byte-level verified
- Document what evidence changed certainty

---

## Quick Reference Checklist

Every analysis session:
- [ ] Read docs/IDA_AUTOMATION_GUIDE.md workflow
- [ ] Extract actual disassembly (never guess!)
- [ ] Rename functions/globals/structs in IDA
- [ ] Add comments (function-level + inline)
- [ ] Update registry/functions.yaml
- [ ] Update docs/architecture/*.md
- [ ] Add key addresses to index.md
- [ ] Create analysis/*.md if deep dive
- [ ] Update TOP_100_PROGRESS.md
- [ ] Verify all operations in log files
- [ ] Create SYNC_STATUS doc if major session

---

**These rules ensure:**
1. Consistent methodology across all analysis
2. Complete documentation of discoveries
3. Synchronized state (IDA ↔ Registry ↔ Docs)
4. Traceable evidence for all claims
5. Systematic progress toward full understanding

**Follow these rules on every session. No exceptions.**

