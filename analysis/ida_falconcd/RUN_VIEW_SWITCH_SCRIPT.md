# View Mode Switch Detection Script

## Purpose
Find runtime code that switches between cockpit view (Path A) and external view (Path B) by modifying `r15_external_view_flag` (cs:0x107762).

## Background
- Previous analysis found initialization code (`view_mode_set` @ 0x1086EC) that sets flag to 0 at startup
- Need to find keyboard handlers (F2/F3/F4/F8 view keys) or ACMI controls that change the flag during gameplay

## How to Run

1. Open `FALCONCD.EXE.i64` in IDA Pro
2. Go to **File → Script File** (or press Alt+F7)
3. Select `find_view_mode_switches.py`
4. Wait for the script to complete (will auto-exit IDA)
5. Review results in `view_mode_switches.json`

## What the Script Does

### Strategy 1: Conditional Flag Writes
- Searches for functions that write to the flag with conditional logic (jumps before writes)
- These are likely the runtime switchers (not initialization code)

### Strategy 2: Keyboard + Flag References
- Looks for functions that:
  - Call keyboard input handlers (`kb_record_key_event`, `key_code_pending_drain`, etc.)
  - AND reference the view flag
- These are likely view key handlers (F2/F3/F4/F8)

### Strategy 3: ACMI Functions
- Searches for functions with "acmi" in their name
- Checks if they reference the view flag
- ACMI playback mode allows view switching via button

### Strategy 4: View/Camera Function Names
- Looks for functions with keywords: view, camera, external, cockpit, chase
- Checks if they reference the flag
- May find view management functions

## Expected Output

The script will print findings to IDA's console and save structured results to:
```
c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\view_mode_switches.json
```

## Next Steps After Running

Once results are available:
1. Analyze identified functions that write to the flag
2. Trace keyboard scan code handling for view keys
3. Document complete view switching mechanism
4. Update IDA database with findings (rename functions, add comments)

## Related Files
- `view_mode_set` (0x1086EC) - Initialization (already analyzed)
- `r15_simulation_loop` (0x108BAC) - Checks flag to dispatch Path A vs Path B
- `PATH_B_ANALYSIS.md` - Complete analysis of external view rendering path
