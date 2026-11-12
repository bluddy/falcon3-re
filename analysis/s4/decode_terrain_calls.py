"""
Decode actual addresses for terrain system call chain.
Use function names from disassembly, not relative offsets.
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_call_chain.json"

def main():
    try:
        idaapi.auto_wait()
        
        # Functions to analyze (by name from previous disassemblies)
        functions = [
            "terrain_frame_update_driver",
            "terrain_attr_walk_13110",
            "terrain_lookup_gated_b",
            "terrain_attr_lookup_3840_b",
            "ds_swap_fail_ret"
        ]
        
        result = {}
        
        for func_name in functions:
            addr = idc.get_name_ea_simple(func_name)
            
            if addr == idc.BADADDR:
                result[func_name] = {"found": False}
                continue
            
            func = idaapi.get_func(addr)
            if not func:
                result[func_name] = {
                    "found": False,
                    "address": hex(addr),
                    "note": "Address exists but no function"
                }
                continue
            
            # Get calls
            calls = []
            ea = func.start_ea
            while ea < func.end_ea:
                if idc.print_insn_mnem(ea) == "call":
                    disasm = idc.GetDisasm(ea)
                    target_name = disasm.split()[-1] if ' ' in disasm else "unknown"
                    calls.append(target_name)
                ea = idc.next_head(ea, func.end_ea)
            
            result[func_name] = {
                "found": True,
                "address": hex(addr),
                "size": func.end_ea - func.start_ea,
                "calls": calls
            }
        
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
