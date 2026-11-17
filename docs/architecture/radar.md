# Falcon 3.0 Radar System Architecture

**Status:** 95% Complete  
**Last Updated:** 2026-11-17

---

## Overview

The Falcon 3.0 radar system provides three distinct radar types selectable in the configuration menu, with the High Fidelity Radar (HFR) offering four manual submodes controlled via F5/F6/F7 keys. The system integrates real-time target detection, tracking, and display rendering with simulated radar physics.

### Three Radar Types

| Type | Name | Coverage | Realism | F5/F6/F7 Submodes |
|------|------|----------|---------|-------------------|
| **SAD** | Situation Awareness Display | 360° sphere | Arcade | Disabled |
| **SAM** | Situation Awareness Mode | 120° front cone | Intermediate | Disabled |
| **HFR** | High Fidelity Radar | Manual control | Realistic | **Enabled** |

---

## Architecture Diagram

```
Configuration Menu (706Eh:+0x14)
        │
        │ Load at startup
        v
config_loader_radar_and_audio (0x484C1)
        │
        │ Transform: -(value - 2)
        v
    radar_type_selector (byte_59573)
    ┌────────┼────────┐
    │        │        │
  SAD(0)  SAM(1)  HFR(2)
    │        │        │
    └────────┴────────┘
            │
            │ In-flight: F5/F6/F7 pressed
            v
radar_f5f6f7_mode_dispatcher (0x6CDA8)
            │
            │ Check radar_type_selector
            │
    ┌───────┴───────┐
    │               │
 type≤1         type==2
 (Arcade)       (HFR)
    │               │
    v               v
mode=1          mode=3
(NAM-like)      (ACM)
    │               │
    └───────┬───────┘
            │
            │ Store to radar_mode_state (byte_595B2)
            │
            │ Per-frame update
            v
    radar_acm_target_step (0x39E13)
            │
            │ Check radar_type_selector
            │
    ┌───────┴───────┐
    │               │
 type≤1         type==2
    │               │
    v               v
steerpoint      Entity Scan
navigation      (16 entities)
                    │
                    │ Filter by flags:
                    │ - entity+0x74 bit 0 (ACTIVE)
                    │ - entity+0x74 bit 6 (AIRCRAFT_TYPE)
                    │ - entity+0x79 bit 0 (RADAR_VISIBLE)
                    │
                    v
            Target Found?
            ┌────┴────┐
            │         │
          Yes        No
            │         │
            v         v
        Extract    Default
        Position   Center
        (X,Y,Z)    (159,150)
            │         │
            └────┬────┘
                 │
                 │ Compute 3D perspective
                 │ display_x = ((alt-ref)*1584) + x
                 v
        radar_display_position_calculator (0x39D02)
                 │
                 │ Scale & bounds check
                 v
        Display bounds computed
        (left, right, center offset)
                 │
                 v
        Render mode text & reticle
        ("20 NAM", "20 ACM", etc.)
```

---

## Configuration Loading

### Segment 706Eh - Configuration Data

The radar type is stored in memory segment **706Eh** at offset **+0x14** (1 byte).

**Function:** `config_loader_radar_and_audio` (0x484C1, 126 bytes)

**Transformation:**
```c
uint8_t config_byte = config_segment[0x14];  // Raw value from config
radar_type_selector = -(config_byte - 2);     // Transform
```

**Mapping:**

| Config Byte | Calculation | Result | Radar Type |
|-------------|-------------|--------|------------|
| 0 | -(0-2) = 2 | 2 | HFR |
| 1 | -(1-2) = 1 | 1 | SAM |
| 2 | -(2-2) = 0 | 0 | SAD |

**Global Variable:** `radar_type_selector` (byte_59573, DS:0x59573)

### Configuration Segment Layout

| Offset | Size | Purpose |
|--------|------|---------|
| +0x08 | byte | Config param 1 |
| +0x0A | byte | Config param 2 |
| +0x0C | byte | Radar config related (byte_59574) |
| +0x0E | byte | Audio param (byte_55B4E) |
| +0x10 | byte | Audio param (byte_59380) |
| +0x12 | byte | Audio param (byte_59381) |
| **+0x14** | **byte** | **Radar type (transformed)** |
| +0x18 | byte | Audio param (byte_55B5F) |

---

## Mode State Machine

### Primary State Variable

**Global:** `radar_mode_state` (byte_595B2, DS:0x595B2)  
**Type:** `RadarModeState` enum (uint8)

| Value | Name | Description | Entry Condition |
|-------|------|-------------|-----------------|
| 0 | SEARCH | Radar on, no mode active | Initial state after R key |
| 1 | NAM | Normal Air Mode | F5 in HFR, or default in arcade |
| 2 | SAM | Situation Awareness Mode | Target within tracking range |
| 3 | ACM | Air Combat Maneuvering | F6 in HFR, close-range targets |
| 4 | DISABLED | Mode unavailable | Function returns immediately |
| 5 | STT | Single Target Track | Z key locks target |

### State Transitions

```
[Config Menu: Select SAD/SAM/HFR]
        │
        ↓
[In-Flight: R key] → radar_mode_state = 0 (SEARCH)
        │
        ↓
[F5/F6/F7 pressed] → radar_f5f6f7_mode_dispatcher
        │
        ├─ IF radar_type_selector ≤ 1 (SAD/SAM):
        │    radar_mode_state = 1 (NAM-like arcade)
        │
        └─ IF radar_type_selector == 2 (HFR):
             radar_mode_state = 3 (ACM realistic)
        │
        ↓
[Per-frame scanning]
        │
        ├─ IF target in range: radar_mode_state = 2 (SAM)
        │
        └─ IF Z key pressed: radar_mode_state = 5 (STT locked)
             │
             └─ IF X key pressed: radar_mode_state = 1/3 (break lock)
```

### HFR Submodes (Manual Controls)

Only available when `radar_type_selector == 2` (HFR mode):

| Key | Mode | Full Name | Scan Pattern |
|-----|------|-----------|--------------|
| **F5** | NAM | Normal Air Mode | Standard air search |
| **F6** | ACM | Air Combat Maneuvering | Close-range cycling |
| **F7** | GM | Ground Mapping | Ground targets |
| **Z** | SAM/STT | Target Lock | Lock progression |

**Additional HFR Controls:**

| Key | Function | Values |
|-----|----------|--------|
| F8 | Range | 10 / 20 / 40 / 80 nm |
| F9 | Azimuth | 20° / 60° / 120° |
| F10 | Elevation Bars | 1 / 2 / 4 / 6 |
| R | Radar On/Off | Toggle |
| T | Cycle Targets | Next target |
| X | Break Lock | Clear STT |

---

## Entity Detection & Tracking

### Entity Structure Fields

**Structure:** `EntitySlotRecord` (92 bytes, 16 slots at 0x54AF:0x386F)

**Radar-Relevant Fields:**

| Offset | Name | Type | Purpose |
|--------|------|------|---------|
| +0x74 | `status_flags` | `EntityStatusFlags` | Bit 0: ACTIVE, Bit 6: AIRCRAFT_TYPE |
| +0x79 | `tracking_flags` | `EntityTrackingFlags` | Bit 0: RADAR_VISIBLE (detection flag) |
| +0x96 | `position_x` | int16 | World X coordinate |
| +0x98 | `position_y` | int16 | World Y coordinate |
| +0x9A | `position_z` | int16 | Altitude |

### Entity Status Flags (entity+0x74)

**Enum:** `EntityStatusFlags` (uint8)

```c
#define ENTITY_STATUS_ACTIVE        0x01  // Bit 0: Entity is active/alive
#define ENTITY_STATUS_AIRCRAFT_TYPE 0x40  // Bit 6: Entity is aircraft (not ground unit)
```

**Radar Scanner Checks:**
```c
if (!(entity[+0x74] & 0x01)) continue;  // Skip if not active
if (!(entity[+0x74] & 0x40)) continue;  // Skip if not aircraft
```

### Entity Tracking Flags (entity+0x79)

**Enum:** `EntityTrackingFlags` (uint8)

```c
#define ENTITY_TRACKING_RADAR_VISIBLE 0x01  // Bit 0: Visible on radar
```

**Radar Scanner Checks:**
```c
if (!(entity[+0x79] & 0x01)) continue;  // Skip if not detected by radar
```

### Detection Mechanism

**Detection Flag Setting** (entity+0x79 bit 0):

The `RADAR_VISIBLE` flag is set by a **detection probability function** (not yet fully analyzed) that likely considers:

1. **Range:** Distance from player aircraft
   - Longer range → Lower detection probability
   - Affected by F8 setting (10/20/40/80 nm)

2. **Azimuth Coverage:** Horizontal scan angle
   - Narrower beam (20°) → Higher detection chance per target
   - Wider beam (120°) → Lower chance but more coverage
   - Affected by F9 setting

3. **Elevation Coverage:** Vertical scan bars
   - Fewer bars (1) → More energy per bar → Better detection
   - More bars (6) → Less energy per bar → Wider coverage
   - Affected by F10 setting

4. **Target Characteristics:**
   - RCS (Radar Cross Section) - size of aircraft
   - Aspect angle - front/rear/side profile
   - Altitude difference
   - Speed/velocity

5. **Environmental Factors:**
   - ECM/jamming (if modeled)
   - Weather conditions
   - Ground clutter

6. **Probability Calculation:**
   - Uses RNG to simulate realistic radar behavior
   - Detection is not guaranteed even in optimal conditions
   - Refreshed every N frames

**Current Analysis Status:** The detection probability logic is in a separate function (not yet identified) that runs before the scanner and sets the `RADAR_VISIBLE` flag. The scanner (`radar_acm_target_step`) only *reads* this flag, it doesn't compute detection.

---

## Target Scanning Algorithm

### Function: radar_acm_target_step (0x39E13)

**Size:** 266 bytes  
**Purpose:** F6 ACM target stepping - cycles through detected targets

**Algorithm:**

```c
// Mode checks
if (radar_mode_state == 4) return;  // Disabled
if (radar_mode_state == 5) {
    radar_stt_locked_target_handler();  // STT mode
    return;
}

// Radar type check
if (radar_type_selector <= 1) {
    // SAD/SAM arcade modes: no target tracking
    goto steerpoint_scan_update;
}

// Mode validity (must be 0 or 1 for scanning)
if (radar_mode_state != 0 && radar_mode_state != 1) return;

// Setup: Self-modifying code for entity array bounds
uint16_t boundary = radar_entity_array_scale * 4;
patch_instruction(0x39E69+2, boundary);  // Runtime code modification
patch_instruction(0x39E9C+2, boundary);

// Determine scan start point
uint16_t scan_index;
if (radar_selected_target_index == 0xFFFF) {
    scan_index = 0;  // No previous target: start from beginning
} else {
    scan_index = (radar_selected_target_index + 4) % 0x40;  // Continue from last
}

// Entity scan loop (max 16 entities)
for (int i = 0; i < 16; i++) {
    entity_ptr = entity_array_base + scan_index;
    
    // Filter #1: Active entity
    if (!(entity[+0x74] & ENTITY_STATUS_ACTIVE)) {
        scan_index = (scan_index + 4) % 0x40;
        continue;
    }
    
    // Filter #2: Aircraft type
    if (!(entity[+0x74] & ENTITY_STATUS_AIRCRAFT_TYPE)) {
        scan_index = (scan_index + 4) % 0x40;
        continue;
    }
    
    // Filter #3: Radar visible (detection flag)
    if (!(entity[+0x79] & ENTITY_TRACKING_RADAR_VISIBLE)) {
        scan_index = (scan_index + 4) % 0x40;
        continue;
    }
    
    // VALID TARGET FOUND
    int16_t target_x = entity[+0x96];
    int16_t target_y = entity[+0x98];
    int16_t target_alt = entity[+0x9A];
    
    // 3D perspective projection
    int16_t ref_alt = reference_altitude_ptr[+0x0C];
    int16_t alt_diff = target_alt - ref_alt;
    int32_t display_x_temp = (alt_diff * 1584) >> 16;  // Scale by 1584
    int16_t display_x = display_x_temp + target_x - 1;
    
    // Bounds check: Display X must be [96, 226]
    if (display_x < 96 || display_x > 226) {
        scan_index = (scan_index + 4) % 0x40;
        continue;
    }
    
    // TARGET ACCEPTED - Store and render
    radar_target_x_coordinate = target_x - 1;
    radar_target_y_coordinate = target_y;
    radar_display_x_adjusted = display_x;
    radar_selected_target_index = scan_index;
    
    radar_display_position_calculator();  // Compute display bounds
    return;
    
    scan_index = (scan_index + 4) % 0x40;
}

// NO TARGET FOUND - Default center position
radar_target_x_coordinate = 159;
radar_target_y_coordinate = 150;
radar_display_x_adjusted = 159;
radar_selected_target_index = 0xFFFF;  // Mark as no selection
radar_display_position_calculator();
```

### 3D Perspective Projection

**Formula:**
```
display_x = ((target_altitude - reference_altitude) * 1584) + target_x
```

**Purpose:** Create pseudo-3D effect on radar scope where altitude affects horizontal position. This helps the pilot visualize relative altitude at a glance.

**Scale Factor 1584:** Empirically determined constant that produces appropriate vertical separation visualization on the REO (Radar Electronics Officer) display.

**Bounds:** Display X must be in range [96, 226] pixels (130-pixel width) for valid rendering.

---

## Display Rendering

### Function: radar_display_position_calculator (0x39D02)

**Size:** 106 bytes  
**Purpose:** Calculate screen coordinates for radar target indicator

**Algorithm:**

```c
// Input: radar_display_x_adjusted (word_59597)
int16_t offset_from_center = radar_display_x_adjusted - 159;  // Center at 159
int32_t scaled = (offset_from_center * 2731) / 67;  // Scale factor

// Mode-specific bounds and clamping
int16_t bounds_left, bounds_right, center_offset;

switch (radar_display_mode_flag) {
case 0:  // Large bounds, hard clamping
    bounds_left = 0x1C7;   // 455
    bounds_right = 0xFE39; // -455 (signed)
    if (scaled > 0x8E4) scaled = 0x8E4;      // 2276
    if (scaled < 0xF71C) scaled = 0xF71C;    // -2276 (signed)
    center_offset = scaled;
    bounds_left += scaled;
    bounds_right += scaled;
    break;

case 1:  // Medium bounds, soft clamping
    bounds_left = 0x555;   // 1365
    bounds_right = 0xFAAB; // -1365 (signed)
    if (scaled > bounds_left) scaled = bounds_left;
    if (scaled < bounds_right) scaled = bounds_right;
    center_offset = scaled;
    bounds_left += scaled;
    bounds_right += scaled;
    break;

default:  // Mode 2+: Standard, no clamping
    bounds_left = 0xAAB;   // 2731
    bounds_right = 0xF555; // -2731 (signed)
    center_offset = 0;
    break;
}

// Store output
radar_display_bounds_left = bounds_left;
radar_display_bounds_right = bounds_right;
radar_display_center_offset = center_offset;
```

**Outputs:** These bounds define the screen region for rendering mode text and target reticle.

### Mode Text Rendering

**Format:** `"20 NAM"` where:
- `20` = Current range setting (from F8: 10/20/40/80)
- `NAM` = Mode name (NAM/ACM/GM/SAM/STT)

**Rendering Method:**
- **Character-by-character drawing** using font glyphs
- No stored string literals (explains why strings not found in binary)
- Position computed by `radar_display_position_calculator`
- Bounds: [`radar_display_bounds_left`, `radar_display_bounds_right`]

**Mode Abbreviations:**

| Enum Value | Abbreviation | Full Name |
|------------|--------------|-----------|
| 1 | NAM | Normal Air Mode |
| 2 | SAM | Situation Awareness Mode |
| 3 | ACM | Air Combat Maneuvering |
| 5 | STT | Single Target Track |
| - | GM | Ground Mapping (F7 in HFR) |

---

## Key Handler Functions

### 1. radar_f5f6f7_mode_dispatcher (0x6CDA8)

**Size:** 82 bytes  
**Entry:** Via jump table at `cs:off_6CDA0[bx]` where `bx` indexes the pressed key

**Pseudocode:**
```c
void radar_f5f6f7_mode_dispatcher(void) {
    // Common initialization
    radar_mode_flag = 0;
    radar_active_flag = 1;
    radar_selected_target_index = 0xFFFF;  // Clear target
    state_word_2e12b_set(0xFFFF);
    radar_state_word = 0xFFFF;
    
    // Branch on radar type
    if (radar_type_selector != 2) {
        // SAD/SAM arcade modes
        radar_state_flag = 3;
        radar_mode_state = 1;  // NAM-like
        radar_param_byte = 2;
        r06_state_init_e56();
        state_gate_4ac2_4a83(2);
    } else {
        // HFR realistic mode
        radar_state_flag = 3;
        radar_mode_state = 3;  // ACM
        radar_submode_flag = 0;
        goto r06_state_init_e55;
    }
}
```

**Key Finding:** F5/F6/F7 submodes only work in HFR mode. In arcade modes, all keys map to the same behavior.

### 2. radar_stt_locked_target_handler (0x2C12B)

**Size:** 8 bytes (stub function)  
**Purpose:** Handle STT locked target tracking

**Code:**
```asm
0x2C12B: call    near ptr tail_bridge_overlay_load  ; Misleading name
0x2C12E: jmp     loc_6CF43                          ; Jump to handler
```

**Target at 0x6CF43:**
```asm
0x6CF41: div     di              ; Range calculation
0x6CF43: mov     dx, 106h        ; Scale factor = 262
0x6CF46: mul     dx
0x6CF48: mov     ds:4A8Fh, dx    ; Store scaled range
```

**Purpose:** Continuous target tracking with auto-ranging when locked.

### 3. config_loader_radar_and_audio (0x484C1)

**Size:** 126 bytes  
**Purpose:** Load configuration from segment 706Eh at startup

See "Configuration Loading" section above.

---

## Global Variables

### Primary Control Variables

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x595B2 | `radar_mode_state` | `RadarModeState` | Current mode (0-5) |
| 0x59573 | `radar_type_selector` | `RadarType` | Type (0=SAD, 1=SAM, 2=HFR) |
| 0x5959B | `radar_selected_target_index` | uint16 | Entity index (0xFFFF=none) |

### Position & Display Variables

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x59595 | `radar_target_x_coordinate` | int16 | Target X (world) |
| 0x59597 | `radar_display_x_adjusted` | int16 | Display X with altitude |
| 0x59599 | `radar_target_y_coordinate` | int16 | Target Y (world) |
| 0x5958B | `radar_display_bounds_left` | int16 | Display left bound |
| 0x5958D | `radar_display_bounds_right` | int16 | Display right bound |
| 0x59585 | `radar_display_center_offset` | int16 | Display center offset |

### State Flags

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x595B4 | `radar_mode_flag` | uint8 | Mode flag (cleared on entry) |
| 0x595B3 | `radar_state_flag` | uint8 | State flag (set to 3) |
| 0x595AD | `radar_active_flag` | uint8 | Active (1=on) |
| 0x595AF | `radar_param_byte` | uint8 | Parameter (2 in non-HFR) |
| 0x595B1 | `radar_submode_flag` | uint8 | Submode (0 in HFR) |
| 0x595B6 | `radar_display_mode_flag` | `RadarDisplayMode` | Display mode (0/1/2) |
| 0x595B9 | `radar_temp_flag` | uint8 | Temp flag (scan) |

### Auxiliary Variables

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x593A8 | `radar_entity_array_scale` | uint16 | Array scale (*4 for boundary) |
| 0x593AA | `radar_reference_altitude_ptr` | uint16 | Ref altitude ptr |
| 0x593AC | `radar_state_word` | uint16 | State word |
| 0x59574 | `radar_config_byte_related` | uint8 | Related config |
| 0x59575 | `radar_config_flag_1` | uint8 | Config flag (0 or 2) |
| 0x59576 | `radar_config_flag_2` | uint8 | Config flag (0 or 4) |

**Complete documentation:** See `registry/globals.yaml`

---

## Self-Modifying Code

The radar scanner uses **runtime code modification** for dynamic bounds checking:

```c
uint16_t boundary = radar_entity_array_scale * 4;

// Patch immediate values in CMP instructions
*(uint16_t*)(0x39E69 + 2) = boundary;  // "cmp bx, <boundary>"
*(uint16_t*)(0x39E9C + 2) = boundary;  // "cmp bx, <boundary>"
```

**Purpose:** Dynamically adjust entity array size based on configuration without conditional branches.

**Pattern:** Common in DOS-era games for performance optimization.

---

## Radar Physics Simulation

### Power/Coverage Tradeoff

Classic radar physics applies to F8/F9/F10 settings:

**F8 (Range: 10/20/40/80 nm)**
- Longer range → Signal attenuates with distance² → Lower detection probability
- Short range (10nm): High chance within range
- Long range (80nm): Low chance but farther coverage

**F9 (Azimuth: 20°/60°/120°)**
- Narrow beam (20°): More focused energy → Higher detection chance per target
- Wide beam (120°): Spread energy → Lower chance but more coverage

**F10 (Elevation Bars: 1/2/4/6)**
- Fewer bars (1): Concentrated energy → Best detection in that altitude slice
- More bars (6): Divided energy → See all altitudes but weaker per layer

### Detection Probability Model (Hypothetical)

**Formula:** (Not yet confirmed in code)
```c
float detection_chance = 
    base_rcs_factor * 
    (1.0f / (range * range)) *          // Inverse square law
    (beam_power / azimuth_width) *      // Beam concentration
    (bar_power / elevation_bars) *      // Vertical division
    aspect_angle_factor *               // Front/rear/side
    (1.0f - ecm_effectiveness);         // ECM reduction

if (rand() < detection_chance) {
    entity[+0x79] |= ENTITY_TRACKING_RADAR_VISIBLE;
} else {
    entity[+0x79] &= ~ENTITY_TRACKING_RADAR_VISIBLE;
}
```

---

## Integration with Other Systems

### Entity System
- Reads entity position fields (+0x96, +0x98, +0x9A)
- Filters by status flags (+0x74, +0x79)
- Updates selected target index

### HUD System
- Radar display rendered on HUD overlay
- Mode text and target reticle positioned by bounds calculator
- Integrates with HUD brightness/color settings

### AI System
- AI-controlled aircraft have their `RADAR_VISIBLE` flags updated by detection logic
- Player's radar settings affect AI detection probability
- ECM systems may modify detection flags

### Input System
- F5/F6/F7 keys route through key dispatcher
- F8/F9/F10 modify radar parameters
- R toggles radar on/off
- Z/T/X control target lock/cycling

---

## Performance Considerations

### Per-Frame Cost

**radar_acm_target_step:**
- Checks up to 16 entities per frame
- Early rejection filters minimize processing
- Self-modifying code avoids branches
- Estimated: ~500-1000 CPU cycles per frame (negligible)

**Detection Probability Updates:**
- Likely runs every N frames (not every frame)
- Updates `RADAR_VISIBLE` flags for active entities
- More expensive than scanner (RNG, distance calculations)
- Estimated: Every 4-8 frames for performance

---

## Future Analysis

### Remaining 5%

1. **Detection Probability Function:**
   - Find where `entity+0x79 bit 0` is SET (not just read)
   - Locate RNG calls near entity processing
   - Analyze F8/F9/F10 parameter usage
   - Map detection chance formulas

2. **Character Rendering:**
   - Find function that draws "NAM", "ACM", "STT" text
   - Locate font glyph data
   - Trace from display bounds to pixel output

3. **Z Key Lock Progression:**
   - Find handler for Z key (scan code 0x2C)
   - Analyze mode transitions 1→2→3→5
   - Understand lock acquisition conditions

4. **X Key Break Lock:**
   - Find handler that clears mode 5 → 1/3
   - Target deselection logic

5. **Complete Entity Structure:**
   - Map remaining fields in EntitySlotRecord
   - Document all 92 bytes
   - Create comprehensive struct definition

---

## Testing & Verification

### In-Game Testing

1. **Configuration Menu:**
   - Set radar to SAD → Verify arcade behavior
   - Set radar to SAM → Verify 120° cone
   - Set radar to HFR → Verify F5/F6/F7 work

2. **HFR Mode:**
   - F5 (NAM) → Standard search
   - F6 (ACM) → Cycle targets
   - F7 (GM) → Ground mapping
   - Z → Lock target, observe STT mode

3. **Detection Testing:**
   - F8: Test range settings (10/20/40/80 nm)
   - F9: Test azimuth (20°/60°/120°)
   - F10: Test elevation bars (1/2/4/6)
   - Observe detection probability differences

4. **Memory Inspection:**
   - `DS:0x595B2` = Current mode (0-5)
   - `DS:0x59573` = Radar type (0/1/2)
   - `DS:0x5959B` = Target index (0xFFFF if none)
   - Entity+0x74/+0x79 flags for active aircraft

---

## References

### Primary Documents
- `analysis/RADAR_MODE_STATE_MACHINE.md` - State machine analysis
- `analysis/RADAR_SYSTEM_COMPLETE.md` - Comprehensive summary
- `analysis/mode_stream_select_interpretation.md` - Scanner function analysis
- `manual/extracted/f3keys.txt` - Key bindings reference
- `manual/chapters/09_f_l_i_g_h_t.txt` - Radar description from manual

### Registry Files
- `registry/globals.yaml` - 23 radar global variables
- `registry/functions.yaml` - 5 key radar functions
- `registry/structs.yaml` - EntitySlotRecord, enums

### Analysis Scripts
- `scripts/analyze_radar_system.py`
- `scripts/xrefs_mode_vars.py`
- `scripts/disasm_r06_mode_dispatch.py`

### IDA Database
- `analysis/ida_falconcd/FALCONCD.EXE.i64` - All functions renamed

---

**End of Radar System Architecture Document**
