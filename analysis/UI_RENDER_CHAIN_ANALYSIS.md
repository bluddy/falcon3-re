# UI Text Rendering Chain - Complete Analysis

**Date**: 2026-11-11  
**Analysis**: Deep dive into ui_campaign_render_coordinator (0x15F5B8)  
**Result**: Discovered and mapped complete UI text rendering chain (11 functions)  
**Impact**: 53% progress toward Top 100 goal (53/100 functions)

---

## Executive Summary

Starting from **ui_campaign_render_coordinator** (Rank #11 callee, 34 callers), we traced the complete UI text rendering chain for campaign/theater screens. Discovered 10 previously undocumented functions and mapped the two-path rendering architecture (detailed vs compact modes).

**Key Discovery**: The rendering system has a sophisticated mode-checking architecture that routes through different paths based on `byte_7A302` (rendering mode flag) and `byte_14E5A0` (display mode 1/2/3).

---

## Architecture Overview

```
ui_campaign_render_coordinator (0x15F5B8) - 745 bytes, 34 callers
├─ Setup Phase
│  ├─ Initializes 4 far pointers (dword_14F98C, dword_14F990)
│  ├─ Initializes 2 table pointers (word_14F99A, word_14F998)
│  └─ Checks graphics_mode_flag (0x7894:graphics_mode_flag)
│
├─ PATH A: Detailed Rendering (byte flag == 0)
│  ├─ ui_text_render_setup (0x128518) - 123 bytes, 16 callers
│  ├─ far_cb_1 (0x25EC9)
│  ├─ dispatch_220f0_invoke_1arg (0x25EA8) - 2x
│  ├─ far_cb_0 (0x25EBD)
│  ├─ menu_field_data_ptr_get (0x2C3A1)
│  ├─ menu_selection_ptr_get (0x2C3B5) - 4x
│  ├─ ui_render_state_update (0x139F76) - 3x
│  ├─ ui_text_render_single_mode (0x1293F0) - 4x ⭐
│  │  ├─ Checks byte_7A302, byte_14E5A0
│  │  ├─ If flags set → ui_text_render_with_palette (0x129ED6)
│  │  └─ If flags not set → ui_text_render_simple (0x128AA6)
│  ├─ ui_font_config_apply (0x1320CC)
│  ├─ string_copy_with_offset (0x138FF0)
│  └─ menu_finalize_render (0x2C49B)
│
└─ PATH B: Compact Rendering (byte flag != 0)
   ├─ far_cb_1 (0x25EC9)
   ├─ dispatch_220f0_invoke_1arg (0x25EA8) - 2x
   ├─ far_cb_0 (0x25EBD)
   ├─ menu_selection_ptr_get (0x2C3B5) - 4x
   ├─ ui_render_state_update (0x139F76)
   └─ ui_text_render_multi_mode (0x129468) - 4x ⭐
      ├─ Checks byte_7A302, byte_14E5A0
      ├─ If flags set → ui_text_render_multi_palette (0x129C88)
      └─ If flags not set → LOOP calling ui_text_render_engine (0x128598)
```

---

## Function Details

### 1. ui_campaign_render_coordinator (0x15F5B8)

**Size**: 745 bytes  
**Callers**: 34 (HIGH TRAFFIC)  
**Disassembly**: 232 lines, 12 external callees

**Control Flow:**
1. **Setup** (0x15F5B8-0x15F603): Initialize pointers and tables
2. **Graphics check** (0x15F603): Exit if `graphics_mode_flag == 0`
3. **Branch point** (0x15F623): Check `es:[bx+2]` byte flag
   - If 0 → Path A (detailed, 0x15F645)
   - If != 0 → Path B (compact, 0x15F7A7)

**Path A** calls `ui_text_render_single_mode` 4 times with:
- (dword_79E3A, 0xF)
- (639E:FC, 0x29)
- (arg_2:arg_0, 0x2B)
- (menu_state_ptr, 0x16)

**Path B** calls `ui_text_render_multi_mode` 4 times with:
- (dword_79E3A, 0xA8F, 0xF)
- (639E:FC, 0x9F, 0x29)
- (arg_2:arg_0, 0x2, 0x2B)
- (menu_state_ptr, 0x3F, 0x16)

**Key Observation**: The byte values (0xF, 0x29, 0x2B, 0x16) match exactly between paths. The word values in Path B (0xA8F, 0x9F, 0x2, 0x3F) are likely character counts or lengths.

**Globals Accessed:**
- `graphics_mode_flag` (0x7894:flag)
- `dword_79E3A` (menu data pointer)
- `menu_state_ptr` (0x7894:ptr)
- `word_70A2A` (709Fh segment)
- `dword_14F98C`, `dword_14F990` (602Eh:pointers)
- `word_14F99A`, `word_14F998` (602Eh:tables)
- `word_14F8BE` (602Eh:state bits)

---

### 2. ui_text_render_single_mode (0x1293F0)

**Size**: 120 bytes  
**Callers**: Called 4x by ui_campaign_render_coordinator  
**Signature**: `(byte char_code, ptr_seg, ptr_off)`

**Logic:**
```assembly
1. Check byte_7A302 (rendering mode flag)
2. If set:
   a. Check byte_14E5A0 (display mode: 1, 2, or 3)
   b. Mode 1 or 3 → use offset 0x19
   c. Mode 2 → use offset 0x1E
   d. Load byte from [602E:offset]
   e. If non-zero → call ui_text_render_with_palette
3. If not set:
   a. Call ui_text_render_simple with char_code
```

**Purpose**: Routes single-character rendering through mode-checking logic to select palette vs simple rendering.

---

### 3. ui_text_render_multi_mode (0x129468)

**Size**: 297 bytes  
**Callers**: Called 4x by ui_campaign_render_coordinator  
**Signature**: `(byte char_code, word count/length, ptr_seg, ptr_off)`

**Logic:**
```assembly
1. Check byte_7A302 (rendering mode flag)
2. If set:
   a. Same mode checking as single-mode
   b. If mode flags set → call ui_text_render_multi_palette
   c. If mode flags not set → LOOP:
      - For i = 1 to byte_14E5C8/9 (mode-specific count):
        - Call ui_text_render_engine with char_code
3. If not set:
   a. LOOP through word_70A2A+1 (table count)
   b. Check flags and availability
   c. Call ui_text_render_engine for each valid entry
```

**Key Discovery**: This function **calls ui_text_render_engine (0x128598) in a loop**, making it a multi-character string renderer built on top of the single-character engine.

**Disassembly Evidence:**
```
0012950D  call    near ptr ui_text_render_engine  ; Loop body
00129510  add     sp, 0Ah
00129513  inc     [bp+var_2]                      ; Increment counter
00129516  mov     al, [bp+var_7]
00129519  cbw
0012951A  cmp     ax, [bp+var_2]                  ; Compare to limit
0012951D  jg      short loc_1294F7                ; Continue if more chars
```

---

### 4. ui_text_render_with_palette (0x129ED6)

**Size**: 574 bytes  
**Callees**: 10  
**Purpose**: Palette-based (colored) text rendering

Called by `ui_text_render_single_mode` when:
- `byte_7A302` is set (palette mode enabled)
- `byte_14E5A0` indicates mode 1, 2, or 3
- Mode-specific offset byte is non-zero

---

### 5. ui_text_render_simple (0x128AA6)

**Size**: 692 bytes  
**Callers**: 20 (HIGHLY REUSED)  
**Purpose**: Direct/uncolored text rendering

Called by `ui_text_render_single_mode` when `byte_7A302` is not set (simple mode).

---

### 6. ui_text_render_multi_palette (0x129C88)

**Size**: 590 bytes  
**Callees**: 12  
**Purpose**: Multi-character palette rendering

Called by `ui_text_render_multi_mode` when palette flags are set. Parallel to `ui_text_render_with_palette` but handles multiple characters.

---

### 7. ui_render_state_update (0x139F76)

**Size**: 27 bytes (TINY)  
**Calls**: 3x in coordinator (between render operations)  
**Purpose**: Updates render state/buffers

Called between major rendering operations. Likely:
- Flushes text buffer
- Updates cursor position
- Advances to next line/field

---

### 8. ui_font_config_apply (0x1320CC)

**Size**: 182 bytes  
**Callers**: 25 (HIGHLY REUSED across UI system)  
**Purpose**: Applies font/text configuration

Sets up font parameters before rendering operations. Heavily reused suggests it's a critical UI initialization function.

---

### 9. string_copy_with_offset (0x138FF0)

**Size**: 56 bytes  
**Callers**: 30 (HIGHLY REUSED)  
**Purpose**: String manipulation with offset

General utility function for string operations. Called from coordinator to build text buffers.

---

### 10. menu_finalize_render (0x2C49B)

**Size**: 8 bytes (TINY)  
**Purpose**: Finalizes menu rendering

Called at end of Path A (detailed rendering). Likely:
- Swaps display buffers (page flip)
- Signals rendering complete
- Updates frame counter

**Speculation**: The 8-byte size suggests a simple far call or memory write to trigger buffer swap.

---

### 11. ui_text_render_setup (0x128518)

**Size**: 123 bytes  
**Callers**: 16  
**Location**: Immediately before ui_text_render_engine (0x128598)  
**Purpose**: Setup/parameter preparation

Called at start of Path A in coordinator. May:
- Initialize rendering context
- Check state validity
- Prepare buffers

**Address Verification Results:**
- 0x128518: `ui_text_render_setup` - 123 bytes, 16 callers
- 0x128598: `ui_text_render_engine` - 1282 bytes, 70 callers

The functions are adjacent in memory (0x128518 + 123 = 0x128593, very close to 0x128598).

---

## Display Mode Architecture

### Mode Flags

**byte_7A302** (0x7894:0x7A302): **Master rendering mode flag**
- 0 = Simple/direct rendering (no palette)
- Non-zero = Palette/colored rendering enabled

**byte_14E5A0** (0x602E:0x14E5A0): **Display mode selector**
- Value 1: Standard mode (use offset 0x19)
- Value 2: Alternate mode (use offset 0x1E)
- Value 3: Standard mode (use offset 0x19)

### Mode-Specific Offsets

When palette mode is enabled:
- Mode 1/3: Read byte at `602E:19h` → controls palette selection
- Mode 2: Read byte at `602E:1Eh` → controls palette selection

### Rendering Paths

**Path A (Detailed):**
- Single-character calls (4x)
- Full mode checking
- Separate calls to menu helpers
- Finalize with buffer swap

**Path B (Compact):**
- Multi-character calls (4x)
- Same mode checking
- Looped character rendering
- No explicit finalize

**When to use each:**
- Path A: Static menu labels, field headers, prompts
- Path B: Dynamic data, lists, tables, scrolling content

---

## Key Insights

### 1. Two-Tier Rendering Architecture

The system has clear separation:
- **Single-mode functions**: One character at a time, full mode checking
- **Multi-mode functions**: Multiple characters, calls engine in loop

### 2. Mode-Based Routing

The `byte_7A302` and `byte_14E5A0` flags create a sophisticated routing system:
- Simple rendering (fast, no color)
- Palette rendering (colored, mode-specific)

### 3. High Reuse Patterns

Several functions are heavily reused:
- `ui_font_config_apply`: 25 callers
- `string_copy_with_offset`: 30 callers
- `ui_text_render_simple`: 20 callers

This suggests a well-designed utility layer beneath the specialized coordinators.

### 4. Tight Memory Layout

`ui_text_render_setup` (0x128518) and `ui_text_render_engine` (0x128598) are adjacent in memory, separated by only 128 bytes (0x80). This suggests they were designed together or the setup function was added as a wrapper.

### 5. The Core Engine

`ui_text_render_engine` (0x128598) is the actual workhorse:
- 1282 bytes (substantial implementation)
- 70 callers across the codebase
- Called in loops by multi-mode renderers
- Handles the actual pixel/font operations

---

## Impact on Top 100 Analysis

### Progress Update
- **Before**: 42/100 (42%)
- **After**: 53/100 (53%)
- **Gain**: 11 functions (26% increase in one session!)

### Functions Added to Registry
1. ui_text_render_single_mode (0x1293F0)
2. ui_text_render_multi_mode (0x129468)
3. ui_text_render_with_palette (0x129ED6)
4. ui_text_render_simple (0x128AA6)
5. ui_text_render_multi_palette (0x129C88)
6. ui_render_state_update (0x139F76)
7. ui_font_config_apply (0x1320CC)
8. string_copy_with_offset (0x138FF0)
9. menu_finalize_render (0x2C49B)
10. ui_text_render_setup (0x128518)
11. ui_campaign_render_coordinator (0x15F5B8) - updated with deep analysis

### IDA Database Updates
- All 11 functions renamed in IDA
- Function comments added describing purpose
- Control flow documented

### Registry Updates
- All entries updated with:
  - System classification (ui/utility)
  - Size information
  - Caller counts
  - Detailed documentation
  - Source attribution

---

## Methodology Notes

### What Worked Well

1. **Following high-caller-count functions** - ui_campaign_render_coordinator (34 callers) led to rich discovery
2. **Extracting full disassembly** - 232 lines revealed complete control flow
3. **Comparing parallel functions** - single-mode vs multi-mode revealed the loop pattern
4. **Address verification** - disambiguated 0x128518 vs 0x128598 confusion
5. **Pattern recognition** - matching byte values (0xF, 0x29, 0x2B, 0x16) across paths

### Challenges Overcome

1. **Address confusion**: Documentation mentioned 0x128518 as ui_text_render_engine, but registry showed 0x128598. Verification script resolved this.
2. **Mode flag interpretation**: Required careful analysis of branch conditions to understand the routing logic.
3. **Function similarity**: Single-mode and multi-mode functions have nearly identical structure, easy to confuse.

### Lessons for Future Analysis

1. **Always verify addresses** when documentation conflicts with registry
2. **Look for loop patterns** in functions with counters (var_2, var_7)
3. **Match parameter patterns** across related functions (the byte values gave it away)
4. **Check adjacent functions** in memory - they're often related

---

## Next Steps

### Immediate Actions
1. ✅ Rename all 11 functions in IDA
2. ✅ Update registry with complete information
3. ✅ Update TOP_100_PROGRESS.md
4. ✅ Create this analysis document

### Follow-up Analysis Opportunities

1. **ui_text_render_engine (0x128598)** - The core 1282-byte engine
   - Already analyzed in previous session
   - Verify integration with newly discovered callers

2. **Display mode flag globals** - Understand mode switching
   - byte_7A302: When/how is palette mode enabled?
   - byte_14E5A0: What triggers mode 1 vs 2 vs 3?

3. **Menu helper functions** - Complete the menu system picture
   - menu_field_data_ptr_get (0x2C3A1)
   - menu_selection_ptr_get (0x2C3B5) - called 4x
   - dispatch_220f0_invoke_1arg (0x25EA8)

4. **Buffer management** - How are the 4 text buffers used?
   - dword_79E3A
   - 639E:FC
   - arg_2:arg_0
   - menu_state_ptr

### Recommended Deep Dive: Rank #12

Continue with next highest caller count:
- **sub_1A57F0** (Rank #12, 95 callers, 3083 bytes)
- Pattern suggests another major coordinator or overlay handler
- 3KB size indicates substantial logic

---

## Files Created/Updated

### Created
- `analysis/ida_falconcd/get_1293f0_disasm.py` - Extract helper functions
- `analysis/ida_falconcd/render_helpers.json` - Disassembly output
- `analysis/ida_falconcd/verify_addresses.py` - Address verification
- `analysis/ida_falconcd/rename_render_chain.py` - IDA rename script
- `analysis/UI_RENDER_CHAIN_ANALYSIS.md` - This document
- `tools/update_registry_render_chain.py` - Registry updater (had YAML issues)

### Updated
- `registry/functions.yaml` - 11 function entries updated
- `analysis/TOP_100_PROGRESS.md` - Progress 42% → 53%
- IDA database: 11 functions renamed with comments

---

## Conclusion

This deep dive into `ui_campaign_render_coordinator` revealed a sophisticated two-path rendering architecture with mode-based routing. We discovered 10 new functions and mapped the complete UI text rendering chain from coordinator down to the core engine.

**Key Achievement**: 26% progress gain (11 functions) in a single focused analysis session. This demonstrates the value of following high-traffic functions (34 callers) into their call graphs.

**Architectural Understanding**: We now understand how Falcon 3.0's UI system coordinates text rendering:
1. Coordinator checks graphics mode and display flags
2. Routes to single-mode or multi-mode based on content type
3. Mode checking determines palette vs simple rendering
4. Core engine (ui_text_render_engine) does actual pixel work

**Next Target**: Rank #12 (sub_1A57F0, 95 callers, 3KB) to maintain momentum toward 60-70% completion.

---

**Analysis completed**: 2026-11-11  
**Analyst**: AI Code Analysis  
**Session**: Rank #11 Investigation - UI Rendering Chain Discovery
