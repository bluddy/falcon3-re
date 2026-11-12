# S4 Level Analysis Summary

## Overview

Analysis of call graph levels 0-2 to understand architectural layers and identify optimal naming targets.

## Level Distribution

| Level | Total | Named | Unnamed | % Named |
|-------|-------|-------|---------|---------|
| Level-0 | 2,194 | 1,770 | 424 | 80.7% |
| Level-1 | 1,232 | 808 | 424 | 65.6% |
| Level-2 | 552 | 317 | 235 | 57.4% |

**Note:** Level-0 "named" includes many that are just `sub_*` - actual campaign named 66 high-value functions.

## Level-0: Leaf Functions (Primitives)

**Character**: Tiny accessors and utilities (2-100B)
**Pattern**: 67% CS-segment state accessors, 20% dispatch stubs
**Campaign result**: 66 of 289 hottest named (22.8%)
**Value cliff**: Rank 81+ have dyn=0 (never executed)

**Key discoveries:**
- CS-segment state map (470+ bytes, 21 regions)
- PRNG (triple LCG)
- String formatting (itoa)
- 3D vector operations
- Dispatcher infrastructure

**Status:** ✅ **COMPLETE** (hot path covered, value cliff reached)

## Level-1: First Abstraction Layer

**Character**: Dominated by overlay entry wrappers (73%)
**Pattern**: `call tail_bridge_overlay_load` + `jmp far segment:offset`
**Size**: Mostly 8B (trampolines)

### Level-1 Breakdown

**Overlay wrappers:** ~310 functions (73%)
- 8-byte pattern: load overlay + jump
- Structurally trivial, architecturally critical
- Define entry point interface to overlay code
- **Low naming value** (repetitive pattern)

**Non-wrapper candidates:** 305 functions (72% of unnamed)
- Filtered: no overlay loader call OR size>20B OR out-degree≥3
- Size distribution:
  - 8-20B: 14 (4.6%)
  - 21-50B: 36 (11.8%)
  - 51-100B: 51 (16.7%)
  - **>100B: 204 (66.9%)**

**Non-wrappers with dyn>0:** Only 7 functions!
1. sub_2241E (9,210 calls, 24B) - conditional dual-call overlay
2. sub_254DC (977 calls, 29B) - dispatch stub + wrapper (merged?)
3. sub_2318C (93 calls, 13B) - CS-segment read-modify-write
4. sub_23199 (22 calls, 13B) - CS-segment read-modify-write
5. sub_122AE (17 calls, 114B) - subsystem initialization
6. sub_11A7D (5 calls, 106B) - complex initialization
7. sub_10DA7 (4 calls, 31B) - interrupt-based operation

**Remaining 298 non-wrappers:** dyn=0 but high static fan-in
- Likely: mode handlers, UI/menu functions, error paths
- Not executed in traces (conditional/rare paths)
- Size: 67% are >100B (complex orchestration)

**Status:** ⚠️ **Low priority** for naming (overlay wrappers + unexecuted code)

## Level-2: Second Abstraction Layer

**Character**: Callers of Level-1 (orchestration layer)
**Total unnamed:** 235 functions
**With dyn>0:** 69 (29.4%)

**Top function:** sub_2BFC3 (30,515 calls) - **highest in all levels!**

**Pattern**: Still many 8B functions (overlay wrappers calling overlay wrappers?)

**Call frequency:**
- Top 1: 30,515 calls
- Top 10: 30K → 16 calls
- Steep cliff (similar to Level-0/1)

**Status:** 🔍 **Interesting** - rank 1 has 3x calls of Level-1 rank 1

## Strategic Insights

### Overlay Architecture Dominates

The game uses **multi-layer overlay wrappers**:
- Level-0: primitives (CS-segment, dispatch stubs, utilities)
- Level-1: 73% overlay entry trampolines
- Level-2: More overlay trampolines? (investigating)
- **Real logic**: inside overlay segments (not directly visible in call graph)

### Dynamic Evidence Distribution

**Functions with dyn>0 across levels:**

| Level | Total Unnamed | With dyn>0 | % | Highest Call |
|-------|---------------|------------|---|--------------|
| L0 | 289 | 80 | 27.7% | 18,041 |
| L1 | 424 | ~50 | ~12% | 11,155 |
| L2 | 235 | 69 | 29.4% | **30,515** |

**Observation:** Level-2 rank 1 (30.5K) > Level-0 rank 1 (18K) > Level-1 rank 1 (11K)

This suggests **sub_2BFC3 is a critical hub function** - possibly:
- Main game loop entry
- Frame update dispatcher
- Entity system manager
- Input/event handler

### Value Cliff Phenomenon

All levels show **steep value cliffs**:
- Small number of hot functions (top 10-20%)
- Rapid decline to dyn=0
- Majority of functions unexecuted in traces

**Implication:** Focus on **top 10-20 functions per level** for maximum ROI.

## Recommended Strategy

### Option A: Top Functions Per Level (Recommended)

Target the **hottest 10 functions from each level** with dyn>0:
- Level-0: ✅ Already done (66 functions, covered top 35)
- Level-1: 7 non-wrapper functions with dyn>0 (analyze these)
- Level-2: Top 10 with dyn>0 (30K → ~15 calls)

**Estimated:** ~17 functions total
**ROI:** High - these are the most-executed non-primitive code

### Option B: Architectural Pattern Focus

Ignore overlay wrappers, target unique patterns:
- Complex initializers (>100B, multiple callees)
- State managers (read-modify-write patterns)
- Conditional logic (dual-call, flag-based)
- Hub functions (high fan-in/fan-out)

**Estimated:** ~20-30 functions across levels
**ROI:** Medium-high - architectural insight without overlay noise

### Option C: Level-2 Deep Dive

Focus exclusively on Level-2 top 20:
- Highest call frequencies (30K top)
- Likely orchestration/management layer
- One level removed from overlay wrappers

**Estimated:** 20 functions (top with dyn>0)
**ROI:** High - may reveal game loop and core systems

### Option D: Overlay Target Analysis

Shift from call graph to **overlay segment analysis**:
- Identify high-frequency overlay targets from traces
- Analyze overlay code directly in IDA
- Understand actual game logic (not just entry points)

**Estimated:** Different approach, not function counting
**ROI:** Very high - reveals actual game logic

## Recommendation

**Proceed with Option A + C hybrid:**

1. **Analyze Level-2 top 10** (30K-15 calls range)
   - Starting with sub_2BFC3 (30.5K calls, 8B)
   - Likely reveals main game loop or critical hub

2. **Name Level-1 non-wrapper top 7** (already decoded)
   - Quick wins, already analyzed
   - Includes conditional logic and state managers

3. **Document findings and reassess**
   - If Level-2 is also overlay wrappers, pivot to Option D
   - If Level-2 has real logic, continue upward

**Total effort:** ~17 functions, ~2-3 hours

This approach tests whether higher levels have substantive logic or just more overlay infrastructure.
