# S4 Deep Dive Session 55 Summary

**Date:** 2026-11-11  
**HEAD:** 677a492 (11 commits this session)  
**Status:** Level-0 campaign complete, architectural insights documented

---

## Overview

Session 55 completed the S4 Level-0 bottom-up naming campaign and discovered critical architectural insights about Falcon 3.0's overlay system. The session produced **66 new function names** (22.8% of 289 Level-0 functions), documented **24 findings** (180-204), and mapped the game's multi-layer overlay wrapper architecture.

## Achievements

### 1. Level-0 Naming Campaign (Findings 180-203)

**Batches completed:** 6 (ranks 1-80 by dyn_calls DESC)

**Named:** 66 functions across 6 batches
- Batch 1: 10 functions (ranks 1-10)
- Batch 2: 9 functions (ranks 11-20)  
- Batch 3: 12 functions (ranks 21-35)
- Batch 4: 11 functions (ranks 36-50, 4 duplicates from batch 1)
- Batch 5: 10 functions (ranks 51-65, 5 duplicates from batch 1)
- Batch 6: 14 functions (ranks 66-80, 1 duplicate from batch 2)

**Batch 7 analysis:** All 15 functions have dyn=0 (never executed). This represents a hard "value cliff" — remaining 223 functions likely debug/unused code.

**Decision:** Stop Level-0 at batch 6 (hot path covered).

### 2. CS-Segment State Map (95% Complete)

Mapped **470+ bytes across 21 regions:**
- Core state: 0x0000-0x0002, 0x000C-0x0012, 0x0022, 0x00E8, 0x0128
- Dispatch tables: 0x29D0-0x29EC, 0x2A00-0x2AD8
- PRNG state: 0x3662-0x3708, 0x35B1-0x35B5, 0x35B7-0x35C7
- Dispatcher params: 0x54F0+, 0x54F8-0x54FF, 0x5500-0x5503
- View/state buffers: 0x5762-0x577B, 0x5DC7-0x5DD9, 0x7DB6-0x7DC2

### 3. Key Technical Discoveries

**PRNG (finding 194):** Triple LCG (Linear Congruential Generator)
- Three parallel 16-bit seeds at cs:35B7, cs:35B9, cs:35BB
- Each: `seed = (seed * 0x8405 + 1) & 0xFFFF`
- Output: high byte of final seed

**String formatting (finding 195):** itoa utility
- Converts AX to ASCII decimal string at DS:SI
- 5-digit zero-suppressed with leading spaces

**3D vector operations (finding 197):** Vector clamping
- Fixed-point 3D delta scaling with STOSW
- Boundary enforcement for movement

**Dispatcher infrastructure (findings 180-193):** Multiple dispatch patterns
- FarObj dispatch via far pointers
- Two-stage dispatcher (table lookup + far call)
- Entry stub families for overlay loading

### 4. Architectural Discovery: Multi-Layer Overlay Wrappers (Finding 204)

**Critical insight:** The call graph above Level-0 is dominated by overlay entry trampolines, not game logic.

**Level-1 (424 unnamed functions):**
- ~310 functions (73%) are 8-byte overlay wrappers
- Pattern: `call sub_2AFBD` (tail_bridge_overlay_load) + `jmp far segment:offset`
- Only 7 non-wrapper functions have dyn>0
- Remaining 298 non-wrappers have dyn=0 (unexecuted)

**Level-2 (235 unnamed functions):**
- Top function sub_2BFC3 (30,515 calls) — highest in ALL levels
- Also an 8-byte overlay wrapper
- Pattern continues: wrappers calling wrappers
- 4 non-wrapper functions in top 20 with dyn>0

**Implications:**
- Real game logic resides **inside overlay segments**, not in call graph
- Traditional bottom-up naming hits diminishing returns above Level-0
- Shift strategy: trace-driven overlay target analysis or focus on non-wrappers

### 5. Function Boundary Analysis

**Result:** P1 (pure splits from findings 145-160) already fixed batch 1 collision issues.

**Measured impact:**
- MID targets: 96 → 63 (34% drop)
- EXACT targets: 468 → 653 (39% gain)
- Remaining 63 MIDs: 75% are R30 jump table cases (legitimate)

**Decision:** Boundary fixes declared complete for S4 purposes.

**Deferred:** 4 boundary errors for later phase
- sub_22445 (0x22445, split at 0x2244A, finding 186)
- sub_254D0 (0x254D0, split at 0x254D6, finding 190)
- sub_2765D (0x2765D, split at 0x27667, finding 190)
- sub_10108 (0x10108, splits at 0x1010F and 0x1011F, finding 190)

---

## Commits (11 total)

1. **d208467** - S4: Level-0 naming batch 1 (10 functions, findings 180-182)
2. **8e2c957** - S4: Function boundary analysis (prep for fixes)
3. **f225b5e** - S4: Function boundary analysis complete - P1 already fixed collisions
4. **e5a253c** - S4: Level-0 naming batch 2 (9 functions, findings 184-189)
5. **ec8b051** - S4: Level-0 naming batch 3 (12 functions, findings 190-193)
6. **e5d3b16** - docs: findings 180-193 (S4 Level-0 batches 1-3 documented)
7. **f79e488** - S4: Level-0 naming batch 4 (11 functions, findings 194-197)
8. **504ce9f** - docs: findings 194-200 (S4 Level-0 batches 4-5 documented)
9. **5b3c8e3** - S4: Level-0 naming batch 5 (10 functions, findings 198-200)
10. **49efe63** - S4: Level-0 naming batch 6 (14 functions, findings 201-203)
11. **0561f12** - docs: findings 201-203 (S4 Level-0 batch 6 documented)
12. **4df0253** - S4: Level-0 batch 7 analysis - value cliff wall reached (dyn=0)
13. **89aba43** - S4: Level-1 analysis - overlay wrapper pattern discovered
14. **403f2a4** - S4: Level analysis complete - overlay wrapper layers confirmed
15. **677a492** - Document finding 204 (multi-layer overlay wrapper architecture) and S4 completion

---

## Registry Impact

**naming.yaml:** 2034 → 2105 entries (+71)

**New names applied:** 66 Level-0 functions in `analysis/ida_falconcd/function_bytes.json`

**Findings documented:** 180-204 in `docs/findings_log.md`

---

## Artifacts Created

### Batch Analysis Files
- `analysis/s4/level0_batch[1-7]_*` - bytecode dumps, manual decode, analysis
- `analysis/s4/level1_batch1_manual_decode.md` - Level-1 wrapper pattern analysis
- `analysis/s4/level_analysis_summary.md` - comprehensive level breakdown

### Boundary Analysis
- `analysis/s4/boundary_report.json` - function boundary collision analysis
- `analysis/s4/plan_split_batch1_collisions.py` - collision resolution planning

### Documentation
- `docs/findings_log.md` - findings 180-204 appended
- `status.md` - S4 completion section added

---

## Non-Wrapper High-Value Targets (11 functions)

These functions have substantive logic (not overlay wrappers) and execution evidence:

**Level-1 (7 functions):**
1. sub_2241E (9,210 calls, 24B) - conditional dual-call overlay
2. sub_254DC (977 calls, 29B) - dispatch stub + wrapper (merged?)
3. sub_2318C (93 calls, 13B) - CS-segment read-modify-write
4. sub_23199 (22 calls, 13B) - CS-segment read-modify-write
5. sub_122AE (17 calls, 114B) - subsystem initialization
6. sub_11A7D (5 calls, 106B) - complex initialization
7. sub_10DA7 (4 calls, 31B) - interrupt-based operation

**Level-2 (4 functions):**
1. sub_256A3 (10,222 calls) - highest Level-2 non-wrapper
2. sub_2501A (488 calls)
3. sub_276B4 (194 calls)
4. sub_100C1 (8 calls)

---

## Strategy Recommendations

### Option 1: Name Non-Wrapper Functions (Recommended Next)
- 7 Level-1 functions already decoded in `level1_batch1_manual_decode.md`
- 4 Level-2 functions need decode
- Total: ~11 functions, ~2 hours
- High ROI: substantive logic with execution evidence

### Option 2: Overlay Target Analysis (Long-term)
- Shift from call graph to trace-driven analysis
- Identify high-frequency overlay destinations
- Analyze overlay code directly in IDA
- Very high ROI: reveals actual game logic

### Option 3: Continue Up Call Graph
- Level-3+ may continue overlay wrapper pattern
- Lower priority until overlay architecture understood

---

## Lessons Learned

1. **Value cliffs are real:** Dynamic call frequency drops to zero abruptly (batch 7)
2. **Overlay architecture dominates:** 73%+ of higher-level functions are trampolines
3. **Bottom-up has limits:** Call graph doesn't expose overlay segment logic
4. **Hot path coverage is sufficient:** 66 names cover 22.8% of functions but likely >95% of execution time
5. **Boundary fixes cascade:** P1 splits from findings 145-160 preemptively fixed batch collisions

---

## Session Statistics

**Duration:** ~6 hours (based on commit timestamps)  
**Functions named:** 66  
**Findings documented:** 24 (180-204)  
**Lines of assembly analyzed:** ~800+  
**Commits:** 11  
**Registry growth:** +71 entries (2034 → 2105)  

---

## Next Steps (Priority Order)

1. **Name 11 non-wrapper functions** (~2 hours)
   - 7 Level-1 already decoded
   - 4 Level-2 need decode

2. **Fix 4 deferred boundary errors** (~1 hour)
   - Split functions at documented boundaries

3. **Overlay target analysis** (new approach)
   - Mine traces for high-frequency overlay destinations
   - Analyze overlay code segments directly

4. **Continue S1 IDB stabilization** (parallel track)
   - Resume P4-P8 boundary work
   - Drain auto queue under manifest
