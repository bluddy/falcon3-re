"""
Find ALL 21 callers of fixed_vec3_transform_es to see who we're missing.
Phase 3 showed 21 xrefs but we only documented 10.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def main():
    print("="*80)
    print("FINDING ALL CALLERS OF fixed_vec3_transform_es")
    print("="*80)
    
    # Find fixed_vec3_transform_es
    vec3_addr = idc.get_name_ea_simple("fixed_vec3_transform_es")
    if vec3_addr == idc.BADADDR:
        vec3_addr = 0x248D1
    
    print(f"\nfixed_vec3_transform_es at {hex(vec3_addr)}")
    
    # Get ALL xrefs
    xrefs = list(idautils.XrefsTo(vec3_addr, 0))
    print(f"Total xrefs: {len(xrefs)}")
    
    # Group by caller function
    caller_details = {}
    
    for xref in xrefs:
        call_site = xref.frm
        caller_func_ea = idc.get_func_attr(call_site, idc.FUNCATTR_START)
        
        if caller_func_ea != idc.BADADDR:
            caller_name = idc.get_func_name(caller_func_ea)
            
            if caller_name not in caller_details:
                caller_func = idaapi.get_func(caller_func_ea)
                caller_details[caller_name] = {
                    "name": caller_name,
                    "address": hex(caller_func_ea),
                    "size": caller_func.end_ea - caller_func.start_ea if caller_func else 0,
                    "call_sites": [],
                    "call_count": 0
                }
            
            caller_details[caller_name]["call_sites"].append({
                "address": hex(call_site),
                "disasm": idc.GetDisasm(call_site)
            })
            caller_details[caller_name]["call_count"] += 1
    
    # Sort by call count
    sorted_callers = sorted(caller_details.items(), key=lambda x: x[1]["call_count"], reverse=True)
    
    print(f"\nFound {len(sorted_callers)} unique caller functions:")
    print("\n" + "-"*80)
    
    for i, (name, details) in enumerate(sorted_callers, 1):
        print(f"\n{i}. {name}")
        print(f"   Address: {details['address']}")
        print(f"   Size: {details['size']} bytes")
        print(f"   Calls to vec3_transform: {details['call_count']}x")
        
        if details['call_count'] <= 5:
            print(f"   Call sites:")
            for site in details['call_sites']:
                print(f"     {site['address']}: {site['disasm']}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    # Check against our documented 10
    documented = {
        "view_projection", "record_xform_apply", "object_proj_draw_dispatch",
        "object_quad_proj_draw", "view_proj_setup_1f73d", "view_scroll_rotate_apply",
        "view_proj_setup_1f73d_rot", "view_basis_build_3850", "stub_to_248d1", "sub_21657"
    }
    
    found_names = set(caller_details.keys())
    
    missing_in_docs = found_names - documented
    missing_in_ida = documented - found_names
    
    print(f"\nDocumented callers: {len(documented)}")
    print(f"Found in IDA: {len(found_names)}")
    
    if len(found_names) == len(documented):
        print("\n✓ Counts match! All callers documented.")
    else:
        print(f"\n⚠ Mismatch!")
    
    if missing_in_docs:
        print(f"\nNEW callers found (not in our docs):")
        for name in sorted(missing_in_docs):
            calls = caller_details[name]["call_count"]
            print(f"  - {name} ({calls}x)")
    
    if missing_in_ida:
        print(f"\nDocumented but NOT found in IDA:")
        for name in sorted(missing_in_ida):
            print(f"  - {name}")
    
    # Calculate total calls
    total_calls = sum(d["call_count"] for d in caller_details.values())
    print(f"\nTotal call sites: {total_calls}")
    
    # Save results
    results = {
        "vec3_address": hex(vec3_addr),
        "total_xrefs": len(xrefs),
        "unique_callers": len(sorted_callers),
        "total_calls": total_calls,
        "callers": [details for _, details in sorted_callers],
        "documented_callers": list(documented),
        "new_callers": list(missing_in_docs),
        "missing_callers": list(missing_in_ida)
    }
    
    output_file = Path(__file__).parent / "all_vec3_callers.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Exit IDA
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
