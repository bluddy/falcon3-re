# Session 56 Summary: Finding 206 - Overlay Target Analysis

**Date:** 2026-11-11  
**Branch:** master  
**Commit:** 77a827c  
**Session goal:** Provide maximum value for spec completion - chose S4 overlay analysis over boundary grinding

## Decision: S4 Overlay Analysis (not boundary fixes)

**Context:** User asked to "do what you think will provide the most value" with 91 mid-body boundary targets remaining.

**Analysis:**
- Boundary fixes: P2/P4 grinding, 91 targets, risk of more Finding 205 situations (2 hours spent, reclassified)
- S4 overlay targets: High-value game logic, structural understanding, advances spec

**Recommendation:** S4 overlay target analysis for better ROI
**User decision:** Agreed, proceeded

## What Was Done

### 1. Identified Top Overlay Call Frequencies
- Analyzed 3,558 overlay functions (86% of 4,127 total)
- 434 overlay functions have dynamic calls (12% of overlays)
- Extracted call frequencies from `callgraph_partial.json`

**Key finding:** **Top 30 overlay functions all already named!**
- #1: sub_251C3 (542,872 calls)
- #30: sub_25F64 (38,096 calls)
- Previous naming campaigns achieved excellent hot-path coverage

### 2. Analyzed Top 20 Unnamed Overlay Functions
- Highest unnamed: sub_2BFC3 at rank #31 overall (30,515 calls)
- Created `top_overlay_targets.json` with bytecode for all 20
- Manual bytecode decode of top 5

### 3. Identified 2 High-Value Structural Targets

**sub_263F6 (18,079 calls, rank #2 unnamed): Mode Dispatcher [VERY HIGH VALUE]**
```assembly
call far dword ptr cs:[2A10h]    ; Indirect dispatcher
retf
[116 bytes embedded data table]
```

- Parsed embedded table: **29 entries** (21 valid far pointers, 8 null)
- Format: Little-endian dwords (offset:segment)
- 16 of 21 entries use offset 0x1F6C (common entry point)
- Segments: 0x6E4C to 0x90B4 (overlay link segments)

**Hypothesis:** Game mode/state dispatch table
- CS:2A10 = current mode index
- Table[mode] = handler function far pointer
- ~29 game modes: menus, briefing, flight, debrief, loadout, etc.

**Value:** Reveals game state machine architecture

---

**sub_256A3 (10,222 calls, rank #5 unnamed): DGROUP Accessor [HIGH VALUE]**
```assembly
push ds
mov di, 7B0Eh           ; DGROUP runtime segment
mov ds, di
mov di, 4287h           ; Offset into DGROUP
call near sub_10BDB     ; Resident accessor function
pop ds
retf
```

- Accesses **DGROUP:0x4287** (specific data structure)
- 0x7B0E = DGROUP runtime (confirmed Finding 176)
- 10,222 calls = critical hot path
- sub_10BDB performs the actual access

**Hypothesis:** Central game state accessor
- Could be: player state, frame data, input state, active entities
- High frequency suggests per-frame or per-entity access

**Value:** Reveals core game state structure

### 4. Identified Overlay Wrapper Pattern
**sub_2BFC3 (30,515) + sub_2BEA1 (11,155) = 41,670 calls**

Pattern:
```assembly
call near sub_1AFBD     ; Same hook in both
jmp far segment:offset  ; Different targets
```

**sub_1AFBD is the overlay entry hook**
- Called before every overlay jump
- Likely: state save, segment setup, or overlay loader dispatch

## Artifacts Created

1. **Analysis scripts:**
   - `analysis/s4/top_overlay_targets.py` - Extract top overlay calls
   - `analysis/s4/parse_263F6_table.py` - Parse dispatcher table
   - `analysis/s4/analyze_overlay_targets.py` - Distribution analysis
   - `analysis/s4/analyze_top5.py` - IDA analysis script (for future use)

2. **Data files:**
   - `analysis/s4/top_overlay_targets.json` - Top 20 with bytecode
   - `analysis/s4/sub_263F6_table.json` - Parsed 29-entry table

3. **Documentation:**
   - `analysis/s4/top5_overlay_decode.md` - Manual decode of top 5
   - `analysis/s4/top_overlay_analysis.md` - Detailed analysis
   - `analysis/s4/finding_206_summary.md` - Comprehensive finding doc

## Statistics

**Overlay distribution:**
- Total functions: 4,127
- Overlay: 3,558 (86%)
- Resident: 569 (14%)
- Overlays with dyn>0: 434 (12% of overlays)

**Call coverage:**
- Top 30 named overlays: ~5.4M calls
- Top 20 unnamed overlays: ~150K calls
- **97% of dynamic overlay activity already captured by naming**

**Top 20 unnamed:**
- Combined calls: ~150,000
- Size range: 2B to 163B
- Types: 2 dispatchers, 2 wrappers, 16 utilities/accessors

## Strategic Insights

### Value Shift
- **Previous phase:** Name individual hot functions (S4 Level-0 campaign)
- **Current phase:** Understand structures (dispatch tables, state, mechanisms)
- **Finding 206:** 2 structural targets > 18 utility targets

### Overlay Architecture
- 86% of code in overlays (game logic)
- Only 12% of overlay code executed in traces (rest: rare paths, errors, modes)
- Top overlay functions already named (excellent prior coverage)
- **Real value:** Understanding overlay interactions and shared state

### ROI Analysis
| Approach | Time | Value | Reason |
|----------|------|-------|--------|
| Boundary fixes (91 targets) | ~4-6 hours | Medium | Stabilization, grinding, risk of reclassification |
| Overlay analysis (top 20) | ~3 hours | **Very High** | Structural understanding, game architecture |
| **Dispatcher mapping** | **~1 hour** | **Very High** | Game state machine, 29 modes, enables discovery |

## Next Steps (Recommended)

**Priority 1: Map sub_263F6 dispatcher [1 hour, VERY HIGH VALUE]**
1. Convert link segments (0x6E4C–0x90B4) to IDA addresses
2. Identify which functions the 21 entries point to
3. Classify the 29 modes/states
4. Name sub_263F6 and document game state machine

**Priority 2: Analyze DGROUP:0x4287 [30 min, HIGH VALUE]**
1. Dump DGROUP bytes around offset 0x4287
2. Analyze sub_10BDB access pattern
3. Identify data structure (size, fields, purpose)
4. Name sub_256A3 based on structure

**Priority 3: Analyze sub_1AFBD overlay hook [45 min, MEDIUM VALUE]**
1. Understand overlay entry mechanism
2. Name based on function
3. Name sub_2BFC3/sub_2BEA1 based on far-jump targets

**Alternative: Return to boundary fixes if preferred [4-6 hours, MEDIUM VALUE]**
- 91 mid-body targets remain (1 merged, 19 not_head, 24 secondary, 46 other)
- Stabilization value, but lower insight per hour

## Status

**Complete:**
- ✓ VGRAPH verification (Finding 176 already applied)
- ✓ Overlay call frequency analysis
- ✓ Top 20 unnamed identified and bytecode extracted
- ✓ Top 5 manual decode
- ✓ sub_263F6 table parsed (29 entries, 21 valid pointers)
- ✓ sub_256A3 DGROUP accessor pattern identified

**In Progress:**
- ⚠️ sub_263F6 segment-to-function mapping
- ⚠️ DGROUP:0x4287 structure analysis

**Blocked:** None

## Gates

- **IDB:** analysis/ida_falconcd/FALCONCD.EXE.i64 (modified timestamp but no structural changes)
- **Functions:** 4,127 (stable since Finding 176)
- **Naming registry:** 2,115 entries (no changes this session)
- **Integrity:** Presumed INTACT (no boundary changes)
- **Commits:** 77a827c (Finding 206 analysis)

## Files Changed

```
A  analysis/s4/analyze_overlay_targets.py
A  analysis/s4/analyze_top5.py
A  analysis/s4/finding_206_summary.md
A  analysis/s4/parse_263F6_table.py
A  analysis/s4/sub_263F6_table.json
A  analysis/s4/top5_overlay_decode.md
A  analysis/s4/top_overlay_analysis.md
A  analysis/s4/top_overlay_targets.json
A  analysis/s4/top_overlay_targets.py
```

## Time Spent

- VGRAPH verification: 15 min
- Overlay analysis strategy: 30 min
- Call frequency extraction: 30 min
- Top 20 identification: 15 min
- Manual decode (top 5): 45 min
- Table parsing: 30 min
- Documentation: 45 min
**Total: ~3.5 hours**

## Session Outcome

✓ **Successfully identified 2 very-high-value structural targets** (dispatcher + state accessor)  
✓ **97% hot-path coverage confirmed** (top 30 overlays already named)  
✓ **Clear path forward:** Dispatcher mapping = 1 hour for game state machine understanding  
✓ **Better ROI than boundary grinding:** Structural insight > incremental stabilization  

**Recommendation for next session:** Complete dispatcher mapping (Action #1) - reveals game architecture, enables discovery of 21 mode handlers, high value per hour invested.

