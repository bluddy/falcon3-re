"""
Test string search functionality to debug find_damage_display.py
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\test_string_search_result.json"

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete")
        
        print("\nSearching for 'ENG' string...")
        
        # Method 1: Using idc.find_text
        ea = idc.find_text(0, idc.SEARCH_DOWN, 0, 0, "ENG")
        print(f"find_text result: {hex(ea) if ea != idc.BADADDR else 'NOT FOUND'}")
        
        # Method 2: Using idautils.Strings()
        eng_strings = []
        for s in idautils.Strings():
            str_val = str(s)
            if "ENG" in str_val.upper():
                eng_strings.append({
                    'address': hex(s.ea),
                    'string': str_val[:50]
                })
                if len(eng_strings) >= 10:
                    break
        
        print(f"\nFound {len(eng_strings)} strings containing 'ENG' via Strings():")
        for s in eng_strings[:5]:
            print(f"  {s['address']}: {s['string']}")
        
        result = {
            "find_text_result": hex(ea) if ea != idc.BADADDR else None,
            "strings_found": eng_strings
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
