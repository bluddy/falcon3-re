"""
Find mission editing UI strings and related overlays
Look for: waypoint, altitude, task, flight, mission editor, etc.
"""

import idaapi
import idc
import idautils
import json

def find_mission_edit_strings():
    """Find strings related to mission editing"""
    
    search_terms = [
        'waypoint', 'WAYPOINT',
        'altitude', 'ALTITUDE', 'HEIGHT',
        'task', 'TASK', 'MISSION',
        'flight', 'FLIGHT',
        'plane', 'PLANE', 'AIRCRAFT',
        'edit', 'EDIT', 'MODIFY',
        'add', 'ADD', 'DELETE', 'REMOVE',
        'coordinate', 'COORDINATE',
        'target', 'TARGET',
        'objective', 'OBJECTIVE',
        'route', 'ROUTE', 'PATH',
        'steerpoint', 'STEERPOINT',
        'navigation', 'NAV'
    ]
    
    results = {
        'strings': [],
        'by_term': {}
    }
    
    print("Searching for mission editing strings...")
    print("=" * 80)
    
    # Search through all strings in database
    for string_addr in idautils.Strings():
        str_val = str(string_addr)
        str_addr = string_addr.ea
        
        # Check if any search term appears
        for term in search_terms:
            if term.lower() in str_val.lower():
                # Get cross-references
                xrefs = []
                for xref in idautils.XrefsTo(str_addr):
                    func = idaapi.get_func(xref.frm)
                    if func:
                        func_name = idc.get_func_name(func.start_ea)
                        xrefs.append({
                            'addr': xref.frm,
                            'func': func_name,
                            'func_addr': func.start_ea
                        })
                
                entry = {
                    'addr': str_addr,
                    'string': str_val,
                    'term': term,
                    'xrefs': xrefs
                }
                
                results['strings'].append(entry)
                
                if term not in results['by_term']:
                    results['by_term'][term] = []
                results['by_term'][term].append(entry)
                
                break  # Only count once per string
    
    print(f"\nFound {len(results['strings'])} mission editing strings")
    
    # Show summary by term
    print("\nSTRINGS BY SEARCH TERM:")
    print("-" * 80)
    for term, entries in sorted(results['by_term'].items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{term:20s}: {len(entries):3d} strings")
    
    print("\n\nTOP MISSION EDITING STRINGS:")
    print("-" * 80)
    
    # Show top strings with most references
    sorted_strings = sorted(results['strings'], key=lambda x: len(x['xrefs']), reverse=True)
    
    for entry in sorted_strings[:30]:
        print(f"\n0x{entry['addr']:06X}: \"{entry['string']}\"")
        print(f"  Term: {entry['term']}, References: {len(entry['xrefs'])}")
        
        if entry['xrefs']:
            # Group by function
            funcs = {}
            for xref in entry['xrefs']:
                func_name = xref['func']
                if func_name not in funcs:
                    funcs[func_name] = []
                funcs[func_name].append(xref['addr'])
            
            for func_name, addrs in list(funcs.items())[:5]:  # Top 5 functions
                print(f"    {func_name} @ 0x{addrs[0]:06X} ({len(addrs)} ref(s))")
    
    return results

def find_mission_edit_overlays():
    """Find overlay segments related to mission editing"""
    
    print("\n\n" + "=" * 80)
    print("MISSION EDITING OVERLAYS")
    print("=" * 80)
    
    overlays = []
    
    # Search for R5X overlays (R50-R59 likely candidates)
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Look for R5X segments (mission/campaign management overlays)
        if seg_name and seg_name.startswith('R5'):
            seg_start = idc.get_segm_start(seg_ea)
            seg_end = idc.get_segm_end(seg_ea)
            seg_size = seg_end - seg_start
            
            overlays.append({
                'name': seg_name,
                'start': seg_start,
                'end': seg_end,
                'size': seg_size
            })
    
    # Sort by size (larger overlays likely more complex)
    overlays.sort(key=lambda x: x['size'], reverse=True)
    
    print("\nR5X OVERLAY SEGMENTS:")
    print(f"{'Segment':<20} {'Start':>10} {'End':>10} {'Size':>10}")
    print("-" * 60)
    
    for ov in overlays:
        print(f"{ov['name']:<20} 0x{ov['start']:08X} 0x{ov['end']:08X} {ov['size']:>8} bytes")
    
    return overlays

def main():
    print("Starting mission editing code search...")
    idaapi.auto_wait()
    
    results = find_mission_edit_strings()
    overlays = find_mission_edit_overlays()
    
    output_data = {
        'strings': results,
        'overlays': overlays
    }
    
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\mission_edit_findings.json'
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n\nResults written to {output_path}")
    print(f"Total strings: {len(results['strings'])}")
    print(f"Total overlays: {len(overlays)}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
