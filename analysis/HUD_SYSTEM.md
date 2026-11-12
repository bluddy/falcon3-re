# Falcon 3.0 HUD System Deep Dive

**Version:** 1.0  
**Status:** Active Analysis  
**Last Updated:** 2026-11-11

## Executive Summary

The HUD (Heads-Up Display) system manages the **logic and state** for all cockpit instruments, targeting displays, and pilot-facing information. With 30+ functions identified, it generates the data and commands that the overlay system renders.

**Architecture:** Two-stage design separating **logic (HUD system)** from **rendering (overlay system)**. The HUD system computes what to display, the overlay system draws it.

**System Profile:**
- Functions: 30+ identified
- Role: Logic and state management
- Output: Overlay commands for rendering
- Integration: Feeds overlay system
- Inputs: Game state, sensors, targeting, flight data
- Complexity: Medium (substantial logic layer)

**Analysis Progress:** 15% - Architecture understood, function count estimated, detailed analysis needed

## System Architecture

### Two-Stage Design

```
[GAME STATE]
  ↓ (flight data, sensors, targeting)
  ↓
[HUD SYSTEM - Logic & State]
  ↓ Compute what to display
  ↓ Generate overlay commands
  ↓
[OVERLAY SYSTEM - Rendering]
  ↓ Draw lines, circles, text
  ↓
[SCREEN]
```

**Separation of Concerns:**
- **HUD System:** What to show, where, and when
- **Overlay System:** How to draw it

**Benefits:**
- Clean architecture (logic vs. rendering)
- Reusable overlay primitives
- Easier to modify HUD layout without touching rendering
- Better testability

### Data Flow

```
game_frame_pipeline_step (0x2D98F)
    ↓
[HUD UPDATE FUNCTIONS]
    ↓ Read game state (speed, altitude, heading, etc.)
    ↓ Compute derived values (lead angle, range to target, etc.)
    ↓ Generate overlay commands (draw airspeed tape, heading ladder, etc.)
    ↓
[Overlay command buffer]
    ↓
view_projection (0x202DB)
    ↓
overlay_tail_bridge (0x2C09F)
    ↓
[OVERLAY RENDERING]
```

### Integration Points

**Inputs (Game State):**
- Flight data: airspeed, altitude, vertical speed, G-force
- Attitude: pitch, roll, heading
- Navigation: waypoint, distance, ETA
- Weapons: selected weapon, ammo count, lock status
- Sensors: radar contacts, threat warnings
- Systems: fuel, hydraulics, electrical, warnings

**Outputs (Overlay Commands):**
- Draw line (x1, y1, x2, y2, color)
- Draw circle (cx, cy, radius, color)
- Draw arc (cx, cy, radius, start_angle, end_angle, color)
- Draw text (x, y, string, color)
- Draw sprite (x, y, sprite_id)

**Called From:**
- `game_frame_pipeline_step` or similar main loop function
- Possibly input handlers (to update HUD mode)

**Calls To:**
- Game state accessors (get airspeed, get altitude, etc.)
- Math functions (trigonometry for lead angles, projections)
- Overlay command buffer management

## Core Functions (Expected)

### Status: NEEDS DISCOVERY

The 30+ HUD functions likely fall into these categories:

### 1. Primary Flight Display (~8 functions)

- **hud_draw_airspeed**: Airspeed tape on left side
- **hud_draw_altitude**: Altitude tape on right side
- **hud_draw_vsi**: Vertical speed indicator
- **hud_draw_aoa**: Angle of attack indicator
- **hud_draw_gforce**: G-force meter
- **hud_draw_horizon**: Artificial horizon line
- **hud_draw_pitch_ladder**: Pitch ladder (angle markers)
- **hud_draw_heading_tape**: Heading tape at top

### 2. Navigation Display (~5 functions)

- **hud_draw_compass**: Compass rose
- **hud_draw_waypoint**: Waypoint indicator
- **hud_draw_range**: Range to target/waypoint
- **hud_draw_eta**: Estimated time to arrival
- **hud_draw_course**: Course deviation indicator

### 3. Targeting System (~8 functions)

- **hud_draw_reticle**: Gun sight reticle
- **hud_draw_target_box**: Target designation box
- **hud_draw_lead_indicator**: Gun lead computing sight
- **hud_draw_missile_diamond**: Air-to-air missile cue
- **hud_draw_bomb_fall_line**: Air-to-ground bomb release cue
- **hud_draw_lock_indicator**: Radar/IR lock indicator
- **hud_draw_range_to_target**: Target range readout
- **hud_draw_closure_rate**: Closure rate to target

### 4. Weapons Status (~4 functions)

- **hud_draw_weapon_select**: Current weapon indication
- **hud_draw_ammo_count**: Remaining ammo
- **hud_draw_missile_count**: Missile inventory
- **hud_draw_weapon_status**: Weapon ready/not ready

### 5. Systems Status (~3 functions)

- **hud_draw_fuel**: Fuel quantity
- **hud_draw_warnings**: Master caution/warning
- **hud_draw_gear_status**: Landing gear position

### 6. Utility/Management (~2+ functions)

- **hud_init**: Initialize HUD system
- **hud_update**: Main update function (called per frame)
- **hud_set_mode**: Change HUD mode (air-to-air, air-to-ground, nav, etc.)

## HUD Modes

### Expected Modes

Flight sims typically have multiple HUD modes optimized for different mission phases:

1. **NAV Mode** (Navigation)
   - Emphasis on flight data (speed, altitude, heading)
   - Waypoint and course guidance
   - Minimal weapons info

2. **A/A Mode** (Air-to-Air)
   - Gun reticle prominent
   - Lead indicator active
   - Missile diamond cue
   - Target box and lock status
   - Closure rate and range

3. **A/G Mode** (Air-to-Ground)
   - Bomb fall line (CCIP - Continuously Computed Impact Point)
   - Dive angle
   - Release cue
   - Ground target designation

4. **LAND Mode** (Landing)
   - Glideslope indicator
   - AoA bracket (for proper approach angle)
   - Gear and flaps status
   - Airspeed emphasizing approach speed

**Mode Switching:**
- Likely via specific key bindings
- Possibly automatic based on weapons selection
- Stored in HUD state variable

## Data Structures

### Expected Structures (Need Verification)

```c
// HUD state
struct HUDState {
    uint8_t mode;              // 0=NAV, 1=A/A, 2=A/G, 3=LAND
    uint8_t brightness;        // HUD brightness (0-15)
    uint8_t declutter_level;   // Declutter mode (hide less important elements)
    uint8_t flags;             // Various boolean states
    
    // Cached computed values (to avoid recomputing every element)
    int16_t screen_center_x;
    int16_t screen_center_y;
    int16_t pixels_per_degree;  // For angular elements (pitch ladder, etc.)
};

// Overlay command (sent to overlay system)
struct OverlayCommand {
    uint8_t type;        // LINE, CIRCLE, ARC, TEXT, SPRITE
    uint8_t color;
    int16_t x1, y1;
    int16_t x2, y2;      // or radius, or string pointer
    void* extra_data;
};

// Overlay command buffer
struct OverlayCommandBuffer {
    uint16_t count;
    uint16_t capacity;
    OverlayCommand commands[MAX_OVERLAY_COMMANDS];
};
```

### Memory Locations (Need Discovery)

- HUD state: Unknown (likely in DGROUP)
- Overlay command buffer: Unknown (likely static buffer in DGROUP)
- Font data: Unknown
- Mode constants: Unknown

## HUD Elements Detail

### Airspeed Tape

**Purpose:** Display current airspeed

**Typical Design:**
- Vertical tape on left side of screen
- Current airspeed in center box
- Tick marks every 10-20 knots
- Scrolling tape (only show ±100 knots around current speed)
- Color coding: green arc (safe range), yellow/red (caution/danger)

**Implementation:**
1. Get current airspeed from game state
2. Compute tape position (scroll offset)
3. Generate overlay commands:
   - Draw vertical line (tape edge)
   - Draw tick marks (every 10 knots visible)
   - Draw numbers (every 50 knots)
   - Draw current speed box

### Heading Tape

**Purpose:** Display current heading (compass direction)

**Typical Design:**
- Horizontal tape at top of screen
- Current heading in center
- Cardinal directions (N, S, E, W) and intermediate (NE, SW, etc.)
- Tick marks every 10 degrees
- Scrolling tape

**Implementation:**
1. Get current heading from game state (0-360 degrees)
2. Compute tape position (handle 360° wrap-around)
3. Generate overlay commands:
   - Draw horizontal line (tape edge)
   - Draw tick marks
   - Draw cardinal direction letters
   - Draw current heading number

### Target Box

**Purpose:** Designate current target

**Typical Design:**
- Box or brackets around target on screen
- Uses 3D projection (target world pos → screen pos)
- Color indicates lock status (white=designated, red=locked)
- May flash or pulse

**Implementation:**
1. Get target position from targeting system
2. Transform world coords to screen coords (3D projection)
3. Check if on screen (clipping)
4. Generate overlay commands:
   - Draw 4 corner brackets or closed box
   - Draw range text below box
   - Draw closure rate (if applicable)

### Pitch Ladder

**Purpose:** Show aircraft pitch relative to horizon

**Typical Design:**
- Horizontal lines at 5° or 10° pitch increments
- Lines above horizon (positive pitch) and below (negative pitch)
- Horizon line (0°) may be thicker or different color
- Lines may be shorter for larger angles

**Implementation:**
1. Get aircraft pitch and roll from game state
2. For each ladder rung (-30° to +30° in 10° steps):
   - Compute screen position based on pitch and roll
   - Apply roll rotation (ladder rolls with aircraft)
   - Generate overlay commands to draw line

## Performance Characteristics

### Expected Timings (1991 Hardware)

**HUD Update Budget:** 1-3ms per frame

**Per-Element Costs (estimated):**
- Simple readout (airspeed, altitude): 10-50 µs (read value, format string, queue overlay cmd)
- Tape display (airspeed tape, heading tape): 100-300 µs (compute scroll position, generate multiple line/text cmds)
- 3D-projected element (target box): 200-500 µs (3D transform, clipping, generate cmds)
- Pitch ladder: 300-600 µs (compute 6-12 rungs with rotation)

**Total HUD Cost:** 1-3ms (overlay rendering adds another 2-5ms)

**Optimization Strategies:**
- Update only changed elements (don't regenerate entire HUD if only airspeed changed)
- Cache expensive calculations (3D projections, trig for pitch ladder)
- Declutter mode (hide non-essential elements to reduce cost)
- Fixed-point math (avoid floating point)

## Integration with Other Systems

### Overlay System

**Tight Integration:**
- HUD generates commands
- Overlay renders them
- Clean separation of concerns

### Targeting System

**HUD displays targeting data:**
- Current target position → target box
- Lock status → color/symbol
- Weapon solutions → lead indicators, bomb fall line

### Flight Model

**HUD displays flight data:**
- Airspeed, altitude, VSI
- Pitch, roll, heading
- AoA, G-force

### Weapons System

**HUD displays weapons status:**
- Selected weapon
- Ammo count
- Weapon ready status

### Input System

**Input affects HUD:**
- HUD mode selection (key bindings)
- Target designation (TMS - Target Management Switch)
- HUD brightness adjust

## Discovery Status

### ✅ Completed

1. **Architecture:** Two-stage design (logic vs. rendering) understood
2. **Function Count:** 30+ functions estimated
3. **Integration:** Feeds overlay system, consumes game state

### 🔄 In Progress

1. **Function List:** Need to extract actual HUD function names
2. **Modes:** Need to identify HUD mode implementation
3. **Command Buffer:** Need to locate overlay command buffer

### 📋 Next Steps

1. **Search for HUD Functions:**
   - Pattern: "hud_*"
   - Pattern: "draw_*" (if HUD and overlay use same prefix)
   - Search for strings: "airspeed", "altitude", "heading", etc.

2. **Analyze HUD Update:**
   - Find main HUD update function
   - Trace what it calls
   - Map call graph

3. **Locate Command Buffer:**
   - Search for overlay command writes
   - Find buffer allocation
   - Identify command structure

4. **Identify HUD Modes:**
   - Search for mode switching code
   - Find mode constants/enum
   - Map mode-specific rendering

5. **Map Elements:**
   - Categorize functions by HUD element
   - Document each element's implementation
   - Identify shared utilities

6. **Profile Performance:**
   - Measure HUD update cost
   - Identify expensive elements
   - Check for optimization opportunities

## Open Questions

### Architecture
1. **Command Buffer:** Where is the overlay command buffer? How large?
2. **Update Frequency:** Is HUD updated every frame or less frequently?
3. **Modes:** How many HUD modes? How are they switched?
4. **Declutter:** Is there a declutter mode to hide non-essential elements?

### Implementation
5. **3D Projection:** Does HUD system do its own 3D projection or use rendering system?
6. **Text Formatting:** How are numbers formatted (sprintf equivalent)?
7. **Color Management:** How are HUD element colors defined?
8. **Priority:** If command buffer fills, which elements have priority?

### Performance
9. **Hotspot:** Which HUD element costs the most to update?
10. **Optimization:** Is there any caching or dirty-flag optimization?
11. **Bottleneck:** Is HUD update a performance concern?

### Data
12. **State Location:** Where is HUD state stored in memory?
13. **Constants:** Where are HUD layout constants (tape positions, font sizes, etc.)?
14. **Assets:** Where are HUD-specific assets (fonts, symbols)?

## Next Steps

1. **Search for HUD functions** - Build complete function list
2. **Disassemble main update** - Understand HUD update flow
3. **Locate command buffer** - Find overlay command data structure
4. **Map HUD modes** - Identify mode switching and mode-specific logic
5. **Profile execution** - Measure HUD update cost
6. **Document elements** - Complete analysis of key HUD elements
7. **Update ARCHITECTURE.md** - Add HUD system details

## References

- **ARCHITECTURE.md**: Overall system structure
- **OVERLAY_SYSTEM.md**: Rendering system that draws HUD (downstream)
- **RENDERING_SYSTEM.md**: 3D rendering (for 3D-projected HUD elements)
- **SYSTEM_MAP.md**: Initial discovery of 30+ HUD functions

---

**Analysis Status:** Stage 1 - Architecture defined, function count estimated, detailed analysis needed  
**Confidence:** Medium (architecture based on typical flight sim design), Low (implementation details)  
**Verification:** 15% (architecture assumptions need IDA verification)
