"""
Automated verification using IDA Python API.
Run from within IDA Pro (Alt+F7 or File → Script file)
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def get_segment_base(seg_name):
    """Get base address of a segment by name."""
    seg_sel = idc.selector_by_name(seg_name)
    if seg_sel == idc.BADADDR:
        return None
    return idc.get_segm_by_sel(seg_sel)

def verify_phase1_addresses():
    """Verify all key addresses and data structures."""
    print("\n" + "="*80)
    print("PHASE 1: ADDRESS VERIFICATION")
    print("="*80)
    
    results = {"passed": [], "failed": [], "warnings": []}
    
    # Verify seg020
    seg020_base = get_segment_base("seg020")
    if seg020_base:
        expected = 0x1F6C0
        if seg020_base == expected:
            results["passed"].append(f"seg020 base = {hex(seg020_base)} ✓")
            print(f"✓ seg020 base = {hex(seg020_base)}")
        else:
            results["failed"].append(f"seg020 base = {hex(seg020_base)}, expected {hex(expected)}")
            print(f"✗ seg020 base = {hex(seg020_base)}, expected {hex(expected)}")
    else:
        results["failed"].append("seg020 not found")
        print("✗ seg020 not found")
        return results
    
    # Verify view_projection
    view_proj_addr = 0x20BDB
    view_proj_name = idc.get_func_name(view_proj_addr)
    if view_proj_name == "view_projection":
        results["passed"].append(f"view_projection at {hex(view_proj_addr)} ✓")
        print(f"✓ view_projection at {hex(view_proj_addr)}")
    else:
        results["warnings"].append(f"Function at {hex(view_proj_addr)} is '{view_proj_name}', expected 'view_projection'")
        print(f"⚠ Function at {hex(view_proj_addr)} is '{view_proj_name}'")
    
    # Verify fixed_vec3_transform_es
    vec3_addr = 0x248D1
    vec3_name = idc.get_func_name(vec3_addr)
    if vec3_name == "fixed_vec3_transform_es":
        results["passed"].append(f"fixed_vec3_transform_es at {hex(vec3_addr)} ✓")
        print(f"✓ fixed_vec3_transform_es at {hex(vec3_addr)}")
    else:
        results["warnings"].append(f"Function at {hex(vec3_addr)} is '{vec3_name}', expected 'fixed_vec3_transform_es'")
        print(f"⚠ Function at {hex(vec3_addr)} is '{vec3_name}'")
    
    # Verify DGROUP structures
    dgroup_base = get_segment_base("DGROUP")
    if dgroup_base:
        # Check near queue
        near_queue = dgroup_base + 0x7C054
        near_name = idc.get_name(near_queue)
        print(f"  DGROUP:0x7C054 (near queue) = {near_name} at {hex(near_queue)}")
        results["passed"].append(f"Near queue at {hex(near_queue)}")
        
        # Check far queue
        far_queue = dgroup_base + 0x7D0C6
        far_name = idc.get_name(far_queue)
        separation = far_queue - near_queue
        print(f"  DGROUP:0x7D0C6 (far queue) = {far_name} at {hex(far_queue)}")
        print(f"  Queue separation = {separation} bytes (expected 4,210)")
        
        if separation == 4210:
            results["passed"].append(f"Queue separation = {separation} bytes ✓")
        else:
            results["warnings"].append(f"Queue separation = {separation} bytes, expected 4,210")
    
    return results

def verify_phase2_math_helpers():
    """Verify 10 math helper entry points and their exclusivity."""
    print("\n" + "="*80)
    print("PHASE 2: MATH HELPER VERIFICATION")
    print("="*80)
    
    seg015_base = get_segment_base("seg015")
    seg017_base = get_segment_base("seg017")
    seg020_base = get_segment_base("seg020")
    
    if not all([seg015_base, seg017_base, seg020_base]):
        print("✗ Could not find all required segments")
        return {"passed": [], "failed": ["Segments not found"], "warnings": []}
    
    math_helpers = [
        (seg015_base + 0x0C65, "seg015:0C65", "segment setup"),
        (seg015_base + 0x0C7A, "seg015:0C7A", "complex dispatcher"),
        (seg015_base + 0x0CDB, "seg015:0CDB", "32-bit left shift"),
        (seg015_base + 0x0CF0, "seg015:0CF0", "far call wrapper"),
        (seg015_base + 0x0D51, "seg015:0D51", "wrapper with cleanup"),
        (seg015_base + 0x0D66, "seg015:0D66", "conditional math"),
        (seg017_base + 0x01FE, "seg017:01FE", "table lookup"),
        (seg017_base + 0x021C, "seg017:021C", "multiply-accumulate"),
        (seg017_base + 0x01E3, "seg017:01E3", "conditional epilogue"),
        (seg020_base + 0x1A2F, "seg020:1A2F", "32-bit absolute value"),
    ]
    
    results = {"passed": [], "failed": [], "warnings": [], "details": []}
    view_proj_addr = 0x20BDB
    
    for addr, segoff, desc in math_helpers:
        func = idaapi.get_func(addr)
        if not func:
            results["failed"].append(f"{segoff} - no function found")
            print(f"✗ {segoff} - no function found")
            continue
        
        func_name = idc.get_func_name(addr)
        is_entry = (func.start_ea == addr)
        
        # Get xrefs to this specific address
        xrefs = list(idautils.XrefsTo(addr, 0))
        xref_count = len(xrefs)
        
        # Check if called only by view_projection
        callers = set()
        for xref in xrefs:
            caller_addr = xref.frm
            caller_func = idc.get_func_name(caller_addr)
            if caller_func:
                callers.add(caller_func)
        
        exclusive = (len(callers) == 1 and "view_projection" in list(callers)[0])
        
        detail = {
            "segoff": segoff,
            "address": hex(addr),
            "description": desc,
            "function": func_name,
            "is_entry": is_entry,
            "xref_count": xref_count,
            "callers": list(callers),
            "exclusive": exclusive
        }
        results["details"].append(detail)
        
        status = "ENTRY" if is_entry else "MID"
        excl_status = "✓ EXCLUSIVE" if exclusive else f"⚠ SHARED ({len(callers)} callers)"
        
        print(f"  {segoff} [{status}] = {func_name}")
        print(f"    {desc}")
        print(f"    {xref_count} xrefs, {excl_status}")
        
        if exclusive:
            results["passed"].append(f"{segoff} exclusive to view_projection")
        else:
            results["warnings"].append(f"{segoff} called by: {', '.join(callers)}")
            print(f"    Callers: {', '.join(callers)}")
    
    return results

def verify_phase3_graphics_functions():
    """Verify 6 core graphics functions."""
    print("\n" + "="*80)
    print("PHASE 3: GRAPHICS FUNCTIONS")
    print("="*80)
    
    functions = [
        ("fixed_vec3_transform_es", 0x248D1, 146, 10),
        ("vec2_normalize_seq", None, 17, 2),
        ("farobj_record_step", None, 393, None),
        ("farobj_record_push_7c054", None, 72, None),
        ("farobj_record_lookup_step", None, 72, None),
        ("farobj_record_push_7d0c6", None, 70, None),
    ]
    
    results = {"passed": [], "failed": [], "warnings": [], "details": []}
    
    for func_name, addr, expected_size, expected_callers in functions:
        if addr is None:
            addr = idc.get_name_ea_simple(func_name)
        
        if addr == idc.BADADDR:
            results["failed"].append(f"{func_name} not found")
            print(f"✗ {func_name} not found")
            continue
        
        func = idaapi.get_func(addr)
        if not func:
            results["failed"].append(f"{func_name} at {hex(addr)} - no function")
            print(f"✗ {func_name} at {hex(addr)} - no function")
            continue
        
        actual_name = idc.get_func_name(addr)
        actual_size = func.end_ea - func.start_ea
        
        # Count callers
        xrefs = list(idautils.XrefsTo(func.start_ea, 0))
        caller_count = len(xrefs)
        
        detail = {
            "expected_name": func_name,
            "actual_name": actual_name,
            "address": hex(addr),
            "expected_size": expected_size,
            "actual_size": actual_size,
            "expected_callers": expected_callers,
            "actual_callers": caller_count
        }
        results["details"].append(detail)
        
        print(f"  {actual_name} at {hex(addr)}")
        
        # Check size
        if expected_size:
            if actual_size == expected_size:
                print(f"    Size: {actual_size} bytes ✓")
                results["passed"].append(f"{func_name} size correct")
            else:
                print(f"    Size: {actual_size} bytes (expected {expected_size}) ⚠")
                results["warnings"].append(f"{func_name} size {actual_size} vs expected {expected_size}")
        else:
            print(f"    Size: {actual_size} bytes")
        
        # Check callers
        if expected_callers:
            if caller_count == expected_callers:
                print(f"    Callers: {caller_count} ✓")
                results["passed"].append(f"{func_name} caller count correct")
            else:
                print(f"    Callers: {caller_count} (expected {expected_callers}) ⚠")
                results["warnings"].append(f"{func_name} has {caller_count} callers, expected {expected_callers}")
        else:
            print(f"    Callers: {caller_count}")
    
    return results

def verify_phase4_vec3_callers():
    """Verify all callers of fixed_vec3_transform_es."""
    print("\n" + "="*80)
    print("PHASE 4: VEC3_TRANSFORM CALLERS")
    print("="*80)
    
    vec3_addr = idc.get_name_ea_simple("fixed_vec3_transform_es")
    if vec3_addr == idc.BADADDR:
        vec3_addr = 0x248D1
    
    expected_calls = {
        "view_projection": 1,
        "record_xform_apply": 4,
        "object_proj_draw_dispatch": 1,
        "object_quad_proj_draw": 4,
        "view_proj_setup_1f73d": 3,
        "view_scroll_rotate_apply": 1,
        "view_proj_setup_1f73d_rot": 3,
        "view_basis_build_3850": 2,
        "stub_to_248d1": 1,
        "sub_21657": 1,
    }
    
    # Get all xrefs
    xrefs = list(idautils.XrefsTo(vec3_addr, 0))
    
    # Group by caller
    caller_calls = {}
    for xref in xrefs:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            if caller_name not in caller_calls:
                caller_calls[caller_name] = 0
            caller_calls[caller_name] += 1
    
    print(f"fixed_vec3_transform_es at {hex(vec3_addr)}")
    print(f"Total: {len(xrefs)} calls from {len(caller_calls)} functions\n")
    
    results = {"passed": [], "failed": [], "warnings": [], "details": []}
    
    # Check each caller
    for caller, actual_count in sorted(caller_calls.items()):
        expected_count = expected_calls.get(caller, None)
        
        detail = {
            "caller": caller,
            "actual_calls": actual_count,
            "expected_calls": expected_count
        }
        results["details"].append(detail)
        
        if expected_count is None:
            print(f"  {caller}: {actual_count} calls ⚠ UNEXPECTED CALLER")
            results["warnings"].append(f"Unexpected caller: {caller} ({actual_count} calls)")
        elif actual_count == expected_count:
            print(f"  {caller}: {actual_count} calls ✓")
            results["passed"].append(f"{caller} call count correct")
        else:
            print(f"  {caller}: {actual_count} calls (expected {expected_count}) ⚠")
            results["warnings"].append(f"{caller} has {actual_count} calls, expected {expected_count}")
    
    # Check for missing expected callers
    for expected_caller, expected_count in expected_calls.items():
        if expected_caller not in caller_calls:
            print(f"  {expected_caller}: MISSING ✗")
            results["failed"].append(f"Missing caller: {expected_caller}")
    
    return results

def verify_sub_21657():
    """Special check for sub_21657 - should have no direct callers."""
    print("\n" + "="*80)
    print("PHASE 5: SUB_21657 SPECIAL CHECK")
    print("="*80)
    
    # Try to find sub_21657
    addr = idc.get_name_ea_simple("sub_21657")
    if addr == idc.BADADDR:
        print("✗ sub_21657 not found")
        return {"failed": ["sub_21657 not found"]}
    
    func = idaapi.get_func(addr)
    if not func:
        print("✗ No function at sub_21657 address")
        return {"failed": ["No function at sub_21657"]}
    
    # Check for direct callers (xrefs to function start)
    xrefs = list(idautils.XrefsTo(func.start_ea, 0))
    direct_callers = len(xrefs)
    
    print(f"sub_21657 at {hex(addr)}")
    print(f"Direct callers: {direct_callers}")
    
    if direct_callers == 0:
        print("✓ No direct callers (as expected - indirect call)")
        return {"passed": ["sub_21657 has no direct callers (indirect call)"]}
    else:
        print(f"⚠ Found {direct_callers} direct callers:")
        for xref in xrefs:
            caller = idc.get_func_name(xref.frm)
            print(f"    - {caller} at {hex(xref.frm)}")
        return {"warnings": [f"sub_21657 has {direct_callers} direct callers, expected 0"]}

def main():
    """Run all verification phases."""
    print("="*80)
    print("AUTOMATED GRAPHICS PIPELINE VERIFICATION")
    print("="*80)
    
    all_results = {
        "phase1_addresses": verify_phase1_addresses(),
        "phase2_math_helpers": verify_phase2_math_helpers(),
        "phase3_graphics": verify_phase3_graphics_functions(),
        "phase4_vec3_callers": verify_phase4_vec3_callers(),
        "phase5_sub_21657": verify_sub_21657(),
    }
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    total_passed = sum(len(r.get("passed", [])) for r in all_results.values())
    total_warnings = sum(len(r.get("warnings", [])) for r in all_results.values())
    total_failed = sum(len(r.get("failed", [])) for r in all_results.values())
    
    print(f"\n✓ Passed: {total_passed}")
    print(f"⚠ Warnings: {total_warnings}")
    print(f"✗ Failed: {total_failed}")
    
    if total_warnings > 0:
        print("\nWarnings:")
        for phase, results in all_results.items():
            for warning in results.get("warnings", []):
                print(f"  - {warning}")
    
    if total_failed > 0:
        print("\nFailures:")
        for phase, results in all_results.items():
            for failure in results.get("failed", []):
                print(f"  - {failure}")
    
    # Save results
    output_file = Path(__file__).parent / "auto_verification_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    idaapi.auto_wait()  # Wait for auto-analysis to complete
    main()
    idc.qexit(0)  # Exit IDA after completion
