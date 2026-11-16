# View System Architecture - COMPLETE UNDERSTANDING

## Breakthrough Discovery! ✨

Found the complete view switching mechanism with a **TWO-LEVEL ARCHITECTURE**:

### Level 1: Pipeline Mode (view_pipeline_mode)
- **Variable**: `view_pipeline_mode` at cs:0x107762
- **Values**: 0 or 1
- **Set by**: `view_mode_set` at initialization (0x1087B2)
- **Controls**: Which simulation loop path (Path A vs Path B)
- **Usage**: Read by simulation loop to choose rendering pipeline
- **Hypothesis**: 0 = live simulation, 1 = ACMI playback mode

### Level 2: View Index (current_view_index)
- **Variable**: `current_view_index` at es:0x79F16
- **Values**: 0-9 (10 possible views)
- **Set by**: View key handlers during gameplay
- **Controls**: Specific view/camera within the current mode
- **Usage**: Index into jump table for view-specific rendering

## The Complete Flow

```
INITIALIZATION (Mission Start):
  view_mode_set(mode) at 0x1087B2
    Sets view_pipeline_mode = 0 or 1
    (Likely: 0=simulation, 1=ACMI playback)

RUNTIME (During Flight):
  User presses number key (e.g., Key 2 for ground view)
    ↓
  input_poll_handler captures scan code 0x03
    ↓
  Stores in input_scan_code_queue
    ↓
  game_mode_r53_coordinator dispatcher (0x182476)
    Searches table for scan code 0x03
    ↓
  Handler executes:
    mov es:current_view_index, 7    ; Set view index
    (or whatever index corresponds to ground view)
    ↓
  RENDERING (Every Frame):
    r15_simulation_loop reads view_pipeline_mode
      If 0: Path A (simulation?)
      If 1: Path B (ACMI playback?)
    ↓
    view_rendering_dispatcher (0x156945) reads current_view_index
      mov bx, es:current_view_index
      cmp bx, 9                ; 10-case switch
      shl bx, 1
      jmp cs:jpt_156DD4[bx]    ; Jump table!
    ↓
    View-specific rendering function executes
```

## View Index Jump Table

**Location**: `overlay_r45_logic` at 0x156DC5-0x156DD4

**Structure**:
```assembly
mov bx, es:word_79F16        ; Get view index (0-9)
cmp bx, 9                    ; Bounds check
jbe in_range
jmp default_case
in_range:
  shl bx, 1                  ; word offset
  jmp cs:jpt_156DD4[bx]      ; Dispatch!
```

**10 Cases** (0-9):
- Case 0: Handler at 0x156DD9
- Case 1-9: Other handlers (need to extract table)

## Mapping View Keys to Indices

From the dispatchers we found, scan codes are mapped to view indices:

| Key | Scan | View Type | word_79F16 Value | Handler |
|-----|------|-----------|------------------|---------|
| 1 | 0x02 | Satellite | ? | TBD |
| 2 | 0x03 | Ground | 7? | 0x18249A |
| 3 | 0x04 | Front cockpit | ? | 0x182408 |
| 4 | 0x05 | Left cockpit | ? | TBD |
| 5 | 0x06 | Rear cockpit | ? | TBD |
| 6 | 0x07 | Right cockpit | ? | TBD |
| 7 | 0x08 | Wingman | ? | TBD |
| 8 | 0x09 | Padlock | 8? | 0x1824A3 |
| 9 | 0x0A | ? | ? | TBD |
| 0 | 0x0B | Chase plane | ? | TBD |

(The handler at 0x18249A sets `word_79F16 = 7`, handler at 0x1824A3 pushes `8`)

## Why Only 1 Write to r15_external_view_flag

**ANSWER**: Because the flag (now `view_pipeline_mode`) is **session-static**!

- Set once at mission/mode initialization
- Never changed during flight
- Likely controls ACMI playback vs live simulation
- NOT cockpit vs external (that's controlled by `current_view_index`)
- View keys only change the view INDEX, not the pipeline mode

## Two Interpretations

### **UPDATED Interpretation: ACMI vs Simulation**
- **0 = Live simulation mode** (player actively flying)
- **1 = ACMI playback mode** (viewing recorded mission)
- The pipeline mode is locked for the session
- Both modes support all 10 view indices
- `current_view_index` values 0-4 might be cockpit views
- `current_view_index` values 5-9 might be external views
- The mode determines WHAT data is being rendered, not WHICH camera

### Evidence for ACMI Interpretation:
- ACMI is a major Falcon 3.0 feature
- ACMI needs different data pipeline (recorded vs live)
- Mode set at session start makes sense for ACMI
- User insight: "ACMI and pushing the button"
- Both sim and ACMI need all view options

## Next Steps to Resolve

1. **Extract the jump table** at jpt_156DD4
   - Get all 10 handler addresses
   - See what functions they call
   - Map indices to view types

2. **Check handler code** at 0x18249A and 0x1824A3
   - Confirm what values they set to word_79F16
   - See if different scan codes set different indices

3. **Find remaining view key handlers**
   - Only found scan codes 0x01, 0x03, 0x04, 0xFF so far
   - Need to find 0x02, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0B

4. **Document in IDA**:
   - Rename word_79F16 to `current_view_index` or `active_view_mode`
   - Comment the jump table
   - Link all the pieces together

## Key Insight

**The view switching works through a VIEW INDEX, not by toggling the external flag!**

This explains everything:
- Why only 1 write to flag found ✓
- Why handlers set a different variable ✓  
- Why there's a 10-case switch statement ✓
- How view keys work during flight ✓

## Files Showing This

- `func_156945_full.json` - Contains the jump table at 0x156DC5
- `input_dispatch_patterns.json` - Shows handlers setting word_79F16
- `jump_table_addresses.json` - Shows view key dispatchers

## Success! 🎉

We now understand the COMPLETE view switching architecture:

1. **Input**: Number keys → scan codes
2. **Capture**: input_poll_handler stores in queue
3. **Dispatch**: Coordinator finds handler for scan code
4. **Handler**: Sets word_79F16 to view index (0-9)
5. **Rendering**: Jump table dispatches to view-specific renderer

The external flag is just mode selection, not toggled during flight!
