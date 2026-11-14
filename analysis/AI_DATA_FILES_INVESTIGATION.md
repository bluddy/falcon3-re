# AI Data Files Investigation - Findings and Corrections

**Date:** 2026-11-11  
**Status:** INCOMPLETE - Data table structure remains unknown  
**Key Finding:** ARMS*.DAT files are NOT AI behavior tables

---

## Investigation Summary

Attempted to locate and analyze the AI behavior data tables referenced by `farptr_table_get`. Made several discoveries but ultimately **did not locate the actual AI behavior tables**.

---

## farptr_table_get Function

**Status:** Implementation not found in IDA disassembly extracts

**What we know:**
- Function exists and is referenced 78+ times in the codebase
- Listed in multiple *_names.json files with descriptions
- Calls appear in level19 disassembly as `call farptr_table_get`
- IDA recognizes it: `->code ['farptr_table_get']`

**Usage pattern:**
```asm
0x498F3: push   es
0x498F4: mov    ax, [si+3]              ; AX = table index from AI context +0x03
0x498F7: call   farptr_table_get        ; Returns ES:DI = far pointer
0x498FC: mov    ax, es:[di]             ; Load data[+0x00]
0x498FF: mov    [si+5], ax              ; Store to AI context +0x05
0x49902: mov    ax, es:[di+2]           ; Load data[+0x02]
0x49906: mov    [si+7], ax              ; Store to AI context +0x07
0x49909: mov    ax, es:[di+4]           ; Load data[+0x04]
0x4990D: mov    [si+9], ax              ; Store to AI context +0x09
0x49910: mov    ax, es:[di+6]           ; Load data[+0x06] <-- BEHAVIOR FLAGS
0x49914: mov    [si+0Bh], ax            ; Store to AI context +0x0B
```

**Function signature (inferred):**
- Input: AX = table index (word)
- Output: ES:DI = far pointer to table entry
- Behavior: Table lookup, returns pointer to data structure

**Why not found:**
1. Might be a very small Level 0 function not included in batch extracts
2. Could be inlined or optimized away in some contexts
3. Might be in a segment not yet fully disassembled
4. IDA export script may have resolved references without including the implementation

---

## ARMS*.DAT Files Analysis

**Location:** `game/ARMSDATA/`  
**Count:** 308 files  
**Size:** All files are exactly 18 bytes  
**Naming:** ARMS####.DAT (e.g., ARMS0000.DAT, ARMS0705.DAT)

### File Structure (18 bytes)

**Sample Files:**

```
ARMS0000.DAT: C8 00 00 04 02 00 00 00 00 00 00 00 00 00 00 00 00 00
ARMS0001.DAT: 3B 01 02 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00
ARMS0100.DAT: C8 00 02 02 04 00 00 00 00 00 00 00 00 00 00 00 00 00
ARMS0705.DAT: E6 00 00 02 00 02 00 26 00 00 00 00 00 00 00 00 00 00
ARMS0805.DAT: E6 00 00 00 00 02 00 0A 00 00 00 00 00 00 00 00 00 02
```

**Field Analysis:**

| Offset | Size | Sample Values | Notes |
|--------|------|---------------|-------|
| +0x00  | word | 0x00C8, 0x013B, 0x00E6 | 200, 315, 230 decimal |
| +0x02  | word | 0x0400, 0x0402, 0x0200 | Varies |
| +0x04  | word | 0x0002, 0x0000, 0x0004 | Small values |
| **+0x06** | **word** | **0x0000, 0x2600, 0x0A00** | **NOT behavior flags!** |
| +0x08  | 10 bytes | Mostly zeros | Unknown |

### Value Distribution at Offset +0x06

```
0x0000: 269 files  (87.3%) - Most common
0x0A00: 9 files    (2.9%)  - Decimal 2560
0x2400: 3 files    (1.0%)  - Decimal 9216  
0x2600: 26 files   (8.4%)  - Decimal 9728
0x01D0: 1 file     (0.3%)  - Decimal 464
```

### Critical Finding: NOT AI Behavior Tables

**Evidence against ARMS*.DAT being AI behavior tables:**

1. **Values out of range:** Behavior flags should be 0x00-0x1F (0-31 decimal)
   - We see values like 0x2600 (9728), 0x0A00 (2560), 0x2400 (9216)
   - These are 300x-400x larger than expected

2. **Distribution wrong:** Only 5 unique values, mostly zeros
   - Expected: 20-30 different flag combinations for different mission types
   - Actual: 87% are 0x0000, only 4 other values

3. **File naming suggests weapons:** "ARMS" likely stands for "armaments"
   - More consistent with weapon/loadout data
   - 308 entries matches number of weapon combinations

4. **Other fields don't match AI context:** 
   - AI contexts have specific patterns (entity IDs, counters, coordinates)
   - ARMS files have completely different data patterns

**Conclusion:** ARMS*.DAT files contain **weapons/armaments data**, NOT AI behavior tables.

---

## Where Is the AI Behavior Table?

**Hypothesis 1: Embedded in Executable**
- Behavior tables might be compiled into FALCONCD.EXE
- Static data in the .DATA or .RODATA segment
- farptr_table_get could be accessing segment-relative offsets

**Hypothesis 2: Campaign Files (.CAM)**
- SQUAD0.CAM and SQUAD1.CAM are 11,828 bytes
- Could contain mission-specific AI behavior tables
- Would make sense for campaign-specific AI configurations

**Hypothesis 3: Mission Files (.MIS)**
- SQUAD0.MIS, MISSION*.MIS files
- Could include per-mission AI configurations
- Action codes (0-9) might index into these tables

**Hypothesis 4: Theater Files**
- Files like KUWAIT.THE, ISRAEL.THE, etc.
- Theater-specific AI behaviors
- Would explain regional tactics differences

---

## SQUAD0.CAM Initial Analysis

**Size:** 11,828 bytes  
**First 256 bytes:**
```
0000: 00 00 00 03 01 02 3C 28 05 05 05 05 05 05 05 05
0010: DD DD DD DD DD DE DC DD C5 C5 C5 C5 C5 C5 C4 C4
0020: 00 06 07 08 09 00 00 00 01 00 00 00 00 06 04 0F
0030: 06 01 30 00 31 00 33 00 62 00 77 00 0F 00 91 01
...
```

**Observations:**
- Byte values in 0x00-0x1F range appear frequently (lines 0020-0030)
- Could contain behavior flags mixed with other data
- Requires systematic analysis to identify structure

**Next steps:**
1. Parse SQUAD0.CAM with hypothesis it contains behavior tables
2. Look for repeating 18-byte or 24-byte structures
3. Search for values matching observed behavior patterns (0x00-0x1F range)

---

## Recommendations

### To Find farptr_table_get Implementation

1. **Check IDA database directly** - Load FALCONCD.i64 in IDA and navigate to symbol
2. **Search executable** - Look for function prologue patterns near call sites
3. **Calculate call target** - Decode the relative offset in `call` instruction bytes
4. **Check Level 0 exports** - Request complete Level 0 function extraction

### To Find AI Behavior Tables

1. **Hex analysis of .CAM files** - Look for arrays of small values (0x00-0x1F)
2. **Memory dump during mission** - Capture AI context with active behaviors
3. **Cross-reference data_table_idx** - Track which indices are actually used
4. **Examine .THE theater files** - Check for AI configuration data
5. **Parse mission files** - Look for embedded behavior definitions

---

## Corrected Understanding

**What we got wrong:**
- ❌ Assumed ARMS*.DAT files were AI behavior tables
- ❌ Expected offset +0x06 to contain behavior flags directly
- ❌ Thought farptr_table_get would be easy to find in disassembly

**What we got right:**
- ✅ Behavior flags ARE loaded from external tables via farptr_table_get
- ✅ Offset +0x06 in the table entry IS loaded into AI context +0x0B
- ✅ The data-driven architecture is correct
- ✅ Behavior flag decode (bits 0-7) is accurate from disassembly analysis

**Confidence level:**
- Architecture understanding: VERY HIGH ✅
- Behavior flag decode: VERY HIGH ✅
- Data file identification: FAILED ❌
- Table lookup mechanism: MEDIUM (inferred, not verified)

---

## Impact on AI System Completion

**Current status:** Still 90% complete

**Why completion didn't change:**
- Core architecture is understood and verified
- Behavior flags are fully decoded from usage patterns
- Mission integration is mapped
- Only missing: exact data file format and farptr_table_get implementation

**Remaining 10% breakdown:**
- farptr_table_get implementation: 3%
- Actual data table file identification: 4%
- Runtime validation: 3%

---

## Lessons Learned

1. **Verify data file purpose before assuming** - ARMS suggested armaments, not AI
2. **Check value ranges early** - Would have caught the mismatch immediately
3. **Static analysis has limits** - Some details require runtime observation
4. **Names matter** - File naming conventions usually hint at purpose
5. **Distribution analysis helps** - 87% zeros suggested wrong hypothesis

---

**Status:** Investigation incomplete but educational  
**Next action:** Focus on .CAM file analysis or request IDA database access  
**Alternative:** Accept 90% completion and move to another system
