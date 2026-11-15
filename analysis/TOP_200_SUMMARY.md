# Top 200 Functions Analysis - Summary

**Status**: 200/200 disassembly extracted, 110/200 analyzed in detail  
**Date**: 2026-11-11  

---

## Progress Overview

### Ranks #1-100: ✓ COMPLETE
- ✓ All functions extracted
- ✓ All functions analyzed
- ✓ All functions renamed in IDA
- ✓ 500+ inline comments added
- ✓ Registry updated
- ✓ Major discovery: r15_simulation_loop

See `TOP_100_COMPLETE.md` for full details.

### Ranks #101-200: Disassembly Extracted
- ✓ All 100 functions extracted to disassembly files
- ✓ Ranks #101-110 analyzed and renamed
- ☐ Ranks #111-200 need analysis and renaming

---

## Ranks #101-110 Detailed Analysis

| Rank | Address | Name | Calls | Size | Category |
|------|---------|------|-------|------|----------|
| 101 | 0x11C884 | utility_11c884 | 24 | 139B | Utility |
| 102 | 0x11C90F | utility_11c90f | 24 | 127B | Utility |
| 103 | 0x13536F | vector_arithmetic_complex | 24 | 1085B | Math/Vector |
| 104 | 0x22EE8 | fixed_abs_div4 | 23 | 16B | Math - Fixed Point |
| 105 | 0x249D8 | trig_table_lookup | 23 | 173B | Math - Trigonometry |
| 106 | 0x13BCE5 | string_cr_null_terminate | 23 | 33B | String |
| 107 | 0x23C9B | angle_xy_far | 22 | 144B | Math - Angle |
| 108 | 0x24CF7 | cs_word_store | 22 | 10B | Utility - Storage |
| 109 | 0x25E22 | dispatch_220f4_stub | 22 | 6B | Dispatch |
| 110 | 0x11C642 | utility_11c642 | 22 | 197B | Utility |

### Key Findings

**Tiny Functions** (under 20 bytes):
- Rank #104: `fixed_abs_div4` (16B) - Fixed-point absolute value / 4
- Rank #108: `cs_word_store` (10B) - Store word to CS segment
- Rank #109: `dispatch_220f4_stub` (6B) - Smallest in this batch!

**Math/Trig Functions**:
- `fixed_abs_div4` - Optimized fixed-point math: multiply by 4, take absolute value, divide by 4
- `trig_table_lookup` - Sin/cos table lookup with quadrant handling (4 paths)
- `angle_xy_far` - Calculate angle from XY delta coordinates, handles all quadrants
- `vector_arithmetic_complex` - Large (1085B) vector arithmetic operations

**String Utilities**:
- `string_cr_null_terminate` - Appends CR (0Dh) + null terminator

---

## Ranks #111-150 Overview

Many functions already have descriptive names from previous analysis:
- `ui_render_coordinator` (Rank #111, 900B)
- `menu_list_index_clamp` (Rank #112, 35B)
- `fixed_vec3_transform_es` (Rank #114, 146B)
- `temp_file_handler` (Rank #117, 280B)
- `menu_loadout_supply_decrement` (Rank #118, 19B)
- `stub_to_205c3` (Rank #119, 4B)
- `flag_table_pop_far_thunk` (Rank #120, 12B)

---

## Ranks #151-200 Overview

All disassembly extracted, awaiting analysis.

---

## Statistics (Ranks 101-200)

### Size Distribution
- **Smallest**: 4 bytes (stub functions)
- **Largest**: 1085 bytes (vector_arithmetic_complex)
- **Average**: ~200 bytes
- **Median**: ~150 bytes

### Call Frequency
- **Highest**: 24 calls (ranks 101-103)
- **Lowest**: ~15 calls (rank 200)
- Steady decrease in call frequency as rank increases

### Categories (Preliminary)
- **Math/Trig**: 15-20% (fixed-point, trig tables, angles, vectors)
- **Utility/Generic**: 30-40% (needs investigation)
- **UI/Menu**: 10-15% (coordinators, clamps, decrements)
- **Dispatch/Stubs**: 10-15% (far call stubs, dispatchers)
- **String**: 5% (terminators, manipulation)
- **File I/O**: 5% (temp file handlers)

---

## Comparison: Top 100 vs Next 100

| Metric | Ranks 1-100 | Ranks 101-200 |
|--------|-------------|---------------|
| Avg Size | ~1500B | ~200B |
| Avg Calls | 100+ | 20-24 |
| Major Discoveries | 1 (simulation loop) | 0 (utilities) |
| State Machines | Many | Few |
| Overlay Processors | 30+ | ~5 |

**Key Insight**: Ranks 1-100 contain the "heavy hitters" - large state machines, overlay processors, and core game loop functions. Ranks 101-200 are dominated by smaller utility functions, math helpers, and glue code.

---

## Next Steps

1. ☐ Analyze ranks 111-150 in detail
2. ☐ Rename functions in IDA for ranks 111-150
3. ☐ Update registry for ranks 111-150
4. ☐ Analyze ranks 151-200
5. ☐ Rename and document ranks 151-200
6. ☐ Create comprehensive Top 200 completion document
7. ☐ Consider expanding to Top 300

---

## Files Created

### Extraction Scripts
- `extract_top_200.py` - Generate top 200 list
- `quick_extract_101_110.py` - Extract disassembly for ranks 101-110
- `extract_ranks_111_150.py` - Extract disassembly for ranks 111-200

### Renaming Scripts
- `rename_batch_101_110.py` - Rename + comment ranks 101-110 in IDA

### Data Files
- `top_200_functions.json` - Complete top 200 list with metadata
- `func_XXXXXX_disasm.txt` - 100 disassembly files for ranks 101-200

### Documentation
- `TOP_200_PROGRESS.md` - Progress tracking
- `TOP_200_SUMMARY.md` - This document

---

*Last Updated*: 2026-11-11  
*Next Milestone*: Complete analysis of ranks 111-200
