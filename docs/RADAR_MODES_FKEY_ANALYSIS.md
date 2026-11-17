# Falcon 3.0 - Radar Modes and F-Key Analysis

**Date**: 2024  
**Status**: PARTIAL - F-key handlers found, mode strings NOT in binary  

---

## Key Findings

### ✅ F-Key Handlers Found

Successfully located handlers for all radar-related F-keys:

| Key | Scan Code | Handlers Found | Notable Functions |
|-----|-----------|----------------|-------------------|
| **F5** | 0x3F | 14 | stream_command_interpret, farobj_config_state_entry |
| **F6** | 0x40 | 35 | mode_stream_select_step, entity_state_load |
| **F7** | 0x41 | 11 | overlay_loader_main, ui_loadout_pylon_config |
| **F8** | 0x42 | 12 | flight_aircraft_slot_physics_step, **input_poll_handler** |
| **F9** | 0x43 | 1 | overlay_loader_main |
| **F10** | 0x44 | 1 | undoc_131001 |
| **R** | 0x13 | (searched) | Radar on/off toggle |
| **Z** | 0x2C | (searched) | Target lock |

### ❌ Mode Strings NOT Found

**Definitive**: SAD and HFR strings are **NOT in FALCONCD.EXE**

Searched:
- ✅ All IDA strings database
- ✅ Raw binary byte search
- ✅ 2-4 character string enumeration
- ✅ Strings near F-key handlers
- ✅ Data segments

**Result**: Zero matches for "SAD" or "HFR" as literal strings.

---

## Hypothesis: Dynamic Mode Display

Since SAD/HFR don't exist as strings, they must be:

### Theory 1: Character-by-Character Drawing
Mode names drawn using individual character codes:
```c
// Pseudocode
void display_mode() {
    if (radar_mode == MODE_SAD) {
        draw_char(x, y, 'S');
        draw_char(x+8, y, 'A');
        draw_char(x+16, y, 'D');
    }
}
```

### Theory 2: Mode Number to String Lookup
Mode displayed as number, manual says "Mode 1 = SAD":
```c
display_number(radar_mode);  // Shows "1" or "2"
// Player knows: 1=SAD, 2=HFR from manual
```

### Theory 3: Encoded/Packed Storage
Strings stored in compressed format:
```c
// Packed: "SADHFRRWSTWSACM..." as single string
char modes[] = "SADHFRRWSTWSACM";
display_string(&modes[mode_id * 3], 3);
```

### Theory 4: External Data File
Mode strings in separate .DAT or resource file, not in .EXE.

---

## Notable F-Key Handlers

### mode_stream_select_step (F6 handler)
- **Address**: 0x39E62
- **Context**: Likely handles mode selection/cycling
- **Name suggests**: Stream processing for mode selection

### input_poll_handler (F8 handler)  
- **Address**: 0x12FDAC
- **Context**: Main input polling function
- **Likely**: General input handler, not radar-specific

### stream_command_interpret (F5 handler)
- **Address**: 0x1CD9F
- **Context**: Interprets commands from input stream
- **Likely**: Command processing, may include mode changes

---

## F-Key Usage Patterns (from user)

| Key | Function | User Description |
|-----|----------|------------------|
| **F5** | Radar Mode | Cycle through radar modes |
| **F6** | Radar Mode | Cycle through radar modes |
| **F7** | Radar Mode | Cycle through radar modes |
| **F8-F10** | Radar Mode | More radar modes |
| **R** | Radar Toggle | Turn radar on/off |
| **Z** | Target Lock | Lock selected target |

**User Notes**:
- SAD and HFR appear in external view field (mode indicator area)
- 3 main radar modes: 2 unrealistic (arcade), 1 realistic (with submodes)
- Realistic mode has submodes including SAD and HFR

---

## Real F-16 Radar Context

### APG-66 Radar Modes:
1. **RWS (Range While Search)** - Search and display multiple targets
2. **TWS (Track While Scan)** - Track 10 targets while scanning
3. **STT (Single Target Track)** - Lock and track one target
4. **ACM (Air Combat Mode)** - Quick acquisition:
   - Boresight - Lock directly ahead
   - Vertical Scan - Scan vertical slice
   - Slewable - Cursor control

### Possible SAD/HFR Meanings:
- **SAD**: "Situation Awareness Display" or "Scan Azimuth Display"?
- **HFR**: "High Frame Rate" or "High Frequency Range"?
- These may be Falcon 3.0-specific simplified names for RWS/TWS

---

## Code Analysis Results

### F5 Handler (stream_command_interpret @ 0x1CD9F)

**Code snippet**:
```assembly
0001CD9F: cmp     byte ptr es:[bx+2], 3Fh    ; Check for F5 scan code
0001CDA4: jnz     short loc_1CDD9            ; Skip if not F5
0001CDA6: mov     ax, 7894h                  ; Load segment
0001CDA9: mov     es, ax
0001CDAB: cmp     word ptr es:byte_78B06+0D18h, 0  ; Check state variable
0001CDB1: jnz     short loc_1CDD9            ; Skip if already set
; ... continues with command processing
```

**Analysis**:
- F5 handler checks a state variable at `es:byte_78B06+0D18h`
- If state is 0, processes F5 command
- Loads additional parameters from input stream
- Calls further processing (likely mode change function)

### F6 Handler Analysis Needed
- **mode_stream_select_step** is the most promising name
- 35 F6 handlers suggest it's used in many contexts
- Need to analyze what "stream" refers to

---

## Variables of Interest

### Potential Mode State Variables:
- `word_78B06+0D18h` - Checked by F5 handler
- `byte_55156` - Set by mode switch functions (seen in previous analysis)
- `word_54EFA` - Mode ID in mode switch (seen with TRACK/EJECT/etc.)

**Note**: These may be general game state, not radar-specific.

---

## Next Steps to Find SAD/HFR

### High Priority:
1. **Analyze mode_stream_select_step in detail**
   - This is the most promising F6 handler
   - Extract full disassembly
   - Trace what it modifies

2. **Find mode indicator display code**
   - Search for functions that draw 3-4 character text
   - Look for external view HUD rendering
   - Find where mode number/ID is converted to display

3. **Runtime debugging**
   - Press F5/F6/F7 in-game
   - Watch memory at potential mode variables
   - Intercept character drawing calls

### Medium Priority:
4. **Analyze R key handler** (radar on/off)
   - Find scan code 0x13 comparisons
   - Locate radar enabled/disabled flag

5. **Analyze Z key handler** (target lock)
   - Find scan code 0x2C comparisons
   - Trace lock-on logic

6. **Check game manual/documentation**
   - Confirm what SAD and HFR actually mean
   - Verify F-key assignments

---

## Summary

**Found**:
- ✅ All F5-F10 key handlers
- ✅ Multiple mode-related functions
- ✅ General mode switching infrastructure

**Not Found**:
- ❌ SAD/HFR strings (definitively not in binary)
- ❌ Radar mode state variable
- ❌ Mode-to-string conversion logic

**Conclusion**: Radar mode names are either:
1. Generated character-by-character
2. Stored as numbers (manual provides meaning)
3. Packed/encoded in non-string format
4. In external data files

**Recommendation**: Focus on `mode_stream_select_step` function analysis and find where mode indicators are actually rendered on screen.

---

## Files Created

1. `analysis/s4/find_fkey_radar_handlers.py` - F-key scan code search
2. `analysis/s4/find_all_short_strings.py` - Exhaustive string search
3. `analysis/s4/analyze_fkey_handlers_detailed.py` - Detailed F-key analysis
4. `analysis/s4/fkey_radar_handlers.json` - All F-key handlers found
5. `analysis/s4/all_short_strings.json` - Short string catalog (empty)
6. `analysis/s4/fkey_handlers_detailed.json` - F-key handler context
7. `docs/RADAR_MODES_FKEY_ANALYSIS.md` (this file)

---

**Status**: Need to analyze `mode_stream_select_step` and find mode indicator rendering to proceed.
