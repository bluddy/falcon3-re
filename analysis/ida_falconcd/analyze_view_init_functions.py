"""
Analyze the view initialization functions that set up the callback pointers.

view_window_state_clamp and view_limits_install_step are the functions
that actually initialize the drawing callback function pointers!
"""

import idc
import idaapi
import idautils
import json

def analyze_function_detailed(func_addr, func_name_override=None):
    """Analyze a function in detail."""
    
    func_name = func_name_override or idc.get_func_name(func_addr)
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    func_size = func_end - func_addr
    
    print("\n" + "=" * 80)
    print(f"FUNCTION: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("=" * 80)
    
    # Get disassembly
    print("\nDISASSEMBLY:")
    print("-" * 80)
    
    ea = func_addr
    disasm_lines = []
    while ea < func_end:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({"addr": ea, "disasm": disasm})
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
    
    # Look for interesting pointer initializations
    print("\n" + "-" * 80)
    print("CALLBACK POINTER INITIALIZATIONS:")
    print("-" * 80)
    
    inits = []
    ea = func_addr
    while ea < func_end:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Look for mov to cs:dword_xxxxx
        if "mov" in disasm.lower() and "cs:dword_" in disasm.lower():
            # Extract target address and value
            print(f"0x{ea:05X}: {disasm}")
            
            # Parse the value being written
            if "," in disasm:
                parts = disasm.split(",")
                value_str = parts[1].strip()
                try:
                    # Handle hex values like 6331h
                    if 'h' in value_str:
                        value = int(value_str.replace('h', ''), 16)
                        target_name = idc.get_func_name(value)
                        if target_name:
                            print(f"  -> Sets pointer to {target_name} at 0x{value:05X}")
                            inits.append({
                                "addr": ea,
                                "value": value,
                                "target_function": target_name,
                                "disasm": disasm
                            })
                except:
                    pass
        
        ea = idc.next_head(ea)
    
    # Look for function calls
    print("\n" + "-" * 80)
    print("FUNCTION CALLS:")
    print("-" * 80)
    
    calls = []
    ea = func_addr
    while ea < func_end:
        if idc.print_insn_mnem(ea) == "call":
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                    target_ea = xref.to
                    target_name = idc.get_func_name(target_ea)
                    disasm = idc.generate_disasm_line(ea, 0)
                    
                    calls.append({
                        "addr": ea,
                        "target": target_ea,
                        "target_name": target_name
                    })
                    
                    print(f"0x{ea:05X}: {target_name}")
        
        ea = idc.next_head(ea)
    
    return {
        "name": func_name,
        "address": func_addr,
        "size": func_size,
        "disassembly": disasm_lines,
        "initializations": inits,
        "calls": calls
    }

def find_initialization_chain():
    """Find the call chain from startup to these init functions."""
    
    print("\n" + "=" * 80)
    print("INITIALIZATION CALL CHAIN")
    print("=" * 80)
    
    target_functions = {
        0x359B2: "view_window_state_clamp",
        0x35B43: "view_limits_install_step"
    }
    
    for func_addr, func_name in target_functions.items():
        print(f"\n[*] Who calls {func_name}?")
        print("-" * 40)
        
        callers = []
        for xref in idautils.XrefsTo(func_addr):
            if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                caller_func = idaapi.get_func(xref.frm)
                if caller_func:
                    caller_name = idc.get_func_name(caller_func.start_ea)
                    callers.append({
                        "name": caller_name,
                        "addr": caller_func.start_ea,
                        "call_site": xref.frm
                    })
                    print(f"  {caller_name} at 0x{caller_func.start_ea:05X} (calls from 0x{xref.frm:05X})")
        
        if not callers:
            print("  (no direct callers found)")
    
def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - VIEW INITIALIZATION ANALYSIS")
    print("Analyzing functions that set up drawing callback pointers")
    print("=" * 80)
    
    # Analyze the two key functions
    results = {}
    
    results["view_window_state_clamp"] = analyze_function_detailed(
        0x359B2, "view_window_state_clamp"
    )
    
    results["view_limits_install_step"] = analyze_function_detailed(
        0x35B43, "view_limits_install_step"
    )
    
    # Find who calls these functions
    find_initialization_chain()
    
    # Save results
    output_path = "view_init_analysis.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
