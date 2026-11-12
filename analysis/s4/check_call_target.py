"""
Check what the CALL at 0x153d7 actually targets.
From terrain analysis: call at 0x153d7 targets "0x1570".
"""

import idc
import idaapi
import json

def main():
    print("="*80)
    print("Checking CALL target at 0x153d7")
    print("="*80)
    
    try:
        idaapi.auto_wait()
        
        result = {}
        
        # The CALL instruction address from terrain analysis
        call_addr = 0x153d7
        
        result["call_instruction"] = {
            "address": hex(call_addr),
            "disasm": idc.GetDisasm(call_addr),
            "mnem": idc.print_insn_mnem(call_addr)
        }
        
        # Get the target
        target = idc.get_operand_value(call_addr, 0)
        result["target"] = {
            "value": hex(target),
            "name": idc.get_func_name(target) or idc.get_name(target) or "unnamed"
        }
        
        # Check if there's a function at the target
        func = idaapi.get_func(target)
        if func:
            result["target_function"] = {
                "found": True,
                "start": hex(func.start_ea),
                "end": hex(func.end_ea),
                "size": func.end_ea - func.start_ea,
                "name": idc.get_func_name(func.start_ea)
            }
        else:
            result["target_function"] = {"found": False}
        
        # Write output
        output = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\call_target_check.json"
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
