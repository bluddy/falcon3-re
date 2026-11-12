# Falcon 3.0 Input System Deep Dive

**Version:** 1.0  
**Status:** Active Analysis  
**Last Updated:** 2026-11-11

## Executive Summary

The input system handles all **player control input** from keyboard, mouse, and joystick. With 74 functions identified, it translates raw hardware input into game commands and aircraft control.

**System Profile:**
- Functions: 74 identified
- Input Devices: Keyboard, mouse, joystick
- Role: Input handling and command mapping
- Update Rate: Polled every frame (~18 Hz)
- Complexity: Medium (device abstraction + command mapping)

**Analysis Progress:** 10% - Function count known, architecture to be discovered

## System Architecture

### Input Pipeline

```
[HARDWARE INPUT]
    ↓ Keyboard scan codes
    ↓ Mouse movement/buttons
    ↓ Joystick axes/buttons
    ↓
[INPUT SYSTEM - 74 functions]
    ↓
    1. READ HARDWARE
       ↓ Poll keyboard (INT 16h or direct port access)
       ↓ Read mouse (INT 33h mouse driver)
       ↓ Read joystick (port 0x201)
       ↓
    2. PROCESS INPUT
       ↓ Debounce buttons
       ↓ Apply deadzone to joystick
       ↓ Scale/calibrate axes
       ↓
    3. MAP TO COMMANDS
       ↓ Key → command (e.g., 'G' = gear up/down)
       ↓ Joystick axes → flight controls
       ↓ Buttons → weapons/views
       ↓
    4. OUTPUT COMMANDS
       ↓ Flight controls (pitch/roll/yaw/throttle)
       ↓ Weapons commands (fire/select)
       ↓ View commands (change view)
       ↓ System commands (pause/quit)
    ↓
[PHYSICS, WEAPONS, VIEW SYSTEMS]
```

### Integration Points

**Inputs (Hardware):**
- Keyboard: Scan codes from BIOS or direct port
- Mouse: Position delta and button state
- Joystick: Analog axes (X, Y, throttle) and buttons (2-4)

**Outputs (Commands):**
- Flight controls: pitch, roll, yaw, throttle (to physics system)
- Weapons: fire gun, launch missile, cycle weapon, select target (to weapons system)
- Views: cycle view, look direction (to camera/rendering system)
- HUD: cycle HUD mode (to HUD system)
- Game: pause, quit, options (to main loop)

**Callers:**
- `game_frame_pipeline_step` - Main game loop calls input system

**Callees:**
- BIOS interrupts (INT 16h keyboard, INT 33h mouse)
- Direct port I/O (joystick at 0x201)

## Core Functions

### Expected Function Categories

### 1. Keyboard Input (~15 functions)

- **input_keyboard_init**: Initialize keyboard handling
- **input_keyboard_read**: Read keyboard state
- **input_keyboard_poll**: Check for key press
- **input_keyboard_get_key**: Get pressed key (blocking or non-blocking)
- **input_keyboard_check_key**: Check if specific key is down
- **input_keyboard_flush**: Clear keyboard buffer

**Keyboard Access Methods:**
- BIOS INT 16h (standard, slow)
- Direct keyboard port (0x60/0x64) (fast, non-portable)

**Scan Codes vs. ASCII:**
- Scan codes: Hardware codes (e.g., 0x1C = Enter)
- ASCII: Character codes (e.g., 0x0D = Enter)
- Flight sim likely uses scan codes for better control detection

### 2. Mouse Input (~10 functions)

- **input_mouse_init**: Initialize mouse driver (INT 33h AX=0)
- **input_mouse_show**: Show mouse cursor
- **input_mouse_hide**: Hide mouse cursor
- **input_mouse_read**: Read mouse position and buttons
- **input_mouse_get_position**: Get (x, y) coordinates
- **input_mouse_get_delta**: Get movement delta since last read
- **input_mouse_get_buttons**: Get button state (left/right/middle)
- **input_mouse_set_sensitivity**: Set mouse sensitivity

**Mouse Usage:**
- View control (mouse look)
- Menu navigation
- Possibly targeting (clickable radar scope?)

### 3. Joystick Input (~15 functions)

- **input_joystick_init**: Initialize joystick
- **input_joystick_calibrate**: Calibrate joystick (min/max/center)
- **input_joystick_read**: Read all joystick axes and buttons
- **input_joystick_get_x**: Get X axis (roll)
- **input_joystick_get_y**: Get Y axis (pitch)
- **input_joystick_get_throttle**: Get throttle slider
- **input_joystick_get_rudder**: Get rudder axis (if available)
- **input_joystick_get_button**: Get button state
- **input_joystick_apply_deadzone**: Apply deadzone to axis
- **input_joystick_scale_axis**: Scale raw value to -100..+100 range

**Joystick Hardware (1991):**
- Game port at 0x201
- Analog axes via RC timing (read time for capacitor discharge)
- 2-4 buttons via digital inputs
- CH Flight Stick, Thrustmaster popular brands

**Calibration:**
- Center position (stick neutral)
- Min/max positions (stick extremes)
- Deadzone (ignore small movements near center)

### 4. Input Processing (~15 functions)

- **input_apply_deadzone**: Ignore input near zero (joystick centering)
- **input_scale_axis**: Convert raw input to game units
- **input_smooth_axis**: Apply smoothing filter (reduce jitter)
- **input_invert_axis**: Invert axis direction (for preferences)
- **input_clamp_value**: Clamp to valid range
- **input_debounce_button**: Prevent button bounce (multiple triggers)

**Deadzone:**
- Typical: ±5-10% near center
- Prevents aircraft drift when stick is "centered"

**Smoothing:**
- Running average or low-pass filter
- Reduces joystick jitter
- Trade-off: adds slight lag

### 5. Command Mapping (~12 functions)

- **input_map_key_to_command**: Map key press to game command
- **input_map_button_to_command**: Map joystick button to command
- **input_execute_command**: Execute mapped command
- **input_set_key_binding**: Change key binding (options menu)
- **input_get_key_binding**: Query current binding
- **input_load_key_bindings**: Load from config file
- **input_save_key_bindings**: Save to config file

**Command Examples:**
- Flight: pitch up/down, roll left/right, yaw left/right, throttle up/down, trim
- Weapons: fire gun, launch missile, cycle weapon, target select, radar lock
- Views: cycle view, look left/right/up/down, zoom
- HUD: HUD mode, declutter
- Game: pause, quit, screenshot

**Configurable Bindings:**
- Player can remap keys
- Stored in config file (FALCON3.CFG or similar)

### 6. Utility (~7 functions)

- **input_init**: Initialize all input devices
- **input_shutdown**: Cleanup input system
- **input_update**: Main update function (called per frame)
- **input_flush_all**: Clear all input buffers
- **input_wait_for_key**: Wait for any key press (menus, pauses)

## Input Devices Detail

### Keyboard

**Hardware Interface:**
- Scan codes from keyboard controller (Intel 8042)
- Port 0x60: Data port (read scan code)
- Port 0x64: Status/command port

**BIOS Interface:**
- INT 16h AH=0: Wait for key (blocking)
- INT 16h AH=1: Check for key (non-blocking)
- INT 16h AH=2: Get shift key status

**Common Flight Sim Keys (Expected):**
- Arrow keys: View direction
- Numpad: Trim controls
- Space: Brakes
- G: Gear up/down
- F: Flaps
- B: Speed brakes
- W: Cycle weapon
- T: Target select
- R: Radar lock
- Tab: Cycle HUD mode
- Esc: Pause/menu
- F1-F12: Various functions

### Mouse

**Hardware Interface:**
- Mouse driver INT 33h (software interrupt)
- INT 33h AX=0: Init/reset mouse
- INT 33h AX=3: Get position and button status
- INT 33h AX=11: Get motion counters (delta)

**Usage in Flight Sims:**
- View control (mouse look)
- Menu navigation
- Possibly radar scope interaction

**Sensitivity:**
- Raw mickey (mouse unit) to degrees conversion
- Adjustable in options

### Joystick

**Hardware Interface:**
- Game port at I/O address 0x201
- 4 analog axes (2 joysticks, X/Y each)
- 4 digital buttons

**Analog Axis Reading:**
- RC timing method (capacitor discharge)
- Write to 0x201 to trigger
- Read 0x201 and measure time until bit goes low
- Time proportional to axis position

**Typical F-16 Joystick Setup:**
- X axis: Roll (aileron)
- Y axis: Pitch (elevator)
- Throttle slider: Engine throttle
- Button 1: Fire gun/launch missile
- Button 2: Target select or view change

**Calibration Procedure:**
- Center stick, press button (record center)
- Move to all extremes, press button (record min/max)
- Store calibration values

## Data Structures

### Expected Structures (Need Verification)

```c
// Keyboard state
struct KeyboardState {
    uint8_t scan_code;        // Last scan code read
    uint8_t ascii_code;       // Corresponding ASCII code
    uint8_t key_down[128];    // Bitmap of keys currently down
    uint8_t shift_state;      // Shift, Ctrl, Alt status
};

// Mouse state
struct MouseState {
    int16_t x, y;             // Current position (pixels)
    int16_t dx, dy;           // Delta since last read
    uint8_t buttons;          // Button state (bit 0=left, 1=right, 2=middle)
    uint8_t sensitivity;      // Sensitivity multiplier
};

// Joystick calibration
struct JoystickCalibration {
    uint16_t x_min, x_center, x_max;
    uint16_t y_min, y_center, y_max;
    uint16_t throttle_min, throttle_max;
    uint8_t deadzone;         // Deadzone percent (0-20)
};

// Joystick state
struct JoystickState {
    int16_t x, y;             // Scaled -100 to +100
    int16_t throttle;         // Scaled 0 to 100
    int16_t rudder;           // If present
    uint8_t buttons;          // Button state bitmap
    JoystickCalibration cal;  // Calibration data
};

// Control inputs (output of input system)
struct ControlInputs {
    int16_t pitch;            // -100 to +100 (stick forward/back)
    int16_t roll;             // -100 to +100 (stick left/right)
    int16_t yaw;              // -100 to +100 (rudder)
    uint8_t throttle;         // 0-100% (or 0-150% with AB)
    int8_t pitch_trim;        // Trim settings
    int8_t rudder_trim;
};

// Key binding
struct KeyBinding {
    uint8_t scan_code;        // Keyboard scan code
    uint16_t command_id;      // Command enum value
};

// Command map
struct CommandMap {
    KeyBinding bindings[256]; // Map scan code to command
    uint8_t num_bindings;
};
```

### Memory Locations (Need Discovery)

- Keyboard state: Unknown (likely DGROUP)
- Mouse state: Unknown
- Joystick state: Unknown
- Control inputs: Unknown (output consumed by physics system)
- Key bindings: Unknown (loaded from config file)

## Performance Characteristics

### Expected Timings (1991 Hardware)

**Input Update Budget:** 0.5-1ms per frame

**Per-Device Costs (estimated):**
- Keyboard poll: 10-50 µs (BIOS call or port read)
- Mouse read: 50-100 µs (INT 33h call)
- Joystick read: 200-500 µs (RC timing for each axis)
- Input processing: 100-200 µs (scaling, deadzone, mapping)

**Total Input Cost:** 0.5-1ms (minor compared to physics, AI, rendering)

**Optimization:**
- Poll input only once per frame (not multiple times)
- Cache joystick values (reading joystick is slowest)
- Skip devices not in use (if no joystick, don't poll it)

## Integration with Other Systems

### Physics System

**Input controls physics:**
- Stick input → pitch/roll/yaw
- Throttle → engine thrust
- Physics system updates aircraft state

### Weapons System

**Input controls weapons:**
- Fire button → gun/missile launch
- Weapon select → change weapon
- Target select → designate target

### Camera/Rendering System

**Input controls view:**
- View keys/mouse → camera direction
- Zoom keys → FOV change

### HUD System

**Input controls HUD:**
- HUD mode key → change HUD display

### Main Game Loop

**Input controls game:**
- Pause key → pause game
- Quit key → exit game

## Discovery Status

### ✅ Completed

1. **Function Count:** 74 functions identified

### 🔄 In Progress

1. **Function List:** Need to extract actual function names
2. **Architecture:** Need to identify device-specific vs. processing functions
3. **Data Structures:** Need to find input state structures

### 📋 Next Steps

1. **Search for Input Functions:**
   - Pattern: "input_*", "keyboard_*", "mouse_*", "joystick_*", "joy_*"
   - Pattern: "control_*" (control input processing)
   - Search for strings: "calibrate", "deadzone", "key", "button"

2. **Categorize Functions:**
   - Keyboard input
   - Mouse input
   - Joystick input
   - Input processing
   - Command mapping

3. **Analyze Input Update:**
   - Find main input update function
   - Trace device polling
   - Map command execution

4. **Locate Input Data:**
   - Find keyboard/mouse/joystick state structures
   - Find control inputs structure
   - Find key bindings

5. **Test Calibration:**
   - Understand joystick calibration procedure
   - Map calibration data storage

## Open Questions

### Architecture
1. **Device Priority:** Which input device has priority (joystick vs. keyboard)?
2. **Input Mixing:** Can keyboard and joystick be used simultaneously?
3. **Buffering:** Are inputs buffered or immediate?

### Implementation
4. **Keyboard Method:** BIOS INT 16h or direct port access?
5. **Joystick Timing:** How is RC timing implemented?
6. **Calibration Storage:** Where are joystick calibration values stored?
7. **Key Bindings:** Are key bindings configurable? Stored in file?

### Performance
8. **Polling Rate:** Is input polled every frame or at fixed rate?
9. **Bottleneck:** Is joystick reading a performance concern?

### Data
10. **State Location:** Where are input state structures in memory?
11. **Command Map:** Where is the key-to-command mapping stored?

## Next Steps

1. **Search for input functions** - Build complete function list
2. **Analyze input update** - Understand input polling flow
3. **Map device interfaces** - Document keyboard/mouse/joystick access
4. **Locate input data** - Find state structures and bindings
5. **Test joystick calibration** - Understand calibration procedure
6. **Document key bindings** - Map default key assignments
7. **Update ARCHITECTURE.md** - Add input system details

## References

- **ARCHITECTURE.md**: Overall system structure
- **PHYSICS_SYSTEM.md**: Consumes control inputs
- **WEAPONS_AI_SYSTEM.md**: Consumes weapon commands
- **HUD_SYSTEM.md**: Consumes HUD mode commands
- **SYSTEM_MAP.md**: Initial discovery of 74 input functions

---

**Analysis Status:** Stage 1 - Function count known, architecture estimated, detailed analysis needed  
**Confidence:** Medium (architecture based on standard PC input methods)  
**Verification:** 10% (function count known, details need IDA analysis)
