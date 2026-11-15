# IDA Analysis - Next Steps

## Status

We've analyzed 615 functions across 8 depth levels starting from font loaders and found 211 new functions that need to be synced to IDA. We're systematically expanding to find the RLE decompressor.

## What We Know

1. **Graphics Format**: SYSMENU.DAT contains 89 compressed graphics records
   - Format: magic(0x0400), width(2B), height(2B), RLE_compressed_data
   - Compression ratios: 0.34% to 2% (very efficient)
   - Example: 128×384 pixels (49,152 bytes) → 175 bytes compressed

2. **Loading Path**: 
   - Menu system loads graphics through `op_dispatch` with operation 0xA
   - Dispatch table at cs:0x229A0, entry [10] points to decompressor
   - Multiple trampoline layers obscure actual implementation

3. **Current Analysis**:
   - 615 functions analyzed in round 1
   - 211 new functions discovered (appended to functions.yaml)
   - 21 potential decompressor candidates (none match ideal RLE pattern yet)

## Scripts Ready to Run in IDA

### 1. Sync New Functions (PRIORITY)

**Script**: `sync_new_functions.py`

**What it does**: Applies 211 new function names to IDA database

**How to run**:
```
1. Open Falcon CD IDA database
2. File → Script File → sync_new_functions.py
3. Check output: should show ~211 functions renamed
```

**Input**: `new_functions_expansion.yaml` (already created)
**Output**: `sync_new_functions_result.txt`

---

### 2. Expansion Round 2

**Script**: `expand_analysis_round2.py`

**What it does**: 
- Starts from top 20 high-scoring functions from round 1
- Adds dispatch-related functions as seeds
- Expands to depth 8
- Looks for more decompressor candidates

**Seeds**:
- 0x0012DF6A: overlay_handler_large_1 (score 20)
- 0x00015AFD: state_cursor_advance_11c94 (score 16)
- 0x0002AC4C: overlay_segment_load (score 14)
- 0x001820B0: r53_sbi_stream_dispatch (score 13)
- Plus 9 more high-scoring functions
- Plus dispatch system functions

**How to run**:
```
1. File → Script File → expand_analysis_round2.py
2. Wait for completion (may take 5-10 minutes)
3. Review expansion_round2_results.json
```

**Output**: `expansion_round2_results.json`

---

### 3. RLE Pattern Search

**Script**: `find_rle_patterns.py`

**What it does**:
- Scans ALL functions for RLE-specific instruction patterns
- Looks for REP STOSB/STOSW (smoking gun for RLE)
- Looks for LODSB/LODSW (reading compressed data)
- Looks for SI/DI buffer pointer usage
- Scores functions based on pattern matches

**High-value patterns**:
- REP STOSB: +20 points (repeat byte fill)
- REP STOSW: +15 points (repeat word fill)
- LODSB: +8 points (load compressed byte)
- SI+DI together: +10 points (input/output buffers)

**How to run**:
```
1. File → Script File → find_rle_patterns.py
2. Wait for completion (scans entire database)
3. Review rle_pattern_results.json
```

**Output**: `rle_pattern_results.json`

---

---

### 4. Trace Operation 0xA Directly

**Script**: `trace_operation_0xA.py`

**What it does**:
- Directly reads the dispatch table at cs:0x229A0
- Extracts entry [10] (operation 0xA) pointer
- Follows the pointer through all trampolines (up to 8 levels deep)
- Shows disassembly of each function in the chain
- Tries multiple segment base calculations

**How to run**:
```
1. File → Script File → trace_operation_0xA.py
2. Review console output for trace path
3. Check operation_0xA_trace.json for full details
```

**Output**: `operation_0xA_trace.json`

---

## Recommended Execution Order

1. **sync_new_functions.py** - Get IDA up to date with 211 new names
2. **trace_operation_0xA.py** - Follow the dispatch to find actual decompressor
3. **find_rle_patterns.py** - Pattern-based search across all functions
4. **expand_analysis_round2.py** - Continue systematic expansion if needed

## What to Look For

### In `rle_pattern_results.json`:
- Functions with REP STOSB/STOSW (this is THE pattern for RLE output)
- Functions with LODSB + STOSB combination
- Functions with both SI and DI registers used (input + output buffers)
- Functions 100-500 bytes in size
- Functions with count-based loops

### In `expansion_round2_results.json`:
- High-scoring functions (score >= 15)
- Functions at depth 1-3 from overlay_handler or dispatch functions
- Functions with names suggesting data/file handling

## Expected Decompressor Characteristics

Based on typical RLE decompressors in DOS games:

1. **Size**: 100-500 bytes
2. **Key instructions**:
   - REP STOSB or REP STOSW (for run-length output)
   - LODSB or MOV AL, [SI] (reading compressed data)
   - Test/AND for checking flags
   - Loops with CX register
3. **Registers**:
   - SI: source buffer (compressed data)
   - DI: destination buffer (uncompressed output)
   - CX: count register
4. **Few external calls**: Should be mostly self-contained

## If Still Not Found

If the pattern search doesn't find it, next steps:

1. **Manual inspection**: 
   - Review top 10 candidates from both searches
   - Disassemble and read the code
   - Look for dispatcher targets we haven't resolved

2. **Overlay segment search**:
   - RLE might be in an overlay segment
   - Use overlay_handler_large_1 as starting point

3. **Cross-reference from data**:
   - Find xrefs to the 0x0400 magic number
   - Work backward from file loading code

## Files Created This Session

```
analysis/
  ├── expansion_analysis_results.json      (615 functions, round 1)
  ├── new_functions_expansion.yaml         (211 new functions)
  └── ida_scripts/
      ├── sync_new_functions.py            (sync 211 names)
      ├── expand_analysis_round2.py        (continue expansion)
      └── find_rle_patterns.py             (pattern-based search)

registry/
  └── functions.yaml                       (3,019 functions total)
```

## Current Registry Stats

- Total functions: 3,019
- Categories: 28
- Coverage: ~60% of code base named
- This session added: 211 functions

## Notes

- All scripts use `idc.qexit(0)` to quit IDA when done
- Remove that line if you want IDA to stay open
- Scripts save JSON results to `analysis/ida_falconcd/` directory
- Check console output for progress and errors
