# Finding 206 Final: Overlay Analysis Complete, Dispatcher Investigation Inconclusive

**Date:** 2026-11-11  
**Status:** PARTIAL - Overlay analysis complete, dispatcher mapping blocked  
**Time spent:** ~5 hours total (3.5h analysis + 1.5h dispatcher mapping attempts)

## Summary

Successfully analyzed overlay function call frequencies and identified high-value targets. **Dispatcher table mapping unsuccessful** - sub_263F6's embedded data does not map to valid IDA functions using any tested addressing scheme.

## What Was Accomplished

### 1. Overlay Call Frequency Analysis ✓ COMPLETE

**Key findings:**
- 3,558 overlay functions (86% of 4,127 total)
- 434 have dynamic calls (12% of overlays)
- **Top 30 overlays ALL named** (542K to 38K calls)
- **97% hot-path coverage already achieved**

**Top 20 unnamed overlay functions identified:**
1. sub_2BFC3 (30,515 calls) - overlay wrapper
2. sub_263F6 (18,079 calls) - **investigated, inconclusive**
3. sub_2BEA1 (11,155 calls) - overlay wrapper
4. sub_2295C (11,154 calls) - zero-return
5. sub_256A3 (10,222 calls) - DGROUP:0x4287 accessor
... (15 more)

### 2. High-Value Targets Identified ✓ COMPLETE

**sub_256A3 (10,222 calls): DGROUP Accessor [HIGH VALUE, actionable]**
```assembly
push ds
mov di, 7B0Eh           ; DGROUP runtime
mov ds, di
mov di, 4287h           ; Offset 0x4287
call near sub_10BDB
pop ds
retf
```

**Next action:** Dump DGROUP:0x4287 and analyze sub_10BDB

**sub_1AFBD: Overlay Entry Hook (41,670 calls via wrappers)**
- Called by sub_2BFC3 and sub_2BEA1 before overlay jumps
- Understanding this reveals overlay mechanism

**Next action:** Analyze sub_1AFBD disassembly

### 3. Dispatcher Investigation ⚠️ INCONCLUSIVE

**sub_263F6 (18,079 calls, 122 bytes):**
```assembly
call far dword ptr cs:[2A10h]
retf
[116 bytes following]
```

**Attempted mappings:**
1. ❌ Offset:segment little-endian → addresses 0x7FFBC-0xA2AAC (out of IDB range)
2. ❌ Segment:offset little-endian → addresses 0x364C5-0x38774 (way out of range, max IDB=0x1AACD4)
3. ❌ Runtime segments (0x6E05-0x90B4) → no matches in runtime_seg_map
4. ❌ Runtime-to-link conversion (subtract 0x1F5) → 7 matched overlay record 69, but record 69 has ZERO functions in IDB
5. ❌ Link segments direct → no matches in segsplit registry

**Theories tested:**
- Far pointer dispatch table (multiple formats)
- Runtime CS segment values
- Link segment values
- Overlay record offsets
- Direct IDA linear addresses

**Result:** The 116 bytes do NOT map to valid IDA function addresses using any tested addressing scheme.

**Possible explanations:**
1. **Not a dispatch table** - might be data, configuration, or padding
2. **Unanalyzed overlay** - points to overlay record 69 which has no functions in IDB
3. **Different addressing mode** - protected mode, EMS, or other scheme
4. **Corrupt data** - not actually meaningful bytes
5. **Wrong interpretation** - the function does something else entirely

**Recommendation:** **Defer dispatcher investigation**. Without being able to map the table entries to actual code, further analysis requires either:
- IDA interactive analysis of the function
- Runtime debugging to see what CS:2A10 actually points to
- Analysis of overlay record 69 to add missing functions to IDB

## Artifacts Created

**Analysis scripts:**
- `top_overlay_targets.py` - Extract overlay call frequencies
- `parse_263F6_table.py` - Parse embedded data
- `map_dispatcher_segments.py` - Segment mapping (multiple formats)
- `check_table_segments.py` - Segsplit registry matching
- `final_segment_check.py` - Overlay record range checking
- `map_record69.py` - Record 69 specific mapping
- `check_rec69_funcs.py` - Verify record 69 in IDB
- `reparse_table_segoff.py` - Corrected segment:offset parsing

**Data files:**
- `top_overlay_targets.json` - Top 20 unnamed with bytecode
- `sub_263F6_table.json` - Initial parse (offset:segment)
- `dispatcher_mapping.json` - Direct IDA address attempts
- `dispatcher_record69_mapping.json` - Record 69 attempts
- `dispatcher_corrected.json` - Corrected segment:offset parse

**Documentation:**
- `top5_overlay_decode.md` - Manual decode
- `top_overlay_analysis.md` - Comprehensive analysis
- `finding_206_summary.md` - Initial summary
- `finding_206_final.md` - This document

## Lessons Learned

**What worked:**
- Overlay call frequency analysis - identified hot functions efficiently
- Top 30 all named - confirmed excellent prior coverage
- Pattern recognition - identified wrappers, accessors, dispatchers by bytecode

**What didn't work:**
- Dispatcher table mapping - invested 1.5 hours, tried 5+ addressing schemes, no valid results
- Overlay record 69 - placed in IDB but not analyzed (no functions)
- Segment translation - complex overlay addressing prevented straightforward mapping

**Time management:**
- Should have stopped dispatcher investigation after 30-45 min when first 2-3 approaches failed
- Got into "sunk cost" mentality trying to make it work
- Better ROI would have been moving to sub_256A3 or sub_1AFBD after initial failure

## Recommendations for Next Session

### Option A: Complete Actionable Targets [RECOMMENDED, 1-2 hours]

**1. Analyze sub_256A3 DGROUP accessor (30 min, HIGH VALUE)**
- Dump DGROUP bytes around offset 0x4287
- Analyze sub_10BDB to understand access pattern
- Identify data structure (player state? frame data?)
- Name sub_256A3 based on findings

**2. Analyze sub_1AFBD overlay hook (45 min, MEDIUM-HIGH VALUE)**
- Disassemble and understand mechanism
- Likely: state save, segment setup, or loader dispatch
- Name sub_1AFBD
- Then name sub_2BFC3/sub_2BEA1 based on their jump targets

**3. Quick wins from top 20 list (30 min, MEDIUM VALUE)**
- sub_2295C (11K calls) - verify if real function
- Ranks 6-10: utilities and accessors
- Low-hanging naming fruit

**Total:** 2 hours, 2-3 functions named, 2 data structures understood

### Option B: Return to Boundary Fixes [4-6 hours, MEDIUM VALUE]

- 91 mid-body targets remaining
- Stabilization work
- Grinding but necessary eventually

### Option C: Defer and Move to Different Phase

- S5: Another decompilation phase
- P10: Trace analysis
- Documentation cleanup

## Status

**Complete:**
- ✓ Overlay call frequency analysis
- ✓ Top 20 unnamed identified
- ✓ High-value targets (sub_256A3, sub_1AFBD) identified
- ✓ Overlay wrapper pattern documented

**Inconclusive:**
- ⚠️ sub_263F6 dispatcher table mapping (tried 5+ approaches, none worked)

**Not started:**
- sub_256A3 DGROUP analysis
- sub_1AFBD overlay hook analysis
- Ranks 6-20 overlay analysis

**Blocked:**
- sub_263F6 requires IDA interactive or runtime debugging

## Gates

- **Functions:** 4,127 (stable)
- **Naming registry:** 2,115 entries (no changes this session)
- **IDB:** Unmodified
- **Integrity:** INTACT

## Time Breakdown

- VGRAPH verification: 15 min
- Overlay analysis: 2 hours
- Dispatcher investigation: 1.5 hours
- Documentation: 45 min
- **Total:** ~4.5 hours

## Value Assessment

**High value achieved:**
- Confirmed 97% hot-path coverage (top 30 named)
- Identified 2 actionable high-value targets (sub_256A3, sub_1AFBD)
- Documented overlay architecture patterns

**Medium value:**
- Top 20 list for future naming
- Elimination of sub_263F6 as immediate target

**Low/negative value:**
- 1.5 hours on dispatcher mapping with no results
- Should have cut losses earlier

**Overall:** Good session with one failed branch. Net positive value.

## Next Session Start Point

**Immediate action:** Analyze sub_256A3 DGROUP accessor
- Script: Create `analyze_dgroup_4287.py`
- Dump DGROUP bytes around 0x4287
- Analyze sub_10BDB disassembly
- Identify structure, name function

**Estimated time:** 30 minutes  
**Expected value:** HIGH (reveals core game state structure)

