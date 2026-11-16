# R45 Menu System Analysis

**Date**: 2024  
**Overlay**: R45  
**Primary Function**: `overlay_r45_logic` (0x156945)  
**Status**: Initial extraction complete

---

## Overview

R45 is one of the menu overlay systems in Falcon 3.0, alongside R52, R56, and R57 (weapons loadout).

**Functions Found**:
1. `overlay_r45_logic` (0x156945) - 2614 bytes, 59 calls - Main coordinator
2. `r45_menu_element_dispatcher` (0x1573C3) - 167 bytes, 6 calls - Element renderer

---

## Function: overlay_r45_logic (0x156945)

**Size**: 2614 bytes (0xA36)  
**Calls**: 59 function calls  
**Pattern**: Large menu coordinator with multiple subsystems

### Call Analysis

The function calls several key subsystems repeatedly:

**Frequent callees**:
- `sub_1213` - Called 14 times - Likely UI element renderer
- `sub_18C` - Called 14 times - Possibly coordinate/position calculator
- `sub_137C` - Called 4 times - Unknown utility
- `sub_C3` - Called 3 times - Small utility
- `sub_1139` - Called 2 times - Medium utility

**Pattern**: Repetitive call sequences like:
```
call sub_1213
call sub_18C
call sub_137C
call sub_1213
call sub_18C
call sub_C3
```

This suggests a loop rendering multiple menu elements, each with similar processing:
1. Setup/calculate position (sub_18C)
2. Render element (sub_1213)  
3. Apply style/effect (sub_137C or sub_C3)

### Initialization Sequence

Early calls (offsets 0x28-0x48):
```
0x28:  call sub_ABC   - Early init
0xB1:  call sub_A02   - Setup
0xFA:  call sub_B72   - More setup
0x100: call sub_168F  - Configure
0x10F: call sub_6872  - Large utility (26KB offset)
0x117: call sub_1921  - Setup complete?
```

---

## Function: r45_menu_element_dispatcher (0x1573C3)

**Size**: 167 bytes (0xA7)  
**Calls**: 6 function calls

### Callees

1. `undoc_11C576` (called at offset 0x36)
   - Size: 102 bytes
   - 18 total calls across codebase
   - Needs investigation

2. `utility_11c90f` (called at offset 0x60)
   - 24 total calls across codebase
   - Utility function

**Note**: Both of these are also called by R57 loadout menu, suggesting shared UI rendering infrastructure.

---

## Next Steps

### Priority 1: Identify Menu Type

**Action**: Examine string references to determine what menu R45 represents
- Check for menu title strings
- Look for button labels
- Find screen identifiers

**Method**: Already have strings extracted in JSON, need to review

### Priority 2: Understand Element Rendering

**Functions to analyze**:
- `sub_1213` (0x1213) - Called 14 times, likely core renderer
- `sub_18C` (0x18C) - Called 14 times with sub_1213, likely position calc
- `sub_137C` (0x137C) - Called 4 times, style/effect?

**Method**: Extract these functions' disassembly and analyze calling patterns

### Priority 3: Compare with R57

We have R57 (weapons loadout) fully documented. Compare:
- Shared UI functions (undoc_11C576, utility_11c90f)
- State machine patterns
- Input handling
- Rendering pipeline

**Goal**: Understand menu architecture differences

### Priority 4: Trace State Machine

Large coordinators like this (2614 bytes, 59 calls) typically implement state machines.

**Look for**:
- Switch/jump table (checking state variable)
- State transition logic
- Input processing per state
- Rendering dispatch per state

---

## Comparison with Other Menu Overlays

| Overlay | Size | Calls | Purpose |
|---------|------|-------|---------|
| R45 | 2614B | 59 | Unknown menu |
| R52 | 2026B | ? | Flight briefing |
| R56 | 2837B | ? | Flight briefing (duplicate of R52) |
| R57 | 3083B | 952 instr | Weapons loadout |

**Observation**: R45 is similar in size to other menu overlays, suggesting comparable complexity.

---

## Extracted Data Available

From `r45_menu_extraction.json`:
- ✓ Complete call list (59 calls with addresses and targets)
- ✓ Cross-reference count
- ✓ String references (if any)
- ✓ First 200 instructions disassembly

**Next**: Parse JSON and analyze calling patterns, string content, and state machine structure.

---

## Questions to Answer

1. **What menu is R45?**
   - Main menu?
   - Campaign selection?
   - Options/settings?
   - Squadron management?

2. **How does it differ from R52/R56?**
   - Different menu elements?
   - Different input handling?
   - Different data sources?

3. **What state machine does it implement?**
   - How many states?
   - What triggers transitions?
   - What does each state render?

4. **What shared infrastructure does it use?**
   - Same UI renderers as R57?
   - Same input system?
   - Same state management?

---

## Files Created

- `ida_scripts/extract_r45_menu.py` - IDA extraction script
- `ida_scripts/r45_menu_extraction.json` - Raw extracted data
- `R45_MENU_ANALYSIS.md` - This document

---

## Status

**Progress**: 10% - Initial extraction complete  
**Next Action**: Analyze JSON data for strings and calling patterns  
**Blocked**: None  
**ETA to 50%**: 2-3 hours of focused analysis
