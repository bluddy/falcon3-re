# IDA Verification Plan for Graphics Pipeline Analysis

## Purpose
Verify and cross-check all findings from automated analysis against IDA Pro database.

## Phase 1: Address Translation Verification (30 min)
- [ ] Verify seg020 base address calculation (0x1F6C0)
- [ ] Confirm view_projection at seg020:151B = 0x20BDB
- [ ] Verify sub_256A3 at seg020:5FE3 = 0x256A3
- [ ] Spot-check 5 random multi-entry functions from segment_map.json
- [ ] Verify DGROUP:0x4287 (3D coordinate structure)
- [ ] Verify DGROUP:0x7C054 (near object queue)
- [ ] Verify DGROUP:0x7D0C6 (far object queue)

## Phase 2: Math Helper Verification (45 min)
Verify all 10 math helper entry points called exclusively by view_projection:
- [ ] seg015:0C65 - segment setup
- [ ] seg015:0C7A - complex dispatcher
- [ ] seg015:0CDB - 32-bit left shift
- [ ] seg015:0CF0 - far call to 0x1994:0D94
- [ ] seg015:0D51 - wrapper with cleanup
- [ ] seg015:0D66 - conditional math
- [ ] seg017:01FE - table lookup at 0x7772:0x0F34
- [ ] seg017:021C - multiply-accumulate loop
- [ ] seg017:01E3 - conditional epilogue
- [ ] seg020:1A2F - 32-bit absolute value

For each:
1. Navigate to address in IDA
2. Verify function exists at that location
3. Check xrefs - confirm only called by view_projection
4. Document actual function name if different from parent

## Phase 3: Graphics Function Verification (30 min)
Verify all 6 core graphics functions:
- [ ] fixed_vec3_transform_es (seg020:5211) - verify 10 callers
- [ ] vec2_normalize_seq - verify 2 callers
- [ ] farobj_record_step - verify size 393 bytes
- [ ] farobj_record_push_7c054 - verify near queue access
- [ ] farobj_record_lookup_step - verify size 72 bytes
- [ ] farobj_record_push_7d0c6 - verify far queue access

## Phase 4: vec3_transform Caller Verification (30 min)
Verify all 10 callers of fixed_vec3_transform_es:
- [ ] view_projection - 1x call
- [ ] record_xform_apply - 4x calls
- [ ] object_proj_draw_dispatch - 1x call
- [ ] object_quad_proj_draw - 4x calls
- [ ] view_proj_setup_1f73d - 3x calls
- [ ] view_scroll_rotate_apply - 1x call
- [ ] view_proj_setup_1f73d_rot - 3x calls
- [ ] view_basis_build_3850 - 2x calls
- [ ] stub_to_248d1 - 1x call
- [ ] sub_21657 - 1x call (verify no direct callers)

## Phase 5: Data Structure Verification (30 min)
- [ ] Examine DGROUP:0x4287 structure (used by sub_256A3)
- [ ] Examine 0x7772:0x0F34 lookup table (used by seg017:01FE)
- [ ] Examine near object queue at DGROUP:0x7C054
- [ ] Examine far object queue at DGROUP:0x7D0C6
- [ ] Measure queue separation (should be 4,210 bytes)

## Phase 6: Pipeline Flow Verification (30 min)
- [ ] Trace complete view_projection call graph (all 16 calls)
- [ ] Verify transformation stages (setup → transform → normalize → project)
- [ ] Check for any missed function calls
- [ ] Verify farobj_sort_and_step orchestration

## Phase 7: Multi-Entry Function Audit (30 min)
- [ ] Verify segment_map.json statistics (2,385 multi-entry = 57%)
- [ ] Spot-check 10 random multi-entry functions
- [ ] Verify seg020:051B is within record_xform_apply but NOT listed as multi-entry
- [ ] Document any export issues found

## Outputs
Create verification report: `ida_verification_report.md` with:
- All confirmed findings
- Any discrepancies found
- Corrections needed to analysis
- New discoveries made during verification
- Updated function names from IDA

## Estimated Time
3-4 hours total for thorough verification
