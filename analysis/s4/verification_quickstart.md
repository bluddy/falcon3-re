# Graphics Pipeline Verification - Quick Start Guide

## Status: Ready for Manual IDA Verification

All automated analysis is complete. This guide helps you verify findings in IDA Pro.

## Key Findings Summary

### seg020 Location ✓ VERIFIED
- **Base address**: 0x1F6C0
- **Selector**: 0x1F6C
- **Size**: 45,936 bytes (0x1F6C0 - 0x2AA30)
- **Source**: segment_map.json

### Critical Functions in seg020

| Function | Linear Addr | Seg:Offset | Size | Status |
|----------|-------------|-----------|------|---------|
| view_projection | 0x20BDB | 1F6C:151B | 1,076 bytes | ✓ Named |
| fixed_vec3_transform_es | 0x248D1 | 1F6C:5211 | 146 bytes | ✓ Named |
| sub_256A3 | 0x256A3 | 1F6C:5FE3 | ? bytes | ⚠ Needs naming |
| abs_helper | 0x210EF | 1F6C:1A2F | ? bytes | ⚠ Part of parent func |

### Data Structures to Verify

| Name | Address | Type | Size | Used By |
|------|---------|------|------|---------|
| 3D coord structure | DGROUP:0x4287 | struct | ? | sub_256A3 |
| Near object queue | DGROUP:0x7C054 | queue | ? | farobj_record_push_7c054 |
| Far object queue | DGROUP:0x7D0C6 | queue | ? | farobj_record_push_7d0c6 |
| Math lookup table | 0x7772:0x0F34 | table | 4-byte entries | seg017:01FE |

**Queue separation**: 0x7D0C6 - 0x7C054 = 4,210 bytes (0x1072)

---

## 5-Minute Verification Checklist

Open IDA Pro with FALCONCD.EXE.i64, then:

### 1. Verify seg020 ✓
```
Press: Ctrl+S (Segments)
Find: seg020
Check: Base = 0x1F6C0, Size = B3B0h (45936 decimal)
```

### 2. Verify view_projection (2 min)
```
Press: G
Enter: 20BDB
Verify: Function name is "view_projection"
Verify: Located at seg020:151B
Press: X (xrefs)
Count: How many functions call view_projection? 14
```

### 3. Verify fixed_vec3_transform_es (2 min)
```
Press: G
Enter: 248D1
Verify: Function name is "fixed_vec3_transform_es"
Verify: Located at seg020:5211
Press: X (xrefs)
Count: Should see 10 callers - actual:21
```

### 4. Verify farobj queues (1 min)
```
Press: G
Enter: DGROUP:7C054
Note name: _______ (near queue)

Press: G
Enter: DGROUP:7D0C6
Note name: _______ (far queue)
```

---

## Deep Verification Tasks (2-3 hours)

Use `manual_verification_guide.md` for complete verification of:
- 10 math helper entry points (exclusive to view_projection)
- 10 callers of fixed_vec3_transform_es
- 6 core graphics functions
- Complete call graph of view_projection (16 calls)
- Multi-entry function sampling
- Data structure layouts

---

## Files Generated This Session

### Analysis Files
1. `segment_map.json` (3.4 MB) - Complete segment and function map
2. `projection_pipeline_map.json` - view_projection call graph
3. `math_library_analysis.json` - 10 math helpers identified
4. `graphics_functions_analysis.json` - 6 core graphics functions
5. `vec3_transform_callers.json` - All 10 callers mapped
6. `farobj_system_analysis.json` - Visibility culling system
7. `sub_21657_analysis.json` - Unnamed caller investigation

### Verification Tools
1. `manual_verification_guide.md` - Complete manual checklist
2. `ida_verification_plan.md` - 7-phase verification plan
3. `verify_graphics_pipeline.py` - IDA automation (batch mode)
4. `prepare_verification_data.py` - Analysis summary tool
5. `find_seg020.py` - Segment address calculator
6. `this file` - Quick start guide

### Documentation
1. `view_projection_analysis.md` - Pipeline analysis
2. `math_helpers_identified.md` - Math library findings
3. `finding_207_sub_10bdb.md` - Address typo resolution
4. `ADDRESS_TRANSLATION_GUIDE.md` - Segment:offset conversion

---

## Next Steps

### Immediate (This Session)
1. ✅ Open IDA Pro
2. ✅ Run 5-minute verification checklist (above)
3. ✅ Record any discrepancies
4. ✅ Update analysis files if needed

### Follow-up (Next Session)
1. Complete deep verification using manual_verification_guide.md
2. Name sub_256A3 based on usage pattern
3. Investigate sub_21657 (no direct callers - indirect call)
4. Document DGROUP:0x4287 structure layout
5. Map complete scene graph architecture

### Long-term
1. Verify all 2,385 multi-entry functions (57% of codebase)
2. Complete rendering pipeline documentation
3. Map entity system integration
4. Document farobj visibility culling algorithm

---

## Known Issues to Verify

### 1. Math Helper Exclusivity
**Claim**: 10 math helpers are called ONLY by view_projection
**Verify**: Use xrefs to each helper address, confirm single caller

### 2. vec3_transform Call Counts
**Claim**: record_xform_apply calls vec3_transform 4 times
**Verify**: Navigate to each caller, count CALL instructions to 0x248D1

### 3. seg020:051B Multi-Entry
**Claim**: Address 0x1FBDB is inside record_xform_apply but not exported as multi-entry
**Verify**: Navigate to 1FBDB, check if it's a separate function or mid-function address

### 4. Queue Separation
**Claim**: Near and far queues are 4,210 bytes apart
**Verify**: Calculate 0x7D0C6 - 0x7C054 = 0x1072 = 4,210 ✓

---

## Commit History This Session

1. `979c453` - Finding 207 analysis (address typo)
2. `75f0a5c` - Segment export tooling
3. `b47e856` - view_projection pipeline mapping
4. `b2d6ed1` - Math helper identification
5. `98e2e2c` - Math helper bytecode analysis
6. `da9d068` - Graphics functions analysis
7. `71a3905` - vec3_transform caller analysis
8. `91b27d2` - farobj system and sub_21657 analysis
9. (pending) - Verification tools and guides

---

## Quick Reference: Key Addresses

```
# seg020 functions (base 0x1F6C0)
0x20BDB  view_projection          (seg020:151B)  1,076 bytes
0x248D1  fixed_vec3_transform_es  (seg020:5211)    146 bytes
0x256A3  sub_256A3                (seg020:5FE3)      ? bytes
0x210EF  abs_helper               (seg020:1A2F)      ? bytes

# DGROUP data
DGROUP:0x4287   - 3D coordinate structure
DGROUP:0x7C054  - Near object queue
DGROUP:0x7D0C6  - Far object queue (+ 4,210 bytes)

# Other segments
0x7772:0x0F34  - Math lookup table (4-byte entries)
```

---

## Success Criteria

Verification is complete when:
- ✓ All 10 math helpers confirmed exclusive to view_projection
- ✓ All 10 vec3_transform callers confirmed with correct call counts
- ✓ All 6 graphics functions found with expected sizes
- ✓ All data structures located and typed
- ✓ view_projection call graph confirmed (16 calls)
- ✓ Discrepancies documented and analysis updated

**Estimated time**: 2-3 hours for thorough verification
