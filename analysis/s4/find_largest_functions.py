"""
Find the largest and most complex functions in the codebase.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\largest_functions.json"

def main():
    try:
        idaapi.auto_wait()
        
        all_funcs = []
        
        # Analyze all functions
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            name = idc.get_func_name(func_ea)
            size = func.end_ea - func.start_ea
            
            # Count calls
            call_count = 0
            ea = func.start_ea
            while ea < func.end_ea:
                if idc.print_insn_mnem(ea) == "call":
                    call_count += 1
                ea = idc.next_head(ea, func.end_ea)
            
            # Count xrefs (callers)
            xrefs = list(idautils.XrefsTo(func_ea, 0))
            
            all_funcs.append({
                "address": hex(func_ea),
                "name": name,
                "size": size,
                "calls": call_count,
                "callers": len(xrefs)
            })
        
        # Sort by size
        all_funcs.sort(key=lambda x: x["size"], reverse=True)
        
        # Get top 100 by size
        largest = all_funcs[:100]
        
        # Also get functions with most calls (complexity)
        by_calls = sorted(all_funcs, key=lambda x: x["calls"], reverse=True)[:50]
        
        result = {
            "total_functions": len(all_funcs),
            "largest_100": largest,
            "most_calls_50": by_calls,
            "stats": {
                "avg_size": sum(f["size"] for f in all_funcs) / len(all_funcs),
                "avg_calls": sum(f["calls"] for f in all_funcs) / len(all_funcs),
                "total_code_bytes": sum(f["size"] for f in all_funcs)
            }
        }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
