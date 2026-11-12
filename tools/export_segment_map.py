"""
Enhanced IDA export script to capture segment information and multi-entry points.

This script exports:
1. Segment definitions (name, start_ea, end_ea, selector, class)
2. Multi-entry functions (xrefs that land mid-function)
3. Enhanced function info with segment:offset addressing

Run in IDA via File > Script file or idat.exe -A -S"export_segment_map.py" FALCONCD.EXE.i64
"""

import idaapi
import idautils
import idc
import json
from collections import defaultdict

def get_segment_map():
    """Export all segment definitions."""
    segments = []
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if seg:
            seg_info = {
                'name': idaapi.get_segm_name(seg),
                'start_ea': seg.start_ea,
                'end_ea': seg.end_ea,
                'selector': seg.sel,
                'class': idaapi.get_segm_class(seg),
                'type': seg.type,
                'bitness': seg.bitness,
            }
            segments.append(seg_info)
    return segments

def linear_to_segoff(ea):
    """Convert linear address to segment:offset string."""
    seg = idaapi.getseg(ea)
    if seg:
        seg_name = idaapi.get_segm_name(seg)
        offset = ea - seg.start_ea
        return f"{seg_name}:{offset:04X}"
    return f"0x{ea:X}"

def find_multi_entry_functions():
    """
    Find functions with multiple entry points by detecting xrefs
    that land mid-function (not at function start).
    """
    multi_entry = defaultdict(list)
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
            
        func_name = idc.get_func_name(func_ea)
        func_start = func.start_ea
        func_end = func.end_ea
        
        # Check all addresses in the function
        ea = func_start
        while ea < func_end:
            # Skip the main entry point
            if ea != func_start:
                # Check for code xrefs to this address
                xrefs = list(idautils.CodeRefsTo(ea, 0))
                if xrefs:
                    # Filter out fall-through refs (sequential flow)
                    non_fallthrough = []
                    for ref in xrefs:
                        # Check if this is a call or jump (not fall-through)
                        if ref + idc.get_item_size(ref) != ea:
                            non_fallthrough.append(ref)
                    
                    if non_fallthrough:
                        entry_info = {
                            'address': ea,
                            'segoff': linear_to_segoff(ea),
                            'offset_from_start': ea - func_start,
                            'xref_count': len(non_fallthrough),
                            'xrefs_from': [{'ea': ref, 'segoff': linear_to_segoff(ref)} 
                                          for ref in non_fallthrough[:10]]  # Limit to 10
                        }
                        multi_entry[func_name].append(entry_info)
            
            ea = idc.next_head(ea, func_end)
    
    return dict(multi_entry)

def export_enhanced_functions():
    """Export function information with segment addressing."""
    functions = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Count total xrefs to this function (at entry point)
        xrefs_to_entry = len(list(idautils.CodeRefsTo(func_ea, 0)))
        
        func_info = {
            'name': func_name,
            'start_ea': func.start_ea,
            'end_ea': func.end_ea,
            'size': func.end_ea - func.start_ea,
            'segoff': linear_to_segoff(func.start_ea),
            'xrefs_to_entry': xrefs_to_entry,
        }
        
        functions.append(func_info)
    
    return functions

def main():
    print("=" * 60)
    print("Enhanced Segment Export")
    print("=" * 60)
    
    try:
        # Wait for autoanalysis to complete
        print("\nWaiting for autoanalysis...")
        idaapi.auto_wait()
        
        # Export segments
        print("\n[1/3] Exporting segment map...")
        segments = get_segment_map()
        print(f"  Found {len(segments)} segments")
        
        # Find multi-entry functions
        print("\n[2/3] Finding multi-entry functions...")
        multi_entry = find_multi_entry_functions()
        print(f"  Found {len(multi_entry)} functions with secondary entry points")
        
        # Export enhanced function info
        print("\n[3/3] Exporting enhanced function information...")
        functions = export_enhanced_functions()
        print(f"  Exported {len(functions)} functions")
        
        # Prepare output
        output = {
            'segments': segments,
            'multi_entry_functions': multi_entry,
            'functions': functions,
            'summary': {
                'total_segments': len(segments),
                'total_functions': len(functions),
                'multi_entry_count': len(multi_entry),
                'total_secondary_entries': sum(len(entries) for entries in multi_entry.values())
            }
        }
        
        # Determine output path
        # First try idc.ARGV[1], then try a path relative to IDB
        output_path = None
        if len(idc.ARGV) > 1:
            output_path = idc.ARGV[1]
        else:
            # Use path relative to IDB location
            idb_path = idc.get_idb_path()
            import os
            idb_dir = os.path.dirname(idb_path)
            output_path = os.path.join(idb_dir, 'segment_map.json')
        
        print(f"\nWriting to: {output_path}")
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Export complete: {output_path}")
        print(f"  - {output['summary']['total_segments']} segments")
        print(f"  - {output['summary']['total_functions']} functions")
        print(f"  - {output['summary']['multi_entry_count']} multi-entry functions")
        print(f"  - {output['summary']['total_secondary_entries']} secondary entry points")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    idc.qexit(0 if success else 1)  # Exit IDA with status code
