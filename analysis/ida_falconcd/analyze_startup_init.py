"""
Analyze startup_overlay_init and related initialization to find where
the HUD drawing function pointers (cs:0x35924, cs:0x35920) are set.
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\startup_init_analysis.json"

def find_writes_to_address(target_addr, search_name):
    """Find all instructions that write to a specific address."""
    idaapi.auto_wait()
    
    writes = []
    
    # Search all code segments
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if not seg or seg.type != idaapi.SEG_CODE:
            continue
        
        # Scan through segment
        ea = seg.start_ea
        while ea < seg.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            # Look for mov instructions
            if mnem == "mov":
                # Check if destination operand is our target
                op0_type = idc.get_operand_type(ea, 0)
                if op0_type == idc.o_mem:
                    op0_val = idc.get_operand_value(ea, 0)
                    if op0_val == target_addr:
                        disasm = idc.GetDisasm(ea)
                        
                        # Get function containing this instruction
                        func = idaapi.get_func(ea)
                        func_name = "unknown"
                        if func:
                            func_name = idc.get_name(func.start_ea, idc.GN_VISIBLE)
                            if not func_name:
                                func_name = f"sub_{func.start_ea:X}"
                        
                        writes.append({
                            "address": hex(ea),
                            "instruction": disasm,
                            "function": func_name,
                            "function_addr": hex(func.start_ea) if func else None
                        })
            
            ea = idc.next_head(ea, seg.end_ea)
    
    return {
        "target": search_name,
        "target_address": hex(target_addr),
        "num_writes": len(writes),
        "writes": writes
    }

def analyze_function_complete(func_name):
    """Complete analysis of a function."""
    idaapi.auto_wait()
    
    addr = idc.get_name_ea_simple(func_name)
    if addr == idc.BADADDR:
        return {"error": f"Function {func_name} not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": f"No function at {hex(addr)}"}
    
    result = {
        "name": func_name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": [],
        "calls": [],
        "writes_to_cs": []
    }
    
    # Get disassembly and track writes to code segment
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        
        result["disassembly"].append({
            "address": hex(ea),
            "mnemonic": mnem,
            "instruction": disasm
        })
        
        # Track calls
        if mnem == "call":
            parts = disasm.split()
            if len(parts) >= 2:
                result["calls"].append({
                    "from": hex(ea),
                    "target": parts[-1]
                })
        
        # Track writes to memory (potential function pointer assignments)
        if mnem == "mov":
            op0_type = idc.get_operand_type(ea, 0)
            if op0_type == idc.o_mem:
                op0_val = idc.get_operand_value(ea, 0)
                # Check if writing to code segment addresses
                if 0x30000 <= op0_val <= 0x40000:  # Approximate CS range
                    result["writes_to_cs"].append({
                        "address": hex(ea),
                        "target": hex(op0_val),
                        "instruction": disasm
                    })
        
        ea = idc.next_head(ea, func.end_ea)
    
    result["num_calls"] = len(result["calls"])
    result["num_writes_to_cs"] = len(result["writes_to_cs"])
    
    return result

# Main execution
try:
    print("Searching for function pointer initialization...")
    
    results = {
        "pointer_writes": [],
        "startup_functions": []
    }
    
    # Search for writes to the two function pointers
    print("\n1. Searching for writes to cs:dword_35924 (primary drawing)...")
    writes1 = find_writes_to_address(0x35924, "cs:dword_35924")
    results["pointer_writes"].append(writes1)
    print(f"   Found {writes1['num_writes']} writes")
    for w in writes1["writes"]:
        print(f"   {w['address']}: {w['instruction']} (in {w['function']})")
    
    print("\n2. Searching for writes to cs:dword_35920 (secondary drawing)...")
    writes2 = find_writes_to_address(0x35920, "cs:dword_35920")
    results["pointer_writes"].append(writes2)
    print(f"   Found {writes2['num_writes']} writes")
    for w in writes2["writes"]:
        print(f"   {w['address']}: {w['instruction']} (in {w['function']})")
    
    # Analyze key startup functions
    startup_funcs = [
        "startup_overlay_init",
        "startup_entry_stack_swap", 
        "mode_slot_setup",
        "mode_slot_enter"
    ]
    
    print("\n3. Analyzing startup functions for CS writes...")
    for func_name in startup_funcs:
        print(f"\n   Analyzing {func_name}...")
        analysis = analyze_function_complete(func_name)
        
        if "error" not in analysis:
            print(f"      Size: {analysis['size']} bytes")
            print(f"      Calls: {analysis['num_calls']}")
            print(f"      Writes to CS: {analysis['num_writes_to_cs']}")
            
            if analysis["writes_to_cs"]:
                print(f"      CS writes:")
                for w in analysis["writes_to_cs"][:5]:
                    print(f"         {w['address']}: {w['instruction']}")
        else:
            print(f"      ERROR: {analysis['error']}")
        
        results["startup_functions"].append(analysis)
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nAnalysis saved: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
