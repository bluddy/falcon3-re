"""
Analyze hud_readout_render - the main HUD rendering function (908 bytes, 23 calls).
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\hud_readout_render_analysis.json"

def analyze_hud_function(func_name):
    """Detailed analysis of HUD rendering function."""
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
        "calls": [],
        "data_refs": [],
        "loops": [],
        "strings": []
    }
    
    # Extract calls
    for ea in idautils.FuncItems(addr):
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        
        if mnem == "call":
            # Extract function name from disassembly
            parts = disasm.split()
            if len(parts) >= 2:
                target_name = parts[-1]
                result["calls"].append({
                    "from": hex(ea),
                    "target": target_name,
                    "instruction": disasm
                })
        
        # Look for string references
        for op_idx in range(2):
            op_type = idc.get_operand_type(ea, op_idx)
            if op_type == idc.o_imm:  # Immediate value (could be string address)
                val = idc.get_operand_value(ea, op_idx)
                str_val = idc.get_strlit_contents(val, -1, idc.STRTYPE_C)
                if str_val:
                    try:
                        result["strings"].append({
                            "address": hex(ea),
                            "string": str_val.decode('ascii', errors='ignore'),
                            "instruction": disasm
                        })
                    except:
                        pass
        
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
        
        # Look for loops (backward branches)
        if mnem in ["jmp", "je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge",
                   "ja", "jae", "jb", "jbe", "loop", "loope", "loopne"]:
            target_ea = idc.get_operand_value(ea, 0)
            if target_ea < ea:  # Backward branch = loop
                result["loops"].append({
                    "from": hex(ea),
                    "to": hex(target_ea),
                    "type": mnem,
                    "instruction": disasm
                })
    
    result["num_calls"] = len(result["calls"])
    result["num_data_refs"] = len(result["data_refs"])
    result["num_loops"] = len(result["loops"])
    result["num_strings"] = len(result["strings"])
    
    return result

# Main execution
try:
    print("Analyzing hud_readout_render...")
    analysis = analyze_hud_function("hud_readout_render")
    
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
    else:
        print(f"  Address: {analysis['address']}")
        print(f"  Size: {analysis['size']} bytes")
        print(f"  Calls: {analysis['num_calls']}")
        print(f"  Data refs: {analysis['num_data_refs']}")
        print(f"  Loops: {analysis['num_loops']}")
        print(f"  Strings: {analysis['num_strings']}")
        
        if analysis['calls']:
            print("\nFunction calls:")
            for call in analysis['calls']:
                print(f"  {call['from']}: {call['target']}")
        
        if analysis['strings']:
            print("\nString references:")
            for s in analysis['strings']:
                print(f"  {s['address']}: '{s['string']}'")
        
        if analysis['loops']:
            print(f"\nLoops: {len(analysis['loops'])} found")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\nAnalysis saved: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
