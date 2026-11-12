# Corrected Graphics Pipeline Findings

**Date**: After automated IDA API verification  
**Status**: ✅ VERIFIED via actual call graph analysis

---

## What Changed

**Before**: Manual bytecode analysis → False conclusions  
**After**: IDA API xref + disassembly → Ground truth

---

## view_projection Pipeline - CORRECTED

### Actual CALL Instructions (7 total, not 16)

| Call Address | Target | Function Name |
|--------------|--------|---------------|
| 0x20F2B | 0x5211 | **fixed_vec3_transform_es** |
| 0x20F77 | 0x47A6 | **vec2_normalize_seq** |
| 0x20FBA | 0x1D6E | **farobj_record_step** |
| 0x20FD3 | 0x166F | **overlay_tail_bridge** ⭐ NEW |
| 0x20FE5 | 0x1BCE | **farobj_record_push_7c054** |
| 0x21006 | 0x1D26 | **farobj_record_lookup_step** |
| 0x2100B | 0x1C16 | **farobj_record_push_7d0c6** |

### Pipeline Stages (CORRECTED)

1. **Transform**: fixed_vec3_transform_es
2. **Normalize**: vec2_normalize_seq
3. **Visibility Culling**: farobj_record_step
4. **Overlay Bridge**: overlay_tail_bridge (NEWLY DISCOVERED)
5. **Near Queue**: farobj_record_push_7c054
6. **Visibility Check**: farobj_record_lookup_step
7. **Far Queue**: farobj_record_push_7d0c6

---

## "Math Helpers" Finding ✗ INVALIDATED

### Original Claim (WRONG)
"10 math helper functions called exclusively by view_projection"

### Reality (VERIFIED)
These addresses are **mid-function internal jump targets** in UNRELATED functions:

- **seg015:0C65-0D66**: Inside `stream_command_interpret` (NOT math!)
- **seg017:01FE-021C**: Inside `group_children_release`
- **seg017:01E3**: Inside `channel_list_register_batch`
- **seg020:1A2F**: Inside `vec_delta_norm_1f6ee`

**XRef count = 0**: No external CALL instructions. These are JMP/JZ/JNZ targets or fall-through code.

### Why the Error Occurred
- Bytecode pattern matching without call graph verification
- Assumed addresses with code = function entry points
- Did not verify with IDA xrefs

---

## vec3_transform Callers - VERIFIED ✓

### 10 Callers with 21 Total Calls

All 10 identified callers and their call counts are **CORRECT**:

| Caller | Calls | Status |
|--------|-------|--------|
| view_projection | 1 | ✅ |
| record_xform_apply | 4 | ✅ |
| object_quad_proj_draw | 4 | ✅ |
| view_proj_setup_1f73d | 3 | ✅ |
| view_proj_setup_1f73d_rot | 3 | ✅ |
| view_basis_build_3850 | 2 | ✅ |
| object_proj_draw_dispatch | 1 | ✅ |
| view_scroll_rotate_apply | 1 | ✅ |
| stub_to_248d1 | 1 | ✅ |
| sub_21657 | 1 | ✅ |
| **Total** | **21** | ✅ |

**Clarification**: "21 callers" in Phase 3 means 21 call sites, not 21 functions. We correctly identified all 10 caller functions.

---

## Graphics Functions - VERIFIED ✓

### All Sizes Correct

| Function | Size | Callers | Status |
|----------|------|---------|--------|
| fixed_vec3_transform_es | 146 bytes | 21 calls | ✅ |
| vec2_normalize_seq | 17 bytes | 3 calls | ✅ |
| farobj_record_step | 393 bytes | 2 calls | ✅ |
| farobj_record_push_7c054 | 72 bytes | 1 call | ✅ |
| farobj_record_lookup_step | 72 bytes | 2 calls | ✅ |
| farobj_record_push_7d0c6 | 70 bytes | 1 call | ✅ |

---

## New Discovery: overlay_tail_bridge

**Address**: 0x166F  
**Called by**: view_projection at 0x20FD3  
**Purpose**: Bridge to overlay-swapped code

This was **missed** in original analysis. It suggests view_projection can trigger overlay swaps during rendering.

---

## Addresses - VERIFIED ✓

### All Core Addresses Correct

- ✅ seg020 base = 0x1F6C0
- ✅ view_projection = 0x20BDB (seg020:151B)
- ✅ fixed_vec3_transform_es = 0x248D1 (seg020:5211)
- ✅ DGROUP:0x7C054 (near queue)
- ✅ DGROUP:0x7D0C6 (far queue)
- ✅ Queue separation = 4,210 bytes

---

## sub_21657 - VERIFIED ✓

**Status**: No direct callers (indirect call via function pointer)

This was correct in original analysis.

---

## Corrected Statistics

### view_projection
- **Size**: 1,076 bytes ✓
- **CALL instructions**: 7 (not 16)
- **Direct calls**: 7
- **Indirect calls**: 0
- **Unique targets**: 7

### record_xform_apply
- **CALL instructions**: 18
- **fixed_vec3_transform_es calls**: 4 ✓
- **Most called**: farobj_field4_get_stc (4x), orient_classify_fallback (2x)

---

## What Was Correct ✓

1. **seg020 base address** (0x1F6C0)
2. **All function addresses** (view_projection, vec3_transform, etc.)
3. **All function sizes** (146, 17, 393, 72, 72, 70 bytes)
4. **vec3_transform callers** (10 functions, 21 call sites)
5. **farobj system architecture** (4 functions, 2 queues)
6. **Multi-entry architecture** (57% of codebase)
7. **sub_21657 indirect call** (0 direct callers)

---

## What Was Wrong ✗

1. **"10 exclusive math helpers"** - These don't exist
2. **"16 function calls in view_projection"** - Actually 7
3. **Math helper parent names** - stream_command_interpret is NOT related
4. **Pipeline complexity** - Simpler than originally thought

---

## Lessons Learned

### ✅ DO
- Use IDA API for call graph analysis
- Verify xrefs for every finding
- Extract actual CALL/JMP instructions
- Cross-check with multiple methods

### ✗ DON'T
- Trust bytecode patterns alone
- Assume address with code = function entry
- Skip xref verification
- Rely on static analysis without validation

---

## Updated Architecture

### view_projection Pipeline (SIMPLIFIED)

```
view_projection (0x20BDB)
  │
  ├─→ fixed_vec3_transform_es      (3D transform)
  ├─→ vec2_normalize_seq            (2D normalize)
  ├─→ farobj_record_step            (iterate objects)
  ├─→ overlay_tail_bridge           (swap overlay if needed)
  ├─→ farobj_record_push_7c054      (add to near queue)
  ├─→ farobj_record_lookup_step     (visibility check)
  └─→ farobj_record_push_7d0c6      (add to far queue)
```

**Flow**: Transform → Normalize → Iterate → Bridge → Queue Near → Check → Queue Far

---

## Action Items Completed ✅

1. ✅ Run automated IDA API verification
2. ✅ Extract actual CALL instructions
3. ✅ Identify false "math helpers" claim
4. ✅ Document corrected findings
5. ✅ Discover overlay_tail_bridge

## Next Steps

1. ⬜ Analyze overlay_tail_bridge function
2. ⬜ Update all session documentation
3. ⬜ Re-generate pipeline diagrams
4. ⬜ Create "lessons learned" guide for future analysis
5. ⬜ Verify other findings from session (farobj details, etc.)

---

## Files

### Verification
- `auto_verify_all.py` - Automated IDA API verification
- `extract_real_calls.py` - CALL instruction extractor
- `auto_verification_results.json` - Verification data
- `actual_call_targets.json` - Real call targets
- `VERIFICATION_RESULTS.md` - Detailed analysis
- `this file` - Corrected findings summary

### Supersedes
- ~~math_library_analysis.json~~ - INVALIDATED
- ~~math_helpers_identified.md~~ - INVALIDATED
- ~~projection_pipeline_map.json~~ - NEEDS UPDATE
- ~~view_projection_analysis.md~~ - NEEDS UPDATE

---

**Bottom Line**: Always use API verification. Bytecode analysis caught major architectural details (multi-entry, farobj system) but failed on call graph. The pipeline is simpler (7 calls vs claimed 16) but our understanding of the overall architecture remains sound.
