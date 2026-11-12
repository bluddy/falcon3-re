"""
Find the actual address of sub_1570.
"""

import idc
import idaapi
import idautils
import json

def main():
    print("="*80)
    print("Finding sub_1570")
    print("="*80)
    
    try:
        idaapi.auto_wait()
        
        result = {}
        
        # Method 1: By name
        addr_by_name = idc.get_name_ea_simple("sub_1570")
        result["by_name"] = hex(addr_by_name) if addr_by_name != idc.BADADDR else "not found"
        
        # Method 2: Check if 0x1570 exists
        func_1570 = idaapi.get_func(0x1570)
        if func_1570:
            result["at_0x1570"] = {
                "found": True,
                "start": hex(func_1570.start_ea),
                "end": hex(func_1570.end_ea),
                "name": idc.get_func_name(func_1570.start_ea)
            }
        else:
            result["at_0x1570"] = {"found": False}
        
        # Method 3: Search for functions named like sub_1570
        result["search_results"] = []
        for func_ea in idautils.Functions():
            name = idc.get_func_name(func_ea)
            if "1570" in name.lower():
                result["search_results"].append({
                    "address": hex(func_ea),
                    "name": name
                })
        
        # Method 4: Check what segment 0x1570 is in
        seg = idaapi.getseg(0x1570)
        if seg:
            result["segment_at_0x1570"] = {
                "name": idaapi.get_segm_name(seg),
                "start": hex(seg.start_ea),
                "end": hex(seg.end_ea)
            }
        
        # Write output
        output = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\find_sub_1570.json"
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"Results written to: {output}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
