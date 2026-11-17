"""
Find the damage display function that shows subsystem faults on the cockpit panel.

GOAL: Find the function that:
1. Reads the entity[0xCA] bitfield
2. Maps bits to subsystem names (ENG, HYD, FUEL, etc.)
3. Displays them on the right inner view fault panel

STRATEGY:
- Look for functions that reference BOTH:
  a) Multiple subsystem name strings (ENG, HYD, FUEL, ELEC, RDR, etc.)
  b) The 0xCA status bitfield
- Look for string arrays of subsystem abbreviations
- Search for "right" + "view" or "panel" + "damage" or "fault" + "display"
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\damage_display_found.json"

def find_functions_with_multiple_subsystem_refs():
    """Find functions that reference multiple subsystem name strings."""
    subsys_names = ["ENG", "HYD", "FUEL", "ELEC", "RDR", "RADAR", "ECM", "RWR", "FCC", "GEAR", "NAV"]
    
    func_subsys_counts = {}
    
    # For each subsystem string
    for subsys in subsys_names:
        # Find the string
        ea = idc.find_text(0, idc.SEARCH_DOWN, 0, 0, subsys)
        
        while ea != idc.BADADDR:
            # Get xrefs to this string
            for xref in idautils.XrefsTo(ea, 0):
                func_ea = idc.get_func_attr(xref.frm, idc.FUNCATTR_START)
                if func_ea != idc.BADADDR:
                    func_name = idc.get_func_name(func_ea)
                    
                    if func_name not in func_subsys_counts:
                        func_subsys_counts[func_name] = {
                            'address': hex(func_ea),
                            'subsystems': set(),
                            'string_addresses': []
                        }
                    
                    func_subsys_counts[func_name]['subsystems'].add(subsys)
                    func_subsys_counts[func_name]['string_addresses'].append({
                        'subsys': subsys,
                        'string_addr': hex(ea),
                        'ref_addr': hex(xref.frm)
                    })
            
            # Find next occurrence
            ea = idc.find_text(ea + 1, idc.SEARCH_DOWN, 0, 0, subsys)
    
    # Filter to functions with 3+ subsystem references
    multi_subsys_funcs = []
    for func_name, info in func_subsys_counts.items():
        count = len(info['subsystems'])
        if count >= 3:
            multi_subsys_funcs.append({
                'function': func_name,
                'address': info['address'],
                'subsystem_count': count,
                'subsystems': sorted(list(info['subsystems'])),
                'string_refs': info['string_addresses']
            })
    
    # Sort by subsystem count
    multi_subsys_funcs.sort(key=lambda x: x['subsystem_count'], reverse=True)
    
    return multi_subsys_funcs

def find_subsystem_name_arrays():
    """Find arrays of subsystem name strings."""
    # Look for consecutive string pointers or string data
    # Pattern: "ENG", "HYD", "FUEL", "ELEC", etc. in sequence
    
    arrays_found = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Look in data segments
        if not any(x in seg_name.lower() for x in ["data", "rodata", "const"]):
            continue
        
        ea = seg_ea
        end_ea = idc.get_segm_end(seg_ea)
        
        while ea < end_ea:
            # Check if this is a string
            if idc.is_strlit(idc.get_full_flags(ea)):
                str_val = idc.get_strlit_contents(ea)
                if str_val:
                    str_decoded = str_val.decode('ascii', errors='ignore').upper()
                    
                    # Check if it's a subsystem name
                    if str_decoded in ["ENG", "HYD", "FUEL", "ELEC", "RDR", "RADAR", "ECM", "RWR", "FCC", "GEAR", "NAV", "AVION"]:
                        # Found one! Check nearby for more
                        array_start = ea
                        strings_in_array = [str_decoded]
                        
                        next_ea = ea + len(str_val) + 1
                        
                        # Check next 10 items
                        for i in range(10):
                            if next_ea >= end_ea:
                                break
                            
                            if idc.is_strlit(idc.get_full_flags(next_ea)):
                                next_str = idc.get_strlit_contents(next_ea)
                                if next_str:
                                    next_decoded = next_str.decode('ascii', errors='ignore').upper()
                                    strings_in_array.append(next_decoded)
                                    next_ea += len(next_str) + 1
                                else:
                                    break
                            else:
                                break
                        
                        if len(strings_in_array) >= 3:
                            arrays_found.append({
                                'address': hex(array_start),
                                'segment': seg_name,
                                'count': len(strings_in_array),
                                'strings': strings_in_array
                            })
                        
                        ea = next_ea
                    else:
                        ea = idc.next_head(ea, end_ea)
                else:
                    ea = idc.next_head(ea, end_ea)
            else:
                ea = idc.next_head(ea, end_ea)
    
    return arrays_found[:20]

def find_view_mode_functions():
    """Find functions related to cockpit views, especially right panel."""
    keywords = ["view", "cockpit", "panel", "right", "inner", "mfd", "display", "instrument"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    
                    # Check if this function also references 0xCA
                    has_0xca = False
                    ea = func.start_ea
                    while ea < func.end_ea:
                        disasm = idc.GetDisasm(ea)
                        if "+0CAh]" in disasm or "+0CA]" in disasm:
                            has_0xca = True
                            break
                        ea = idc.next_head(ea, func.end_ea)
                    
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": kw,
                        "accesses_0xCA": has_0xca
                    })
                    break
    
    return funcs[:30]

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete")
        
        print("\n[1] Finding functions with multiple subsystem references...")
        multi_subsys = find_functions_with_multiple_subsystem_refs()
        print(f"Found {len(multi_subsys)} functions")
        for func in multi_subsys[:5]:
            print(f"  {func['function']}: {func['subsystem_count']} subsystems - {func['subsystems']}")
        
        print("\n[2] Finding subsystem name arrays...")
        arrays = find_subsystem_name_arrays()
        print(f"Found {len(arrays)} potential arrays")
        for arr in arrays[:5]:
            print(f"  {arr['address']}: {arr['count']} strings - {arr['strings']}")
        
        print("\n[3] Finding cockpit view functions...")
        view_funcs = find_view_mode_functions()
        print(f"Found {len(view_funcs)} view-related functions")
        
        with_0xca = [f for f in view_funcs if f['accesses_0xCA']]
        print(f"  {len(with_0xca)} of them access entity[0xCA]:")
        for func in with_0xca[:5]:
            print(f"    {func['name']} @ {func['address']}")
        
        result = {
            "functions_with_multiple_subsystems": multi_subsys,
            "subsystem_name_arrays": arrays,
            "view_functions": view_funcs,
            "view_functions_with_0xCA": with_0xca
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[4] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
