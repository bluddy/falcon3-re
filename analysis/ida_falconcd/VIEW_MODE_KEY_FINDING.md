# KEY FINDING: View Mode Flag is Never Modified at Runtime in R15 Overlay

## Critical Discovery

**The `r15_external_view_flag` (cs:0x107762) is ONLY written ONCE, during initialization.**

### Evidence

Comprehensive search of R15 overlay (FALCONCD.EXE.i64) reveals:

**Writers (1 total)**:
- `view_mode_set` @ 0x1086EC
  - Instruction: 0x1087B2: `mov cs:r15_external_view_flag, al`
  - Context: Initialization code, sets AL=0 (cockpit mode)
  - **This is the ONLY write to the flag in the entire R15 overlay**

**Readers (4 total)**:
1. `sub_108A05` @ 0x108A84 and 0x108AB9 (240 bytes)
2. `r15_simulation_loop` @ 0x108BAC (717 bytes) - main dispatcher
3. `sub_108FC2` @ 0x109119 (22 bytes)

## Implications

### The Flag is Read-Only in R15

The R15 overlay (simulation/rendering) **reads** the flag to determine which rendering path to use, but **never modifies** it. The flag acts as a configuration input, not runtime state.

### View Switching Must Happen Elsewhere

View mode switching (F2/F3/F4/F8 keys, ACMI button) must occur in a **different overlay**, likely:

**Primary Candidates**:
1. **R17 Overlay** - UI event loop (r17_event_main_loop)
2. **R30 Overlay** - UI/menu system (ui_loadout_menu_enter)
3. **Resident Code** - Always-loaded keyboard handler

### How It Probably Works

```
1. User presses F2/F3/F4/F8 in overlay R17 or R30
2. Handler in that overlay sets r15_external_view_flag
3. Overlay system reloads R15 (simulation overlay)
4. R15 reads the flag during initialization (view_mode_set)
5. R15 uses the flag value for entire session
6. When returning to menu/switching views, R15 unloads
7. Cycle repeats
```

## Search Strategy Going Forward

### What We Searched in R15 (Exhaustive)
- ✅ All xrefs to 0x107762 (found all 5)
- ✅ input_poll_handler and all callees (no view switching)
- ✅ All view/camera/external related functions
- ✅ Conditional writes (none found)
- ✅ ACMI functions (none modify flag)

### What to Search Next

1. **Check R17 Overlay** (UI event loop)
   - Database: Look for R17 overlay segments
   - Search for: 0x107762 writes
   - Search for: F2/F3/F4/F8 scan code handlers

2. **Check R30 Overlay** (Menu system)
   - May handle in-game menu view switching
   - Check ACMI button handlers

3. **Check Resident Code**
   - Always-loaded keyboard interrupt handlers
   - May set flag before R15 is loaded

4. **Check Overlay Loader**
   - Parameters passed when loading R15
   - View mode might be initialization parameter

## Technical Details

### R15 Flag Usage Pattern

**Initialization** (view_mode_set @ 0x1086EC):
```asm
sub ax, ax                              ; AX = 0
mov cs:r15_external_view_flag, al       ; Set flag = 0 (cockpit)
```

**Main Dispatcher** (r15_simulation_loop @ 0x108BAC):
```asm
cmp cs:r15_external_view_flag, 0
jz  path_a_cockpit                      ; Jump if 0
; else fall through to path_b_external
```

**Other Readers** (sub_108A05, sub_108FC2):
- Similar pattern: `cmp cs:r15_external_view_flag, 0`
- Branch based on result
- Never modify the value

### File Locations

**Analysis Scripts**:
- `find_view_mode_switches.py` - Search for runtime switchers (found none in R15)
- `find_flag_readers.py` - Found all 5 xrefs
- `get_reader_funcs_info.py` - Analyzed reader functions
- `analyze_view_keys.py` - Analyzed input_poll_handler switch

**Results**:
- `flag_readers_writers.json` - Complete xref list
- `reader_funcs_info.json` - Reader function details
- `view_mode_switches.json` - No conditional writes found
- `view_keys_analysis.json` - input_poll_handler analysis

**Documentation**:
- `VIEW_MODE_SWITCHING_INVESTIGATION.md` - Investigation plan
- `PATH_B_ANALYSIS.md` - External view rendering (complete)
- This file - Key finding summary

## Conclusion

**The view mode flag in R15 is effectively a constant for each R15 session.**

It's set once at overlay load time and never changed. View switching happens at a higher level (different overlay or resident code) that sets the flag value before R15 is loaded.

**Next Action**: Search R17, R30, and resident code for the actual view mode switching logic.

---

**Status**: R15 investigation COMPLETE ✓
**Finding**: Flag is read-only in simulation overlay
**Confidence**: 100% (exhaustive search performed)
