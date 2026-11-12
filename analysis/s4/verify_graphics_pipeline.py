"""
Comprehensive IDA verification script for graphics pipeline analysis.
Run with: idat.exe -A -S"verify_graphics_pipeline.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json

def seg_to_linear(seg, off):
    """Convert segment:offset to linear address."""
    seg_base = idc.get_segm_by_sel(seg)
    if seg_base == idc.BADADDR:
        return None
    return seg_base + off

def verify_address_translation():
    """Phase 1: Verify key address translations."""
    print("\n=== PHASE 1: Address Translation Verification ===")
    results = {
        "seg020_base": None,
        "view_projection": None,
        "sub_256A3": None,
        "dgroup_4287": None,
        "near_queue_7C054": None,
        "far_queue_7D0C6": None,
    }
    
    # Find seg020 base
    seg020_sel = idc.selector_by_name("seg020")
    if seg020_sel != idc.BADADDR:
        seg020_base = idc.get_segm_by_sel(seg020_sel)
        results["seg020_base"] = hex(seg020_base)
        print(f"✓ seg020 base: {hex(seg020_base)} (expected 0x1F6C0)")
        
        # view_projection at seg020:151B
        view_proj_addr = seg020_base + 0x151B
        view_proj_name = idc.get_func_name(view_proj_addr)
        results["view_projection"] = {
            "address": hex(view_proj_addr),
            "name": view_proj_name,
            "expected_addr": "0x20BDB",
            "expected_name": "view_projection"
        }
        print(f"✓ 0x20BDB = {view_proj_name} at {hex(view_proj_addr)}")
        
        # sub_256A3 at seg020:5FE3
        sub_256A3_addr = seg020_base + 0x5FE3
        sub_256A3_name = idc.get_func_name(sub_256A3_addr)
        results["sub_256A3"] = {
            "address": hex(sub_256A3_addr),
            "name": sub_256A3_name,
            "expected_addr": "0x256A3"
        }
        print(f"✓ 0x256A3 = {sub_256A3_name} at {hex(sub_256A3_addr)}")
    
    # Verify DGROUP addresses
    dgroup_sel = idc.selector_by_name("DGROUP")
    if dgroup_sel != idc.BADADDR:
        dgroup_base = idc.get_segm_by_sel(dgroup_sel)
        
        addr_4287 = dgroup_base + 0x4287
        name_4287 = idc.get_name(addr_4287)
        results["dgroup_4287"] = {
            "address": hex(addr_4287),
            "name": name_4287,
            "type": idc.get_type(addr_4287)
        }
        print(f"✓ DGROUP:0x4287 = {name_4287} at {hex(addr_4287)}")
        
        addr_7C054 = dgroup_base + 0x7C054
        name_7C054 = idc.get_name(addr_7C054)
        results["near_queue_7C054"] = {
            "address": hex(addr_7C054),
            "name": name_7C054
        }
        print(f"✓ DGROUP:0x7C054 (near queue) = {name_7C054} at {hex(addr_7C054)}")
        
        addr_7D0C6 = dgroup_base + 0x7D0C6
        name_7D0C6 = idc.get_name(addr_7D0C6)
        queue_separation = addr_7D0C6 - addr_7C054
        results["far_queue_7D0C6"] = {
            "address": hex(addr_7D0C6),
            "name": name_7D0C6,
            "separation_from_near": queue_separation
        }
        print(f"✓ DGROUP:0x7D0C6 (far queue) = {name_7D0C6} at {hex(addr_7D0C6)}")
        print(f"  Queue separation: {queue_separation} bytes (expected 4,210)")
    
    return results

def verify_math_helpers():
    """Phase 2: Verify 10 math helper entry points."""
    print("\n=== PHASE 2: Math Helper Verification ===")
    
    math_helpers = [
        ("seg015", 0x0C65, "segment setup"),
        ("seg015", 0x0C7A, "complex dispatcher"),
        ("seg015", 0x0CDB, "32-bit left shift"),
        ("seg015", 0x0CF0, "far call to 0x1994:0D94"),
        ("seg015", 0x0D51, "wrapper with cleanup"),
        ("seg015", 0x0D66, "conditional math"),
        ("seg017", 0x01FE, "table lookup at 0x7772:0x0F34"),
        ("seg017", 0x021C, "multiply-accumulate loop"),
        ("seg017", 0x01E3, "conditional epilogue"),
        ("seg020", 0x1A2F, "32-bit absolute value"),
    ]
    
    results = []
    for seg_name, offset, description in math_helpers:
        seg_sel = idc.selector_by_name(seg_name)
        if seg_sel == idc.BADADDR:
            print(f"✗ Segment {seg_name} not found")
            continue
        
        seg_base = idc.get_segm_by_sel(seg_sel)
        addr = seg_base + offset
        
        # Get function at this address (may be middle of function)
        func = idaapi.get_func(addr)
        if func:
            func_name = idc.get_func_name(addr)
            func_start = func.start_ea
            
            # Get xrefs to this specific address
            xrefs = list(idautils.XrefsTo(addr, 0))
            xref_count = len(xrefs)
            xref_sources = [hex(x.frm) for x in xrefs[:5]]  # First 5
            
            result = {
                "segoff": f"{seg_name}:{hex(offset)}",
                "address": hex(addr),
                "description": description,
                "function_name": func_name,
                "function_start": hex(func_start),
                "is_entry_point": (addr == func_start),
                "xref_count": xref_count,
                "xref_sources": xref_sources
            }
            results.append(result)
            
            status = "ENTRY" if addr == func_start else "MID"
            print(f"✓ {seg_name}:{hex(offset)} [{status}] = {func_name} ({xref_count} xrefs)")
            if xref_count <= 3:
                for xref in xrefs:
                    caller = idc.get_func_name(xref.frm)
                    print(f"    Called from {caller} at {hex(xref.frm)}")
        else:
            print(f"✗ {seg_name}:{hex(offset)} - no function found")
            results.append({
                "segoff": f"{seg_name}:{hex(offset)}",
                "address": hex(addr),
                "description": description,
                "error": "no_function"
            })
    
    return results

def verify_graphics_functions():
    """Phase 3: Verify 6 core graphics functions."""
    print("\n=== PHASE 3: Graphics Function Verification ===")
    
    graphics_funcs = [
        ("seg020", 0x5211, "fixed_vec3_transform_es", 146, 10),
        ("seg020", None, "vec2_normalize_seq", 17, 2),
        ("seg020", None, "farobj_record_step", 393, None),
        ("seg020", None, "farobj_record_push_7c054", 72, None),
        ("seg020", None, "farobj_record_lookup_step", 72, None),
        ("seg020", None, "farobj_record_push_7d0c6", 70, None),
    ]
    
    results = []
    seg020_sel = idc.selector_by_name("seg020")
    if seg020_sel == idc.BADADDR:
        print("✗ seg020 not found")
        return results
    
    seg020_base = idc.get_segm_by_sel(seg020_sel)
    
    for seg_name, offset, expected_name, expected_size, expected_callers in graphics_funcs:
        if offset is not None:
            # Find by offset
            addr = seg020_base + offset
        else:
            # Find by name
            addr = idc.get_name_ea_simple(expected_name)
            if addr == idc.BADADDR:
                print(f"✗ {expected_name} not found by name")
                results.append({
                    "name": expected_name,
                    "error": "not_found"
                })
                continue
        
        func = idaapi.get_func(addr)
        if not func:
            print(f"✗ {expected_name} at {hex(addr)} - no function")
            results.append({
                "name": expected_name,
                "address": hex(addr),
                "error": "no_function"
            })
            continue
        
        actual_name = idc.get_func_name(addr)
        actual_size = func.end_ea - func.start_ea
        
        # Count callers
        xrefs = list(idautils.XrefsTo(func.start_ea, 0))
        caller_count = len(xrefs)
        callers = []
        for xref in xrefs:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                callers.append(caller_name)
        
        result = {
            "expected_name": expected_name,
            "actual_name": actual_name,
            "address": hex(addr),
            "expected_size": expected_size,
            "actual_size": actual_size,
            "expected_callers": expected_callers,
            "actual_caller_count": caller_count,
            "callers": callers[:10]  # First 10
        }
        results.append(result)
        
        size_match = "✓" if expected_size is None or actual_size == expected_size else f"✗ ({actual_size} vs {expected_size})"
        caller_match = "✓" if expected_callers is None or caller_count == expected_callers else f"✗ ({caller_count} vs {expected_callers})"
        
        print(f"✓ {actual_name} at {hex(addr)}")
        print(f"    Size: {actual_size} bytes {size_match}")
        print(f"    Callers: {caller_count} {caller_match}")
        if caller_count <= 10:
            for caller in callers:
                print(f"      - {caller}")
    
    return results

def verify_vec3_callers():
    """Phase 4: Verify all callers of fixed_vec3_transform_es."""
    print("\n=== PHASE 4: vec3_transform Caller Verification ===")
    
    vec3_addr = idc.get_name_ea_simple("fixed_vec3_transform_es")
    if vec3_addr == idc.BADADDR:
        print("✗ fixed_vec3_transform_es not found")
        return []
    
    print(f"fixed_vec3_transform_es at {hex(vec3_addr)}")
    
    # Expected callers with call counts
    expected = {
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
                caller_calls[caller_name] = []
            caller_calls[caller_name].append(hex(xref.frm))
    
    print(f"\nFound {len(xrefs)} total calls from {len(caller_calls)} functions:")
    
    results = []
    for caller, call_sites in sorted(caller_calls.items()):
        call_count = len(call_sites)
        expected_count = expected.get(caller, "?")
        match = "✓" if expected_count == call_count else f"✗ (expected {expected_count})"
        
        print(f"  {caller}: {call_count} calls {match}")
        
        results.append({
            "caller": caller,
            "call_count": call_count,
            "expected_count": expected_count,
            "call_sites": call_sites
        })
    
    # Check for missing expected callers
    for expected_caller in expected:
        if expected_caller not in caller_calls:
            print(f"  ✗ MISSING: {expected_caller}")
            results.append({
                "caller": expected_caller,
                "call_count": 0,
                "expected_count": expected[expected_caller],
                "error": "not_found"
            })
    
    return results

def verify_multi_entry_sample():
    """Phase 7: Spot-check multi-entry functions."""
    print("\n=== PHASE 7: Multi-Entry Function Sample Verification ===")
    
    # Load segment_map.json if available
    try:
        with open("segment_map.json", "r") as f:
            segment_map = json.load(f)
    except:
        print("✗ segment_map.json not found")
        return []
    
    multi_entry_funcs = segment_map.get("multi_entry_functions", {})
    total_multi = len(multi_entry_funcs)
    print(f"Found {total_multi} multi-entry functions in segment_map.json")
    
    # Sample 10 random ones
    import random
    sample_addrs = random.sample(list(multi_entry_funcs.keys()), min(10, total_multi))
    
    results = []
    for addr_str in sample_addrs:
        addr = int(addr_str, 16)
        entry_info = multi_entry_funcs[addr_str]
        
        # Verify function exists
        func = idaapi.get_func(addr)
        if func:
            func_name = idc.get_func_name(addr)
            is_start = (func.start_ea == addr)
            
            result = {
                "address": hex(addr),
                "expected_entries": entry_info.get("entry_count", 1),
                "function_name": func_name,
                "function_start": hex(func.start_ea),
                "is_entry_point": is_start,
                "verified": True
            }
            print(f"✓ {hex(addr)} = {func_name} (start={hex(func.start_ea)})")
        else:
            result = {
                "address": hex(addr),
                "expected_entries": entry_info.get("entry_count", 1),
                "error": "no_function",
                "verified": False
            }
            print(f"✗ {hex(addr)} - no function found")
        
        results.append(result)
    
    return results

def main():
    """Run all verification phases."""
    print("=" * 80)
    print("GRAPHICS PIPELINE VERIFICATION")
    print("=" * 80)
    
    report = {
        "phase1_addresses": verify_address_translation(),
        "phase2_math_helpers": verify_math_helpers(),
        "phase3_graphics_functions": verify_graphics_functions(),
        "phase4_vec3_callers": verify_vec3_callers(),
        "phase7_multi_entry_sample": verify_multi_entry_sample(),
    }
    
    # Save report
    output_file = "ida_verification_results.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Verification complete. Results saved to {output_file}")
    print("=" * 80)
    
    # Auto-quit IDA
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
