# R45 Menu System Analysis

## Overview

**IDENTIFIED**: R45 is the **SQUADRON MANAGEMENT MENU** - the central hub for managing squadrons, pilots, missions, and campaign status.

The R45 overlay implements a comprehensive squadron management interface with state management and input handling. Analysis reveals a pattern similar to R57 (weapons loadout menu), with a state machine driving menu element rendering through repeated calls to a dispatcher and position calculator.

**Status**: IDENTIFIED - Squadron management menu with 9-11 menu options

## Function Summary

| Function | Address | Size | Purpose |
|----------|---------|------|---------|
| `overlay_r45_logic` | 0x156945 | 2614 bytes | Main menu state machine |
| `r45_menu_element_dispatcher` | 0x1573C3 | 167 bytes | Renders individual menu elements (called 9x) |
| `r45_position_calculator` | 0x1561B0 | 1132 bytes | Calculates UI positions and handles input |

## Segment Information

- **Segment**: R32_569Fs
- **Range**: 0x1560B0 - 0x15AAC0
- **Size**: 18,160 bytes

## Main State Machine: overlay_r45_logic

### Structure

**Address**: 0x156945  
**Size**: 2614 bytes (59 function calls)

The function follows a pattern identical to R57 loadout menu:
1. Initialize state variables
2. Main loop with state comparisons
3. Repeated calls to renderer + position calculator
4. Input processing

### State Variable

**Primary State**: `word_13E012` (0x13E012)
- Compared to value 5 at multiple locations
- Increment/decrement operations modify state
- Value 0xFFFF appears to be exit condition

### Key Initialization Sequence

```assembly
; Clear flags
mov es:word_79B60, 0
mov es:word_79E86, 0

; Apply font configuration
push es:word_13E012
call ui_font_config_apply

; Store previous state
mov ax, es:word_13E012
mov [bp+var_4], ax

; Initialize pointers
mov ax, word ptr es:dword_79E3A+2
mov dx, word ptr es:dword_79E3A
add dx, 3Dh
mov word ptr [bp+var_A+2], ax
mov word ptr [bp+var_A], dx
```

### Rendering Pattern

The menu is rendered through **9-10 repetitions** of this call sequence:
```assembly
call sub_1213 (r45_menu_element_dispatcher)
call sub_18C (r45_position_calculator)
call <utility_function>
```

**Example occurrences** (call addresses):
- 0x156D8B: dispatcher → 0x156D91: position → 0x156D96: utility (sub_102F)
- 0x156DF1: dispatcher → 0x156DF7: position → 0x156DFC: utility (sub_137C)
- 0x156E40: dispatcher → 0x156E46: position → 0x156E4B: utility (sub_C3)
- ... (9 total pairs)

This pattern indicates **9-10 menu elements** being rendered each frame.

## Core Function 1: r45_menu_element_dispatcher

### Overview

**Address**: 0x1573C3  
**Size**: 167 bytes (57 instructions)  
**Purpose**: Dispatches rendering for a single menu element

This is the "renderer" function called 9 times per frame. It's a small dispatcher that implements a **switch statement** (jump table) with **11 cases** (0-10), calling 6 different rendering functions based on element type.

### Switch Structure

```assembly
mov si, [bp+arg_0]     ; Element index
mov bx, si
cmp bx, 0Ah            ; switch 11 cases (0-10)
jbe short continue
jmp default_case
continue:
shl bx, 1              ; multiply by 2 for word index
jmp cs:jpt_1573D6[bx]  ; switch jump
```

### Render Functions Called

| Function | Address | IDA Name | Purpose |
|----------|---------|----------|---------|
| 1 | 0x1573EA | `ui_element_render_variant_a` | Render variant A (case 0) |
| 2 | 0x157400 | `ui_element_render_variant_b` | Render variant B (case 5) |
| 3 | 0x157417 | `undoc_11C576` | Utility renderer (case 6) |
| 4 | 0x157442 | `ui_element_render_complex_a` | Complex render A (case 7-8) |
| 5 | 0x157459 | `utility_11c90f` | Utility renderer (case 9-10) |
| 6 | 0x157461 | `ui_element_render_single` | Single element render |

### Strings Found in Dispatcher

**Primary menu option strings** (with formatting codes):

| Address | String | Element Type |
|---------|--------|--------------|
| 0x1519B1 | ".`SQUADRON" | Squadron selection button |
| 0x151895 | ".`PILOT INFORMATION" | Pilot info button |
| 0x1515BC | ".`COMMS." | Communications button |
| 0x1516AF | ".`DONE" | Exit button |

The `.` prefix appears to be a formatting/color code.

### Case Analysis

- **Case 0**: Render with `ui_element_render_variant_a` if `word_79E80 >= 0x12C`
- **Case 5**: Render with `ui_element_render_variant_b` if `word_79E80 >= 0x12C`
- **Case 6**: Render "SQUADRON" string with `undoc_11C576`
- **Cases 7-8**: Render with `ui_element_render_complex_a`
- **Cases 9-10**: Render with `utility_11c90f`
- **Cases 1-4**: Default case (no rendering?)

The `word_79E80` comparison suggests **conditional rendering** based on screen state or animation timer (0x12C = 300 decimal, possibly frame counter or coordinate).

### Data References

11 data references, including:
- String pointers for menu text
- `word_79E80`: Render condition flag/counter
- Element-specific data tables

## Core Function 2: r45_position_calculator

### Overview

**Address**: 0x1561B0 (originally sub_18C offset)  
**Size**: 1132 bytes (330 instructions)  
**Purpose**: Calculate UI positions, handle keyboard input, manage menu navigation

This is the "position calculator" called 9 times per frame, immediately after the dispatcher. It's significantly larger (1132 bytes vs 167 bytes), indicating complex logic for:
- Input handling (keyboard polling)
- Coordinate calculations
- Menu navigation state management

### Key Features

#### 1. Input Processing

Multiple references to input system globals:
- `input_scan_code_queue` (0x79B66): Keyboard scan code buffer
- `input_flag_pending_1` (0x79B68): Input pending flag
- Calls to `input_poll_handler` (sub_C3): Keyboard polling

**Input handling pattern**:
```assembly
; Clear input
mov es:input_scan_code_queue, 0
mov es:input_flag_pending_1, 0

; Poll for input
call input_poll_handler

; Check if input pending
cmp es:input_flag_pending_1, 0
jle loc_no_input

; Convert input to ENTER key (0x1C)
mov es:input_scan_code_queue, 1Ch
mov es:input_flag_pending_1, 0
```

This reveals the function converts various inputs into standardized scan codes for menu navigation.

#### 2. Jump Table

Contains a jump table at **0x15657C** (`jpt_1564A1`), indicating switch/case logic for handling different scan codes or menu states.

#### 3. State Management

References to state variable `word_13E012`:
- Multiple comparisons
- Increment/decrement operations
- Passed to other functions (sub_A02, sub_ABC)

#### 4. Coordinate Systems

References to multiple coordinate pointer globals:
- `dword_79E3A`: Primary UI pointer (offset by 0x3D)
- `dword_79E60`: Secondary pointer
- `dword_79E5C`: Tertiary pointer (offset by 0xAFC8)
- `dword_79E64`: Quaternary pointer
- `dword_79E68`: Another pointer (set to 0x4FC2:0x734)
- `dword_79E2C`: Yet another pointer (also 0x4FC2:0x734)

Calls to `ui_coordinate_transform` (sub_11F0) suggest transformation between different coordinate spaces (screen vs logical).

#### 5. Major Function Calls

| Function | Purpose (estimated) |
|----------|---------------------|
| `flag_block_zero_5762_5c63` (sub_5B87) | Flag/state initialization |
| `undoc_130B39` (sub_1139) | Unknown utility |
| `stub_to_1f6c_61df` (sub_B5) | Far stub |
| `ui_coordinate_transform` (sub_11F0) | Coordinate transformation |
| `event_irq_sync_handler` (sub_54B4) | IRQ sync (arg: 3) |
| `menu_record_field_copy` (sub_5403) | Copy menu data structures |
| `input_poll_handler` (sub_C3) | Keyboard input polling |

### Loop Structure

The function contains multiple nested loops:
1. Main event loop waiting for input
2. Inner loops for specific key handling
3. Iterative loops for menu element positioning

Evidence of loop with counter checking:
```assembly
inc si
cmp si, 0Bh  ; Loop 11 times
jl loop_start
```

This suggests iterating over 11 menu elements (matching the 9-10 dispatcher calls in the main state machine).

## Menu Element Structure

Based on the rendering pattern, the R45 menu likely has:
- **9-10 visible elements** rendered each frame
- **11 total elements** in the data structure (loop counter = 0xB)
- Each element processed through:
  1. `r45_menu_element_dispatcher`: Select rendering type
  2. `r45_position_calculator`: Calculate position and handle input
  3. Utility function: Perform element-specific operations

### Data Structure Hints

From position_calculator initialization:
```assembly
; 28-byte records (0x1C)
mov ax, si
mov dx, 1Ch
imul dx        ; si * 28 bytes
mov bx, ax
mov es, dx
mov word ptr es:[bx+606h], 4FC2h
mov word ptr es:[bx+604h], 0A68h
mov word ptr es:[bx+608h], 0Ah
```

**Element structure** (28 bytes per element):
- +0x604: Pointer low word (0x0A68)
- +0x606: Pointer high word (0x4FC2)
- +0x608: Value (0x0A = 10 decimal)

## Comparison with R57 Loadout Menu

| Feature | R57 Loadout | R45 Menu |
|---------|-------------|----------|
| **State variable** | `word_13E012` | `word_13E012` (same) |
| **State count** | 7 states | ~6 states (0-5 + exit) |
| **Elements** | Variable | 9-11 elements |
| **Renderer calls** | Multiple per state | 9-10 per frame |
| **Size** | 3083 bytes | 2614 bytes |
| **Architecture** | State machine + rendering | State machine + rendering |

Both menus share:
- Same state variable (`word_13E012`)
- Similar initialization sequences
- Font configuration via `ui_font_config_apply`
- Input handling through `input_poll_handler`
- Coordinate transformation systems
- Repeated renderer + calculator pattern

**Hypothesis**: R45 and R57 are **template-based menus** using a shared framework, with the specific differences being:
- Number of menu elements (R45: 9-11, R57: variable by state)
- Element types and rendering functions
- State machine complexity (R57 more complex with 7 states)

## Input Handling

### Scan Codes Processed

From the jump table and switch logic:
- `0x01`: ESC key (likely exit/cancel)
- `0x1C`: ENTER key (likely select/confirm)
- `0xFF`: Special code (possibly from mouse or synthetic input)

### Input Flow

1. **Poll keyboard**: `input_poll_handler`
2. **Check flag**: `input_flag_pending_1`
3. **Read scan code**: `input_scan_code_queue`
4. **Process code**: Jump table dispatch
5. **Update state**: Modify `word_13E012` or other state vars
6. **Clear input**: Reset queue and flags

## Menu Identification: Squadron Management

### Menu Elements (from strings found)

The dispatcher references 4 primary strings that identify the menu options:

1. **SQUADRON** (0x1519B1) - Squadron selection and management
2. **PILOT INFORMATION** (0x151895) - View/edit pilot details
3. **COMMS.** (0x1515BC) - Communications/multiplayer
4. **DONE** (0x1516AF) - Exit menu

### Complete String Database

Found **200+ strings** in segment R29_502Es related to squadron management:

**Squadron Management**:
- "SQUADRON NAME:", "SQUADRON COMMANDER:", "SQUADRON RECORDS"
- "SELECT SQUADRON", "DELETE SQUADRON", "SELECT INSIGNIA"
- "NUMBER OF MISSIONS FLOWN:", "NUMBER OF PILOTS ACTIVE:", "NUMBER OF PILOTS KILLED:", "NUMBER OF PILOTS MIA:"
- "AVAILABLE PILOTS:"

**Pilot Management**:
- "NAME:", "CALLSIGN:", "RANK:", "CURRENT STATUS:", "PILOT ABILITIES:"
- "MISSIONS:", "AWARDS:", "FLIGHT HOURS:", "PLANE KILLS:"
- "PILOT TRANSFER", "ADD FLIGHT", "ASSIGN PILOTS", "DELETE FLIGHT"
- "F-16 PILOTS"
- Status: "ACTIVE", "FATIGUED", "INJURED", "COURT MARTIALED"
- Ranks: "LT.", "CAPT.", "MAJOR", "LT COL.", "COL."

**Mission Management**:
- "CHOOSE MISSION", "CLEAR MISSION", "DELETE MISSION", "LOAD MISSION", "SAVE MISSION"
- "NEXT MISSION", "CURRENT MISSION:", "EDIT FLIGHTS"
- "MISSION #", "----MISSION #"

**Campaign Status**:
- "CAMPAIGN STATUS", "SUPPLY STATUS"
- "CURRENT DATE: DAY", "CURRENT TIME:"
- "MISSIONS FLOWN:", "MISSIONS ACCOMPLISHED:", "SORTIES FLOWN:"
- "ALLIED AIRCRAFT SHOT DOWN:", "ENEMY AIRCRAFT SHOT DOWN:"
- "GROUND TARGETS DESTROYED:", "ORDNANCE EFFICIENCY RATING:", "OVERALL CAMPAIGN RATING:"

**Multiplayer/Comms**:
- "Sending theater name to other players."
- "You must choose a squadron and theater before entering communications."
- "Waiting to transfer pilot info to squadron leader."
- "Sending pilot info to squadron leader."
- "Receiving pilot info from"
- "Sending squadron info to other pilots"
- "Receiving squadron info"

**Theater Selection**:
- "Kuwait", "Israel", "Panama", "Japan", "Korea", "India"

**Wings**:
- "1ST WING", "2ND WING", "3RD WING", "4TH WING", "5TH WING", "6TH WING", "7TH WING"

**Data Files**:
- "NAMES.BIN", "CALLSIGN.BIN", "sqdnames.str"

### Menu Element Count Hypothesis

Based on the 9-10 dispatcher calls and the string evidence, the likely menu elements are:

1. **SQUADRON** - Select/manage squadron
2. **PILOT INFORMATION** - View pilot details
3. **ASSIGN PILOTS** - Assign pilots to flights
4. **EDIT FLIGHTS** - Configure flight loadouts
5. **CHOOSE MISSION** - Select next mission
6. **CAMPAIGN STATUS** - View campaign progress
7. **SUPPLY STATUS** - View supply/equipment
8. **COMMS.** - Communications menu
9. **DONE** - Exit

Additional elements (explaining count of 11):
10. **LOAD/SAVE MISSION**
11. **Squadron name/insignia display** (non-interactive)

## Next Steps

1. ~~**Extract dispatcher render functions**~~ DONE - Found 6 render variants
2. ~~**Find string data**~~ DONE - Found 200+ strings, identified as Squadron Management menu
3. **Map the 9-11 menu elements** to their render functions and handlers
4. **Analyze jump table** at 0x15657C to understand input case handling
5. **Map element data structure** - Find the 28-byte element array at 0x4FC2:0x600
6. **Extract utility functions** (sub_102F, sub_137C, etc.) to understand element behavior
7. **Compare with R57 template** - Document shared framework vs menu-specific code
8. **Move to next menu**: R52 (flight briefing) or R53 (stream dispatcher)

## Unknown/TODO

### Element-to-String Mapping
We know there are 9-11 elements and found 4 primary strings in the dispatcher:
- Which element corresponds to which menu option?
- How are the other 5-7 elements rendered?
- Are some elements dynamic (e.g., mission list)?

### Utility Functions
The third function in each render cycle varies:
- `sub_102F`, `sub_137C`, `sub_C3` (input_poll_handler), others
- Need extraction to understand element-specific behavior

### Data Files
Found references to:
- `NAMES.BIN` - Pilot name database
- `CALLSIGN.BIN` - Callsign database  
- `sqdnames.str` - Squadron name strings
- Where are these loaded and how are they structured?

## Files

- **Extraction**: `analysis/ida_scripts/r45_menu_extraction.json`
- **Segment analysis**: `analysis/ida_scripts/r45_segment_analysis.json`
- **Core functions**: `analysis/ida_scripts/r45_core_functions.json`
- **String database**: `analysis/ida_scripts/r45_all_strings.txt` (200+ strings)
- **Relevant strings**: `analysis/ida_scripts/r45_relevant_strings.txt` (filtered menu strings)
- **This document**: `docs/R45_MENU_ANALYSIS.md`

## Summary

**R45 is the Squadron Management Menu** - confirmed through string analysis revealing 200+ UI strings including:
- Squadron selection and management
- Pilot roster and information
- Mission planning and status
- Campaign progress tracking
- Multiplayer communications
- Supply status

**Architecture**: Follows the same template-based menu framework as R57, with:
- State-driven rendering (9-10 elements per frame)
- Switch-based element dispatcher (11 cases)
- Input handling through jump table
- 28-byte element data structures
- Shared utility functions (`ui_font_config_apply`, `input_poll_handler`, coordinate transformers)

**Key Menu Options** (from string evidence):
1. SQUADRON - Squadron selection/management
2. PILOT INFORMATION - View pilot details
3. ASSIGN PILOTS - Configure flight rosters
4. EDIT FLIGHTS - Mission planning
5. CHOOSE MISSION - Mission selection
6. CAMPAIGN STATUS - Progress tracking
7. SUPPLY STATUS - Equipment status
8. COMMS. - Multiplayer
9. DONE - Exit

This analysis establishes R45 as the **central campaign management interface** in Falcon 3.0.
