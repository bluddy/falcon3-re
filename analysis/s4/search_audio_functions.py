"""
Search for audio/sound functions.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\audio_functions.json"

def main():
    try:
        idaapi.auto_wait()
        
        # Search keywords
        keywords = ["sound", "audio", "music", "tone", "speaker", "voice", "wave",
                   "midi", "pcm", "sample", "volume", "pitch", "freq"]
        
        funcs = []
        
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            name_lower = name.lower()
            
            if any(kw in name_lower for kw in keywords):
                func = idaapi.get_func(func_ea)
                funcs.append({
                    "address": hex(func_ea),
                    "name": name,
                    "size": func.end_ea - func.start_ea if func else 0
                })
        
        result = {
            "count": len(funcs),
            "functions": funcs[:60]  # First 60
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
