# Top 200 Functions - Categorization Progress

**Session**: 2026-11-16  
**Goal**: Properly categorize all 200 functions with descriptive names

---

## Summary

| Category | Count | Percentage |
|----------|-------|------------|
| **Well categorized** | 72 | 36% |
| **Descriptive** | 86 | 43% |
| **Overlay specific** | 1 | 0.5% |
| **Needs investigation** | 20 remaining | 10% |
| **Uncategorized** | 0 remaining | 0% ✓ |
| **TOTAL** | 200 | 100% |

---

## Progress

### Completed ✓

#### Uncategorized Functions (16/16 = 100%)

All functions with generic `sub_XXXXXX` names have been analyzed and renamed:

| Rank | Old Name | New Name | Category |
|------|----------|----------|----------|
| 5 | sub_13DD40 | signed_mul_32bit | Math - 32-bit signed multiply |
| 7 | sub_12805C | mouse_input_sync_wait | Input - Mouse synchronization |
| 8 | sub_13DD83 | signed_div_32bit | Math - 32-bit signed divide |
| 9 | sub_2C59F | overlay_bridge_to_66e97 | Overlay bridge |
| 10 | sub_2C4FF | overlay_bridge_to_r30_state_init | Overlay bridge |
| 19 | sub_13DE3A | table_dispatch_interpreter | Dispatcher - Table-driven |
| 26 | sub_88384 | dynamic_farcall_patcher | Code generation - Far call patcher |
| 30 | sub_2C351 | overlay_bridge_to_66a05 | Overlay bridge |
| 46 | sub_13DE82 | ui_text_width_calculate | UI - Text width calculation |
| 47 | sub_131530 | get_system_time_bios | System - BIOS timer read |
| 54 | sub_2C58B | overlay_bridge_to_menu_frame | Overlay bridge |
| 84 | sub_135C57 | text_line_parser | UI - Text formatting/parsing |
| 86 | sub_11C707 | ui_text_render_entry | UI - Text rendering |
| 87 | sub_11D274 | menu_input_handler | UI - Menu input handling |
| 88 | sub_13504F | campaign_value_calculator | Campaign - Parameter calculator |
| 100 | sub_2C595 | overlay_bridge_to_r30_table_copy | Overlay bridge |

**Key Discoveries**:
- **Math helpers**: High-ranked 32-bit signed multiply/divide (ranks #5, #8)
- **Overlay bridges**: 6 tiny trampolines (8 bytes each) for overlay loading
- **UI/Text system**: Multiple text rendering and formatting functions
- **Dynamic code**: Far call patcher for overlay/callback patching
- **System integration**: BIOS timer access for timing control

#### Utility Functions (5/25 = 20%)

Functions with `utility_` prefix that have been properly categorized:

| Rank | Old Name | New Name | Category |
|------|----------|----------|----------|
| 73 | utility_overlay_dispatcher | overlay_dispatcher_indexed | Overlay - Indexed dispatcher |
| 101 | utility_11c884 | ui_element_render_cc_14 | UI - Element renderer (col 0xCC, row 0x14) |
| 102 | utility_11c90f | ui_element_render_cc_13 | UI - Element renderer (col 0xCC, row 0x13) |
| 110 | utility_11c642 | ui_element_render_102_14 | UI - Element renderer (col 0x102, row 0x14) |
| 116 | utility_12c2f7 | timing_frame_limiter | System - Frame-rate limiter |

**Patterns Identified**:
- **UI element renderers**: Functions following pattern of coordinate calculation (shl ax, 4; add ax, offset), loading ES with 7894h, calling dispatch_220ec_invoke and ui_text_width_calculate
- **Column positions**: 0xCC and 0x102 represent different screen columns for UI elements
- **Timing control**: BIOS timer-based frame limiting with OUT instruction for hardware timing

---

### In Progress

#### Utility Functions (20 remaining)

Functions still marked as `utility_XXXXX` needing investigation:

| Rank | Name | Calls | Size | Notes |
|------|------|-------|------|-------|
| 132 | utility_large_134c3a | 19 | 1045B | Large function |
| 140 | utility_11c576 | 18 | 102B | |
| 141 | utility_11ca9e | 18 | 133B | |
| 142 | utility_127fc4 | 18 | 50B | |
| 143 | utility_135c07 | 18 | 80B | |
| 147 | utility_11c504 | 17 | 114B | |
| 148 | utility_13d77c | 17 | 237B | |
| 149 | utility_167f75 | 17 | 101B | |
| 158 | utility_1786_leaf | 16 | 1786B | Largest utility function |
| 159 | utility_135df4 | 16 | 473B | |
| 160 | utility_137f93 | 16 | 38B | |
| 162 | utility_13dad0 | 16 | 133B | |
| 172 | utility_11cd43 | 15 | 60B | |
| 173 | utility_11cdaf | 15 | 60B | |
| 175 | utility_135208 | 15 | 359B | |
| 188 | utility_49c67 | 14 | 25B | |
| 189 | utility_12bba6 | 14 | 169B | |
| 191 | utility_large_1357ac | 14 | 1021B | Large function |
| 192 | utility_138ed4 | 14 | 200B | |
| 193 | utility_1909a0 | 14 | 308B | |

---

## Analysis Scripts Created

1. `get_top_200_status.py` - Extract current categorization status
2. `analyze_uncategorized_batch.py` - Analyze top 8 uncategorized functions
3. `rename_uncategorized_top8.py` - Rename first batch (ranks #5-30)
4. `analyze_remaining_uncategorized.py` - Analyze remaining 8 uncategorized
5. `rename_remaining_uncategorized.py` - Rename second batch (ranks #46-100)
6. `analyze_utility_batch1.py` - Analyze first 5 utility functions
7. `rename_utility_batch1.py` - Rename first utility batch (ranks #73-116)

All scripts stored in: `C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\`

---

## Categories Established

### Core Categories

1. **Math & Arithmetic** (2 functions so far)
   - 32-bit signed multiply/divide
   - Fixed-point operations
   - Trigonometry helpers

2. **UI & Rendering** (8 functions so far)
   - Text width calculation
   - Text rendering
   - Element rendering at specific coordinates
   - Menu input handling
   - Text line parsing/formatting

3. **Overlay System** (7 functions so far)
   - Overlay bridges (trampolines)
   - Indexed overlay dispatcher
   - Overlay loading and state management

4. **Input System** (1 function so far)
   - Mouse synchronization

5. **System Integration** (2 functions so far)
   - BIOS timer access
   - Frame-rate limiting
   - Timing control

6. **Dispatchers** (1 function so far)
   - Table-driven interpreter
   - State machines

7. **Code Generation** (1 function so far)
   - Dynamic far call patching
   - Self-modifying code

8. **Campaign/Mission** (1 function so far)
   - Parameter calculators
   - Value lookup and computation

---

## Next Steps

### Immediate
1. ☐ Analyze next batch of utility functions (ranks #132-162, 10 functions)
2. ☐ Analyze final batch of utility functions (ranks #172-193, 10 functions)
3. ☐ Verify all 200 functions have proper names
4. ☐ Update top_200_current_status.json with final results

### Documentation
5. ☐ Create comprehensive category index
6. ☐ Document UI rendering coordinate system
7. ☐ Document overlay bridge pattern
8. ☐ Update TOP_200_COMPLETE.md with categorization results

### Integration
9. ☐ Update function registry
10. ☐ Add IDA bookmarks for key functions
11. ☐ Cross-reference with existing documentation
12. ☐ Git commit with detailed message

---

## Quality Metrics

- **Naming consistency**: All renamed functions follow established prefixes
- **Documentation**: Every renamed function has detailed comment
- **Verification**: All renamings verified via check scripts
- **IDA sync**: All changes saved to IDA database

---

**Last Updated**: 2026-11-16  
**Analyst**: Kiro AI + User collaboration  
**IDA Database**: `C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64`
