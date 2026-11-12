"""
Analyze sprite_offset_dispatch_343e - the sprite positioning/drawing dispatcher.
This function is called 5 times by hud_readout_render and itself calls cs:dword_35924.
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\sprite_dispatch_analysis.json"

def analyze_function_detailed(func_name):
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
        "size": func.end_ea - func.start_ea,
        "disassembly": []
    }
    
    # Get disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        
        inst_info = {
            "address": hex(ea),
            "mnemonic": mnem,
            "instruction": disasm
        }
        
        # For calls, note what's being called
        if mnem == "call":
            parts = disasm.split()
            if len(parts) >= 2:
                inst_info["call_target"] = parts[-1]
        
        result["disassembly"].append(inst_info)
        ea = idc.next_head(ea, func.end_ea)
    
    return result

# Main execution
try:
    print("Analyzing sprite dispatch functions...")
    
    results = {}
    
    # Analyze sprite_offset_dispatch_343e
    print("\n1. Analyzing sprite_offset_dispatch_343e...")
    sprite_dispatch = analyze_function_detailed("sprite_offset_dispatch_343e")
    results["sprite_offset_dispatch"] = sprite_dispatch
    
    if "error" not in sprite_dispatch:
        print(f"   Size: {sprite_dispatch['size']} bytes")
        print(f"   Instructions: {len(sprite_dispatch['disassembly'])}")
        print("\n   Disassembly:")
        for inst in sprite_dispatch["disassembly"]:
            marker = " <-- CALL" if inst.get("call_target") else ""
            print(f"     {inst['address']}: {inst['instruction']}{marker}")
    
    # Analyze sprite_in_view_test
    print("\n2. Analyzing sprite_in_view_test...")
    sprite_view_test = analyze_function_detailed("sprite_in_view_test")
    results["sprite_in_view_test"] = sprite_view_test
    
    if "error" not in sprite_view_test:
        print(f"   Size: {sprite_view_test['size']} bytes")
        print(f"   Instructions: {len(sprite_view_test['disassembly'])}")
    
    # Analyze int32_to_ascii
    print("\n3. Analyzing int32_to_ascii...")
    int_to_ascii = analyze_function_detailed("int32_to_ascii")
    results["int32_to_ascii"] = int_to_ascii
    
    if "error" not in int_to_ascii:
        print(f"   Size: {int_to_ascii['size']} bytes")
        print(f"   Instructions: {len(int_to_ascii['disassembly'])}")
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nAnalysis saved: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
