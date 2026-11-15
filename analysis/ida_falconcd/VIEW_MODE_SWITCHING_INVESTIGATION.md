# View Mode Switching Investigation

## Goal
Find the runtime code that changes `r15_external_view_flag` (cs:0x107762) from cockpit view (0) to external view (1) and back.

## Background

### The Flag
- **Address**: cs:0x107762
- **Name**: `r15_external_view_flag`
- **Values**: 0 = cockpit/first-person (Path A), 1 = external/chase camera (Path B)
- **Usage**: Checked by `r15_simulation_loop` (0x108BAC) to dispatch rendering paths

### Known Initialization
- **Function**: `view_mode_set` (formerly `undoc_1086EC`) @ 0x1086EC
- **Action**: Sets flag to 0 at R15 overlay startup (initialization only)
- **Instruction**: 0x1087B2: `mov cs:r15_external_view_flag, al` (where AL=0)

### User Intel
View mode switching should occur via:
1. **View keys**: F2, F3, F4, F8 (scan codes: 0x3C, 0x3D, 0x3E, 0x42)
2. **ACMI playback**: Button press during ACMI mode

## Investigation Progress

### Phase 1: Identify Candidate Functions ✓

From Top 200 functions analysis:

**View-Related Functions**:
- Rank 43: `hud_external_vector_dispatch` (0x263F0, 6B, 47 calls)
- Rank 78: `hud_external_far_callback` (0x24DB8, 18B, 30 calls)
- Rank 145: `view_limits_wrap` (0x25F64, 22B, 17 calls)
- Rank 180: `view_projection` (0x20BDB, 1076B, 14 calls)

**Input-Related Functions**:
- Rank 11: `input_sync_and_wait` (0x130A2F, 42B, 180 calls)
- **Rank 37**: `input_poll_handler` (0x12FAC3, **3814B**, 56 calls) ← **PRIMARY CANDIDATE**
- Rank 64: `input_finalization` (0x130B39, 183B, 36 calls)
- Rank 186: `key_code_pending_drain` (0x348AD, 84B, 14 calls)
- Rank 196: `kb_field_get_22` (0x19CE7, 62B, 13 calls)

### Phase 2: Analyze input_poll_handler

**Details**:
- Address: 0x12FAC3
- Size: 3814 bytes (very large function)
- Contains: **67-case switch statement** starting at 0x12FDA7
- Switch index: `var_6` (scan code >> 8)
- Cases: Process keyboard scan codes 15-78 (0x0F-0x4E)

**Key scan codes to investigate**:
- Case 0x3C (60): F2 key - ?
- Case 0x3D (61): F3 key - ?
- Case 0x3E (62): F4 key - ?
- Case 0x42 (66): F8 key - ?

**Existing Deep Dive**:
- File: `analysis/ida_falconcd/input_poll_handler_deepdive.json`
- Contains: Full disassembly with instruction-level detail
- **Action needed**: Search this file for writes to cs:0x107762

### Phase 3: Search Strategies (Pending IDA Execution)

Created script: `find_view_mode_switches.py`

**Strategy 1**: Find conditional flag writes
- Look for `mov cs:r15_external_view_flag, ...` preceded by conditional jumps
- Runtime switchers will have conditional logic (not unconditional like initialization)

**Strategy 2**: Keyboard + Flag Cross-reference
- Find functions that call keyboard handlers AND reference 0x107762
- These are likely the view key handlers

**Strategy 3**: ACMI Functions
- Search for functions with "acmi" in name
- Check if they reference the view flag
- ACMI playback has view switching button

**Strategy 4**: View/Camera Function Names
- Functions containing: view, camera, external, cockpit, chase
- Check for flag references

## Next Steps

### Immediate Actions

1. **Run IDA Script**:
   ```
   Open FALCONCD.EXE.i64 in IDA Pro
   File → Script File → find_view_mode_switches.py
   Review output in view_mode_switches.json
   ```

2. **Manual Search in input_poll_handler**:
   - Extract cases 0x3C-0x42 from deepdive JSON
   - Look for flag writes or calls to view-switching functions
   - Trace callees for flag modifications

3. **Search ACMI Code**:
   - Find ACMI-related functions in top 200 or full function list
   - Check for flag references
   - ACMI likely has its own input handler

### Alternative Approaches

If direct flag writes aren't found:

1. **Indirect Switching**: Flag might be set by a function pointer dispatch
   - Search for calls that pass 0x107762 as parameter
   - Look for table-driven flag setters

2. **State Machine**: View mode might be part of larger state structure
   - Find the parent structure containing the flag
   - Search for structure writes

3. **Overlay Communication**: R15 flag might be set by another overlay
   - Check inter-overlay communication
   - Look for far calls that pass view mode parameter

### Expected Findings

**Pattern for F2/F3/F4/F8 handlers**:
```asm
; In input_poll_handler switch
case_3C:  ; F2 key
    test [bp+var_4], 8      ; check ALT modifier
    jnz  short set_view_mode
    jmp  default_case
    
set_view_mode:
    mov  ax, cs
    mov  es, ax
    mov  byte ptr es:r15_external_view_flag, X  ; X = 0 or 1
    ; possibly call view initialization function
    jmp  end_switch
```

**Pattern for ACMI button**:
```asm
acmi_button_handler:
    ; check if in ACMI mode
    ; check button state
    xor  byte ptr cs:r15_external_view_flag, 1  ; toggle 0↔1
    ; or: explicit set to 0 or 1
    retn
```

## Files

### Analysis Files
- `view_input_candidates.json` - List of view/input functions from Top 200
- `input_poll_handler_deepdive.json` - Full disassembly of main keyboard handler
- `view_mode_setter_analysis.json` - Analysis of initialization function
- `view_flag_writes.json` - All known writes to 0x107762

### Scripts
- `find_view_input_funcs.py` - Extract candidates from Top 200 (run standalone)
- `find_view_mode_switches.py` - Search for runtime switchers (run in IDA)
- `trace_view_flag_writes.py` - Find all xrefs to flag (already run)
- `analyze_view_mode_setter.py` - Analyze initialization (already run)

### Documentation
- `PATH_B_ANALYSIS.md` - Complete analysis of external view rendering path
- `RUN_VIEW_SWITCH_SCRIPT.md` - Instructions for running IDA script
- `TOP_200_COMPLETE.md` - Top 200 function analysis results

## Status

- ✓ View flag identified and documented
- ✓ Initialization code found and renamed
- ✓ Path A/B rendering fully analyzed
- ✓ Candidate functions identified
- ⏳ Runtime switching mechanism - IN PROGRESS
- ⏳ View key handlers - PENDING IDA SCRIPT
- ⏳ ACMI button handler - PENDING IDA SCRIPT

## References

- **R15 Simulation Loop**: `docs/architecture/game_loop.md`
- **Path B Analysis**: `docs/PATH_B_ANALYSIS.md`
- **Top 200 Functions**: `docs/TOP_200_COMPLETE.md`
- **Input System**: `docs/INPUT_SYSTEM_100_PERCENT_COMPLETE.md`
