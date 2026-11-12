"""
Verify the actual address of terrain_attr_lookup_3840_b.
"""

import idc
import idaapi
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\verify_address.json"

def main():
    try:
        idaapi.auto_wait()
        
        # Try by name
        addr_by_name = idc.get_name_ea_simple("terrain_attr_lookup_3840_b")
        
        # Try the address from gated_b analysis
        target_addr = 0x14040
        func_at_target = idaapi.get_func(target_addr)
        
        result = {
            "by_name": hex(addr_by_name) if addr_by_name != idc.BADADDR else "not found",
            "at_0x14040": {
                "found": func_at_target is not None,
                "start": hex(func_at_target.start_ea) if func_at_target else None,
                "name": idc.get_func_name(func_at_target.start_ea) if func_at_target else None
            }
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"Results: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
