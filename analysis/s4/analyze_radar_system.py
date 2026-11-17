"""
Analyze Falcon 3.0 radar/avionics system.

USER CONTEXT:
- At least 3 radar modes (2 unrealistic, 1 realistic)
- Realistic mode has submodes
- Strings include: SAD, HFR

SEARCH FOR:
1. Radar mode strings (SAD, HFR, etc.)
2. Radar mode switching logic
3. Submode implementations
4. Radar display functions
5. Target tracking/lock functions

F-16 Radar Background:
- APG-66 radar in F-16A/C
- Modes: ACM (dogfight), RWS (range-while-search), TWS (track-while-scan)
- Real modes: RWS, TWS, VS (velocity search)
- Arcade modes: All-aspect, beyond-visual-range locks
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\radar_system_analysis.json"

def find_radar_mode_strings():
    """Find radar mode strings (SAD, HFR, etc.)."""
    
    # Known radar/avionics terms
    search_terms = [
        "SAD", "HFR",  # From user
        "RWS", "TWS", "ACM", "VS",  # Real F-16 modes
        "RADAR", "TRACK", "LOCK", "SCAN",
        "STT", "SAM", "SLAVE", "BORE",  # More F-16 terms
        "RANGE", "AZIMUTH", "ELEVATION",
        "FCR", "FCM"  # Fire control
    ]
    
    found_strings = {}
    
    for term in search_terms:
        found_strings[term] = []
        
        # Search through all strings
        for s in idautils.Strings():
            str_val = str(s)
            if term.upper() in str_val.upper():
                # Get xrefs to this string
                xrefs = list(idautils.XrefsTo(s.ea, 0))
                
                found_strings[term].append({
                    "address": hex(s.ea),
                    "string": str_val[:80],
                    "xref_count": len(xrefs),
                    "used_by": [idc.get_func_name(x.frm) for x in xrefs[:5] if idc.get_func_name(x.frm)]
                })
    
    # Filter out empty results
    return {k: v for k, v in found_strings.items() if v}

def find_radar_functions():
    """Find radar-related functions."""
    
    keywords = ["radar", "track", "lock", "scan", "fcr", "target", "aim", "acm", "rws", "tws"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": kw
                    })
                    break
    
    return funcs

def find_mode_switching_logic():
    """Find radar mode switching logic (likely keyboard handlers or menu selections)."""
    
    # Look for functions that handle mode selection
    # Typically: compare/switch statements with 2-4 mode values
    
    mode_switchers = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        func_name = idc.get_func_name(func_ea)
        
        # Look for switch/jump tables (common for mode selection)
        ea = func.start_ea
        cmp_count = 0
        je_count = 0
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == "cmp":
                cmp_count += 1
            elif mnem in ["je", "jz", "jne", "jnz", "ja", "jb", "jg", "jl"]:
                je_count += 1
            
            ea = idc.next_head(ea, func.end_ea)
        
        # Functions with multiple comparisons and jumps likely handle mode selection
        if cmp_count >= 3 and je_count >= 3:
            mode_switchers.append({
                "function": func_name,
                "address": hex(func_ea),
                "size": func.end_ea - func.start_ea,
                "cmp_count": cmp_count,
                "jump_count": je_count
            })
    
    # Sort by cmp count (more comparisons = more modes)
    mode_switchers.sort(key=lambda x: x['cmp_count'], reverse=True)
    
    return mode_switchers[:20]

def find_radar_display_functions():
    """Find radar display/HUD functions."""
    
    # From previous analysis, we know HUD functions
    # Look for radar-specific display
    
    keywords = ["radar", "scope", "display", "indicator", "symbology", "reticle", "pipper"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": kw
                    })
                    break
    
    return funcs

def find_target_tracking_structures():
    """Find target tracking data structures."""
    
    # Look for arrays/tables that might store target data
    # Typically in data segment
    
    tracking_vars = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        # Focus on data segments
        if not any(x in seg_name.lower() for x in ["data", "bss"]):
            continue
        
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            name = idc.get_name(head)
            if name:
                name_lower = name.lower()
                
                # Look for target/track/lock related variables
                if any(kw in name_lower for kw in ["target", "track", "lock", "radar", "aim"]):
                    if idc.is_data(idc.get_full_flags(head)):
                        tracking_vars.append({
                            "name": name,
                            "address": hex(head),
                            "segment": seg_name,
                            "size": idc.get_item_size(head)
                        })
    
    return tracking_vars[:30]

def analyze_hud_mode_indicators():
    """Find HUD mode indicator text (displayed mode name on screen)."""
    
    # Look for short strings (3-4 chars) that could be mode indicators
    # SAD, HFR, RWS, TWS, ACM, etc.
    
    mode_indicators = []
    
    for s in idautils.Strings():
        str_val = str(s)
        
        # Look for short uppercase strings (likely mode abbreviations)
        if len(str_val) >= 2 and len(str_val) <= 5:
            if str_val.isupper() or str_val.upper() in ["SAD", "HFR", "RWS", "TWS", "ACM", "VS", "STT"]:
                xrefs = list(idautils.XrefsTo(s.ea, 0))
                
                if xrefs:  # Only include if referenced
                    mode_indicators.append({
                        "address": hex(s.ea),
                        "string": str_val,
                        "length": len(str_val),
                        "xref_count": len(xrefs),
                        "used_by": [idc.get_func_name(x.frm) for x in xrefs[:3] if idc.get_func_name(x.frm)]
                    })
    
    return mode_indicators[:50]

def find_key_handlers():
    """Find keyboard handler functions (mode switching via keys)."""
    
    # Look for functions that handle specific keys
    # F-16 radar modes typically on numbered keys or function keys
    
    keywords = ["key", "input", "handler", "event", "press", "button"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea if func else 0,
                        "keyword": kw
                    })
                    break
    
    return funcs[:30]

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Finding radar mode strings (SAD, HFR, etc.)...")
        mode_strings = find_radar_mode_strings()
        print(f"Found strings for {len(mode_strings)} terms:")
        for term, occurrences in mode_strings.items():
            print(f"  {term}: {len(occurrences)} occurrences")
        
        print("\n[2] Finding radar-related functions...")
        radar_funcs = find_radar_functions()
        print(f"Found {len(radar_funcs)} radar functions")
        for func in radar_funcs[:5]:
            print(f"  {func['name']} @ {func['address']}")
        
        print("\n[3] Finding mode switching logic...")
        mode_switchers = find_mode_switching_logic()
        print(f"Found {len(mode_switchers)} potential mode switch functions")
        for func in mode_switchers[:5]:
            print(f"  {func['function']}: {func['cmp_count']} compares, {func['jump_count']} jumps")
        
        print("\n[4] Finding radar display functions...")
        display_funcs = find_radar_display_functions()
        print(f"Found {len(display_funcs)} display functions")
        
        print("\n[5] Finding target tracking structures...")
        tracking_vars = find_target_tracking_structures()
        print(f"Found {len(tracking_vars)} tracking variables")
        
        print("\n[6] Finding HUD mode indicators...")
        indicators = analyze_hud_mode_indicators()
        print(f"Found {len(indicators)} potential mode indicator strings")
        
        print("\n[7] Finding keyboard handlers...")
        key_handlers = find_key_handlers()
        print(f"Found {len(key_handlers)} keyboard handler functions")
        
        result = {
            "radar_mode_strings": mode_strings,
            "radar_functions": radar_funcs,
            "mode_switching_functions": mode_switchers,
            "radar_display_functions": display_funcs,
            "target_tracking_variables": tracking_vars,
            "hud_mode_indicators": indicators,
            "keyboard_handlers": key_handlers,
            "summary": {
                "mode_string_terms": len(mode_strings),
                "radar_functions": len(radar_funcs),
                "mode_switchers": len(mode_switchers),
                "display_functions": len(display_funcs),
                "tracking_vars": len(tracking_vars),
                "mode_indicators": len(indicators),
                "key_handlers": len(key_handlers)
            }
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[8] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
