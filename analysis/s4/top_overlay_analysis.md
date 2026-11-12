# Top Unnamed Overlay Functions - Deep Analysis

## Finding 206: High-Value Overlay Function Analysis

**Date:** 2026-11-11  
**Status:** CONFIRMED

### Objective
Analyze the top unnamed overlay functions (by dynamic call frequency) to identify game systems and naming opportunities.

### Methodology
1. Extracted overlay call frequencies from `callgraph_partial.json`
2. Filtered to overlay functions (ea >= 0x1FBC0)
3. Cross-referenced with naming status
4. Manual bytecode decode of top 5 unnamed functions

### Results: Top 20 Unnamed Overlay Functions

See `top_overlay_targets.json` for full data.

**Key finding:** Top 30 overlay functions by call frequency are ALL already named. The highest unnamed is rank #31 overall.

| Rank | Function | Calls | Size | Pattern |
|------|----------|-------|------|---------|
| 1 | sub_2BFC3 | 30,515 | 8B | Overlay wrapper |
| 2 | **sub_263F6** | 18,079 | 122B | **Dispatcher + table** |
| 3 | sub_2BEA1 | 11,155 | 8B | Overlay wrapper |
| 4 | sub_2295C | 11,154 | 2B | Zero-return |
| 5 | **sub_256A3** | 10,222 | 15B | **DGROUP accessor** |

### Detailed Analysis

---

## sub_263F6: Mode Dispatcher with Embedded Table (18,079 calls)

**Bytecode:**
```
2e ff 1e 10 2a    call far dword ptr cs:[2A10h]
cb                retf
[116 bytes of data]
```

**Code structure:**
- Indirect far call via CS:2A10 (dispatch pointer)
- Immediate return
- **Embedded data table: 116 bytes**

**Data table analysis:**
```
Offset  Hex Data          Interpretation
------  ----------------  --------------
+0x00   00 00 00 00       Null dword
+0x04   FF FF 00 00       -1, 0 (sentinel?)
+0x08   00 00 00 00       Nulls (repeated)
...
+0x12   6E 00 58 00       Word pairs (addresses?)
+0x14   00 01 00 00       
+0x18   00 00 00 00
+0x1C   00 00 00 00
+0x20   0E 90 6C 1F       Segment:offset pair? (1F6C:900E)
+0x24   B4 90 6C 1F       Another seg:off
+0x28   87 8A 6C 1F
+0x2C   C0 7A 6C 1F
```

**Pattern recognition:**
- Data after code is common for **jump tables** or **dispatch tables**
- Far pointer format (segment:offset dwords)
- ~30 entries (116 bytes / 4 bytes per entry = 29 entries)

**Hypothesis:** This is a **mode handler dispatch table**
- CS:2A10 points to current mode
- Table contains far pointers to 29 different mode handlers
- Could be: menu states, UI screens, game modes, etc.

**Value:** **VERY HIGH** - Understanding this table reveals major game state structure

**Recommended name:** `mode_dispatcher_table` or `ui_state_dispatch_table`

---

## sub_256A3: DGROUP Data Structure Accessor (10,222 calls)

**Bytecode:**
```
1E                push ds
BF 0E 7B          mov di, 7B0Eh
8E DF             mov ds, di        ; DS = 0x7B0E
BF 87 42          mov di, 4287h     ; DI = offset 0x4287
0E                push cs
E8 2B B5          call near 0x10BDB ; sub_10BDB
1F                pop ds
CB                retf
```

**Analysis:**
- Saves DS
- Sets DS to **0x7B0E** (DGROUP runtime segment from VGRAPH analysis)
- Sets DI to offset **0x4287** in DGROUP
- Calls `sub_10BDB` (resident function)
- Restores DS and returns

**DGROUP context:**
- 0x7B0E is the runtime DGROUP segment (confirmed in Finding 176)
- This is the main data segment for global variables
- Offset 0x4287 = specific data structure

**What's at DGROUP:0x4287?**
Need to check DGROUP map or dump to see what data structure lives there.

**sub_10BDB analysis needed:**
- What does it do with DS:DI?
- Read? Write? Both?
- Return value?

**Hypothesis:** Accessor for a **frequently-used game state structure**
- 10,222 calls = critical hot path
- Direct DGROUP access = not overlay data
- Could be: player state, frame state, input buffer, etc.

**Value:** **HIGH** - Reveals central game state structure

**Recommended investigation:**
1. Check what's at DGROUP runtime address 0x7B0E:0x4287
2. Analyze sub_10BDB to understand access pattern
3. Name based on data structure purpose

---

## sub_2295C: Zero-Return Utility (11,154 calls)

**Bytecode:**
```
2B C0             sub ax, ax    ; AX = 0
[implicit retf?]
```

**Problem:** Only 2 bytes, no explicit `retf` (0xCB)

**Possibilities:**
1. **Misclassification:** Not actually a function, part of larger function
2. **Thunk:** Falls through to next instruction which is `retf`
3. **Incomplete export:** Missing trailing `retf` byte

**Need to verify:** Check bytes at 0x2295E and 0x2295F

If this is legitimate:
- Returns AX=0 (false/null)
- 11,154 calls = extremely common
- Could be: `return_false`, `get_null_ptr`, `clear_accumulator`

**Value:** LOW until verified (may not be real function)

---

## sub_2BFC3 & sub_2BEA1: Overlay Entry Wrappers (30,515 & 11,155 calls)

**Pattern (both functions):**
```
E8 xx xx          call near sub_1AFBD
EA xx xx xx xx    jmp far [segment:offset]
```

**Analysis:**
- Both call the SAME resident function: `sub_1AFBD`
- Then far jump to different overlay segments
- sub_2BFC3 → 2CF6:0D01
- sub_2BEA1 → 4DAD:0010

**sub_1AFBD role:**
This function is the **overlay load hook** or **state setup routine**
- Called before every overlay jump
- Likely saves state, prepares segments, or logs entry
- Could be overlay loader itself

**Value:** MEDIUM - Understanding sub_1AFBD reveals overlay mechanism, but these wrappers themselves are structurally simple

**Recommended:**
1. Analyze sub_1AFBD first
2. Name it based on function (e.g., `overlay_entry_hook`)
3. Then name wrappers based on their far-jump targets

---

## Recommendations

### Immediate Actions (High Value)

**1. Analyze sub_263F6 dispatcher table (18,079 calls)**
   - Export 116-byte data table
   - Parse as far pointer array (29 entries)
   - Check what segments/functions they point to
   - Identify mode/state structure
   - **Est. time:** 30min
   - **Value:** Reveals major game architecture

**2. Investigate DGROUP:0x4287 accessed by sub_256A3 (10,222 calls)**
   - Dump DGROUP around offset 0x4287
   - Analyze sub_10BDB behavior
   - Identify data structure type
   - **Est. time:** 30min
   - **Value:** Reveals central game state

**3. Verify sub_2295C (11,154 calls)**
   - Check if it's a real function or misclassification
   - If real, name it `return_zero` or similar
   - **Est. time:** 5min
   - **Value:** Quick win if legitimate

### Secondary Actions (Medium Value)

**4. Analyze sub_1AFBD overlay hook**
   - Called by top 2 wrappers (41,670 total calls via wrappers)
   - Understanding this reveals overlay loading mechanism
   - **Est. time:** 45min
   - **Value:** Architectural understanding

**5. Continue down top 20 list**
   - Ranks 6-20 have 9,698 down to 534 calls
   - Mix of accessors, dispatchers, and utilities
   - **Est. time:** 2-3 hours for all
   - **Value:** Incremental

### Summary

**Total overlay functions:** 3,558 (86% of codebase)  
**Overlay functions with dynamic calls:** 434 (12% of overlays)  
**Top 30 overlay functions:** All already named ✓  
**Top unnamed:** sub_2BFC3 at rank #31 (30,515 calls)

**Next step:** Analyze sub_263F6 dispatcher table and sub_256A3 DGROUP accessor (est. 1 hour total, very high value).

