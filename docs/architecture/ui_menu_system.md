# UI and Menu System Architecture

**Last Updated**: 2026-11-11  
**Status**: STRONG (byte-level analysis complete)  
**Analysis**: Based on deep-dive of 17 functions, 15,000+ bytes of code

---

## Overview

Falcon 3.0's UI and menu system is a sophisticated, performance-optimized architecture handling:
- Text rendering and layout
- Multi-device input (keyboard, mouse, joystick)
- Menu navigation and state management
- Random UI variation for "feel"
- Multi-graphics-mode support (VGA, EGA, CGA)

**Key Characteristic**: Heavy inline optimization (98.5% in input handler) for performance in the critical UI path.

---

## Architecture Layers

### Layer 1: Input System

```
Hardware (Keyboard/Mouse/Joystick)
    ↓
input_poll_handler (0x12FC43, 3814 bytes)
    ├─> bda_kb_flag_get (keyboard flags from 0x0040:0x0017)
    ├─> mouse_int33_dispatch (INT 33h)
    └─> [11 processing functions]
    ↓
Input Buffer & Flags (0x7894 segment)
    ├─> input_buffer[3] at 0x15A6
    ├─> input_flag_pending_1 at 0x79B68
    └─> input_flag_pending_2 at 0x79B66
    ↓
input_sync_and_wait (0x130A2F, 42 bytes, 194 CALLERS!)
    ↓
input_finalization (0x130B39, 183 bytes)
    ↓
Menu/Game Logic
```

### Layer 2: Rendering Pipeline

```
Menu Entry (e.g., ui_loadout_menu_enter)
    ↓
ui_text_render_engine (0x128518, 1282 bytes, 70 callers)
    ├─> Reads config: render_config_byte_1/2/3 (0x602E:0x14E76C-E)
    ├─> Checks graphics_mode_flag (0x7894:0x78940)
    └─> Special handling for '=' character (0x3D)
    ↓
ui_render_coordinator (0x128D5A, 900 bytes, 22 callers)
    ├─> Dispatches based on rendering mode
    └─> Manages rendering state
    ↓
Mode-Specific Adapters (60-62 bytes each)
    ├─> draw_primitive_mode_1 (0x12BE93)
    └─> draw_primitive_mode_2 (0x12BED1)
    ↓
VGA Memory Write (via dynamic function pointers)
    └─> vga_draw_func_ptr (0x22084, set at runtime)
```

### Layer 3: Menu State Management

```
Menu Initialization
    ↓
menu_state_init_with_random (0x12841F, 105 bytes)
    ├─> pit_channel0_latch_read (0x22C38, reads port 0x40)
    ├─> farobj_vec3_accum_b_ret × 4 (timing-based variation)
    └─> Populates menu_random_state (10 bytes at 0x602E:0x1400)
    ↓
Menu Slot Management
    ├─> ui_slot_scan_step (0x68159, 97 bytes)
    └─> current_menu_slot_ptr (0x602E:0x14F99C)
    ↓
Menu Navigation
    └─> menu_selection_ptr_get (0x2C3B5, 8 bytes, 14 callers)
```

---

## Key Functions

### Input Processing

| Function | Address | Size | Callers | Purpose |
|----------|---------|------|---------|---------|
| `input_poll_handler` | 0x12FC43 | 3814 bytes | 56 | Main input processing (K/M/J) |
| `input_sync_and_wait` | 0x130A2F | 42 bytes | **194** | Universal input synchronization |
| `input_finalization` | 0x130B39 | 183 bytes | 36 | Cleanup after input processed |
| `pit_channel0_latch_read` | 0x22C38 | 43 bytes | 14 | Read 8253 PIT for entropy |

### Rendering

| Function | Address | Size | Callers | Purpose |
|----------|---------|------|---------|---------|
| `ui_text_render_engine` | 0x128518 | 1282 bytes | 70 | Core text rendering |
| `ui_render_coordinator` | 0x128D5A | 900 bytes | 22 | Rendering dispatcher |
| `ui_text_render_loop` | 0x1295A9 | 54 bytes | 16 | Render N lines in loop |
| `draw_primitive_mode_1` | 0x12BE93 | 62 bytes | 6 | VGA adapter #1 |
| `draw_primitive_mode_2` | 0x12BED1 | 61 bytes | 6 | VGA adapter #2 |
| `draw_coord_wrapper` | 0x127FA7 | 29 bytes | 60 | Coordinate-based drawing |

### Menu Management

| Function | Address | Size | Callers | Purpose |
|----------|---------|------|---------|---------|
| `ui_loadout_menu_enter` | 0x683C1 | 4170 bytes | entry | Weapons loadout screen |
| `menu_state_init_with_random` | 0x12841F | 105 bytes | 1 | Initialize random UI state |
| `ui_slot_scan_step` | 0x68159 | 97 bytes | 1 | Menu slot iteration |
| `menu_selection_ptr_get` | 0x2C3B5 | 8 bytes | 14 | Get current menu slot |

### Utility

| Function | Address | Size | Callers | Purpose |
|----------|---------|------|---------|---------|
| `farobj_vec3_accum_b_ret` | 0x22C89 | 8 bytes | 142 | Vec3 math + pseudo-RNG |

---

## Data Structures

### Input State (Segment 0x7894)

```c
// Input synchronization flags
volatile uint16_t input_flag_pending_1;  // 0x7894:0x79B68
volatile uint16_t input_flag_pending_2;  // 0x7894:0x79B66

// Input buffer (3 words)
uint16_t input_buffer[3];                // 0x7894:0x15A6
// Hypothesis: [keyboard_state, mouse_state, joystick_state]

// Graphics mode flag
uint16_t graphics_mode_flag;             // 0x7894:0x78940
// 0 = text mode, non-zero = graphics mode

// Menu state pointer
void __far *menu_state_ptr;              // 0x7894:0x79B52
```

### Menu Random State (Segment 0x602E)

```c
// Structure at 0x602E:0x1400
struct menu_random_state {
    uint16_t frame_counter;    // +0x00: From global_frame_counter
    uint16_t random_value_1;   // +0x02: Timing-based pseudo-random
    uint16_t random_value_2;   // +0x04: Timing-based pseudo-random
    uint16_t random_value_3;   // +0x06: Timing-based pseudo-random
    uint16_t variant_index;    // +0x08: UI variant selector (0-3)
};  // Total: 10 bytes

// Current menu slot pointer
void __far *current_menu_slot_ptr;       // 0x602E:0x14F99C

// Rendering configuration
uint8_t render_config_byte_1;            // 0x602E:0x14E76C
uint8_t render_config_byte_2;            // 0x602E:0x14E76D
uint8_t render_config_byte_3;            // 0x602E:0x14E76E
```

### Global Counters (Segment 0x709F)

```c
// Global frame/loop counter
uint16_t global_frame_counter;           // 0x709F:0x70A2B

// Call counter
uint16_t call_counter;                   // 0x709F:0x70A2D
```

---

## Input System Details

### Input Sources

**1. Keyboard**
- **BIOS Data Area**: 0x0040:0x0017 (keyboard flags: Shift, Ctrl, Alt, etc.)
- **Hardware**: Keyboard controller (likely port 0x60 scan codes)
- **Processing**: Via `bda_kb_flag_get` and unknown callees

**2. Mouse**
- **Driver**: INT 33h (DOS mouse driver)
- **Operations**: Position, buttons, motion delta
- **Sensitivity**: `mouse_delta_scale_far_entry` applies scaling
- **Processing**: Via `mouse_int33_dispatch`

**3. Joystick**
- **Hardware**: Game port 0x201 (analog)
- **Processing**: Via unknown callees in input_poll_handler

### Input Synchronization Pattern

**Busy-Wait Loop** (194 callers use this pattern):

```c
void wait_for_input_ready(void) {
    // Busy-wait until both flags are clear
    while (input_flag_pending_1 != 0 || input_flag_pending_2 != 0) {
        input_poll_handler();
    }
    
    // Both flags zero - input processed
    input_finalization();
}
```

**Flag State Machine**:
- **State 0**: Ready for new input
- **State 1-2**: Input being processed
- **State 3**: Uninitialized (reset to 0 on first poll)

### Why Busy-Wait?

**1991 Design Rationale**:
- Simple and deterministic
- No interrupt handler complexity
- Fast response (no context switch)
- Works reliably in DOS
- Acceptable CPU usage on slower 1991 processors

---

## Rendering System Details

### Three-Tier Architecture

**Tier 1: Coordinators** (1000+ bytes)
- High-level logic, mode selection, state management
- Examples: `ui_text_render_engine`, `ui_render_coordinator`

**Tier 2: Adapters** (60-100 bytes)
- Mode-specific parameter marshaling
- Examples: `draw_primitive_mode_1`, `draw_primitive_mode_2`

**Tier 3: Primitives** (in overlays)
- Direct VGA memory writes
- Accessed via function pointers (e.g., `vga_draw_func_ptr`)

### Dynamic Graphics Mode Support

```c
// Function pointer set at runtime based on detected hardware
typedef void (__far *vga_draw_func_t)(...);

vga_draw_func_t vga_draw_func_ptr;  // at 0x22084

// Initialized during startup based on graphics_mode_flag:
// - VGA mode 13h (320×200×256)
// - EGA (16 colors)
// - CGA (4 colors)
// - MCGA
```

### Special Character Handling

The '=' character (ASCII 0x3D) has special rendering in `ui_text_render_engine`:
```c
if (char_or_attr == '=') {
    // Special rendering path
    // Likely: horizontal line, separator, box drawing
    goto special_equals_handler;
}
```

---

## Menu Random State System

### Purpose: UI Variation

The menu system uses timing-based pseudo-randomization to add "feel" and prevent memorization:

```c
void init_menu_with_variation(void) {
    // Seed with timer
    pit_channel0_latch_read();  // Reads port 0x40 three times
    
    // Get 4 "random" values via timing variation
    menu_random_state.random_value_1 = farobj_vec3_accum_b_ret();
    menu_random_state.random_value_2 = farobj_vec3_accum_b_ret();
    menu_random_state.random_value_3 = farobj_vec3_accum_b_ret();
    menu_random_state.variant_index = farobj_vec3_accum_b_ret() & 0x03;
    
    // Store global counter
    menu_random_state.frame_counter = global_frame_counter;
}
```

**How It Works**:
1. PIT timer provides microsecond-level timing variance
2. Vector accumulator function called 4 times
3. Each call has slightly different timing → different accumulated state
4. Results in pseudo-random values (not cryptographic, but good enough for UI)

**Uses**:
- Menu animation speed variation
- Item spawn position variation
- UI element placement variation
- Visual "life" to prevent static feel

**Elegant 1991 Hack**: Reuses existing vector math function as zero-overhead PRNG!

---

## Performance Characteristics

### input_poll_handler Optimization

**98.5% Inline Code**:
- 1205 instructions
- Only 18 function calls (1.5%)
- 657 MOV instructions (54.5%) - heavy data movement
- 132 CMP + 247 branches = complex state machine

**Why Monolithic?**:
- Avoids function call overhead (critical in 18.2 Hz game loop)
- Keeps input processing tight and fast
- Single function easier to optimize in 1991 compilers

**Tradeoff**: Performance over maintainability

### Universal Synchronization

**input_sync_and_wait**:
- Only 42 bytes
- Called from **194 locations**!
- Every interactive overlay depends on it
- Simple busy-wait loop
- Critical infrastructure function

**Impact**: ~30-60 calls per second during gameplay

---

## Overlay Integration

### Tail-Call Bridge Pattern

Menu functions use tail-call bridges to overlay functions:

```asm
menu_selection_ptr_get:     ; Base function (8 bytes)
    ; Minimal setup
    jmp far ptr ui_slot_scan_step  ; Jump to overlay
```

**Purpose**: 
- Maintains call interface while loading overlays
- Allows late binding to overlay code
- Keeps resident code small

### Overlay Function Pointers

Graphics operations use runtime-initialized function pointers:

```c
// Pointer at 0x22084 (initially NULL)
vga_draw_func_t vga_draw_func_ptr;

// Set during initialization based on detected hardware
if (vga_detected) {
    vga_draw_func_ptr = &vga_mode13_draw;
} else if (ega_detected) {
    vga_draw_func_ptr = &ega_draw;
} else if (cga_detected) {
    vga_draw_func_ptr = &cga_draw;
}
```

---

## Key Insights

### 1. Largest Single Function

`input_poll_handler` at 3814 bytes is unusually large for 1991 DOS code. Most games split input handling into 5-10 functions. This monolithic approach prioritizes performance.

### 2. Universal Synchronization Primitive

`input_sync_and_wait` with 194 callers is the universal input synchronization mechanism. Every interactive code path uses it.

### 3. Dual-Purpose Functions

`farobj_vec3_accum_b_ret` serves two purposes:
- Primary: Vector math (returns CX component)
- Secondary: Timing-based pseudo-RNG
- Zero overhead for dual use

### 4. Inline Performance Optimization

98.5% inline code in `input_poll_handler` shows aggressive optimization of critical path.

### 5. Simple Synchronization

Busy-wait over interrupts - simpler, more reliable for 1991 DOS environment.

---

## Comparison: 1991 vs Modern

| Aspect | Falcon 3.0 (1991) | Modern Games (2020s) |
|--------|-------------------|----------------------|
| **Input handler size** | 3,814 bytes (1 function) | Split into 10-50 functions |
| **Inline ratio** | 98.5% | Heavy abstraction/function calls |
| **Synchronization** | Busy-wait flags | Event queues, async callbacks |
| **Rendering tiers** | 3 tiers | Many abstraction layers |
| **Graphics modes** | Runtime function pointers | Shader systems, render graphs |
| **Input polling** | ~30-60 Hz | 125-1000 Hz |
| **Abstraction** | Direct hardware | OS API layers |

---

## Known Issues & Mysteries

### Resolved
- ✅ "menu_cursor_position_set" was misnomer (actually input_sync_and_wait)
- ✅ farobj_vec3_accum_b_ret dual purpose explained
- ✅ Complete input → rendering pipeline mapped
- ✅ Random state generation mechanism understood

### Remaining Mysteries

1. **7 unknown callees in input_poll_handler**:
   - undoc_130C80, undoc_130CE7, undoc_130E48
   - undoc_131001, undoc_131235, undoc_1312DF
   - Likely: joystick handling, key repeat, mouse acceleration

2. **Input buffer structure**:
   - What do the 3 words at 0x7894:0x15A6 represent?
   - Hypothesis: [keyboard_state, mouse_state, joystick_state]

3. **Menu slot structure**:
   - What fields does menu_slot contain?
   - Pointed to by current_menu_slot_ptr

4. **Compressed graphics formats**:
   - PEOPLE.DAT (pilot faces) - format unknown
   - MONITOR.DAT (setup screens) - format unknown
   - Likely uses overlay R02 decompressor

---

## Reference Addresses

### Functions (Segment:Offset)
```
input_poll_handler:          CS:0x12FC43 (3814 bytes)
input_sync_and_wait:         CS:0x130A2F (42 bytes, 194 callers)
input_finalization:          CS:0x130B39 (183 bytes)
ui_text_render_engine:       CS:0x128518 (1282 bytes, 70 callers)
ui_render_coordinator:       CS:0x128D5A (900 bytes)
menu_state_init_with_random: CS:0x12841F (105 bytes)
```

### Data (Segment:Offset)
```
input_flag_pending_1:        0x7894:0x79B68 (word)
input_flag_pending_2:        0x7894:0x79B66 (word)
input_buffer[3]:             0x7894:0x15A6  (3 words)
graphics_mode_flag:          0x7894:0x78940 (word)
menu_random_state:           0x602E:0x1400  (10 bytes)
current_menu_slot_ptr:       0x602E:0x14F99C (far pointer)
global_frame_counter:        0x709F:0x70A2B (word)
vga_draw_func_ptr:           CS:0x22084 (far function pointer)
```

---

## Related Documents

- **SESSION_SUMMARY_2026-11-11.md** - Complete analysis session
- **INPUT_POLL_HANDLER_ANALYSIS.md** - Deep-dive into 3814-byte function
- **MENU_ANALYSIS_PROGRESS.md** - Ongoing analysis tracking
- **hardware_io.md** - Hardware I/O details (keyboard, mouse, joystick)
- **game_loop.md** - Integration with main game loop

---

**Status**: STRONG certainty based on byte-level reverse engineering of 17 functions totaling 15,000+ bytes of code.
