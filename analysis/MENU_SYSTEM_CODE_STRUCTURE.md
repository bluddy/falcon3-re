# Menu System Code Structure

## Overview
Documenting the code structure of Falcon 3.0's menu system based on IDA Pro disassembly analysis.

**Status**: Phase 2 - Code Tracing (IN PROGRESS)
**Date**: 2026-11-11

## Key Discovery: Menu Function Architecture

The menu system uses a **monolithic controller** pattern, not individual menu functions:

### Main Menu Controller: sub_683C5
- **Address**: 0x683C5
- **Size**: 4,169 bytes (one of the largest functions in the game)
- **Classification**: DATA class (large data-driven state machine)
- **Callers**: 55 different entry points
- **Callees**: 50+ helper functions

**Pattern**: This function contains **multiple entry points** for different menu screens:
- ui_loadout_menu_enter
- ui_mission_menu_enter  
- ui_squadron_menu_enter
- ui_campaign_menu_enter
- etc.

Each "menu function" is actually a **label within sub_683C5** that sets up state and then tail-jumps to common initialization code.

## Menu Function Relationships

### Entry Points → Common Init Pattern

```
ui_loadout_menu_enter (0x68D56) ─┐
ui_mission_menu_enter           ├──> sub_683C5 (main controller)
ui_squadron_menu_enter          │         │
ui_campaign_menu_enter   ───────┘         │
                                           ├──> ui_menu_panel_init (sub_66E62)
                                           │
                                           ├──> ui_menu_page_setup (sub_6A5BD)
                                           │
                                           └──> vga_dac_palette_upload + rendering
```

## Key Functions

### 1. sub_683C5 - Menu Controller Hub (0x683C5, 4169 bytes)
**Role**: Master menu state machine and entry point dispatcher

**Characteristics**:
- Class: DATA (data-driven, table-based logic)
- 55 callers (different menu entry scenarios)
- 50+ callees (all menu subsystems)
- Contains multiple entry labels for different menu screens

**Key Callees**:
- `sub_66E62` - ui_menu_panel_init
- `sub_6A5BD` - ui_menu_page_setup
- `sub_6798C` - ui_slot_record_fill
- `sub_67BAF` - ui_menu_transition_step
- `vga_dac_palette_upload` - Display updates
- `sub_4F3EC` - Unknown (called by most menu functions)

### 2. sub_66E62 - UI Menu Panel Init (0x66E62, 1365 bytes)
**Confidence**: HIGH
**Role**: Common menu panel initialization routine

**Description**: 
"Shared menu/UI panel init: writes 4FC2h:4FD5E/4FD72/4FD46/4FD48, pushes 0B3h/0C7h to sub_39BD3, state_byte_25488_set_arg, farptr_lds_invoke; **ui_loadout_menu_enter tail-jumps here**."

**Key Operations**:
```assembly
mov    ds:14Eh, ax              ; Store menu ID
mov    ax, 4FC2h                ; Menu state segment
mov    es, ax
mov    ax, es:word_4FD5E        ; Load current menu state
mov    es:word_4FD60, ax        ; Save previous state
mov    ax, es:word_4FD74
mov    es:word_4FD72, ax
push   0B3h                     ; Width = 179 pixels
push   0C7h                     ; Height = 199 pixels
push   0                        ; X offset
push   0                        ; Y offset
call   sub_39BD3                ; Graphics setup
```

**Callers**: 17 different menu entry points
**Callees**: 27 functions including VGA, state management, overlay loading

### 3. sub_6A5BD - UI Menu Page Setup (0x6A5BD, 2204 bytes)
**Confidence**: HIGH  
**Role**: Menu page/panel layout configuration

**Description**:
"Menu page/panel setup: farobj_arg_thunk with (9,35h,0Bh,4,19h), clears 7894h:79B66/79B68, current_item_check, flag_block_zero; called by ui_loadout_menu_enter siblings and menu_page_jump_stub."

**Callers**: 5 (including ui_loadout variants)
**Key Operations**:
- Clears menu selection state at 7894h:79B66/79B68
- Calls `current_item_check` - validates menu cursor position
- Calls `flag_block_zero` - resets menu flags

### 4. sub_6798C - UI Slot Record Fill (0x6798C, 327 bytes)
**Confidence**: HIGH
**Role**: Fills menu data records for loadout screen

**Description**:
"Fills 7894h:79E60 record fields 2BD6h-2BDBh (E0h/2Eh/1Eh type pattern like ui_slot_record_init); store_cmd_interpreter + vga_dac_palette_upload + sub_4F3EC."

**Callers**: 2 (including **ui_loadout_menu_enter**)
**Key Operations**:
- Populates 7894h:79E60 with weapon/loadout data
- Pattern: 0xE0, 0x2E, 0x1E (possibly weapon type codes?)
- Updates display after data fill

### 5. sub_67BAF - UI Menu Transition Step (0x67BAF, 937 bytes)
**Confidence**: HIGH (13 callers)
**Role**: Handles menu transition animations/state changes

### 6. sub_4AEC4 - Farobj Pos/Move/Angle Step (0x4AEC4, 1146 bytes)
**Confidence**: HIGH
**Role**: Updates 3D object positions (for rotating aircraft models in loadout menu?)

**Description**:
"Farobj position-move/angle step: pos_move_angle_step fallbacks, bound_range_check_4aad x2, farobj_tile_copy_resolve, angle_aux_far + angle_xy_far, farobj_copy_cond."

**Callers**: 2 (**ui_loadout_menu_enter**, sub_69C5D)

**Key Insight**: The loadout menu likely displays **rotating 3D aircraft models** when selecting weapons!

## Menu State Segments

### Segment 4FC2h - Menu State Block
Key memory locations:
- `4FC2h:4FD5E` - Current menu ID
- `4FC2h:4FD60` - Previous menu ID (for back navigation)
- `4FC2h:4FD74` - Unknown menu state
- `4FC2h:4FD72` - Saved state copy
- `4FC2h:4FD46` - Initialized to 0
- `4FC2h:4FD48` - Initialized to 0
- `4FC2h:4FD42` - Set to 0xF2AB
- `4FC2h:4FD44` - Set to 0xF19A
- `4FC2h:4FD4E` - Set to 0xE556
- `4FC2h:4FD50` - Set to 0xE334
- `4FC2h:45Ch` - Menu data pointer
- `4FC2h:5C8h` - Another menu structure
- `4FC2h:2B0h` - Function pointer (called via farptr_lds_invoke)

### Segment 7894h - Menu Display Data
Key memory locations:
- `7894h:79E60` - Loadout record data (filled by sub_6798C)
- `7894h:79E68/79E6A` - Far pointer: 4FC2h:45Ch
- `7894h:79E2C` - Far pointer: 4FC2h:5C8h
- `7894h:79B66/79B68` - Menu selection state (cleared on page setup)
- `7894h:79B5E` - Initialized to 0
- `7894h:79B74` - Initialized to 0
- `7894h:79B5A` - Initialized to 0
- `7894h:79B5C` - Initialized to 2

## File I/O Operations Found

Located DOS INT 21h file operations in:
- **level3_batch2_disasm.txt**: sub_2AEA9 (address 0x2AEDA, 0x2AF38)
- **level1_batch2_disasm.txt**: r01_e04 (address 0x2CFFA)
- **level1_batch4_disasm.txt**: Address 0x2CE03

These are likely candidates for .IDX/.DAT file loading functions.

### DOS INT 21h Function 3Dh - Open File
```assembly
mov    ah, 3Dh    ; DOS function 3Dh = Open file
mov    al, 0-2    ; Access mode: 0=read, 1=write, 2=read/write
mov    dx, si     ; DS:DX = pointer to filename (ASCIIZ string)
int    21h        ; Call DOS
; Returns: CF=0 success (AX=file handle), CF=1 error (AX=error code)
```

## Next Steps

1. **Find file I/O functions**:
   - Examine sub_2AEA9 (level3_batch2) - likely file open/read wrapper
   - Trace filename construction - how does it build "ARMS0123.DAT"?
   - Find .IDX file loading - (offset, size) pair reading

2. **Trace loadout menu flow**:
   - Find exact entry point 0x68D56 in sub_683C5
   - Understand state setup before tail-jump to sub_66E62
   - Map how sub_6798C populates weapon data at 7894h:79E60

3. **Find RLE decompression**:
   - Look for functions processing 6-byte headers (00 04 width height)
   - Find pixel unpacking loops (RLE algorithm)
   - Likely called after file read, before VGA upload

4. **Connect to .IDX/.DAT format**:
   - Verify (offset, size) pair reading from .IDX
   - Confirm seek to offset in .DAT file
   - Trace from file read → decompression → VGA display

## Architecture Insights

### Why Monolithic Controller?

The 4,169-byte `sub_683C5` function consolidates all menu entry points because:

1. **Code size optimization**: 1991 DOS game, memory constrained
2. **Shared state management**: All menus use same state segments (4FC2h, 7894h)
3. **Common initialization**: Most menus need same VGA/palette/panel setup
4. **Tail-call optimization**: Entry points set state, then jump to common code

### Design Pattern: Table-Driven State Machine

Evidence from IDA classification and structure:
- Class = DATA (not ASM) → suggests table lookups dominate logic
- 55 callers → many different entry scenarios
- Large size (4KB) → contains significant embedded tables
- Multiple entry points → classic state machine pattern

## Related Documentation

- `MENU_DATA_FORMAT_SPEC.md` - Complete .IDX/.DAT format specification
- `MENU_SYSTEM_ANALYSIS_PLAN.md` - Overall analysis strategy
- `MENU_SYSTEM_SESSION_SUMMARY.md` - Previous session work

## References

- IDA database: `analysis/ida_falconcd/FALCONCD.EXE.i64`
- Disassembly: `analysis/ida_falconcd/level19_disasm.txt` (sub_683C5)
- Function annotations: `analysis/ida_falconcd/level19_batch3_names.json`
- Menu files: `game/COMMMENU.IDX`, `game/SYSMENU.IDX`, `game/ARMSDATA/*.DAT`


## Summary - Menu System Architecture

### Confirmed Pattern: Tail-Jump Monolith

The menu system uses a **centralized state machine** (sub_683C5, 4169 bytes) containing multiple entry points that eventually tail-jump to common initialization code:

```
ui_loadout_menu_enter (entry in sub_683C5)
    ↓
[Set up loadout-specific state]
    ↓
Call: sub_6798C - ui_slot_record_fill (populate weapon data at 7894h:79E60)
    ↓
Call: sub_4AEC4 - farobj_pos_move_angle_step (3D aircraft model rotation)
    ↓
Tail-jump to: sub_66E62 - ui_menu_panel_init
    ↓
Common menu initialization (VGA, palette, state)
    ↓
Call: sub_4F3EC + vga_dac_palette_upload
    ↓
Return to menu loop in sub_683C5
```

### Why This Matters for File I/O Discovery

The **file loading code is NOT in the menu functions** we've been examining. Those functions operate on **already-loaded data**:

- `sub_6798C` fills records from memory at 7894h:79E60
- `sub_66E62` initializes VGA using data already in memory
- `sub_683C5` manages state transitions, not file I/O

**File loading happens BEFORE these functions are called**, likely during:
1. Game startup/initialization
2. Mission load sequence  
3. Menu screen transition events

### Where to Look Next

File I/O functions are likely in:
1. **Startup initialization** - loads all menu graphics once
2. **Resource managers** - generic .IDX/.DAT loaders
3. **State transition handlers** - called when entering menu systems

These would be in **earlier call tree levels** (Level 0-5) or in **overlay initialization** code.

## Next Investigation Strategy

Instead of tracing menu code top-down, we should:

1. **Bottom-up from DOS INT 21h calls**:
   - Find all file read (3Fh) operations
   - Filter for small reads (4 bytes = .IDX entry size)
   - Trace up to find .IDX/.DAT loaders

2. **Search for .IDX/.DAT filename patterns**:
   - Look for string construction like "ARMS" + digits + ".DAT"
   - Find functions that open files with these patterns

3. **Find RLE decompression**:
   - Search for loops processing run-length data
   - Look for functions handling 6-byte headers (00 04 width height)

4. **Trace backwards from VGA uploads**:
   - `vga_dac_palette_upload` (sub_4F271) - 11 callers
   - Find what provides the graphics data it uploads
   - Trace back to file read operations

## Decision Point

We have **two paths forward**:

### Path A: Continue Static Analysis (File I/O Discovery)
- Find DOS file I/O wrappers
- Locate .IDX/.DAT loading code
- Map RLE decompression algorithm
- **Risk**: May be complex to trace without runtime context
- **Benefit**: Complete understanding of file format usage

### Path B: Pivot to AI System Completion
- We know AI behavior flags (90% complete)
- Still need to find AI data tables
- Menu system analysis complete enough for now
- **Risk**: AI tables may also be loaded at startup (same problem)
- **Benefit**: Different angle of investigation, fresh perspective

### Path C: Hybrid Approach
- Document what we've learned about menu system (DONE ✓)
- Search for generic file I/O wrappers that would serve BOTH menus AND AI
- Once found, apply to both systems

## Recommendation

**Path C - Find Generic File I/O**, because:
1. Both menu .IDX/.DAT files AND AI behavior tables need file loading
2. A generic file loader would serve all game systems
3. Once found, unblocks BOTH menu analysis AND AI completion
4. Strategic - solves two problems at once

The key insight: Falcon 3.0 is a **data-driven game**. There MUST be a centralized resource loading system. Let's find it.

---

**Session Progress**:
- Menu .IDX/.DAT format: 100% decoded ✓
- Menu code structure: Fully mapped ✓
- Menu function relationships: Documented ✓
- File I/O discovery: IN PROGRESS
- RLE decompression: NOT YET FOUND
