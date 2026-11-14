# IDA Naming Process - CRITICAL WORKFLOW

**Priority**: CRITICAL  
**Last Updated**: 2026-11-14  
**Purpose**: Ensure IDA database stays synchronized with our knowledge

---

## The Problem We're Solving

As we reverse engineer Falcon 3.0, we learn what functions do. If we don't immediately apply this knowledge to the IDA database, **we lose it**. 

Later agents won't know:
- What file_open does
- Where menu initialization happens  
- Which function loads AI data

**The IDA database is our permanent knowledge store.**

---

## The Solution: Continuous Synchronization

### Rule #1: Learn → Document → Rename (Immediately)

When you discover what a function does:

1. **Document it** in analysis/*.md files
2. **Add to naming script** (`apply_known_names.py`)
3. **Run the script** to update IDA
4. **Commit both** documentation and IDA changes

**Do this in the SAME session** - don't defer!

---

## Quick Reference

### When You Learn a Function Name:

```python
# 1. Edit analysis/ida_scripts/apply_known_names.py
# Add to KNOWN_FUNCTIONS dict:
0xADDRESS: "descriptive_name",  # Brief comment

# 2. Run the script
cd C:\Users\ybarnoy\projects\falcon3
"C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\apply_known_names.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"

# 3. Check the report
Get-Content analysis\ida_naming_report.json

# 4. Commit everything
git add analysis/ida_scripts/apply_known_names.py
git add analysis/ida_naming_report.json
git add docs/architecture/SYSTEM.md  # or whatever you updated
git commit -m "IDA: Renamed function_name based on analysis"
```

---

## Naming Conventions

### Functions

**Pattern**: `system_action_target`

**Examples**:
- `file_open` - File I/O system, open action
- `ui_menu_panel_init` - UI system, menu subsystem, panel target, init action
- `idx_dat_loader` - Resource system, loads .IDX/.DAT pairs
- `vga_dac_palette_upload` - Graphics system, VGA DAC subsystem, palette upload

**Avoid**:
- Generic names: `func1`, `helper`, `util`
- Unclear abbreviations: `fop`, `mnu`, `ld`
- Implementation details: `uses_int21h_3d`

**Use**:
- What it does: `file_open` (not `dos_int21_3d`)
- System context: `ui_menu_controller` (not `menu_func`)
- Clear purpose: `idx_dat_loader` (not `load_data`)

### Data Structures

**Pattern**: `system_purpose_data`

**Examples**:
- `menu_current_id` - Current menu ID
- `ai_behavior_flags` - AI behavior flag array
- `vga_palette_buffer` - VGA palette data

### Globals

**Pattern**: `g_system_name`

**Examples**:
- `g_current_mission` - Global current mission pointer
- `g_player_aircraft` - Global player aircraft state

---

## Current Knowledge (Applied to IDA)

### File I/O System ✓
- `file_open` (0x226BD) - Open file
- `file_close` (0x226E4) - Close file
- `file_read` (0x226F5) - Read from file
- `file_write` (0x2271F) - Write to file
- `file_lseek` (0x2274D) - Seek to offset

### .IDX/.DAT Loaders ✓
- `idx_dat_loader` (0x1297F0) - PICFONT loader
- `madfont_idx_loader` (0x1397CE) - madfont loader
- `squad_file_handler` (0x6A651) - SQUAD files (46 refs!)
- `harpoon_dat_loader` (0x1779A6) - HARPOON.DAT

### Menu System ✓
- `ui_menu_controller` (0x683C5) - Main controller (4169 bytes)
- `ui_menu_panel_init` (0x66E62) - Panel initialization
- `ui_menu_page_setup` (0x6A5BD) - Page setup
- `ui_slot_record_fill` (0x6798C) - Fill loadout record
- `ui_menu_transition_step` (0x67BAF) - Menu transitions
- `farobj_pos_move_angle_step` (0x4AEC4) - 3D model rotation

### Graphics System ✓
- `vga_dac_palette_upload` (0x4F271) - Upload palette

### Overlay System ✓
- `overlay_file_open` (0x2AEA9) - Open overlay file
- `overlay_segment_load` (0x2AC4C) - Load overlay segment

**Total Functions Named**: 19

---

## What Still Needs Names

### High Priority (Discovered but Not Yet Named)

From FILE_IO_ANALYSIS.md:
- `sub_4F3EC` (0x4F3EC) - Unknown graphics function (called by many menu functions)
- DOS operations at other addresses (delete, find_first, find_next)

From MENU_SYSTEM_CODE_STRUCTURE.md:
- Menu state machine handlers
- Menu event dispatchers

From AI_SYSTEM_STATUS.md:
- AI behavior dispatcher functions
- AI context management
- farptr_table_get implementation (when found)

### Investigation Needed
- RLE decompression function (search for 6-byte header processing)
- op_dispatch_far_entry and its operations
- Campaign/mission loading system

---

## Verification

### After Running apply_known_names.py:

1. **Check the report**:
```powershell
Get-Content analysis\ida_naming_report.json | ConvertFrom-Json
```

2. **Look for**:
- `renamed`: How many functions got new names
- `already_correct`: How many were already named
- `failed`: Any failures (investigate these!)

3. **Test in IDA** (optional):
```
Open IDA GUI
Press G (goto)
Type: file_open
Should jump to 0x226BD
```

---

## Integration with Analysis Workflow

### Standard Analysis Session Flow:

```
1. Investigate system (e.g., file I/O)
   ↓
2. Document findings (e.g., FILE_IO_ANALYSIS.md)
   ↓
3. Identify functions (addresses + purposes)
   ↓
4. Add to apply_known_names.py
   ↓
5. Run naming script
   ↓
6. Commit documentation + script + report
   ↓
7. Continue analysis (names now in IDA!)
```

**Don't skip steps 4-6!** Future work depends on these names.

---

## Maintenance

### Weekly (or after major discoveries):

Run naming script even if you didn't add new names:
- Verifies IDA database integrity
- Catches any names that got lost
- Updates the report

### When Starting New Analysis:

Check `ida_naming_report.json`:
- See what's already named
- Avoid re-discovering known functions
- Build on existing knowledge

### Before Major Commits:

Run the script to ensure IDA is up-to-date:
```bash
# Update IDA names
idat.exe -A -S"analysis\ida_scripts\apply_known_names.py" "database.i64"

# Commit together
git add analysis/ida_scripts/apply_known_names.py
git add analysis/ida_naming_report.json
git add docs/...  # your documentation
git commit -m "System X: Complete analysis and update IDA names"
```

---

## Adding New Systems

When you start analyzing a new system:

1. **Create system document** (e.g., `WEAPON_SYSTEM.md`)
2. **Add section to apply_known_names.py**:
```python
# Weapon System (from WEAPON_SYSTEM.md)
0xADDR1: "weapon_fire",
0xADDR2: "weapon_reload",
0xADDR3: "weapon_select",
```
3. **Run naming script**
4. **Document in this file** (IDA_NAMING_PROCESS.md)

---

## Common Issues

### Issue: "Function already named differently"

**Symptom**: Script reports failure or current_name != desired name

**Cause**: IDA has old/incorrect name

**Fix**: Script will rename it automatically. If it fails, manually rename in IDA GUI first, then re-run script.

### Issue: "Not a function"

**Symptom**: Script says address is not a function

**Cause**: 
- Address is wrong (typo?)
- Address is a label within a function
- IDA didn't recognize it as a function

**Fix**:
1. Verify address with `analysis/s4/address_translator.py`
2. Check if it's a secondary entry point (57% of functions!)
3. If needed, create function in IDA: Press 'P' at address

### Issue: "Names got lost after IDA reload"

**Symptom**: Functions are back to sub_XXXXX

**Cause**: Names not committed to IDA database properly

**Fix**: Re-run `apply_known_names.py` - it's idempotent!

---

## Success Metrics

**Good IDA Database**:
- ✅ 100+ functions with descriptive names
- ✅ All core systems have named entry points
- ✅ Comments explain what functions do
- ✅ Naming report shows <5% failures

**Bad IDA Database**:
- ❌ Most functions still sub_XXXXX
- ❌ No comments
- ❌ Have to re-discover what functions do
- ❌ Future agents waste time

---

## Files Involved

**Master Script**:
- `analysis/ida_scripts/apply_known_names.py` - Applies all knowledge

**Reports**:
- `analysis/ida_naming_report.json` - Last run results

**Documentation (Sources of Knowledge)**:
- `analysis/FILE_IO_ANALYSIS.md`
- `analysis/MENU_SYSTEM_CODE_STRUCTURE.md`
- `analysis/AI_SYSTEM_STATUS.md`
- `docs/architecture/*.md`

**Database**:
- `analysis/ida_falconcd/FALCONCD.EXE.i64` - The IDA database itself

---

## Quick Troubleshooting

**Script hangs**: Missing `qexit(0)` call (check script)  
**No report**: Check file paths in script  
**Names not applied**: Run script again (idempotent)  
**IDA won't open**: Database might be locked (close other IDA instances)

---

## Next Steps

As we continue analysis:

1. **AI System** (90% complete):
   - Name behavior dispatcher functions
   - Name context management functions
   - Name farptr_table_get (when found)

2. **Menu System** (Phase 2 complete):
   - Name remaining menu handlers
   - Name event dispatchers

3. **File I/O** (System identified):
   - Name RLE decompression function
   - Name op_dispatch_far_entry operations

**Remember**: Learn → Document → Rename → Commit!

---

**This process is CRITICAL for long-term success.**

Without it, we re-discover the same functions over and over.

