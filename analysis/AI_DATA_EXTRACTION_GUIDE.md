# AI Data Extraction Guide

**Date:** November 11, 2026  
**Session:** AI System - Session 4 (Data Extraction)  
**Status:** Data structures documented, extraction approach defined

---

## What We Know

### AI Context Array Location

**Segment:** 0x65A7  
**Offset:** 0x000C  
**Full Address:** 0x65A7:0x000C

**Structure:**
- **Count:** 40 entities (0x28)
- **Stride:** 24 bytes (0x18)
- **Total size:** 960 bytes

**Memory layout:**
```
0x65A7:0x000C  = Context[0]  (24 bytes)
0x65A7:0x0024  = Context[1]  (24 bytes)
0x65A7:0x003C  = Context[2]  (24 bytes)
...
0x65A7:0x03B4  = Context[39] (24 bytes)
```

### Context Structure (24 bytes)

| Offset | Size | Field | Contains |
|--------|------|-------|----------|
| +0 | byte | active | 1=active, 0=inactive |
| +1 | word | entity_id | Entity/slot reference |
| +3 | word | data_table_index | Index for farptr_table_get |
| +5 | word | field_5 | Data param 1 |
| +7 | word | field_7 | Data param 2 |
| +9 | word | field_9 | Data param 3 |
| **+0Bh** | **word** | **behavior_flags** | **AI state from data[+6]** |
| +0Dh | byte | field_D | Unknown |
| +0Eh | byte | counter | Timer/counter |
| +0Fh | byte | field_F | Threshold |
| +10h | word | velocity_x | Movement param |
| +12h | word | velocity_y | Movement param |
| +14h | 4 bytes | unknown | Remaining |

### Data Table Format (ES:DI from farptr_table_get)

| Offset | Size | Field | Purpose |
|--------|------|-------|---------|
| +0 | word | param_1 | Unknown parameter |
| +2 | word | param_2 | Unknown parameter |
| +4 | word | param_3 | Unknown parameter |
| **+6** | **word** | **behavior_flags** | **AI tactical state!** |
| +8+ | ? | ? | More data (unknown size) |

---

## Data Extraction Approaches

### Approach 1: Memory Dump (If Running Game)

**If you have DOSBox or can run the game:**

1. Run Falcon 3.0 in DOSBox with debugger
2. Load a mission with AI aircraft
3. Break execution
4. Dump memory at 0x65A7:0x000C (960 bytes)
5. Parse 40 × 24-byte structures

**Command (DOSBox debugger):**
```
memdump 0x65A7:0x000C 960
```

**Benefits:**
- ✅ See actual runtime values
- ✅ Confirm structure layout
- ✅ Get real behavior flag values
- ✅ See which contexts are active

**Limitations:**
- ⏳ Requires running game
- ⏳ Dynamic data (changes each mission)

### Approach 2: Data File Analysis

**Extract from mission/scenario files:**

1. Locate .DAT or mission files
2. Find entity definition records
3. Parse structure to find behavior flags at +6
4. Map to waypoint actions

**Known file types:**
- .TAC files (tactical scenarios?)
- .CAM files (campaigns?)
- .DAT files (data tables?)

**Benefits:**
- ✅ Static data (always available)
- ✅ Can analyze all missions
- ✅ Shows mission designer intent

**Limitations:**
- ⏳ Need to find files
- ⏳ Unknown file format
- ⏳ May need decompression/decryption

### Approach 3: Code Tracing (Current Approach)

**Trace through code execution:**

1. Find farptr_table_get implementation
2. Understand table structure
3. Locate data table in binary
4. Extract values

**Benefits:**
- ✅ No runtime needed
- ✅ Complete understanding
- ✅ Documents system fully

**Limitations:**
- ⏳ Time-intensive
- ⏳ Complex tracing

---

## Behavior Flag Expected Values

Based on waypoint actions from manual:

| Action | Expected Flags | Bits | Tactical State |
|--------|---------------|------|----------------|
| **CAP** (Combat Air Patrol) | 0x0004 | 0x04 | Cruise/patrol |
| **CAS** (Close Air Support) | 0x0001 | 0x01 | Ground attack |
| **INTERCEPT** | 0x0008 | 0x08 | Combat mode |
| **S AND D** (Search & Destroy) | 0x0009 | 0x08+0x01 | Combat + Ground |
| **LOITER** | 0x0004 | 0x04 | Cruise/hold |
| **Landing** | 0x0002 | 0x02 | Approach |
| **STRIKE** | 0x0001 | 0x01 | Ground attack |
| **SWEEP** | 0x0008 | 0x08 | Combat patrol |

**Special values:**
- 0x0000 = Inactive/idle
- 0x0010 = Special mission mode
- 0x????  = Combined states

---

## farptr_table_get Analysis

### Function Signature

```c
// Input: AX = table index
// Output: ES:DI = pointer to data entry
farptr_table_get(uint16_t index)
```

### Usage Pattern

```asm
; Load data table index
0x498F4: mov    ax, [si+3]          ; index from context[+3]
0x498F7: call   farptr_table_get    ; Returns ES:DI
0x498FC: mov    ax, es:[di]         ; Access data[+0]
...
0x49910: mov    ax, es:[di+6]       ; Access data[+6] = behavior flags
```

### Expected Implementation

Since it's Level 0 (no callees), likely simple:

```asm
farptr_table_get:
    ; AX = index
    mov    bx, [table_base]     ; Load base address
    shl    ax, 3                ; index * 8 (assuming 8-byte entries)
    add    bx, ax               ; base + offset
    mov    di, bx               ; Return in DI
    mov    ax, [table_segment]  ; Load segment
    mov    es, ax               ; Return in ES
    ret
```

**Or simpler (if table in fixed location):**
```asm
farptr_table_get:
    mov    di, ax               ; DI = index
    shl    di, 3                ; DI = index * 8
    add    di, [offset]         ; Add base offset
    mov    ax, [segment]        ; Load segment
    mov    es, ax
    ret
```

---

## Practical Next Steps

### Immediate (15 min): Find Table References

**Search for:**
1. Data segment references (0x65A7)
2. Table base addresses in data segment
3. farptr_table_get calls with constant indices

**Commands:**
```bash
# Search for segment 0x65A7 usage
grep -r "65A7h" analysis/ida_falconcd/*.txt

# Search for table_get calls with immediate values
grep -r "mov.*ax.*[0-9].*call.*farptr_table_get" analysis/ida_falconcd/*.txt
```

### Short-term (30 min): Document farptr_table_get

**Goals:**
1. Find function address
2. Understand implementation
3. Locate data table base
4. Calculate entry size

### Medium-term (1 hour): Extract Sample Data

**Goals:**
1. Find one or two actual data entries
2. Confirm behavior flag values
3. Validate structure understanding
4. Map to mission entities

---

## Alternative: Theoretical Analysis

**If data extraction proves difficult**, we can:

1. ✅ **Document architecture** (DONE - 70%)
2. ✅ **Understand code flow** (DONE)
3. ✅ **Map structure** (DONE)
4. ⏳ **Hypothesize values** (based on manual)
5. ⏳ **Create modding guide** (using known structure)

**Result:** Complete documentation even without actual data values

**Value:** 
- Mission designers can use structure
- Modders know what to change
- Future analysts have roadmap

---

## Data Extraction Value Assessment

### High Value (Worth pursuing):
- ✅ Confirms all hypotheses
- ✅ Shows real behavior flag values
- ✅ Identifies enemy aircraft in data
- ✅ Complete picture of mission data

### Medium Value (Nice to have):
- ⏳ Additional validation
- ⏳ Example values for documentation
- ⏳ Modding reference

### Low Value (Not essential):
- ⏳ We already understand system (70%)
- ⏳ Code flow documented
- ⏳ Architecture clear

---

## Recommendation

**Option A: Quick Win (30 min)**
- Search for constant data table indices
- Find a few sample entries
- Confirm behavior flag structure
- Move to 75% completion

**Option B: Deep Dive (2 hours)**
- Fully reverse farptr_table_get
- Extract all data tables
- Parse mission files
- Reach 85% completion

**Option C: Skip to Documentation (1 hour)**
- Accept 70% as "complete"
- Focus on synthesis documents
- Create modding guides
- Move to next system

---

## Current Recommendation: Option A (Quick Win)

**Rationale:**
1. ✅ 30 minutes for significant validation
2. ✅ Confirms our understanding
3. ✅ Provides concrete examples
4. ✅ Pushes to 75% without huge time investment

**After Option A:**
- Can decide: continue to B, move to C, or switch systems
- Have solid examples to reference
- Validated architecture

---

## Summary

**Data location:** 0x65A7:0x000C (40 contexts × 24 bytes)  
**Data format:** Known (8+ byte records with behavior flags at +6)  
**Extraction approaches:** 3 options (memory, files, code)  
**Recommended:** Quick win - find sample entries (30 min)  
**Value:** Validation + examples + 5% progress boost

**Current completion:** 70%  
**After quick win:** 75%  
**After full extraction:** 85%

---

*Document created: November 11, 2026*  
*Status: Ready for data extraction*  
*Next: Search for sample data entries*


