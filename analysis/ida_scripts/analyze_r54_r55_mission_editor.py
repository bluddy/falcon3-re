"""
Analyze R54/R55/R56 overlays for mission editing functionality
These overlays handle campaign and mission management
"""

import idaapi
import idc
import idautils
import json

def analyze_r5x_overlay(seg_name):
    """Analyze a specific R5X overlay segment"""
    
    # Find segment
    seg = idaapi.get_segm_by_name(seg_name)
    if not seg:
        print(f"Segment {seg_name} not found")
        return None
    
    print(f"\n{'=' * 80}")
    print(f"ANALYZING SEGMENT: {seg_name}")
    print(f"Address Range: 0x{seg.start_ea:08X} - 0x{seg.end_ea:08X}")
    print(f"Size: {seg.end_ea - seg.start_ea} bytes")
    print(f"{'=' * 80}\n")
    
    result = {
        'segment': seg_name,
        'start': seg.start_ea,
        'end': seg.end_ea,
        'size': seg.end_ea - seg.start_ea,
        'functions': [],
        'strings': [],
        'data_refs': {}
    }
    
    # Find all functions in segment
    func_count = 0
    for func_ea in idautils.Functions(seg.start_ea, seg.end_ea):
        func_name = idc.get_func_name(func_ea)
        func = idaapi.get_func(func_ea)
        
        if func:
            result['functions'].append({
                'name': func_name,
                'addr': func_ea,
                'size': func.end_ea - func_ea
            })
            func_count += 1
    
    print(f"Found {func_count} functions")
    
    # Find strings in segment
    for string_ea in idautils.Strings():
        if seg.start_ea <= string_ea.ea < seg.end_ea:
            result['strings'].append({
                'addr': string_ea.ea,
                'string': str(string_ea)
            })
    
    print(f"Found {len(result['strings'])} strings")
    
    # Look for references to mission/waypoint structures
    # Search for known pointers
    known_ptrs = {
        'dword_79D3E': 0x79D3E,  # Mission slot array
        'dword_79E3A': 0x79E3A,  # Mission context
        'dword_79BEC': 0x79BEC,  # Flight array
        'dword_79EDE': 0x79EDE,  # Unknown mission data
    }
    
    for ptr_name, ptr_addr in known_ptrs.items():
        refs = []
        for xref in idautils.XrefsTo(ptr_addr):
            if seg.start_ea <= xref.frm < seg.end_ea:
                func = idaapi.get_func(xref.frm)
                refs.append({
                    'addr': xref.frm,
                    'func': idc.get_func_name(func.start_ea) if func else None,
                    'disasm': idc.GetDisasm(xref.frm)
                })
        
        if refs:
            result['data_refs'][ptr_name] = refs
            print(f"  {ptr_name}: {len(refs)} references")
    
    return result

def search_mission_edit_keywords():
    """Search for keywords in all R5X segments"""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR MISSION EDITING KEYWORDS IN R5X SEGMENTS")
    print("=" * 80 + "\n")
    
    # Keywords to search
    keywords = [
        b'WAYPOINT', b'STEERPOINT', b'ALTITUDE', b'SPEED',
        b'TARGET', b'TASK', b'FLIGHT', b'MISSION',
        b'ADD', b'DELETE', b'MODIFY', b'EDIT'
    ]
    
    results = {}
    
    # Search in each R5X segment
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        if seg_name and (seg_name.startswith('R54') or seg_name.startswith('R55') or seg_name.startswith('R56')):
            seg_start = idc.get_segm_start(seg_ea)
            seg_end = idc.get_segm_end(seg_ea)
            
            print(f"\nSearching {seg_name} (0x{seg_start:08X} - 0x{seg_end:08X})...")
            
            seg_results = []
            
            # Search for each keyword
            for keyword in keywords:
                ea = seg_start
                while ea < seg_end:
                    ea = idc.find_binary(ea, idc.SEARCH_DOWN | idc.SEARCH_CASE, 
                                        ' '.join(f'{b:02X}' for b in keyword))
                    if ea == idc.BADADDR or ea >= seg_end:
                        break
                    
                    # Get context
                    func = idaapi.get_func(ea)
                    func_name = idc.get_func_name(func.start_ea) if func else "No function"
                    
                    seg_results.append({
                        'addr': ea,
                        'keyword': keyword.decode('ascii'),
                        'func': func_name,
                        'func_addr': func.start_ea if func else None
                    })
                    
                    ea += 1  # Continue search
            
            if seg_results:
                results[seg_name] = seg_results
                print(f"  Found {len(seg_results)} keyword matches")
    
    return results

def main():
    print("Starting R5X mission editor analysis...")
    idaapi.auto_wait()
    
    # Analyze specific overlays
    segments_to_analyze = ['R54_5CDC', 'R55_5B45s', 'R56_5DACs']
    
    all_results = {
        'overlays': {},
        'keyword_search': {}
    }
    
    for seg_name in segments_to_analyze:
        result = analyze_r5x_overlay(seg_name)
        if result:
            all_results['overlays'][seg_name] = result
    
    # Search for keywords
    keyword_results = search_mission_edit_keywords()
    all_results['keyword_search'] = keyword_results
    
    # Print summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for seg_name, data in all_results['overlays'].items():
        print(f"\n{seg_name}:")
        print(f"  Functions: {len(data['functions'])}")
        print(f"  Strings: {len(data['strings'])}")
        print(f"  Data references: {len(data['data_refs'])}")
    
    print(f"\nKeyword matches across all R5X segments:")
    total_keywords = sum(len(v) for v in keyword_results.values())
    print(f"  Total: {total_keywords} matches")
    
    for seg_name, matches in keyword_results.items():
        print(f"  {seg_name}: {len(matches)} matches")
    
    # Save results
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r5x_mission_editor_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n\nResults written to {output_path}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
