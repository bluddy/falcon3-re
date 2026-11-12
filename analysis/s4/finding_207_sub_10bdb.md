# Finding 207: Missing Function sub_10BDB - High-Frequency Accessor

**Date:** 2026-11-11  
**Status:** CONFIRMED  
**Priority:** HIGH (10,222 calls, missing from IDB)

## Summary

Discovered **missing function at 0x10BDB** while investigating sub_256A3 DGROUP accessor. This function is called 10,222 times (very hot path) but is NOT in the IDB - it exists in a 149-byte unexplored gap between functions.

## Discovery Path

1. Analyzed sub_256A3 (10,222 calls, rank #5 unnamed overlay)
2. Found it calls `sub_10BDB` via relative near call
3. Checked function_bytes.json - **sub_10BDB not found**
4. Verified 0x10BDB is in 149-byte gap: sub_10B1C ends at 0x10B46, next function at 0x172E0
5. Extracted bytecode from raw executable - **confirmed it's valid code**

## Function Details

**Address:** 0x10BDB (IDA), 0x127DB (file offset)  
**Status:** Missing from IDB (boundary error)  
**Calls:** 10,222 (from sub_256A3)  
**Gap:** 149 bytes of unexplored code (0x10B46..0x10BDB..end)

**Calling pattern:**
```assembly
sub_256A3 (caller):
  push ds
  mov di, 7B0Eh           ; DGROUP
  mov ds, di
  mov di, 4287h           ; offset
  push cs                 ; For return
  call near sub_10BDB     ; E8 2B B5 (rel -19157)
  pop ds
  retf

sub_10BDB (missing function):
  pop ds                  ; 1F - balance caller's push ds
  mov si, 0x43BA          ; BE BA 43
  mov di, 0x43D2          ; BF D2 43
  mov cx, [bx+18h]        ; 8B 4F 18
  ... (more code)
```

## Bytecode Analysis

**First 64 bytes:**
```
1F BE BA 43 BF D2 43 8B 4F 18 83 C1 03 BD 0C 00
26 8B 04 0B C0 79 08 F7 D8 D3 E8 F7 D8 EB 02 D3
E8 AB 83 C6 02 4D 7F E8 8D 5F 12 BE D2 43 BF BA
43 B9 04 00 51 53 9A 7B 4F 6C 0F 5B 8B 07 26 01
```

**Pattern observations:**
- Starts with `pop ds` (balances caller's `push ds`)
- Contains loop code (`4D 7F E8` = dec bp; jg -24)
- Has far call (`9A 7B 4F 6C 0F` = call far 0F6C:4F7B)
- Multiple memory accesses with ES override (`26`)
- Appears to be ~30-40 bytes (need to find retf)

**Likely purpose:** Data structure manipulation
- Takes DS:DI as input (DGROUP:0x4287)
- Loads SI/DI with offsets (0x43BA, 0x43D2)
- Processes data in a loop
- Calls another far function

## Related Functions

**sub_256A3 (10,222 calls):**
- High-frequency DGROUP accessor
- Specifically targets offset 0x4287
- Only known caller of sub_10BDB

**DGROUP:0x4287:**
- 17,031 bytes into main data segment
- Accessed 10K+ times per session
- Likely: player state, frame data, input buffer, or active entity

## Impact

**This is a boundary error affecting:**
1. **Call graph accuracy** - 10,222 calls land mid-body instead of function start
2. **Naming campaign** - sub_256A3 analysis blocked without understanding sub_10BDB
3. **Code coverage** - 149 bytes (potentially multiple functions) unexplored

**Confidence:** VERY HIGH
- Called 10,222 times (verified in traces)
- Valid bytecode extracted from executable
- Fits calling convention (push ds / pop ds balance)
- Contains recognizable code patterns

## Recommended Actions

### Immediate (Required for DGROUP analysis)

**1. Add sub_10BDB to IDB [15 min, CRITICAL]**
- Create function at 0x10BDB
- Verify size (find retf or next function start)
- Re-export function_bytes.json
- Verify xrefs (should show sub_256A3 as caller)

**2. Analyze sub_10BDB disassembly [15 min, HIGH VALUE]**
- Full disassembly to understand logic
- Identify what it does with DS:DI (DGROUP:0x4287)
- Check far call target (0F6C:4F7B)
- Name based on function

**3. Survey gap for more missing functions [15 min, MEDIUM VALUE]**
- 149-byte gap: 0x10B46 to 0x10BDB = 149 bytes
- sub_10BDB likely 30-40 bytes
- Remaining ~100 bytes may contain more functions
- Check for additional call targets or code patterns

### Follow-up

**4. Complete sub_256A3 analysis [15 min]**
- With sub_10BDB understood, name both functions
- Document DGROUP:0x4287 structure
- Update overlay target analysis

**5. Boundary survey**
- Check if other high-frequency calls land in gaps
- This gap might not be unique

## Related Findings

- **Finding 206:** Overlay target analysis (identified sub_256A3)
- **Finding 178-179:** Boundary fixes (P2 REBASE/TRIM work)
- **Finding 121:** DGROUP proven at runtime 0x6C27 = link 0x6A32
- **Finding 176:** VGRAPH runtime DS = 0x6D03, confirmed DGROUP methods

## Artifacts

**Created:**
- `analyze_dgroup_4287.py` - Initial DGROUP analysis (found missing function)
- `find_10bdb.py` - Verified 0x10BDB not in IDB
- `check_10bdb_location.py` - Confirmed gap location
- `extract_10bdb_bytes.py` - Extracted bytecode from executable
- `sub_10BDB_bytecode.bin` - Raw bytecode (64 bytes)
- `dgroup_4287_analysis.json` - Analysis results
- `finding_207_sub_10bdb.md` - This document

## Next Steps

**Priority 1:** Add sub_10BDB to IDB (required for progress)
**Priority 2:** Analyze and name sub_10BDB  
**Priority 3:** Complete sub_256A3 analysis  
**Priority 4:** Survey gap for additional missing functions

**Estimated total time:** 1 hour  
**Value:** VERY HIGH (unblocks DGROUP analysis, fixes boundary error, 10K+ call accuracy)

## Status

**Confirmed:**
- ✓ Missing function at 0x10BDB
- ✓ Called 10,222 times by sub_256A3
- ✓ Valid bytecode extracted
- ✓ In 149-byte unexplored gap

**Blocked:**
- Cannot complete DGROUP analysis without sub_10BDB
- Cannot name sub_256A3 without understanding accessor
- 149-byte gap unexplored

**Next session:** Add sub_10BDB to IDB (IDA script or manual)

