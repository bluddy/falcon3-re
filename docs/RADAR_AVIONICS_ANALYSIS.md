# Falcon 3.0 - Radar and Avionics System Analysis

**Date**: 2024  
**Status**: IN PROGRESS (60%)  
**User Context**: At least 3 radar modes (2 unrealistic, 1 realistic with submodes), strings include SAD and HFR

---

## Executive Summary

The radar/avionics system in Falcon 3.0 includes multiple radar modes for air-to-air combat. Based on user information, there should be:
1. **2 unrealistic "arcade" modes** - Likely all-aspect lock and long-range tracking
2. **1 realistic mode with submodes** - Likely RWS (Range While Search) with SAD/HFR submodes

**Current Status**: Found mode switching infrastructure but unable to locate SAD/HFR strings in binary. May require runtime analysis or be stored in overlay files.

---

## F-16 Radar Background

The F-16A/C uses the **APG-66 radar** with multiple operating modes:

### Real F-16 Modes:
1. **RWS (Range While Scan)** - Search mode, multiple targets displayed
2. **TWS (Track While Scan)** - Tracks 10 targets, scans for more
3. **STT (Single Target Track)** - Locks one target for weapons
4. **ACM (Air Combat Mode)** - Quick acquisition modes:
   - **Boresight** - Locks directly ahead
   - **Vertical Scan** - Scans up/down ahead
   - **Slewable** - Cursor-controlled acquisition

### Realistic vs Arcade in Falcon 3.0:
- **Arcade modes**: Likely all-aspect long-range locks (unrealistic for 1991 F-16)
- **Realistic mode**: Limited radar cone, realistic range, scan patterns

### SAD and HFR (User Mentioned):
- **SAD** - Unknown, possibly "Situation Awareness Display" or radar submode
- **HFR** - Unknown, possibly "High Frame Rate" scan or "High Frequency Range"
- These may be Falcon 3.0-specific terms or abbreviations for real modes

---

## Mode Switching Infrastructure

### Key Function: key_mode_switch_step @ 0x33116

**Purpose**: Handle mode switching via keyboard input

**Size**: 206 bytes

**Mode Strings Found**:
1. **"TRACK"** @ 0x54DFD - Target tracking mode
2. **"EJECT"** @ 0x54E1F - Ejection mode
3. **"DEATH"** @ 0x54E25 - Death/destruction mode
4. **"PAUSE"** @ 0x54E3C - Pause mode
5. **"CHASE"** @ 0x54E03 - Chase camera mode

**Analysis**:
- These are general view/game modes, not radar-specific
- "TRACK" mode likely enables radar targeting
- Actual radar submodes (SAD, HFR, etc.) not found in this function

### Mode Setup Function: key_mode_state_setup

**Called From**: key_mode_switch_step

**Purpose**: Set up mode display and function pointers

**Pattern**:
```assembly
mov     word_54EFA, <mode_number>      ; Set mode ID
mov     word_54E42, offset <mode_str>  ; Set mode display string
mov     word_54E44, ds                 ; String segment
call    mode_extent_recompute          ; Recalculate view extents
mov     word_54F9B, <handler_offset>   ; Set mode handler function
mov     word_54F9D, cs                 ; Handler segment
```

---

## Radar-Related Functions Found

### 1. HUD Targeting Functions

From previous HUD analysis:

| Function | Address | Size | Purpose |
|----------|---------|------|---------|
| hud_ai_target_tracking_draw | 0x425A2 | 88 | Draw target brackets |
| hud_state_table_processor | 0x45074 | 508 | Batch process targets |
| hud_rowlist_timer_step | 0x47BDE | 535 | Update target list |
| hud_track_marker_draw | 0x42686 | 70 | Draw targeting marker |
| hud_track_distance_draw | 0x426CC | 101 | Display range to target |

### 2. Target Tracking

**String Found**: "TRACK" @ 0x54DFD
- Referenced by: `key_mode_switch_step`
- Likely enables active target tracking mode
- Sets up HUD to display targeting information

### 3. Radar Warnings

**Strings Found**:
- "RADAR CONTACT+NNN DEGREES+NN MILES." @ 0x57E33
- "ENEMY LOCK ON!" @ 0x57CDB
- "BANDIT! BANDIT +NN O'CLOCK HIGH" @ 0x57E13

**Purpose**: Voice/text warnings for:
- Radar contacts detected
- Enemy radar lock warning
- Threat callouts

---

## Search Results

### SAD String Search: ❌ NOT FOUND
- Searched all strings in binary
- No direct match for "SAD"
- May be in overlay file or encoded differently

### HFR String Search: ❌ NOT FOUND
- Searched all strings in binary
- No direct match for "HFR"
- May be in overlay file or encoded differently

### Possible Explanations:
1. **Overlay Files**: Radar modes may be in separate overlay (.OVL) files
2. **Encoded**: Strings may be packed or encoded (unlikely for display text)
3. **Dynamic**: Mode names generated from abbreviation tables
4. **Terminology**: SAD/HFR may be from manual/docs, not in-game strings

---

## Radar System Architecture (Hypothesis)

Based on found functions and F-16 knowledge:

```
Keyboard Input
    ↓
key_mode_switch_step (0x33116)
    ├─ "TRACK" mode → Enable radar targeting
    └─ Radar submode cycling (not yet found)
    ↓
Radar Mode State Variable (not yet located)
    ├─ Mode 0: All-Aspect (arcade)
    ├─ Mode 1: Boresight (arcade)
    └─ Mode 2: RWS (realistic)
        ├─ Submode: SAD
        └─ Submode: HFR
    ↓
Target Acquisition Logic
    ├─ Search pattern (depends on mode)
    ├─ Lock-on conditions (depends on mode)
    └─ Range/aspect limits (realistic mode only)
    ↓
HUD Display
    ├─ Target brackets
    ├─ Range/closure rate
    ├─ Mode indicator (SAD/HFR/etc.)
    └─ Lock status
```

---

## Mode Comparison (Hypothesis)

### Mode 0: All-Aspect Lock (Arcade)
- **Realism**: Low
- **Range**: Unlimited (or very long, 40+ nm)
- **Aspect**: All-aspect (can lock from any angle)
- **Lock Time**: Instant
- **Best For**: Beginners, unrealistic but easy

### Mode 1: Boresight/Vertical Scan (Arcade)
- **Realism**: Medium
- **Range**: Long (20-30 nm)
- **Aspect**: Forward hemisphere only
- **Lock Time**: Fast (1-2 seconds)
- **Best For**: Quick locks in dogfights

### Mode 2: RWS with SAD/HFR Submodes (Realistic)
- **Realism**: High
- **Range**: Limited (20 nm typical for F-16A)
- **Aspect**: Depends on missile (AIM-7: front, AIM-9: rear)
- **Lock Time**: Realistic (3-5 seconds)
- **Submodes**:
  - **SAD**: Possibly "Situational Awareness Display" or wider scan
  - **HFR**: Possibly "High Frame Rate" or faster update rate
- **Best For**: Realistic gameplay

---

## Data Structures (Hypothetical)

### Radar Mode State

```c
struct RadarState {
    uint8_t current_mode;          // 0=all-aspect, 1=boresight, 2=RWS
    uint8_t current_submode;       // For RWS: 0=SAD, 1=HFR, etc.
    uint16_t locked_target_id;     // Entity ID of locked target
    uint16_t scan_azimuth;         // Current scan position (degrees)
    uint16_t scan_elevation;       // Elevation angle
    uint8_t lock_strength;         // 0-100, signal strength
    uint8_t lock_timer;            // Time to full lock
};
```

### Mode Configuration

```c
struct RadarModeConfig {
    uint16_t max_range;            // Nautical miles × 10
    uint8_t scan_width;            // Azimuth degrees
    uint8_t scan_height;           // Elevation degrees
    uint8_t lock_time;             // Frames to lock
    bool all_aspect;               // Ignore target aspect?
    bool require_los;              // Line of sight required?
};

// Mode configurations
RadarModeConfig modes[3] = {
    // Mode 0: All-Aspect (Arcade)
    {500, 180, 90, 1, true, false},  // 50nm, 180°, instant
    
    // Mode 1: Boresight (Arcade)
    {300, 20, 20, 30, false, true},  // 30nm, 20°, 1 sec
    
    // Mode 2: RWS (Realistic)
    {200, 60, 60, 90, false, true},  // 20nm, 60°, 3 sec
};
```

---

## Next Steps

### High Priority:
1. **Find SAD/HFR strings**:
   - Check overlay files (.OVL)
   - Search for 2-3 letter abbreviations near mode code
   - Check if dynamically generated from char arrays

2. **Locate radar mode state variable**:
   - Find byte/word with values 0-2 (or 0-3)
   - Written by mode switch function
   - Read by target acquisition logic

3. **Analyze mode cycling**:
   - Find keyboard binding (likely a function key or number)
   - Trace mode increment/wrap logic
   - Find mode-specific behavior branches

### Medium Priority:
4. **Map target acquisition logic**:
   - Find lock-on conditions per mode
   - Identify range/aspect checks
   - Locate lock timer code

5. **Decode radar display**:
   - Find mode indicator rendering
   - Locate scan pattern drawing
   - Identify target return symbols

### Low Priority:
6. **Runtime verification**:
   - Test each mode in-game
   - Verify range/aspect limits
   - Confirm SAD/HFR submode behavior

---

## Files Created

1. `analysis/s4/analyze_radar_system.py` - Initial radar system search
2. `analysis/s4/find_sad_hfr_modes.py` - SAD/HFR specific search
3. `analysis/s4/find_radar_mode_enum.py` - Mode enum/state search
4. `analysis/s4/radar_system_analysis.json` - General radar data
5. `analysis/s4/sad_hfr_modes.json` - SAD/HFR search results
6. `analysis/s4/radar_mode_enum.json` - Mode comparison data
7. `docs/RADAR_AVIONICS_ANALYSIS.md` (this file)

---

## Open Questions

1. ❓ What do SAD and HFR stand for?
2. ❓ Are SAD/HFR in overlay files or main executable?
3. ❓ How many total radar modes/submodes exist?
4. ❓ Which keyboard keys cycle radar modes?
5. ❓ Is there a radar scope display or only HUD indicators?
6. ❓ Do different aircraft have different radar modes? (F-16 vs MiG-29)

---

## Recommendations

**For Complete Analysis**:
1. **Check game manual/documentation** - May explain SAD/HFR meaning
2. **Runtime debugging** - Set breakpoints on mode switching
3. **Overlay analysis** - Extract and analyze .OVL files for radar code
4. **Play-through** - Test each mode to understand behavior differences

**Most Efficient**: Ask user to clarify what SAD/HFR mean or provide game manual reference.

---

**Status**: Awaiting clarification on SAD/HFR before continuing detailed analysis.
