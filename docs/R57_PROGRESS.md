# R57 Loadout Menu Analysis - Progress Report

## Summary

Started deep dive into R57 loadout menu system. Extracted 7 R57 functions, identified main state machine architecture with 7 states, documented initialization and State 0 (flight selection). Ready to extract complete state machine disassembly.

**Current Status**: Core architecture documented, ~30% complete

---

## Completed

### ✅ Function Extraction
- Extracted all 7 R57 functions with disassembly, calls, and strings
- Output: `analysis/r57_loadout_menu_complete.json` (7 functions)
- Functions identified:
  - r57_menu_state_machine (3083B, 105 calls) - main controller
  - r57_loadout_display_handler (4549B, 96 calls) - display logic
  - menu_r57_flight_display_handler (850B, 14 calls) - flight list UI
  - menu_r57_loadout_flight_display (572B, 14 calls) - loadout details UI
  - overlay_r57_logic (2423B, 31 calls) - overlay coordination
  - overlay_r57_processor_2 (2090B, 54 calls) - overlay processing
  - overlay_r57_simple_helper (26B, 0 calls) - simple helper

### ✅ Architecture Analysis
- Identified 4 overlay entry points (no external callers)
- Mapped call hierarchy:
  - State machine → menu_r57_flight_display_handler (7 calls)
  - Display handler → menu_r57_loadout_flight_display (7 calls)
  - Processor → overlay_r57_simple_helper (10 calls)
- Documented function call frequencies (14x menu_cursor_position_set, etc.)

### ✅ State Machine Structure
- **State variable**: `current_view_index` (word_79F16)
- **State count**: 7 (states 0-6)
- **Dispatch**: Jump table at jpt_1A5A25[bx*2]
- **Entry**: 0x1A57F0 (3083 bytes total)

### ✅ Initialization Sequence
- Documented complete init (0x1A57F0 - 0x1A5A11):
  - Clear 4 global flags (word_79B60, word_79E86, word_79E88, word_79B62)
  - Initialize 11 records (28 bytes each, 0x1C stride)
  - Set up 2 data pointers (dword_79E68, dword_79E2C)
  - Transform coordinates
- Stack frame: 12 bytes with 2 local vars

### ✅ State 0 Documentation
- **Purpose**: Flight selection / initial state
- **Entry**: 0x1A5A2A (line 162)
- **Logic**:
  - Animate transition
  - Update display and cursor
  - Handle key '6': Previous flight navigation
  - Navigation: `current = (current + total - 1) % total`
  - Compute flight record pointer: `base + (index * 130)`
- **Flight records**: 130-byte stride from menu_flight_records_ptr

### ✅ Input Handling
- Documented pre-dispatch input handler:
  - Mode check: word_79B6C == 0x32 ('2')
  - Scan code 1 (ESC): Animate exit, set local state
  - Scan code 3: Exit to view 6
  - Scan code 0xFF: Finalize render
- Additional checks: keys '4' and '6' route to dispatch

### ✅ Global Variables
- Mapped 12 globals in segment 7894h:
  - **current_view_index** (word_79F16) - State (0-6)
  - **menu_current_flight_index** (word_79B62) - Current flight
  - **menu_total_flights_count** (word_79EEC) - Total flights
  - **menu_loadout_mode_flag** (word_79EA4) - Mode flag
  - **menu_loadout_data_ptr** (dword_79E60) - Armament data
  - **menu_flight_records_ptr** (dword_79BEC) - Flight records (130B stride)
  - **input_scan_code_queue** (word_7994B) - Keyboard input
  - Plus 5 unknowns (word_79EA0, word_79B60, word_79E86, word_79E88, word_79B6C)

### ✅ Documentation
- Created `docs/R57_LOADOUT_MENU_FLOW.md` (450+ lines)
  - Architecture overview
  - Entry points and call hierarchy
  - Complete initialization sequence with assembly
  - State machine switch structure
  - Input handling with scan codes
  - State 0 detailed analysis
  - Global variable table
  - Data structure specifications
  - Rendering pipeline
  - 9 outstanding questions
  - Next steps

### ✅ Analysis Scripts
- `analysis/ida_scripts/extract_r57_loadout_menu.py` - Extract all R57 functions
- `analysis/analyze_r57_menu_flow.py` - Build call graph and hierarchy
- `analysis/examine_state_machine.py` - Examine state machine structure
- `analysis/find_state_loop.py` - Find loop and state comparisons
- `analysis/extract_state_cases.py` - Extract state case structure
- `analysis/show_jump_table.py` - Display jump table area
- **NEW**: `analysis/ida_scripts/extract_full_state_machine.py` - Extract complete disassembly

### ✅ Git Commits
- Commit ea28607: "R57 menu flow: Initial analysis and state machine structure"

---

## In Progress

### 🔄 State Machine Disassembly
- **Issue**: JSON extraction truncated at ~200 lines (function is 3083B, ~700+ instructions)
- **Solution**: Created extract_full_state_machine.py IDA script
- **Next**: Run script in IDA to get complete disassembly

---

## Pending

### 📋 States 1-6 Documentation
- State 1: ? (need full disassembly)
- State 2: ? (need full disassembly)
- State 3: ? (need full disassembly)
- State 4: ? (need full disassembly)
- State 5: ? (need full disassembly)
- State 6: ? (possibly exit state)

**Blocked by**: Need complete state machine disassembly

### 📋 State Transitions
- How do states progress? (0 → 1 → 2, etc.)
- What triggers each transition?
- Are transitions linear or branching?
- Do all states call menu_r57_flight_display_handler?

**Blocked by**: Need complete state machine disassembly

### 📋 Display Handler Integration
- How is r57_loadout_display_handler called?
- When does it switch between flight list and loadout view?
- Relationship between state machine and display handler entry points

**Requires**: Tracing overlay system or finding entry point callers

### 📋 Data Structures
- Flight record (130 bytes) - internal layout unknown
- Menu record (28 bytes, 11 records) - purpose and fields unknown
- What is in dword_79E68 and dword_79E2C pointers?

**Requires**: Analyzing display handlers and record usage

### 📋 Unknown Variables
- word_79EA0 - "menu field index" (set to 0, used in BX addressing)
- word_79B60 - Unknown flag (initialized to 0)
- word_79E86 - Unknown flag (initialized to 0)
- word_79E88 - Unknown flag (initialized to 0, copied to word_79F34)
- word_79B6C - Input/command byte ('2', '4', '6') - source?
- word[7894:15AC] - Modulo divisor (likely = menu_total_flights_count?)

**Requires**: Tracing usage across all functions

### 📋 Input Flow
- Complete keyboard input → scan code → action mapping
- What other keys are handled? (found '6', ESC, scan 3, 0xFF, '4')
- Mouse input? (likely not in 1991 DOS game)

**Requires**: Complete state machine disassembly

### 📋 Rendering Pipeline
- When are display handlers called relative to state changes?
- What are the 489 "strings" in r57_loadout_display_handler?
- UI element structure (referenced 16-byte elements in original notes)

**Requires**: Analyzing display handler functions

### 📋 Overlay System Integration
- How do overlays load/unload?
- What do overlay_bridge_to_XXXXX functions do?
- Why 4 separate entry points?

**Requires**: Broader overlay system analysis

---

## Outstanding Questions

1. **What are states 1-6?** Need complete disassembly
2. **What triggers state transitions?** Aside from direct assignment, how do states progress?
3. **What is word_79B6C?** Input checking byte ('2', '4', '6') - populated how?
4. **Flight record structure?** 130-byte stride, but internal layout unknown
5. **Menu record structure?** 28-byte records, array of 11 - what are they for?
6. **Loadout mode flag usage?** word_79EA4 named but not seen in extracted code
7. **String references?** 489 in display handler, 327 in state machine - templates or artifacts?
8. **r57_loadout_display_handler integration?** Separate entry point, how does it fit?
9. **word[7894:15AC] identity?** Modulo divisor - is it menu_total_flights_count or separate?

---

## Next Actions

### Immediate (extract complete disassembly)
1. ✅ Create extract_full_state_machine.py IDA script
2. ⏳ Run script in IDA to extract all ~700 instructions
3. ⏳ Analyze complete state machine
4. ⏳ Document states 1-6

### Short-term (complete state machine)
5. ⏳ Map all state transitions
6. ⏳ Document complete input handling
7. ⏳ Identify all menu_r57_flight_display_handler call sites
8. ⏳ Trace state progression logic

### Medium-term (display handlers)
9. ⏳ Analyze menu_r57_flight_display_handler (850B)
10. ⏳ Analyze menu_r57_loadout_flight_display (572B)
11. ⏳ Analyze r57_loadout_display_handler (4549B)
12. ⏳ Document rendering pipeline

### Long-term (data structures)
13. ⏳ Reverse engineer flight record structure (130B)
14. ⏳ Reverse engineer menu record structure (28B x 11)
15. ⏳ Document UI element structure (16B?)
16. ⏳ Map all unknown globals

---

## Key Insights

1. **7-state machine**: Clean switch statement with 0-6 states, not a simple loop
2. **Wrapping navigation**: Previous flight uses `(current + total - 1) % total` pattern
3. **Overlay architecture**: 4 entry points suggest modular overlay loading system
4. **Consistent patterns**: Display handlers called 7 times each (once per state?)
5. **Record-based**: Multiple record arrays (11x 28B, flight 130B stride)
6. **Input preprocessing**: Significant input handling before state dispatch
7. **State-driven rendering**: Each state likely has its own display configuration

---

## Files Modified/Created

### New Files (9)
- `docs/R57_LOADOUT_MENU_FLOW.md` - Main documentation (450+ lines)
- `docs/R57_PROGRESS.md` - This file
- `analysis/r57_loadout_menu_complete.json` - Extracted R57 functions
- `analysis/ida_scripts/extract_r57_loadout_menu.py` - Extraction script
- `analysis/ida_scripts/extract_full_state_machine.py` - Full disasm extractor
- `analysis/analyze_r57_menu_flow.py` - Flow analysis
- `analysis/examine_state_machine.py` - State machine examination
- `analysis/find_state_loop.py` - Loop finder
- `analysis/extract_state_cases.py` - Case extractor
- `analysis/show_jump_table.py` - Jump table display

### Modified Files (1)
- `analysis/ida_falconcd/FALCONCD.EXE.i64` - IDA database (automated edits)

---

## Metrics

- **Functions analyzed**: 7 (R57 menu system)
- **Lines of documentation**: 450+ (R57_LOADOUT_MENU_FLOW.md)
- **Scripts created**: 7 (6 analysis + 1 extraction)
- **State machine coverage**: ~30% (State 0 + initialization complete, States 1-6 pending)
- **Globals documented**: 12 (7 named, 5 unknown)
- **Time investment**: ~2-3 hours
- **Completion estimate**: ~60% more work to document all states + display handlers + data structures

---

## Recommendations

1. **Run extract_full_state_machine.py** in IDA ASAP to unblock States 1-6 analysis
2. **Focus on state machine first** before diving into display handlers (more foundational)
3. **Create state diagram** once all transitions are understood (visual aid)
4. **Consider parallel analysis** of overlay system to understand entry point architecture
5. **Document incrementally** - add each state to R57_LOADOUT_MENU_FLOW.md as discovered

---

*Last updated: [Current session]*
*Status: Ready for IDA script execution*
