"""
Find functions that call graphics_line_draw_bresenham.
This should reveal what draws lines on the tactical map.
"""

import idc
import idautils
import idaapi
import json
from pathlib import Path

def main():
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # graphics_line_draw_bresenham address
    line_draw_func = 0x028B08
    
    print(f"=== Analyzing callers of graphics_line_draw_bresenham (0x{line_draw_func:X}) ===\n")
    
    # Get all xrefs
    xrefs = list(idautils.XrefsTo(line_draw_func))
    print(f"Total xrefs: {len(xrefs)}")
    
    # Group by calling function
    callers = {}
    for xref in xrefs:
        func = idaapi.get_func(xref.frm)
        if func:
            fname = idc.get_func_name(func.start_ea)
            if fname not in callers:
                callers[fname] = {
                    'start': func.start_ea,
                    'end': func.end_ea,
                    'size': func.end_ea - func.start_ea,
                    'calls': []
                }
            callers[fname]['calls'].append(xref.frm)
    
    # Sort by number of calls
    sorted_callers = sorted(callers.items(), 
                           key=lambda x: len(x[1]['calls']), 
                           reverse=True)
    
    # Format results
    results = {
        'graphics_line_draw_bresenham': {
            'address': hex(line_draw_func),
            'total_xrefs': len(xrefs),
            'callers': []
        }
    }
    
    for fname, info in sorted_callers:  # All callers
        caller_data = {
            'name': fname,
            'address': hex(info['start']),
            'size': info['size'],
            'call_count': len(info['calls']),
            'call_sites': [hex(addr) for addr in info['calls'][:10]]  # First 10
        }
        results['graphics_line_draw_bresenham']['callers'].append(caller_data)
        
        print(f"{fname}: {len(info['calls'])} calls at 0x{info['start']:X} ({info['size']} bytes)")
    
    # Save results
    output_path = Path(__file__).parent / "line_draw_callers.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
