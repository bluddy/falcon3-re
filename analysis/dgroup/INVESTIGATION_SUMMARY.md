# View Switching Investigation Summary

## Problem Statement

Find the runtime code that handles view switching when the player presses number keys (0-9) during flight. Specifically, determine how `r15_external_view_flag` at `0x107762` gets modified when switching between internal (cockpit) and external (satellite/chase/etc.) views.

## What We've Found

### ✅ Input Capture - COMPLETE

**Location**: `input_poll_handler` at `0x12FAC3` in R29_3174s segment

**Key Code Block**: `0x130709` - `0x130749`
```
loc_130709:  ; Number key capture loop
  ...scan keyboard for keys 1-9, 0
  ...on match, DI contains scan code (0x02-0x0B)
  0x130749: mov es:input_flag_pending_2, di  ; Store for later processing
```

**Scan Code Mapping**:
- Key 1 → 0x02 (Satellite view - external)
- Key 2 → 0x03 (Ground view - external)
- Key 3 → 0x04 (Front cockpit - internal)
- Key 4 → 0x05 (Left cockpit - internal)
- Key 5 → 0x06 (Rear cockpit - internal)
- Key 6 → 0x07 (Right cockpit - internal)
- Key 7 → 0x08 (Wingman view - external)
- Key 8 → 0x09 (Padlock view - external)
- Key 9 → 0x0A (?)
- Key 0 → 0x0B (Chase plane - external)

**Input Queue**: `input_flag_pending_2` at `es:0x79B66`

### ❓ Input Dispatch - MISSING

**What We Know**:
- 37 functions across multiple overlays READ `input_flag_pending_2`
- Most likely candidates:
  - `r29_tactical_screen_coordinator` (3 reads at 0x12DFD6, 0x12EEDC, 0x12F512)
  - `game_mode_r53_main_coordinator` (5 reads at 0x182476, 0x183834, 0x183FA6, 0x184B10, 0x185068)

**What We Need**:
- Find the dispatcher that reads `input_flag_pending_2` and branches based on scan code value
- Identify handler functions called for each view key
- Determine if handlers modify `r15_external_view_flag`

### ⚠️ View Flag Modification - SUSPICIOUS

**Flag**: `r15_external_view_flag` at `cs:0x107762` in R15_5E0Bs segment

**References Found**:
- **1 WRITE**: Only in `view_mode_set` at `0x1087B2` (initialization)
- **4 READS**: In simulation loop paths (Path A vs Path B decision)

**The Mystery**:
- User confirmed views CAN switch during flight
- But we only found initialization write, no runtime writes!
- Three possibilities:
  1. **Indirect write** - Flag written via pointer/indirect addressing we haven't found
  2. **View functions set flag** - Dispatcher calls view setup functions, they set flag as side effect
  3. **Flag is session-static** - Set once per mission, view keys change camera not mode

## Architecture Understanding

```
Keyboard Input → input_poll_handler (0x12FAC3)
                 ↓
                 Scan code stored in input_flag_pending_2
                 ↓
Game Loop → [MISSING DISPATCHER] reads input_flag_pending_2
            ↓
            Dispatch based on scan code (0x02-0x0B)
            ↓
            ┌─────────────┬──────────────┐
            ↓             ↓              ↓
         View Handler  View Handler  View Handler
         (satellite)   (cockpit)     (chase)
            ↓             ↓              ↓
            [UNKNOWN: Set r15_external_view_flag?]
            ↓
Simulation Loop → Reads r15_external_view_flag at 0x108BC5
                  ↓
                  Path A (flag=0) → Cockpit view rendering
                  Path B (flag=1) → External view rendering
```

## Key Files Created

1. **MANUAL_INSPECTION_TARGETS.txt** - 8 specific addresses to examine in IDA
2. **VIEW_SWITCHING_NEXT_INVESTIGATION.md** - Detailed investigation guide
3. **hypothesis_view_switching.md** - Initial hypothesis
4. **find_view_key_dispatch.py** - Analysis of input_flag reads
5. **examine_input_dispatch_context.py** - IDA script to find dispatch patterns (needs to be run)

## Scripts Ready to Run (when IDA automation available)

- `examine_input_dispatch_context.py` - Will analyze code after each input_flag read
- `find_all_writes_to_flag.py` - Exhaustive search for all writes to view flag

## Current Status: BLOCKED

**Need**: Manual inspection in IDA of the 8 target addresses to find the dispatcher

**Next Step**: Open IDA database and examine code at:
- 0x12DFD6, 0x12EEDC, 0x12F512 (r29_tactical_screen_coordinator)
- 0x182476, 0x183834, 0x183FA6, 0x184B10, 0x185068 (game_mode_r53_main_coordinator)

Look for dispatch patterns: jump tables, if/else chains, or parameterized calls.

## Renamed in IDA

- `input_flag_pending_2` - Input queue variable
- `input_poll_handler` - Keyboard polling function
- `input_sync_and_wait` - Input synchronization
- `input_finalization` - Input cleanup
- `r15_external_view_flag` - View mode flag
- `view_mode_set` - View flag initialization
- Added comments at key capture loop (0x130709-0x130749)

## Statistics

- **Segments searched**: All 147
- **Functions reading input_flag**: 37
- **Functions reading view flag**: 4
- **Functions writing view flag**: 1 (initialization only)
- **Scripts created**: 20+
- **Comments added to IDA**: 38+
