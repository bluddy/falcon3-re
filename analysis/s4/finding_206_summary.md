# Finding 206: Overlay Target Analysis - High-Value Functions Identified

**Date:** 2026-11-11  
**Status:** IN PROGRESS

## Summary

Analyzed overlay function call frequencies to identify high-value unnamed targets for reverse engineering. Discovered that **top 30 overlay functions are all named**, with highest unnamed at rank #31 (sub_2BFC3, 30,515 calls).

## Key Findings

### 1. Overlay vs Resident Distribution

- **Total functions:** 4,127
- **Overlay functions:** 3,558 (86%)
- **Resident functions:** 569 (14%)
- **Overlay functions with dynamic calls:** 434 (12% of overlays, 75% of all executed functions)

**Insight:** Most game logic is in overlays, but only ~12% of overlay code is actually executed in traces.

### 2. Top 30 Overlay Functions: All Named ✓

The 30 most-frequently-called overlay functions are all already named, ranging from:
- #1: sub_251C3 (542,872 calls) - already named
- #30: sub_25F64 (38,096 calls) - already named

**Insight:** Previous naming campaigns successfully covered the hottest overlay paths.

### 3. Top 20 Unnamed Overlay Functions

See `top_overlay_targets.json` for full data.

| Rank | Function | Calls | Size | Type | Value |
|------|----------|-------|------|------|-------|
| 1 | sub_2BFC3 | 30,515 | 8B | Overlay wrapper | Med |
| 2 | **sub_263F6** | 18,079 | 122B | **Dispatcher + table** | **VERY HIGH** |
| 3 | sub_2BEA1 | 11,155 | 8B | Overlay wrapper | Med |
| 4 | sub_2295C | 11,154 | 2B | Zero-return | Low |
| 5 | **sub_256A3** | 10,222 | 15B | **DGROUP accessor** | **HIGH** |
| 6-20 | Various | 9,698-534 | Mixed | Mixed utilities | Med |

### 4. Detailed Analysis: sub_263F6 (18,079 calls)

**Code structure:**
```assembly
call far dword ptr cs:[2A10h]    ; Indirect far call
retf
[116 bytes embedded data table]
```

**Embedded table analysis:**
- **29 entries** (116 bytes / 4 bytes per entry)
- **21 valid far pointers** (segment:offset format)
- **8 null entries**
- Format: Little-endian dwords (offset:segment)

**Sample entries:**
```
Entry 11: segment 0x90B4, offset 0x1F6C  (link-time address)
Entry 12: segment 0x8A87, offset 0x1F6C
Entry 13: segment 0x7AC0, offset 0x1F6C
...
```

**Pattern:** All non-null entries have **offset 0x1F6C** (except entries 1, 5, 6, 25, 27)
- 0x1F6C appears in 16 out of 21 valid entries
- This offset likely refers to a **common entry point** or **dispatch offset**
- Segments vary widely: 0x6E4C to 0x90B4 (overlay segments)

**Hypothesis:** This is a **mode/state dispatch table**
- CS:2A10 contains current mode index
- Table[mode] = far pointer to handler function
- ~29 different modes/states in game
- Could be: main menu, briefing, flight, debriefing, loadout, etc.

**Value:** **VERY HIGH** - reveals game state machine structure

**Status:** Table parsed (`sub_263F6_table.json`), needs segment-to-function mapping

---

### 5. Detailed Analysis: sub_256A3 (10,222 calls)

**Code:**
```assembly
push ds
mov di, 7B0Eh           ; DGROUP runtime segment
mov ds, di              ; DS = DGROUP
mov di, 4287h           ; DI = offset 0x4287
push cs
call near sub_10BDB     ; Resident function
pop ds
retf
```

**Analysis:**
- Accesses **DGROUP:0x4287** (global data segment, specific offset)
- 0x7B0E confirmed as DGROUP runtime segment (Finding 176)
- Calls sub_10BDB with DS:DI pointing to data structure
- 10,222 calls = **critical hot-path accessor**

**Questions:**
1. What data structure is at DGROUP:0x4287?
2. What does sub_10BDB do with DS:DI? (read/write/modify)
3. Why 10K+ calls? (per-frame? per-entity? per-event?)

**Hypothesis:** Accessor for **central game state structure**
- Could be: player state, current frame data, input state, active entity list, etc.
- High frequency suggests per-frame or per-entity access

**Value:** **HIGH** - reveals core game state architecture

**Status:** Decoded, needs DGROUP dump and sub_10BDB analysis

---

### 6. Overlay Wrapper Pattern (sub_2BFC3, sub_2BEA1)

**Pattern:**
```assembly
call near sub_1AFBD     ; Pre-call hook (same function in both)
jmp far segment:offset  ; Far jump to overlay
```

**Combined calls:** 41,670 (30,515 + 11,155)

**Insight:** sub_1AFBD is the **overlay entry hook**
- Called before every overlay far-jump
- Likely: state save, segment setup, or logging
- Could be the overlay loader dispatch itself

**Value:** MEDIUM - understanding sub_1AFBD reveals overlay mechanism, but wrappers are structurally simple

---

## Artifacts Created

1. **`top_overlay_targets.py`** - Analysis script
2. **`top_overlay_targets.json`** - Top 20 unnamed overlay functions with bytecode
3. **`parse_263F6_table.py`** - Dispatcher table parser
4. **`sub_263F6_table.json`** - Parsed table (29 entries, 21 valid)
5. **`top5_overlay_decode.md`** - Manual bytecode decode of top 5
6. **`top_overlay_analysis.md`** - Detailed analysis and recommendations
7. **`finding_206_summary.md`** - This document

## Recommendations

### Next Actions (Priority Order)

**1. Map sub_263F6 dispatcher table to functions [HIGH VALUE, 1 hour]**
   - Convert link segments to IDA addresses using runtime_seg_map.json
   - Identify which functions the 21 entries point to
   - Classify the 29 modes/states
   - Name sub_263F6 as `mode_dispatcher` or `state_dispatch_table`

**2. Analyze DGROUP:0x4287 structure [HIGH VALUE, 30 min]**
   - Dump DGROUP bytes around offset 0x4287
   - Analyze sub_10BDB to understand access pattern
   - Identify data structure type (size, fields, purpose)
   - Name sub_256A3 based on structure (e.g., `get_player_state`, `get_frame_data`)

**3. Analyze sub_1AFBD overlay hook [MEDIUM VALUE, 45 min]**
   - Understand overlay entry mechanism
   - Check if it's the loader or just a hook
   - Name based on function
   - Then name sub_2BFC3 and sub_2BEA1 based on their far-jump targets

**4. Verify sub_2295C [QUICK WIN, 5 min]**
   - Check if it's really just `sub ax,ax` with implicit retf
   - Or if it's misclassified
   - Name if legitimate

**5. Continue down top 20 list [INCREMENTAL, 2-3 hours]**
   - Analyze ranks 6-20 (9,698 to 534 calls)
   - Mix of utilities, accessors, dispatchers
   - Good for incremental naming progress

### Strategic Insights

**Overlay architecture dominates:**
- 86% of code is in overlays
- Top overlay functions are all named (great coverage)
- Real value is in understanding **overlay interactions** and **shared state**

**Hot path coverage:**
- Top 30 named = ~5.4M calls covered
- Top 20 unnamed = ~150K calls remaining
- Already captured 97% of dynamic overlay activity

**Value shift:**
- Previous campaigns: name individual functions
- Current phase: understand **structures** (dispatch tables, state, mechanisms)
- Finding 206 targets: **2 structural targets** (dispatcher, state) > **18 utility targets**

## Status

**Complete:**
- ✓ Overlay call frequency analysis
- ✓ Top 20 unnamed identified
- ✓ Top 5 manual bytecode decode
- ✓ sub_263F6 table parsed (29 entries)
- ✓ sub_256A3 pattern identified (DGROUP accessor)

**In Progress:**
- ⚠️ sub_263F6 segment-to-function mapping (need runtime_seg_map translation)
- ⚠️ DGROUP:0x4287 structure analysis (need dump + sub_10BDB analysis)

**Blocked:**
- None

## Gates

- **Naming registry:** 2115 entries (no changes yet this finding)
- **Function count:** 4,127 (stable)
- **Integrity:** Presumed INTACT (no IDB changes)

## Next Session

**Recommended:** Complete sub_263F6 dispatcher mapping (Action #1)
- High value, clear path forward
- Reveals game state machine
- Enables naming of dispatcher + potentially discovering 21 mode handler functions
- **Est. time:** 1 hour
- **Output:** Finding 206 complete, dispatcher named, mode structure documented

