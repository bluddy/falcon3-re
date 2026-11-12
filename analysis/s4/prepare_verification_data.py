"""
Prepare verification data from existing analysis files.
This helps cross-reference findings without needing IDA automation.
"""

import json
import sys
from pathlib import Path

def load_json(filename):
    """Load JSON file if it exists."""
    path = Path(filename)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None

def load_segment_map():
    """Load and analyze segment_map.json."""
    seg_map = load_json("segment_map.json")
    if not seg_map:
        print("Warning: segment_map.json not found")
        return None
    
    print("=== SEGMENT MAP ANALYSIS ===")
    print(f"Total segments: {seg_map.get('segment_count', 0)}")
    print(f"Total functions: {seg_map.get('function_count', 0)}")
    
    segments = seg_map.get('segments', {})
    
    # Find seg020
    seg020_found = False
    for seg_addr, seg_info in segments.items():
        if seg_info.get('name') == 'seg020':
            print(f"\nseg020 found:")
            print(f"  Base address: {seg_addr}")
            print(f"  Size: {seg_info.get('size', 'unknown')} bytes")
            print(f"  Functions: {len(seg_info.get('functions', []))}")
            seg020_found = True
            
            # Calculate key addresses
            seg020_base = int(seg_addr, 16)
            print(f"\nKey addresses (seg020 base = {hex(seg020_base)}):")
            print(f"  seg020:151B (view_projection) = {hex(seg020_base + 0x151B)}")
            print(f"  seg020:5211 (fixed_vec3_transform_es) = {hex(seg020_base + 0x5211)}")
            print(f"  seg020:5FE3 (sub_256A3) = {hex(seg020_base + 0x5FE3)}")
            print(f"  seg020:1A2F (abs helper) = {hex(seg020_base + 0x1A2F)}")
            break
    
    if not seg020_found:
        print("\nWarning: seg020 not found in segment map")
    
    # Multi-entry statistics
    multi_entry = seg_map.get('multi_entry_functions', {})
    if multi_entry:
        print(f"\nMulti-entry functions: {len(multi_entry)}")
        total_funcs = seg_map.get('function_count', 0)
        if total_funcs > 0:
            percentage = (len(multi_entry) / total_funcs) * 100
            print(f"Percentage: {percentage:.1f}%")
    
    return seg_map

def load_graphics_analysis():
    """Load graphics function analysis."""
    graphics = load_json("graphics_functions_analysis.json")
    if not graphics:
        print("\nWarning: graphics_functions_analysis.json not found")
        return None
    
    print("\n=== GRAPHICS FUNCTIONS ===")
    for func_name, func_info in graphics.items():
        print(f"\n{func_name}:")
        print(f"  Address: {func_info.get('address', 'unknown')}")
        print(f"  Size: {func_info.get('size', 'unknown')} bytes")
        callers = func_info.get('callers', [])
        print(f"  Callers: {len(callers)}")
        for caller in callers[:5]:  # First 5
            print(f"    - {caller}")
        if len(callers) > 5:
            print(f"    ... and {len(callers) - 5} more")
    
    return graphics

def load_vec3_callers():
    """Load vec3_transform caller analysis."""
    vec3 = load_json("vec3_transform_callers.json")
    if not vec3:
        print("\nWarning: vec3_transform_callers.json not found")
        return None
    
    print("\n=== VEC3_TRANSFORM CALLERS ===")
    callers = vec3.get('callers', [])
    print(f"Total callers: {len(callers)}")
    
    total_calls = 0
    for caller_info in callers:
        caller_name = caller_info.get('name', 'unknown')
        call_count = caller_info.get('call_count', 0)
        total_calls += call_count
        print(f"  {caller_name}: {call_count} calls")
        
        # Check for unnamed
        if caller_name.startswith('sub_'):
            print(f"    ^ UNNAMED FUNCTION - needs investigation")
    
    print(f"\nTotal calls to vec3_transform: {total_calls}")
    return vec3

def load_projection_pipeline():
    """Load projection pipeline map."""
    pipeline = load_json("projection_pipeline_map.json")
    if not pipeline:
        print("\nWarning: projection_pipeline_map.json not found")
        return None
    
    print("\n=== PROJECTION PIPELINE ===")
    
    view_proj = pipeline.get('view_projection', {})
    print(f"view_projection:")
    print(f"  Address: {view_proj.get('address', 'unknown')}")
    print(f"  Size: {view_proj.get('size', 'unknown')} bytes")
    
    stages = view_proj.get('transformation_stages', {})
    if stages:
        print(f"\nTransformation stages:")
        for stage_name, stage_funcs in stages.items():
            print(f"  {stage_name}: {len(stage_funcs)} functions")
            for func in stage_funcs:
                print(f"    - {func}")
    
    return pipeline

def load_math_helpers():
    """Load math helper analysis."""
    helpers = load_json("math_library_analysis.json")
    if not helpers:
        print("\nWarning: math_library_analysis.json not found")
        return None
    
    print("\n=== MATH HELPERS ===")
    
    exclusive = helpers.get('exclusive_to_view_projection', [])
    print(f"Helpers exclusive to view_projection: {len(exclusive)}")
    
    for helper_info in exclusive:
        addr = helper_info.get('address', 'unknown')
        desc = helper_info.get('description', 'no description')
        print(f"  {addr}: {desc}")
    
    return helpers

def load_farobj_analysis():
    """Load farobj system analysis."""
    farobj = load_json("farobj_system_analysis.json")
    if not farobj:
        print("\nWarning: farobj_system_analysis.json not found")
        return None
    
    print("\n=== FAROBJ SYSTEM ===")
    
    functions = farobj.get('functions', [])
    print(f"Core functions: {len(functions)}")
    for func in functions:
        print(f"  {func.get('name', 'unknown')}:")
        print(f"    Address: {func.get('address', 'unknown')}")
        print(f"    Size: {func.get('size', 'unknown')} bytes")
    
    queues = farobj.get('queues', [])
    print(f"\nQueues: {len(queues)}")
    for queue in queues:
        print(f"  {queue.get('name', 'unknown')}:")
        print(f"    Address: {queue.get('address', 'unknown')}")
        print(f"    Type: {queue.get('type', 'unknown')}")
    
    return farobj

def generate_verification_checklist():
    """Generate a verification checklist from all analysis data."""
    print("\n" + "="*80)
    print("VERIFICATION CHECKLIST GENERATION")
    print("="*80 + "\n")
    
    # Load all analysis files
    seg_map = load_segment_map()
    graphics = load_graphics_analysis()
    vec3 = load_vec3_callers()
    pipeline = load_projection_pipeline()
    math = load_math_helpers()
    farobj = load_farobj_analysis()
    
    # Generate summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print("\nFiles loaded:")
    print(f"  segment_map.json: {'✓' if seg_map else '✗'}")
    print(f"  graphics_functions_analysis.json: {'✓' if graphics else '✗'}")
    print(f"  vec3_transform_callers.json: {'✓' if vec3 else '✗'}")
    print(f"  projection_pipeline_map.json: {'✓' if pipeline else '✗'}")
    print(f"  math_library_analysis.json: {'✓' if math else '✗'}")
    print(f"  farobj_system_analysis.json: {'✓' if farobj else '✗'}")
    
    print("\nNext steps:")
    print("1. Use manual_verification_guide.md to verify findings in IDA")
    print("2. Record discrepancies in verification_findings.txt")
    print("3. Update analysis files based on IDA ground truth")
    
    print("\nKey verification priorities:")
    print("  • Confirm seg020 base address = 0x1F6C0")
    print("  • Verify 10 math helpers are exclusive to view_projection")
    print("  • Confirm 10 callers of fixed_vec3_transform_es")
    print("  • Check farobj queue addresses (0x7C054 and 0x7D0C6)")
    print("  • Verify multi-entry function export accuracy")

if __name__ == "__main__":
    generate_verification_checklist()
