#!/usr/bin/env python3
"""
Extract all briefing/mission related strings from the entire database.

Comprehensive string search for mission briefing UI elements.
"""

import idc
import idaapi
import idautils
import json
import re

def categorize_string(string):
    """Categorize a string based on content."""
    s_upper = string.upper()
    
    # Mission types
    if any(kw in s_upper for kw in ['CAP', 'STRIKE', 'CAS', 'SEAD', 'INTERCEPT', 'ESCORT', 'RECON']):
        return 'mission_type'
    
    # Flight parameters
    if any(kw in s_upper for kw in ['ALTITUDE', 'SPEED', 'HEADING', 'DISTANCE', 'FUEL', 'TIME']):
        return 'flight_param'
    
    # Navigation
    if any(kw in s_upper for kw in ['WAYPOINT', 'INGRESS', 'EGRESS', 'IP', 'TARGET', 'BASE', 'AIRFIELD']):
        return 'navigation'
    
    # Mission info
    if any(kw in s_upper for kw in ['MISSION', 'OBJECTIVE', 'BRIEFING', 'DEBRIEF', 'INTEL']):
        return 'mission_info'
    
    # Pilot/Aircraft
    if any(kw in s_upper for kw in ['PILOT', 'AIRCRAFT', 'FLIGHT', 'LOADOUT', 'WEAPONS', 'STORES']):
        return 'pilot_aircraft'
    
    # Enemy/Threat
    if any(kw in s_upper for kw in ['ENEMY', 'THREAT', 'SAM', 'AAA', 'BANDIT', 'BOGEY', 'HOSTILE']):
        return 'threat'
    
    # Weather/Environment
    if any(kw in s_upper for kw in ['WEATHER', 'WIND', 'VISIBILITY', 'CLOUD', 'CEILING', 'TEMPERATURE']):
        return 'weather'
    
    # Results/Statistics
    if any(kw in s_upper for kw in ['SCORE', 'KILL', 'LOSS', 'DAMAGE', 'SUCCESS', 'FAIL', 'RESULT']):
        return 'results'
    
    # UI elements
    if any(kw in s_upper for kw in ['CONTINUE', 'CANCEL', 'OK', 'DONE', 'BACK', 'NEXT', 'MENU']):
        return 'ui_control'
    
    # Map/Display
    if any(kw in s_upper for kw in ['MAP', 'DISPLAY', 'ZOOM', 'VIEW', 'SHOW', 'HIDE']):
        return 'display'
    
    return 'other'

def find_all_strings():
    """Find all strings in the database."""
    all_strings = []
    
    print("[*] Scanning all segments for strings...")
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            str_type = idc.get_str_type(ea)
            if str_type is not None:
                string_val = idc.get_strlit_contents(ea)
                if string_val:
                    try:
                        string_text = string_val.decode('ascii', errors='ignore')
                        
                        # Skip very short or very long strings
                        if 3 <= len(string_text) <= 100:
                            # Get xrefs
                            xrefs = list(idautils.XrefsTo(ea))
                            
                            all_strings.append({
                                'string': string_text,
                                'addr': hex(ea),
                                'segment': seg_name,
                                'xref_count': len(xrefs),
                                'category': categorize_string(string_text)
                            })
                    except:
                        pass
            
            ea = idc.next_head(ea, seg_end)
    
    return all_strings

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("COMPREHENSIVE BRIEFING STRING EXTRACTION")
    print("="*80)
    print()
    
    # Find all strings
    all_strings = find_all_strings()
    
    print(f"[+] Found {len(all_strings)} total strings")
    print()
    
    # Filter for mission/briefing related
    mission_related = [s for s in all_strings if s['category'] != 'other']
    
    print(f"[+] Found {len(mission_related)} mission/briefing related strings")
    print()
    
    # Group by category
    by_category = {}
    for s in mission_related:
        cat = s['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(s)
    
    # Print by category
    for category in sorted(by_category.keys()):
        strings = by_category[category]
        print(f"\n{'='*80}")
        print(f"{category.upper().replace('_', ' ')} ({len(strings)} strings)")
        print('='*80)
        
        # Sort by xref count (most referenced first)
        for s in sorted(strings, key=lambda x: x['xref_count'], reverse=True)[:30]:
            print(f"  [{s['xref_count']:3d} refs] \"{s['string']}\"")
            if s['xref_count'] == 0:
                print(f"             (at {s['addr']}, segment {s['segment']}, UNUSED)")
    
    print()
    
    # Look for specific patterns
    print("\n" + "="*80)
    print("PATTERN ANALYSIS")
    print("="*80)
    print()
    
    # Menu item patterns (Key + code + label)
    menu_items = []
    for s in all_strings:
        # Look for pattern like "j0.`LABEL" or "E1.`LABEL"
        if re.match(r'^[A-Za-z*][0-9\-]\.', s['string']):
            menu_items.append(s)
    
    print(f"[*] Found {len(menu_items)} menu item strings (pattern: [Key][Code].`[Label]):")
    for item in sorted(menu_items, key=lambda x: x['string']):
        print(f"    \"{item['string']}\" ({item['xref_count']} refs)")
    print()
    
    # Numeric patterns (coordinates, altitudes, speeds)
    numeric_strings = []
    for s in all_strings:
        # Look for strings with numbers
        if re.search(r'\d{3,}', s['string']) and s['category'] != 'other':
            numeric_strings.append(s)
    
    if numeric_strings:
        print(f"[*] Found {len(numeric_strings)} strings with numeric values:")
        for item in numeric_strings[:20]:
            print(f"    \"{item['string']}\" (category: {item['category']})")
        print()
    
    # Find R29 segment (likely string data segment based on R45 analysis)
    print("\n" + "="*80)
    print("R29 SEGMENT ANALYSIS (String Segment)")
    print("="*80)
    print()
    
    r29_strings = [s for s in all_strings if 'R29' in s['segment']]
    print(f"[+] Found {len(r29_strings)} strings in R29 segments")
    
    # Categorize R29 strings
    r29_by_cat = {}
    for s in r29_strings:
        cat = s['category']
        if cat not in r29_by_cat:
            r29_by_cat[cat] = []
        r29_by_cat[cat].append(s)
    
    print("\nR29 strings by category:")
    for cat in sorted(r29_by_cat.keys()):
        print(f"  {cat}: {len(r29_by_cat[cat])} strings")
    print()
    
    # Save results
    result = {
        'total_strings': len(all_strings),
        'mission_related': len(mission_related),
        'by_category': {cat: len(strings) for cat, strings in by_category.items()},
        'categories': {
            cat: [
                {
                    'string': s['string'],
                    'addr': s['addr'],
                    'segment': s['segment'],
                    'xref_count': s['xref_count']
                }
                for s in sorted(strings, key=lambda x: x['xref_count'], reverse=True)
            ]
            for cat, strings in by_category.items()
        },
        'menu_items': [
            {
                'string': s['string'],
                'addr': s['addr'],
                'xref_count': s['xref_count']
            }
            for s in menu_items
        ],
        'r29_strings': len(r29_strings)
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\briefing_strings_complete.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("[+] Complete results saved to analysis/briefing_strings_complete.json")
    
    # Also save a human-readable version
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\briefing_strings_complete.txt', 'w') as f:
        f.write("FALCON 3.0 BRIEFING STRINGS - COMPLETE EXTRACTION\n")
        f.write("="*80 + "\n\n")
        
        for category in sorted(by_category.keys()):
            strings = by_category[category]
            f.write(f"\n{category.upper().replace('_', ' ')} ({len(strings)} strings)\n")
            f.write("="*80 + "\n")
            
            for s in sorted(strings, key=lambda x: x['xref_count'], reverse=True):
                f.write(f"[{s['xref_count']:3d}] {s['string']}\n")
                if s['xref_count'] > 0:
                    f.write(f"      Addr: {s['addr']}, Segment: {s['segment']}\n")
        
        f.write(f"\n\nMENU ITEMS ({len(menu_items)} items)\n")
        f.write("="*80 + "\n")
        for item in sorted(menu_items, key=lambda x: x['string']):
            f.write(f"{item['string']}\n")
    
    print("[+] Human-readable version saved to analysis/briefing_strings_complete.txt")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
