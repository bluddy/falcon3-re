"""
Find F-key handlers (F5, F6, F7) for radar mode switching and R/Z key handlers.

USER CONTEXT:
- F5, F6, F7 (and more F-keys) cycle radar modes
- R = Radar on/off toggle
- Z = Lock target
- SAD and HFR appear in external view field (mode indicators)

SEARCH FOR:
1. F-key scan code handlers (F5=0x3F, F6=0x40, F7=0x41)
2. R key handler (scan code 0x13)
3. Z key handler (scan code 0x2C)
4. Radar state variable (on/off flag)
5. Mode display text in external view
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\fkey_radar_handlers.json"

# PC keyboard scan codes
SCAN_CODES = {
    'F1': 0x3B,
    'F2': 0x3C,
    'F3': 0x3D,
    'F4': 0x3E,
    'F5': 0x3F,
    'F6': 0x40,
    'F7': 0x41,
    'F8': 0x42,
    'F9': 0x43,
    'F10': 0x44,
    'R': 0x13,
    'Z': 0x2C
}

def find_scancode_handlers():
    """Find keyboard scan code comparisons (for F5, F6, F7, R, Z)."""
    
    handlers = {}
    
    for key_name, scan_code in SCAN_CODES.items():
        handlers[key_name] = []
        
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            ea = func.start_ea
            while ea < func.end_ea:
                mnem = idc.print_insn_mnem(ea)
                
                # Look for cmp with scan code
                if mnem == "cmp":
                    if idc.get_operand_type(ea, 1) == idc.o_imm:
                        value = idc.get_operand_value(ea, 1)
                        
                        if value == scan_code:
                            # Found it! Get context
                            func_name = idc.get_func_name(func_ea)
                            
                            # Get next few instructions (what happens after compare)
                            context = []
                            ctx_ea = ea
                            for i in range(10):
                                if ctx_ea >= func.end_ea:
                                    break
                                context.append(f"{ctx_ea:08X}: {idc.GetDisasm(ctx_ea)}")
                                ctx_ea = idc.next_head(ctx_ea, func.end_ea)
                            
                            handlers[key_name].append({
                                "function": func_name,
                                "address": hex(ea),
                                "scan_code": hex(scan_code),
                                "context": context
                            })
                
                ea = idc.next_head(ea, func.end_ea)
    
    # Filter out keys with no handlers found
    return {k: v for k, v in handlers.items() if v}

def find_radar_state_variables():
    """Find radar on/off state variable (toggled by R key)."""
    
    # Look for variables with "radar" in name or frequently toggled
    candidates = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        
        if not any(x in seg_name.lower() for x in ["data", "bss"]):
            continue
        
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            name = idc.get_name(head)
            if name:
                name_lower = name.lower()
                
                if any(kw in name_lower for kw in ["radar", "lock", "target", "track", "scan"]):
                    # Count XOR operations (common for toggle)
                    xor_count = 0
                    mov_count = 0
                    
                    for xref in idautils.XrefsTo(head, 0):
                        mnem = idc.print_insn_mnem(xref.frm)
                        if mnem == "xor":
                            xor_count += 1
                        elif mnem == "mov":
                            # Check if destination
                            op0 = idc.get_operand_value(xref.frm, 0)
                            if op0 == head:
                                mov_count += 1
                    
                    if xor_count > 0 or mov_count >= 2:
                        candidates.append({
                            "name": name,
                            "address": hex(head),
                            "segment": seg_name,
                            "xor_ops": xor_count,
                            "mov_ops": mov_count
                        })
    
    return candidates[:30]

def analyze_fkey_function_dispatcher():
    """Find function that dispatches F-key presses to handlers."""
    
    # Look for functions with multiple F-key comparisons in sequence
    # Pattern: cmp al, 3Fh; je f5_handler; cmp al, 40h; je f6_handler; etc.
    
    dispatchers = []
    
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        fkey_compares = []
        
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == "cmp":
                if idc.get_operand_type(ea, 1) == idc.o_imm:
                    value = idc.get_operand_value(ea, 1)
                    
                    # Check if it's an F-key scan code (0x3B-0x44)
                    if 0x3B <= value <= 0x44:
                        fkey_compares.append({
                            "offset": hex(ea - func.start_ea),
                            "address": hex(ea),
                            "scan_code": hex(value),
                            "key": f"F{value - 0x3A}",
                            "instruction": idc.GetDisasm(ea)
                        })
            
            ea = idc.next_head(ea, func.end_ea)
        
        if len(fkey_compares) >= 3:  # At least 3 F-keys
            func_name = idc.get_func_name(func_ea)
            
            dispatchers.append({
                "function": func_name,
                "address": hex(func_ea),
                "size": func.end_ea - func.start_ea,
                "fkey_count": len(fkey_compares),
                "fkeys": fkey_compares
            })
    
    # Sort by F-key count
    dispatchers.sort(key=lambda x: x['fkey_count'], reverse=True)
    
    return dispatchers[:10]

def find_external_view_text_display():
    """Find external view mode indicator display (where SAD/HFR would appear)."""
    
    # Look for "external", "view", "chase" functions that might display mode text
    keywords = ["external", "view", "chase", "camera"]
    
    funcs = []
    for func_ea in idautils.Functions():
        name = idc.get_func_name(func_ea)
        if name:
            name_lower = name.lower()
            for kw in keywords:
                if kw in name_lower:
                    func = idaapi.get_func(func_ea)
                    
                    # Look for string references in this function
                    string_refs = []
                    ea = func.start_ea
                    while ea < func.end_ea:
                        for xref in idautils.XrefsFrom(ea, 0):
                            if idc.is_strlit(idc.get_full_flags(xref.to)):
                                str_val = idc.get_strlit_contents(xref.to)
                                if str_val:
                                    string_refs.append({
                                        "offset": hex(ea - func.start_ea),
                                        "string": str_val.decode('ascii', errors='ignore')[:40]
                                    })
                        ea = idc.next_head(ea, func.end_ea)
                    
                    funcs.append({
                        "name": name,
                        "address": hex(func_ea),
                        "size": func.end_ea - func.start_ea,
                        "keyword": kw,
                        "string_refs": string_refs
                    })
                    break
    
    return funcs[:20]

def search_for_sad_hfr_in_data():
    """Search raw data segments for SAD/HFR as packed chars."""
    
    # Search for byte sequences: 'S','A','D' or 'H','F','R'
    sad_bytes = [ord('S'), ord('A'), ord('D')]
    hfr_bytes = [ord('H'), ord('F'), ord('R')]
    
    found = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        ea = seg_ea
        while ea < seg_end - 3:
            # Check for SAD
            if (idc.get_wide_byte(ea) == sad_bytes[0] and
                idc.get_wide_byte(ea + 1) == sad_bytes[1] and
                idc.get_wide_byte(ea + 2) == sad_bytes[2]):
                
                found.append({
                    "string": "SAD",
                    "address": hex(ea),
                    "segment": seg_name,
                    "bytes": [idc.get_wide_byte(ea + i) for i in range(10)]
                })
            
            # Check for HFR
            if (idc.get_wide_byte(ea) == hfr_bytes[0] and
                idc.get_wide_byte(ea + 1) == hfr_bytes[1] and
                idc.get_wide_byte(ea + 2) == hfr_bytes[2]):
                
                found.append({
                    "string": "HFR",
                    "address": hex(ea),
                    "segment": seg_name,
                    "bytes": [idc.get_wide_byte(ea + i) for i in range(10)]
                })
            
            ea += 1
    
    return found

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Finding F-key and R/Z key handlers...")
        scancode_handlers = find_scancode_handlers()
        print(f"Found handlers for {len(scancode_handlers)} keys:")
        for key, handlers in scancode_handlers.items():
            print(f"  {key}: {len(handlers)} handler(s)")
        
        print("\n[2] Finding radar state variables...")
        radar_vars = find_radar_state_variables()
        print(f"Found {len(radar_vars)} radar-related variables")
        for var in radar_vars[:5]:
            print(f"  {var['name']}: {var['xor_ops']} XOR, {var['mov_ops']} MOV")
        
        print("\n[3] Analyzing F-key dispatcher functions...")
        dispatchers = analyze_fkey_function_dispatcher()
        print(f"Found {len(dispatchers)} F-key dispatcher functions")
        for disp in dispatchers[:3]:
            print(f"  {disp['function']}: {disp['fkey_count']} F-keys")
        
        print("\n[4] Finding external view text display...")
        view_funcs = find_external_view_text_display()
        print(f"Found {len(view_funcs)} view-related functions")
        
        print("\n[5] Searching for SAD/HFR in raw data...")
        sad_hfr = search_for_sad_hfr_in_data()
        print(f"Found {len(sad_hfr)} occurrences")
        for item in sad_hfr[:5]:
            print(f"  {item['string']} @ {item['address']} in {item['segment']}")
        
        result = {
            "scancode_handlers": scancode_handlers,
            "radar_state_variables": radar_vars,
            "fkey_dispatchers": dispatchers,
            "external_view_functions": view_funcs,
            "sad_hfr_raw_search": sad_hfr,
            "summary": {
                "keys_found": list(scancode_handlers.keys()),
                "radar_vars": len(radar_vars),
                "dispatchers": len(dispatchers),
                "view_funcs": len(view_funcs),
                "sad_hfr_found": len(sad_hfr)
            }
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[6] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
