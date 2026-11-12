"""
Search for overlay-related functions.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\overlay_functions.json"

def main():
    try:
        idaapi.auto_wait()
        
        # Search for functions with "overlay" in the name
        overlay_funcs = []
        
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            if "overlay" in name.lower() or "ovl" in name.lower() or "swap" in name.lower():
                func = idaapi.get_func(func_ea)
                overlay_funcs.append({
                    "address": hex(func_ea),
                    "name": name,
                    "size": func.end_ea - func.start_ea if func else 0
                })
        
        result = {
            "count": len(overlay_funcs),
            "functions": overlay_funcs[:50]  # First 50
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
