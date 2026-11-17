"""
Search for functions related to different types of tactical map objects.
Look for aircraft, SAM sites, targets, threats, and other map symbols.
"""

import idc
import idautils
import idaapi
import json
from pathlib import Path

def search_function_names(keywords):
    """Search for functions containing any of the keywords."""
    results = {}
    
    for keyword in keywords:
        results[keyword] = []
        
        # Iterate through all functions
        for func_ea in idautils.Functions():
            func_name = idc.get_func_name(func_ea)
            if func_name and keyword.lower() in func_name.lower():
                func = idaapi.get_func(func_ea)
                if func:
                    results[keyword].append({
                        'name': func_name,
                        'address': hex(func_ea),
                        'size': func.end_ea - func.start_ea
                    })
        
        print(f"Keyword '{keyword}': {len(results[keyword])} matches")
    
    return results

def find_segment_references():
    """
    Find functions that access the tactical map display segment (0x7894).
    This segment contains pointers to map data.
    """
    results = []
    
    # Search for references to segment 0x7894
    target_seg = 0x7894
    
    # This is complex - let's look for mov instructions with this segment
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Check if this function accesses our segment
        has_access = False
        ea = func.start_ea
        while ea < func.end_ea:
            # Look for mov ax, 7894h pattern
            if idc.print_insn_mnem(ea) == 'mov':
                op1 = idc.get_operand_value(ea, 1)
                if op1 == target_seg:
                    has_access = True
                    break
            ea = idc.next_head(ea, func.end_ea)
        
        if has_access:
            results.append({
                'name': func_name,
                'address': hex(func_ea),
                'size': func.end_ea - func.start_ea
            })
            
            if len(results) >= 50:  # Limit to avoid excessive output
                break
    
    return results

def analyze_map_rendering_pipeline():
    """
    Trace from waypoint_display_helper to find the complete rendering pipeline.
    """
    results = {
        'waypoint_helper': {},
        'callers': [],
        'callees': []
    }
    
    waypoint_helper_ea = 0x1A163A
    
    # Get waypoint_display_helper info
    func = idaapi.get_func(waypoint_helper_ea)
    if func:
        results['waypoint_helper'] = {
            'address': hex(func.start_ea),
            'size': func.end_ea - func.start_ea
        }
        
        # Find what calls waypoint_helper
        callers = []
        for xref in idautils.XrefsTo(waypoint_helper_ea):
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(caller_func.start_ea)
                callers.append({
                    'name': caller_name,
                    'address': hex(caller_func.start_ea),
                    'call_site': hex(xref.frm)
                })
        
        results['callers'] = callers
        
        # Find what waypoint_helper calls
        ea = func.start_ea
        callees = []
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == 'call':
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target)
                if target_name:
                    callees.append({
                        'name': target_name,
                        'address': hex(target),
                        'call_site': hex(ea)
                    })
            ea = idc.next_head(ea, func.end_ea)
        
        results['callees'] = callees
    
    return results

def main():
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    results = {}
    
    # Search for object-type related functions
    print("=== Searching Function Names ===\n")
    keywords = [
        'flight', 'plane', 'waypoint', 'map', 'tactical',
        'threat', 'radar', 'sam', 'aaa', 'target', 'bullseye',
        'symbol', 'marker', 'icon', 'draw', 'render', 'display'
    ]
    results['keyword_matches'] = search_function_names(keywords)
    
    # Find segment 0x7894 accessors
    print("\n=== Finding Segment 0x7894 Accessors ===\n")
    results['segment_accessors'] = find_segment_references()
    print(f"Found {len(results['segment_accessors'])} functions")
    
    # Analyze rendering pipeline
    print("\n=== Analyzing Waypoint Rendering Pipeline ===\n")
    results['rendering_pipeline'] = analyze_map_rendering_pipeline()
    print(f"Callers: {len(results['rendering_pipeline']['callers'])}")
    print(f"Callees: {len(results['rendering_pipeline']['callees'])}")
    
    # Save results
    output_path = Path(__file__).parent / "map_object_types.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
