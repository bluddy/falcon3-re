# Automated Verification Results

**Date**: Automated via IDA Python API  
**Script**: auto_verify_all.py  
**Status**: ✅ Complete with findings

---

## Summary

✓ **Passed**: 23 checks  
⚠ **Warnings**: 12 discrepancies found  
✗ **Failed**: 0 critical failures

---

## Phase 1: Address Verification ✓ ALL PASSED

### Confirmed
- ✅ seg020 base = **0x1F6C0** (correct)
- ✅ view_projection at **0x20BDB** (correct)
- ✅ fixed_vec3_transform_es at **0x248D1** (correct)

**Result**: Core addresses match expectations perfectly.

---

## Phase 2: Math Helper Verification ⚠ MAJOR FINDINGS

### Issue: Math Helpers Are NOT Exclusive to view_projection

Our initial analysis claimed these 10 helpers were called ONLY by view_projection. **This is INCORRECT.**

**Actual findings**:

| Entry Point | Parent Function | XRefs | Actual Callers |
|-------------|----------------|-------|----------------|
| seg015:0C65 | stream_command_interpret | 0 | *(none - internal jumps)* |
| seg015:0C7A | stream_command_interpret | 1 | stream_command_interpret |
| seg015:0CDB | stream_command_interpret | 1 | stream_command_interpret |
| seg015:0CF0 | stream_command_interpret | 0 | *(none - internal jumps)* |
| seg015:0D51 | stream_command_interpret | 0 | *(none - internal jumps)* |
| seg015:0D66 | stream_command_interpret | 1 | stream_command_interpret |
| seg017:01FE | group_children_release | 0 | *(none - internal jumps)* |
| seg017:021C | group_children_release | 0 | *(none - internal jumps)* |
| seg017:01E3 | channel_list_register_batch | 0 | *(none - internal jumps)* |
| seg020:1A2F | vec_delta_norm_1f6ee | 1 | vec_delta_norm_1f6ee |

### Analysis

**These are mid-function entry points within larger parent functions**:
- seg015 entries: Part of `stream_command_interpret` (NOT math helpers!)
- seg017 entries: Parts of `group_children_release` and `channel_list_register_batch`
- seg020:1A2F: Part of `vec_delta_norm_1f6ee` (vector delta normalization)

**The xref count of 0 indicates**: These addresses have no external CALL instructions to them. They are likely:
1. Internal jump targets (JMP, JZ, JNZ, etc.)
2. Fall-through code paths
3. Loop entry points

**Conclusion**: Our original analysis was based on bytecode patterns, NOT actual call graph analysis. The "10 exclusive math helpers" finding is **INVALIDATED**.

### Corrected Understanding

view_projection likely calls:
- Standard functions (with proper CALL instructions)
- Uses internal jumps within its own body
- The extracted bytecode at these addresses is coincidental overlap or misidentified pattern

**Action Required**: Re-analyze view_projection's actual CALL instructions to find real helpers.

---

## Phase 3: Graphics Functions ✓ SIZES CORRECT, ⚠ CALLER COUNTS WRONG

### Size Verification (ALL CORRECT ✓)

| Function | Expected | Actual | Status |
|----------|----------|--------|--------|
| fixed_vec3_transform_es | 146 bytes | 146 bytes | ✅ |
| vec2_normalize_seq | 17 bytes | 17 bytes | ✅ |
| farobj_record_step | 393 bytes | 393 bytes | ✅ |
| farobj_record_push_7c054 | 72 bytes | 72 bytes | ✅ |
| farobj_record_lookup_step | 72 bytes | 72 bytes | ✅ |
| farobj_record_push_7d0c6 | 70 bytes | 70 bytes | ✅ |

### Caller Count Discrepancies ⚠

**fixed_vec3_transform_es**:
- Expected: 10 callers
- Actual: **21 callers**
- Finding: We missed 11 additional callers!

**vec2_normalize_seq**:
- Expected: 2 callers
- Actual: **3 callers**
- Finding: We missed 1 additional caller

### Analysis

Our caller analysis was incomplete. The functions are more widely used than documented.

**Action Required**: Re-run caller analysis to find all 21 callers of fixed_vec3_transform_es.

---

## Phase 4: vec3_transform Callers ✅ ALL VERIFIED

### Perfect Match (10/10)

All 10 identified callers have CORRECT call counts:

| Caller | Expected | Actual | Status |
|--------|----------|--------|--------|
| view_projection | 1 | 1 | ✅ |
| record_xform_apply | 4 | 4 | ✅ |
| object_quad_proj_draw | 4 | 4 | ✅ |
| view_proj_setup_1f73d | 3 | 3 | ✅ |
| view_proj_setup_1f73d_rot | 3 | 3 | ✅ |
| view_basis_build_3850 | 2 | 2 | ✅ |
| object_proj_draw_dispatch | 1 | 1 | ✅ |
| view_scroll_rotate_apply | 1 | 1 | ✅ |
| stub_to_248d1 | 1 | 1 | ✅ |
| sub_21657 | 1 | 1 | ✅ |

**Total calls from these 10**: 21 calls

**Conclusion**: We found 10 callers, but there are actually 21 total calls. Since Phase 3 shows 21 callers total, this means **we found all the callers but miscounted the total**.

**Resolution**: Phase 3 counts xrefs to function START (all callers). Our analysis was correct for the 10 callers we documented. The discrepancy in "expected 10 vs actual 21" in Phase 3 is now resolved - we documented 10 callers with 21 total call sites.

---

## Phase 5: sub_21657 ✅ VERIFIED

**Finding**: sub_21657 has **0 direct callers** (as expected)

This confirms it's called indirectly via function pointer.

---

## Critical Corrections Required

### 1. Math Helpers Finding ✗ INVALIDATED

**Original claim**: "10 math helpers exclusive to view_projection"

**Reality**: These addresses are mid-function entry points in unrelated functions (stream_command_interpret, group_children_release, etc.). They have 0 external calls.

**Cause**: Bytecode pattern analysis without call graph verification.

**Fix**: Need to properly disassemble view_projection and extract actual CALL targets.

### 2. vec3_transform Caller Count ✓ CLARIFIED

**Original claim**: "10 callers"

**Reality**: 10 caller functions, 21 total call sites. This is correct when properly understood.

**Fix**: Update documentation to clarify "10 caller functions with 21 total calls".

### 3. Missing Callers ⚠ INCOMPLETE

We documented 10 callers but Phase 3 shows 21. However, Phase 4 shows our 10 callers account for 21 calls total. This is **CONSISTENT**.

**Conclusion**: No missing callers. The "21 callers" in Phase 3 is the xref count (21 call sites), not 21 unique functions.

---

## Updated Statistics

### Verified Correct ✓
- seg020 base address (0x1F6C0)
- view_projection address (0x20BDB)
- fixed_vec3_transform_es address (0x248D1)
- All 6 graphics function sizes (146, 17, 393, 72, 72, 70 bytes)
- 10 vec3_transform callers with 21 total call sites
- sub_21657 has no direct callers

### Invalidated ✗
- "10 exclusive math helpers" claim
- Math helpers are NOT exclusive to view_projection
- Addresses identified are internal jump targets, not function calls

### Needs Re-Analysis ⚠
- Actual functions called by view_projection
- Real math library functions (if any)
- view_projection disassembly to find CALL instructions

---

## Action Items

### High Priority
1. ✅ ~~Run automated verification~~ (DONE)
2. ⬜ Disassemble view_projection to find actual CALL targets
3. ⬜ Update math_library_analysis.json with corrected findings
4. ⬜ Create corrected pipeline map
5. ⬜ Update all documentation to remove "exclusive math helpers" claim

### Medium Priority
1. ⬜ Find all 21 call sites of fixed_vec3_transform_es
2. ⬜ Find 3rd caller of vec2_normalize_seq
3. ⬜ Document actual helper functions (if any)

### Low Priority
1. ⬜ Investigate why bytecode pattern analysis gave false positives
2. ⬜ Create better call graph analysis tools
3. ⬜ Verify other findings from session

---

## Lessons Learned

1. **Always verify with IDA API**: Bytecode analysis alone is insufficient
2. **XRefs = call sites, not callers**: 21 xrefs can mean 10 functions making 21 calls
3. **Mid-function addresses need special handling**: Entry points != function calls
4. **Automated verification catches errors**: This caught a major misunderstanding

---

## Next Steps

1. Create tool to extract actual CALL targets from view_projection
2. Re-analyze pipeline with corrected data
3. Update all session documentation
4. Commit corrected findings

---

**Verification Date**: Auto-generated from IDA API  
**Tool**: auto_verify_all.py  
**IDB**: FALCONCD.EXE.i64
