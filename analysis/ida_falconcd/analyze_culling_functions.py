"""
Analyze the 7 functions called by view_projection to understand rendering flow.
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\culling_functions.json"

def analyze_function(addr):
    """Get basic info about a function."""
    idaapi.auto_wait()
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": f"No function at {hex(addr)}"}
    
    name = idc.get_name(addr, idc.GN_VISIBLE)
    if not name:
        name = f"sub_{addr:X}"
    
    # Count calls
    calls = []
    for ea in idautils.FuncItems(addr):
        if idc.print_insn_mnem(ea) == "call":
            target_ea = idc.get_operand_value(ea, 0)
            target_name = idc.get_name(target_ea, idc.GN_VISIBLE)
            if not target_name:
                target_name = f"sub_{target_ea:X}"
            calls.append({
                "from": hex(ea),
                "to": hex(target_ea),
                "target": target_name
            })
    
    return {
        "name": name,
        "address": hex(addr),
        "start": hex(func.start_ea),
        "end": hex(func.end_ea),
        "size": func.end_ea - func.start_ea,
        "calls": calls,
        "num_calls": len(calls)
    }

# Main execution
try:
    # These are the 7 functions called by view_projection
    targets = [
        0x5211,   # sub_5211
        0x47A6,   # sub_47A6
        0x1D6E,   # sub_1D6E
        0x166F,   # sub_166F
        0x1BCE,   # sub_1BCE
        0x1D26,   # sub_1D26
        0x1C16,   # sub_1C16
    ]
    
    results = []
    for addr in targets:
        print(f"Analyzing function at {hex(addr)}...")
        info = analyze_function(addr)
        results.append(info)
        print(f"  {info.get('name')}: {info.get('size')} bytes, {info.get('num_calls')} calls")
    
    output = {
        "view_projection_callees": results,
        "summary": {
            "total_functions": len(results),
            "total_size": sum(f.get('size', 0) for f in results),
            "total_calls": sum(f.get('num_calls', 0) for f in results)
        }
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nAnalysis complete: {OUTPUT_FILE}")
    print(f"Total: {output['summary']['total_functions']} functions, " + 
          f"{output['summary']['total_size']} bytes, " +
          f"{output['summary']['total_calls']} calls")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
