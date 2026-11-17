"""
Find tactical map object rendering functions.
Searches for functions that call draw_from_struct to identify what draws map objects.
"""

import idc
import idautils
import idaapi

def find_draw_callers():
    """Find all functions that call draw_from_struct."""
    
    # Auto-init IDA if needed
    idaapi.auto_wait()
    
    # draw_from_struct address
    draw_func = 0x02245A
    
    print("=== Functions calling draw_from_struct (0x02245A) ===\n")
    
    # Get all xrefs
    xrefs = list(idautils.XrefsTo(draw_func))
    print(f"Total xrefs: {len(xrefs)}\n")
    
    # Group by calling function
    callers = {}
    for xref in xrefs:
        func = idaapi.get_func(xref.frm)
        if func:
            fname = idc.get_func_name(func.start_ea)
            if fname not in callers:
                callers[fname] = {
                    'start': func.start_ea,
                    'size': func.end_ea - func.start_ea,
                    'calls': []
                }
            callers[fname]['calls'].append(xref.frm)
    
    # Sort by number of calls (descending)
    sorted_callers = sorted(callers.items(), 
                           key=lambda x: len(x[1]['calls']), 
                           reverse=True)
    
    print(f"=== Top 30 Callers by Call Count ===\n")
    for fname, info in sorted_callers[:30]:
        print(f"{fname}:")
        print(f"  Address: 0x{info['start']:X}")
        print(f"  Size: {info['size']} bytes")
        print(f"  Calls to draw_from_struct: {len(info['calls'])}")
        if len(info['calls']) <= 5:
            for addr in info['calls']:
                print(f"    Call at: 0x{addr:X}")
        print()

def search_for_object_keywords():
    """Search for strings related to map objects."""
    
    print("\n=== Searching for Object-Related Strings ===\n")
    
    keywords = [
        'aircraft', 'plane', 'target', 'waypoint', 'symbol', 'icon',
        'marker', 'sam', 'aaa', 'ground', 'threat', 'radar', 'enemy',
        'friendly', 'neutral', 'bullseye', 'steerpoint'
    ]
    
    for keyword in keywords:
        # Search in strings
        matches = []
        for s in idautils.Strings():
            if keyword.lower() in str(s).lower():
                matches.append((s.ea, str(s)))
        
        if matches:
            print(f"Keyword '{keyword}':")
            for ea, text in matches[:5]:  # First 5
                print(f"  0x{ea:X}: {text}")
            if len(matches) > 5:
                print(f"  ... and {len(matches)-5} more")
            print()

if __name__ == "__main__":
    find_draw_callers()
    search_for_object_keywords()
    print("\nDone!")
