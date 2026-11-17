"""
Analyze F5-F10 key handlers in detail to find radar mode switching.

Focus on:
- input_poll_handler (F8 handler)
- Functions with multiple F-key handlers (likely dispatchers)
- Looking for mode state changes after F-key press
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\fkey_handlers_detailed.json"

def analyze_function_context(func_name, scan_code):
    """Analyze a function that handles a specific scan code."""
    
    func_ea = idc.get_name_ea_simple(func_name)
    if func_ea == idc.BADADDR:
        return {"error": "Function not found"}
    
    func = idaapi.get_func(func_ea)
    if not func:
        return {"error": "Not a function"}
    
    # Find the scan code comparison
    ea = func.start_ea
    handler_location = None
    
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "cmp":
            if idc.get_operand_type(ea, 1) == idc.o_imm:
                if idc.get_operand_value(ea, 1) == scan_code:
                    handler_location = ea
                    break
        ea = idc.next_head(ea, func.end_ea)
    
    if not handler_location:
        return {"error": "Scan code not found in function"}
    
    # Get context around the handler (20 instructions after)
    context = []
    ea = handler_location
    for i in range(30):
        if ea >= func.end_ea:
            break
        context.append({
            "offset": hex(ea - func.start_ea),
            "address": hex(ea),
            "instruction": idc.GetDisasm(ea)
        })
        ea = idc.next_head(ea, func.end_ea)
    
    # Look for what gets modified after the comparison
    modifications = []
    ea = handler_location
    for i in range(20):
        if ea >= func.end_ea:
            break
        mnem = idc.print_insn_mnem(ea)
        
        # Track writes to memory
        if mnem in ["mov", "or", "and", "xor", "inc", "dec"]:
            op0_type = idc.get_operand_type(ea, 0)
            if op0_type in [idc.o_mem, idc.o_displ]:
                op0_val = idc.get_operand_value(ea, 0)
                op0_name = idc.get_name(op0_val) if op0_val else None
                
                modifications.append({
                    "offset": hex(ea - func.start_ea),
                    "instruction": idc.GetDisasm(ea),
                    "target": op0_name if op0_name else hex(op0_val),
                    "operation": mnem
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "function": func_name,
        "handler_location": hex(handler_location),
        "context": context,
        "modifications": modifications
    }

def find_radar_mode_variables():
    """Find variables that could be radar mode state."""
    
    candidates = []
    
    # Known F-key scan codes for radar modes
    radar_fkeys = [0x3F, 0x40, 0x41, 0x42, 0x43, 0x44]  # F5-F10
    
    # Find all memory writes in functions that handle these keys
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        if not func:
            continue
        
        # Check if this function handles radar F-keys
        has_radar_fkey = False
        ea = func.start_ea
        while ea < func.end_ea:
            if idc.print_insn_mnem(ea) == "cmp":
                if idc.get_operand_type(ea, 1) == idc.o_imm:
                    if idc.get_operand_value(ea, 1) in radar_fkeys:
                        has_radar_fkey = True
                        break
            ea = idc.next_head(ea, func.end_ea)
        
        if not has_radar_fkey:
            continue
        
        # Find what this function modifies
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            
            if mnem in ["mov", "or", "and", "xor"]:
                op0_type = idc.get_operand_type(ea, 0)
                if op0_type == idc.o_mem:
                    addr = idc.get_operand_value(ea, 0)
                    name = idc.get_name(addr)
                    
                    if name:
                        candidates.append({
                            "variable": name,
                            "address": hex(addr),
                            "function": idc.get_func_name(func_ea),
                            "operation": mnem,
                            "instruction": idc.GetDisasm(ea)
                        })
            
            ea = idc.next_head(ea, func.end_ea)
    
    # Group by variable name
    by_var = {}
    for c in candidates:
        var = c['variable']
        if var not in by_var:
            by_var[var] = []
        by_var[var].append(c)
    
    # Sort by frequency
    result = []
    for var, ops in sorted(by_var.items(), key=lambda x: len(x[1]), reverse=True):
        result.append({
            "variable": var,
            "modification_count": len(ops),
            "operations": ops[:5]  # First 5
        })
    
    return result[:20]

def extract_input_poll_handler():
    """Extract input_poll_handler function (handles F8)."""
    
    func_name = "input_poll_handler"
    func_ea = idc.get_name_ea_simple(func_name)
    
    if func_ea == idc.BADADDR:
        return {"error": "Function not found"}
    
    func = idaapi.get_func(func_ea)
    if not func:
        return {"error": "Not a function"}
    
    # Export full disassembly
    disasm = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm.append(f"{ea:08X}: {idc.GetDisasm(ea)}")
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "function": func_name,
        "address": hex(func_ea),
        "size": func.end_ea - func.start_ea,
        "disassembly": disasm
    }

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        print("[1] Analyzing F5 handler (first one)...")
        f5_analysis = analyze_function_context("stream_command_interpret", 0x3F)
        if "error" not in f5_analysis:
            print(f"  Found handler at {f5_analysis['handler_location']}")
            print(f"  Modifications: {len(f5_analysis['modifications'])}")
        
        print("\n[2] Analyzing F6 handler (input-related)...")
        f6_analysis = analyze_function_context("mode_stream_select_step", 0x40)
        if "error" not in f6_analysis:
            print(f"  Found handler at {f6_analysis['handler_location']}")
            print(f"  Modifications: {len(f6_analysis['modifications'])}")
        
        print("\n[3] Analyzing F8 handler (input_poll_handler)...")
        f8_analysis = analyze_function_context("input_poll_handler", 0x42)
        if "error" not in f8_analysis:
            print(f"  Found handler at {f8_analysis['handler_location']}")
            print(f"  Modifications: {len(f8_analysis['modifications'])}")
        
        print("\n[4] Finding radar mode state variables...")
        mode_vars = find_radar_mode_variables()
        print(f"Found {len(mode_vars)} potential mode variables:")
        for var in mode_vars[:10]:
            print(f"  {var['variable']}: {var['modification_count']} modifications")
        
        print("\n[5] Extracting input_poll_handler full code...")
        input_handler = extract_input_poll_handler()
        if "error" not in input_handler:
            print(f"  Function: {input_handler['size']} bytes")
        
        result = {
            "f5_handler_analysis": f5_analysis,
            "f6_handler_analysis": f6_analysis,
            "f8_handler_analysis": f8_analysis,
            "radar_mode_variables": mode_vars,
            "input_poll_handler_full": input_handler
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n[6] Results saved to: {OUTPUT_FILE}")
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
