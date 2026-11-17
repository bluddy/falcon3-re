"""
Find ALL 2-4 character strings that could be mode indicators.

Strategy: Exhaustive search for short strings, then filter by:
1. All uppercase or mixed case
2. Referenced by code
3. Near radar/view functions
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\all_short_strings.json"

def find_all_short_strings():
    """Find all 2-4 character strings."""
    
    short_strings = []
    
    for s in idautils.Strings():
        str_val = str(s)
        
        # Only 2-4 characters
        if 2 <= len(str_val) <= 4:
            # Must have at least one letter
            if any(c.isalpha() for c in str_val):
                xrefs = list(idautils.XrefsTo(s.ea, 0))
                
                if xrefs:  # Must be referenced
                    short_strings.append({
                        "string": str_val,
                        "length": len(str_val),
                        "address": hex(s.ea),
                        "xref_count": len(xrefs),
                        "used_by": [idc.get_func_name(x.frm) for x in xrefs[:5] if idc.get_func_name(x.frm)]
                    })
    
    # Sort by length then alphabetically
    short_strings.sort(key=lambda x: (x['length'], x['string']))
    
    return short_strings

def search_strings_near_fkey_handlers():
    """Find strings referenced near F5/F6/F7 scan code comparisons."""
    
    fkey_scancodes = [0x3F, 0x40, 0x41]  # F5, F6, F7
    nearby_strings = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        # Find F-key comparisons in this function
        fkey_locations = []
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == "cmp":
                if idc.get_operand_type(ea, 1) == idc.o_imm:
                    value = idc.get_operand_value(ea, 1)
                    if value in fkey_scancodes:
                        fkey_locations.append(ea)
            ea = idc.next_head(ea, func.end_ea)
        
        # If this function has F-key handlers, find strings
        if fkey_locations:
            func_name = idc.get_func_name(func_ea)
            
            # Look for string references in this function
            ea = func.start_ea
            while ea < func.end_ea:
                for xref in idautils.XrefsFrom(ea, 0):
                    if idc.is_strlit(idc.get_full_flags(xref.to)):
                        str_val = idc.get_strlit_contents(xref.to)
                        if str_val:
                            str_decoded = str_val.decode('ascii', errors='ignore')
                            
                            nearby_strings.append({
                                "function": func_name,
                                "string": str_decoded[:40],
                                "string_addr": hex(xref.to),
                                "ref_addr": hex(ea),
                                "fkey_count": len(fkey_locations)
                            })
                ea = idc.next_head(ea, func.end_ea)
    
    return nearby_strings

def find_mode_indicator_display():
    """Find text display functions that might show mode indicators."""
    
    # Look for small text rendering (3-4 chars for SAD/HFR)
    # Pattern: function that takes coordinates + short string
    
    display_funcs = []
    
    # Search for functions with "print", "text", "draw", "label"
    keywords = ["print", "text", "draw", "label", "indicator", "display"]
    
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    
                    # Check if function is small (indicator display should be small)
                    size = func.end_ea - func.start_ea
                    if size < 200:
                        # Get all callers
                        callers = []
                        for xref in idautils.XrefsTo(func_ea, 0):
                            caller_name = idc.get_func_name(xref.frm)
                            if caller_name:
                                callers.append(caller_name)
                        
                        display_funcs.append({
                            "name": name,
                            "address": hex(func_ea),
                            "size": size,
                            "keyword": kw,
                            "caller_count": len(callers),
                            "callers": list(set(callers))[:10]
                        })
                    break
    
    # Sort by caller count (popular functions)
    display_funcs.sort(key=lambda x: x['caller_count'], reverse=True)
    
    return display_funcs[:20]

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Finding ALL 2-4 character strings...")
        short_strings = find_all_short_strings()
        print(f"Found {len(short_strings)} short strings")
        
        # Show 3-letter strings (SAD/HFR candidates)
        three_letter = [s for s in short_strings if s['length'] == 3]
        print(f"\n{len(three_letter)} three-letter strings:")
        for s in three_letter[:30]:
            print(f"  '{s['string']}' @ {s['address']} ({s['xref_count']} refs)")
        
        print("\n[2] Finding strings near F5/F6/F7 handlers...")
        fkey_strings = search_strings_near_fkey_handlers()
        print(f"Found {len(fkey_strings)} strings near F-key handlers")
        for s in fkey_strings[:10]:
            print(f"  '{s['string']}' in {s['function']}")
        
        print("\n[3] Finding mode indicator display functions...")
        display_funcs = find_mode_indicator_display()
        print(f"Found {len(display_funcs)} display functions")
        for func in display_funcs[:5]:
            print(f"  {func['name']}: {func['caller_count']} callers")
        
        result = {
            "all_short_strings": short_strings,
            "three_letter_strings": three_letter,
            "fkey_nearby_strings": fkey_strings,
            "mode_display_functions": display_funcs,
            "summary": {
                "total_short": len(short_strings),
                "three_letter": len(three_letter),
                "fkey_strings": len(fkey_strings),
                "display_funcs": len(display_funcs)
            }
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
