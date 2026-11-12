"""
Analyze overlay_tail_bridge to understand overlay system entry point.
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\overlay_bridge_analysis.json"

def analyze_function_complete(func_name):
    """Get complete analysis of a function."""
    idaapi.auto_wait()
    
    addr = idc.get_name_ea_simple(func_name)
    if addr == idc.BADADDR:
        return {"error": f"Function {func_name} not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": f"No function at address {hex(addr)}"}
    
    result = {
        "name": func_name,
        "address": hex(addr),
        "start": hex(func.start_ea),
        "end": hex(func.end_ea),
        "size": func.end_ea - func.start_ea,
        "disassembly": [],
        "calls": [],
        "data_refs": []
    }
    
    # Extract disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        
        result["disassembly"].append({
            "address": hex(ea),
            "mnemonic": mnem,
            "instruction": disasm
        })
        
        # Track calls
        if mnem == "call":
            # Get target name from disassembly
            parts = disasm.split()
            if len(parts) >= 2:
                target_name = parts[-1]
                result["calls"].append({
                    "from": hex(ea),
                    "target": target_name,
                    "instruction": disasm
                })
        
        # Track data references
        for op_idx in range(2):
            op_type = idc.get_operand_type(ea, op_idx)
            if op_type == idc.o_mem:
                data_ea = idc.get_operand_value(ea, op_idx)
                data_name = idc.get_name(data_ea, idc.GN_VISIBLE)
                result["data_refs"].append({
                    "from": hex(ea),
                    "to": hex(data_ea),
                    "name": data_name if data_name else f"data_{data_ea:X}",
                    "instruction": disasm
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    result["num_instructions"] = len(result["disassembly"])
    result["num_calls"] = len(result["calls"])
    result["num_data_refs"] = len(result["data_refs"])
    
    return result

# Main execution
try:
    print("Analyzing overlay_tail_bridge...")
    analysis = analyze_function_complete("overlay_tail_bridge")
    
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
    else:
        print(f"  Address: {analysis['address']}")
        print(f"  Size: {analysis['size']} bytes")
        print(f"  Instructions: {analysis['num_instructions']}")
        print(f"  Calls: {analysis['num_calls']}")
        print(f"  Data refs: {analysis['num_data_refs']}")
        
        print("\nDisassembly:")
        for inst in analysis['disassembly']:
            print(f"  {inst['address']}: {inst['instruction']}")
        
        if analysis['calls']:
            print("\nFunction calls:")
            for call in analysis['calls']:
                print(f"  {call['from']} -> {call['target']}")
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\nAnalysis saved: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
