"""
Analyze sub_1570 - hot terrain function called 3x from terrain_frame_update_driver.
Output: C:\Users\ybarnoy\projects\falcon3\analysis\s4\sub_1570_analysis.json
"""

import idc
import idaapi
import idautils
import json

def analyze_sub_1570():
    """Analyze the hot terrain function."""
    try:
        idaapi.auto_wait()
        
        addr = 0x1570
        func = idaapi.get_func(addr)
        
        if not func:
            return {"error": f"No function at {hex(addr)}"}
        
        result = {
            "address": hex(addr),
            "name": idc.get_func_name(addr),
            "size": func.end_ea - func.start_ea,
            "start": hex(func.start_ea),
            "end": hex(func.end_ea)
        }
        
        # Get callers
        xrefs_to = list(idautils.XrefsTo(addr, 0))
        result["xref_count"] = len(xrefs_to)
        result["callers"] = []
        
        for xref in xrefs_to[:20]:  # First 20
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                result["callers"].append({
                    "address": hex(xref.frm),
                    "function": idc.get_func_name(caller_func.start_ea),
                    "type": xref.type
                })
        
        # Extract CALL instructions
        result["calls"] = []
        ea = func.start_ea
        call_count = 0
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem == "call":
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target) if target else "unknown"
                
                result["calls"].append({
                    "address": hex(ea),
                    "target": hex(target) if target else "indirect",
                    "target_name": target_name,
                    "disasm": idc.GetDisasm(ea)
                })
                call_count += 1
            
            ea = idc.next_head(ea, func.end_ea)
        
        result["call_count"] = call_count
        
        # Sample first 30 instructions for pattern analysis
        result["disasm_sample"] = []
        ea = func.start_ea
        count = 0
        
        while ea < func.end_ea and count < 30:
            result["disasm_sample"].append({
                "address": hex(ea),
                "disasm": idc.GetDisasm(ea)
            })
            ea = idc.next_head(ea, func.end_ea)
            count += 1
        
        # Check for loops (backward jumps)
        result["loops"] = []
        ea = func.start_ea
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ["jmp", "je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae", "loop"]:
                target = idc.get_operand_value(ea, 0)
                if target < ea:  # Backward jump = loop
                    result["loops"].append({
                        "address": hex(ea),
                        "target": hex(target),
                        "type": mnem,
                        "disasm": idc.GetDisasm(ea)
                    })
            
            ea = idc.next_head(ea, func.end_ea)
        
        result["loop_count"] = len(result["loops"])
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

def main():
    print("="*80)
    print("Analyzing sub_1570 - Hot Terrain Function")
    print("="*80)
    
    result = None
    output_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\sub_1570_analysis.json"
    
    try:
        result = analyze_sub_1570()
        
        print(f"DEBUG: Result keys: {result.keys()}")
        print(f"DEBUG: Writing to: {output_file}")
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"✓ Analysis complete")
        if "error" not in result:
            print(f"  Function: {result.get('name', 'unknown')}")
            print(f"  Size: {result.get('size', 0)} bytes")
            print(f"  Calls: {result.get('call_count', 0)}")
            print(f"  Callers: {result.get('xref_count', 0)}")
            print(f"  Loops: {result.get('loop_count', 0)}")
        else:
            print(f"  ERROR: {result['error']}")
        print(f"✓ Results: {output_file}")
        
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
        error_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\sub_1570_error.json"
        try:
            with open(error_file, "w") as f:
                json.dump({"error": str(e), "traceback": traceback.format_exc()}, f)
        except:
            pass
    
    finally:
        print("Exiting IDA...")
        idc.qexit(0)

if __name__ == "__main__":
    main()
