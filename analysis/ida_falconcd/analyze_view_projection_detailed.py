"""
Analyze view_projection function in detail to find culling logic.
Extract full disassembly, calls, loops, and data accesses.
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\view_projection_detailed.json"

def analyze_function_detailed(func_name):
    """Extract detailed analysis of a function."""
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
        "loops": [],
        "data_refs": [],
        "branches": []
    }
    
    # Extract full disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.GetDisasm(ea)
        mnem = idc.print_insn_mnem(ea)
        result["disassembly"].append({
            "address": hex(ea),
            "instruction": disasm
        })
        
        # Track calls
        if mnem == "call":
            target_ea = idc.get_operand_value(ea, 0)
            target_name = idc.get_name(target_ea, idc.GN_VISIBLE)
            if not target_name:
                target_name = f"sub_{target_ea:X}"
            result["calls"].append({
                "from": hex(ea),
                "to": hex(target_ea),
                "target": target_name
            })
        
        # Track branches (potential loops and conditionals)
        if mnem in ["jmp", "je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", 
                   "ja", "jae", "jb", "jbe", "jcxz", "jecxz", "loop", "loope", "loopne"]:
            target_ea = idc.get_operand_value(ea, 0)
            is_backward = target_ea < ea
            result["branches"].append({
                "from": hex(ea),
                "to": hex(target_ea),
                "mnemonic": mnem,
                "backward": is_backward,
                "instruction": disasm
            })
            
            # Loops are backward branches
            if is_backward:
                result["loops"].append({
                    "branch_from": hex(ea),
                    "branch_to": hex(target_ea),
                    "type": mnem
                })
        
        # Track data references
        for op_idx in range(2):  # Check first 2 operands
            op_type = idc.get_operand_type(ea, op_idx)
            if op_type == idc.o_mem:  # Memory reference
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
    result["num_loops"] = len(result["loops"])
    result["num_data_refs"] = len(result["data_refs"])
    result["num_branches"] = len(result["branches"])
    
    return result

# Main execution
try:
    print("Analyzing view_projection in detail...")
    analysis = analyze_function_detailed("view_projection")
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Analysis complete: {OUTPUT_FILE}")
    print(f"  Size: {analysis.get('size', 0)} bytes")
    print(f"  Instructions: {analysis.get('num_instructions', 0)}")
    print(f"  Calls: {analysis.get('num_calls', 0)}")
    print(f"  Loops: {analysis.get('num_loops', 0)}")
    print(f"  Data refs: {analysis.get('num_data_refs', 0)}")
    print(f"  Branches: {analysis.get('num_branches', 0)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
