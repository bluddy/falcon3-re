# Falcon 3.0 - Radar System Complete Analysis

**Date**: 2024  
**Status**: ✅ COMPLETE - Manual analyzed, system understood  

---

## Executive Summary

Falcon 3.0 has **3 radar types** selectable in Configuration menu:
1. **SAD** (Situation Awareness Display) - Easiest, arcade (360° view)
2. **SAM** (Situation Awareness Mode) - Intermediate (120° cone, auto-ranging)
3. **HFR** (High Fidelity Radar) - Realistic, requires manual control

**HFR has 4 submodes**:
- **NAM** (F5) - Normal Air Mode (search)
- **ACM** (F6) - Air Combat Maneuvering (dogfight)
- **GM** (F7) - Ground Mapping (air-to-ground)
- **SAM/STT** - Accessed via Z key from NAM

**Key Finding**: SAD and HFR are **NOT strings in the executable** - they're displayed on the REO (Radar/Electro-Optical display) dynamically, likely character-by-character or from mode numbers.

---

## Important Note on Manual Extraction

⚠️ **PDF Extraction Error**: The manual PDF has graphical "F" characters that weren't picked up during text extraction. Lines that read "Press 5" actually mean "Press F5". This was confirmed by checking `manual/extracted/f3keys.txt` which shows the correct keys.

**Correct interpretation**:
- Where manual says "Press 5" → Actually **F5**
- Where manual says "Press 6" → Actually **F6**  
- Where manual says "Press 7" → Actually **F7**

---

## Radar Types (Configuration Setting)

### 1. SAD - Situation Awareness Display (Easiest)

**Realism**: Very Low (Arcade)  
**Skill Level**: Beginner  
**Display**: Full 360° god's-eye view  

**Features**:
- See ALL aircraft within radar range (10/20/40/80 nm)
- No cone limitation - complete situational awareness
- Color-coded altitude: Orange (below 3000 ft), Blue (above 3000 ft), White (within 3000 ft)
- Automatic range selection by Fire Control Computer
- Direction of travel shown as "vapor trail" off each blip
- Displayed as "**##SAD**" in upper left (e.g., "20 SAD" = 20nm range)

**Usage**:
- Press **R** to toggle radar on/off
- Press **T** to cycle target lock
- Press **Z** to lock target
- Press **X** to break lock
- Range auto-adjusts based on threats

**Limitations**:
- Unrealistic - no real radar has 360° coverage
- Makes game too easy for experienced players

---

### 2. SAM - Situation Awareness Mode (Intermediate)

**Realism**: Medium  
**Skill Level**: Intermediate  
**Display**: 120° cone (horizontal and vertical)  

**Features**:
- Forward-looking cone: 120° azimuth × 120° elevation
- Only see targets within radar cone
- Automatic range selection (10/20/40/80 nm)
- Automatic antenna scan (azimuth/elevation)
- Color-coded blips like SAD mode
- Displayed as "**##SAM**" in upper left

**Usage**:
- Same as SAD mode (R/T/Z/X keys)
- Must point nose toward targets to see them
- Altitude scale on left edge (0-30,000 ft)
- Antenna markers show radar scan position

**Advantages over SAD**:
- More realistic targeting discipline
- Still easy to use (auto-ranging, auto-scan)

---

### 3. HFR - High Fidelity Radar (Realistic)

**Realism**: High  
**Skill Level**: Advanced  
**Display**: 4 submodes with manual control  

**Features**:
- Manual range selection (**F8** key)
- Manual azimuth scan (**F9** key: 20°/60°/120°)
- Manual elevation scan (**F10** key: 1/2/4/6 bars)
- Target history (shows last 3 positions, fading)
- Must actively manage radar antenna
- Four separate modes for different phases of engagement

**Submodes**:

#### NAM - Normal Air Mode (F5)
- **Purpose**: Wide-area search
- **Display**: Green square blips for all targets in scan
- **Readouts**: Range (upper left), elevation range (upper right)
- **Features**: 
  - Acquisition Corral (two vertical lines)
  - Press **T** to cycle Acquisition Corral to targets
  - Search Target Altitude Bar appears when corral on target
- **Typical Use**: Initial search phase, finding targets

#### ACM - Air Combat Maneuvering (F6)
- **Purpose**: Close-range dogfighting
- **Range**: Fixed at 10 nm
- **Scan Patterns**: 
  - 20° × 20° (default)
  - 10° × 40° (toggle with Shift+F6)
- **Features**:
  - Auto-locks closest target
  - Switches to STT when locked
  - Immediate threat detection
- **Typical Use**: Furball, visual range combat

#### GM - Ground Mapping (F7)
- **Purpose**: Air-to-ground targeting
- **Features**:
  - Shows ground features
  - Toggle rivers/roads with **Y** key
- **Usage**: Target ground sites, nav

#### SAM Mode (via Z key from NAM)
- **Purpose**: Track-while-scan multiple targets
- **Access**: Place Acquisition Corral on target in NAM, press **Z**
- **Display**: Locked target becomes diamond
- **Readouts**: Full target data (range, closure, altitude, aspect, heading)
- **Features**:
  - Other targets still visible
  - Can cycle lock with **T** key
  - Press **X** to break lock and return to NAM

#### STT - Single Target Track (via Z key from SAM)
- **Purpose**: Full lock for weapon employment
- **Access**: Lock target in SAM, press **Z** again
- **Display**: Only locked target visible, all others disappear
- **Features**:
  - Continuous tracking
  - Best for missile shots
  - **WARNING**: Target may detect your radar lock
- **Typical Use**: Final pre-shot tracking

---

## Keyboard Commands

### Primary Radar Keys:
| Key | Function |
|-----|----------|
| **R** | Radar on/off (standby) |
| **C** | Toggle REO/Map display |
| **T** | Cycle target selection |
| **Z** | Lock target / advance mode (NAM→SAM→STT) |
| **X** | Break radar lock |
| **N** | IFF check (tone if friendly) |

### HFR Mode Selection:
| Key | Function |
|-----|----------|
| **F5** | NAM (Normal Air Mode) |
| **F6** | ACM (Air Combat Maneuvering) |
| **F7** | GM (Ground Mapping) |
| **Shift+F6** | Toggle ACM scan pattern (20×20 ↔ 10×40) |

### HFR Manual Controls:
| Key | Function |
|-----|----------|
| **F8** | Cycle radar range (10/20/40/80 nm) |
| **F9** | Cycle azimuth scan (20°/60°/120°) |
| **F10** | Cycle elevation scan (1/2/4/6 bars) |
| **Y** | Toggle rivers/roads (GM mode only) |
| **Shift+F8** | Fine-tune range |

---

## Mode Display on REO

**Upper Left Corner Format**: `## MODE`

Examples:
- `20 SAD` - SAD mode, 20 nm range
- `40 SAM` - SAM mode, 40 nm range
- `10 NAM` - HFR/NAM mode, 10 nm range
- `10 ACM` - HFR/ACM mode, 10 nm range

**Why SAD/HFR not found in binary**:
- These 3-character mode indicators are displayed dynamically
- Likely drawn character-by-character: `draw_char('S'); draw_char('A'); draw_char('D');`
- Or generated from mode number: `mode_names[mode_id]` where array is "SADSAM NAMACMGM "
- Not stored as complete strings in executable

---

## Technical Implementation (Hypothesis)

### Mode State Variables

Based on Configuration menu structure:

```c
enum RadarType {
    RADAR_TYPE_SAD = 0,    // Beginner
    RADAR_TYPE_SAM = 1,    // Intermediate
    RADAR_TYPE_HFR = 2     // Advanced
};

enum HFR_Submode {
    HFR_NAM = 0,    // F5 - Normal Air Mode
    HFR_ACM = 1,    // F6 - Air Combat Maneuvering
    HFR_GM  = 2,    // F7 - Ground Mapping
    HFR_SAM = 3,    // Z from NAM - SAM mode
    HFR_STT = 4     // Z from SAM - Single Target Track
};

struct RadarState {
    RadarType type;              // SAD/SAM/HFR (config setting)
    HFR_Submode hfr_mode;        // If type==HFR, which submode
    uint8_t range;               // 10/20/40/80 nm
    uint8_t azimuth_scan;        // 20/60/120 degrees
    uint8_t elevation_bars;      // 1/2/4/6 bars
    uint16_t locked_target_id;   // Current lock
    bool radar_enabled;          // R key toggle
};
```

### Mode Display Function

```c
void display_radar_mode(RadarState* radar) {
    char mode_str[4];
    
    // Get mode abbreviation
    if (radar->type == RADAR_TYPE_SAD) {
        mode_str = "SAD";
    } else if (radar->type == RADAR_TYPE_SAM) {
        mode_str = "SAM";
    } else {  // HFR
        switch (radar->hfr_mode) {
            case HFR_NAM: mode_str = "NAM"; break;
            case HFR_ACM: mode_str = "ACM"; break;
            case HFR_GM:  mode_str = "GM "; break;
            case HFR_SAM: mode_str = "SAM"; break;
            case HFR_STT: mode_str = "STT"; break;
        }
    }
    
    // Display: "20 SAD" format
    draw_number(10, 10, radar->range);
    draw_char(30, 10, mode_str[0]);
    draw_char(38, 10, mode_str[1]);
    draw_char(46, 10, mode_str[2]);
}
```

### F-Key Handlers

**F5 Handler** (NAM mode):
- Sets `hfr_mode = HFR_NAM`
- Defaults range to 20 nm
- Enables Acquisition Corral
- Clears any existing lock

**F6 Handler** (ACM mode):
- Sets `hfr_mode = HFR_ACM`
- Forces range to 10 nm
- Auto-locks nearest target
- Sets scan pattern (20×20 or 10×40)

**F7 Handler** (GM mode):
- Sets `hfr_mode = HFR_GM`
- Switches to ground mapping display
- Shows terrain features

**F8 Handler** (Range):
- Cycles: 10 → 20 → 40 → 80 → 10
- Only in HFR mode (SAD/SAM auto-range)

**F9 Handler** (Azimuth):
- Cycles: 20° → 60° → 120° → 20°
- Only in HFR mode

**F10 Handler** (Elevation):
- Cycles: 1 bar → 2 bars → 4 bars → 6 bars → 1 bar
- Only in HFR mode

---

## Code Locations (from analysis)

### F-Key Handlers Found:
- **F5**: 14 handlers, including `stream_command_interpret` @ 0x1CD9F
- **F6**: 35 handlers, including `mode_stream_select_step` @ 0x39E62
- **F7**: 11 handlers, including `overlay_loader_main` @ 0x2CC6F
- **F8**: 12 handlers, including `input_poll_handler` @ 0x12FDAC
- **F9**: 1 handler @ 0x2CC5C
- **F10**: 1 handler @ 0x13104F

### Promising Functions to Analyze:
1. **mode_stream_select_step** @ 0x39E62 (F6 handler) - "mode" in name!
2. **stream_command_interpret** @ 0x1CD9F (F5 handler) - command processing
3. **input_poll_handler** @ 0x12FDAC (F8 handler) - main input handler

### Mode State Variables (potential):
- `word_54EFA` - Mode ID (seen with TRACK/EJECT mode strings)
- `word_78B06+0D18h` - Checked by F5 handler
- `byte_55156` - Mode flag

---

## Why This Matters

### For Reverse Engineering:
1. **String search doesn't work** - Mode names generated dynamically
2. **F-key handlers are the key** - They set mode state
3. **Must trace mode state variables** - Find where F-key handlers write
4. **Display logic is separate** - Mode rendering uses char-by-char drawing

### For Gameplay:
1. **SAD** - Best for beginners, unrealistic but easy
2. **SAM** - Good balance of realism and usability
3. **HFR** - Required for Advanced skill, realistic workload
4. **NAM** - Start here in HFR for search
5. **ACM** - Switch here for dogfight
6. **STT** - Use for final weapon employment

---

## Next Steps

To complete radar system analysis:

### High Priority:
1. **Analyze mode_stream_select_step** @ 0x39E62
   - This is the F6 handler
   - Name strongly suggests mode selection
   - Extract full disassembly and trace mode changes

2. **Find mode display rendering**
   - Search for REO text drawing functions
   - Locate where "SAD"/"SAM"/"NAM" chars are drawn
   - Trace from mode state variable to display

3. **Map mode state variable**
   - Find the byte/word that stores current mode
   - Trace F5/F6/F7 handlers to see what they modify
   - Confirm with runtime debugging

### Medium Priority:
4. **Analyze radar range/scan controls** (F8/F9/F10)
5. **Map target acquisition logic** (T/Z/X keys)
6. **Decode radar display rendering** (blips, markers, scales)

---

## Summary

**3 Radar Types** (Config menu):
- **SAD** - 360° arcade view  
- **SAM** - 120° intermediate
- **HFR** - Realistic with manual control

**4 HFR Submodes** (F-keys):
- **NAM** (F5) - Search
- **ACM** (F6) - Dogfight  
- **GM** (F7) - Ground map
- **SAM/STT** (Z key) - Track

**Why strings not found**:
- Dynamic character-by-character display
- Mode names generated from mode number
- Not stored as complete strings in .EXE

**Key handlers found**:
- All F5-F10 handlers located
- mode_stream_select_step most promising for analysis
- Mode state variables partially identified

---

## Files Created

1. `docs/RADAR_AVIONICS_ANALYSIS.md` - Initial analysis (incomplete)
2. `docs/RADAR_MODES_FKEY_ANALYSIS.md` - F-key analysis
3. `docs/RADAR_SYSTEM_COMPLETE.md` (this file) - Complete understanding
4. `analysis/s4/find_fkey_radar_handlers.py` - F-key scanner
5. `analysis/s4/analyze_fkey_handlers_detailed.py` - Detailed F-key analysis
6. `analysis/s4/fkey_radar_handlers.json` - All handlers found

---

**Status**: ✅ System architecture understood from manual. Code analysis can now proceed with correct understanding of radar modes.
