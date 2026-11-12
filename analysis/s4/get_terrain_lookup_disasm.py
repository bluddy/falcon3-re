"""
Get full disassembly of terrain_attr_lookup_3840_b (42 bytes, leaf function).
"""

import idc
import idaapi
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_lookup_leaf.json"

def main():
    try:
        idaapi.auto_wait()
        
        addr = idc.get_name_ea_simple("terrain_attr_lookup_3840_b")
        func = idaapi.get_func(addr)
        
        if not func:
            result = {"error": "Function not found"}
        else:
            disasm = []
            ea = func.start_ea
            while ea < func.end_ea:
                disasm.append({
                    "address": hex(ea),
                    "disasm": idc.GetDisasm(ea)
                })
                ea = idc.next_head(ea, func.end_ea)
            
            result = {
                "name": "terrain_attr_lookup_3840_b",
                "address": hex(addr),
                "size": func.end_ea - func.start_ea,
                "disassembly": disasm
            }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
