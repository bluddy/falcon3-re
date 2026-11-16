"""
Extract the two core R45 menu functions:
- sub_1561B0 (position calculator) at 0x1561B0
- r45_menu_element_dispatcher (renderer) at 0x1573C3
"""
import idaapi
import idautils
import idc
import json

def extract_function_full(address, name):
    """Extract complete function with calls, strings, and data references."""
    func = idaapi.get_func(address)
    if not func:
        print(f"ERROR: No function at 0x{address:X}")
        return None
    
    result = {
        "address": address,
        "name": name,
        "size": func.size(),
        "calls": [],
        "data_refs": [],
        "strings": [],
        "instructions": []
    }
    
    # Extract all instructions
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if not idc.is_code(idc.get_full_flags(head)):
            continue
            
        mnem = idc.print_insn_mnem(head)
        disasm = idc.GetDisasm(head)
        
        result["instructions"].append({
            "address": head,
            "offset": head - func.start_ea,
            "mnem": mnem,
            "disasm": disasm
        })
        
        # Check for calls
        if mnem == "call":
            target = idc.get_operand_value(head, 0)
            target_name = idc.get_func_name(target) or f"sub_{target:X}"
            result["calls"].append({
                "addr": head,
                "target": target,
                "name": target_name
            })
        
        # Check for data references
        for ref in idautils.DataRefsFrom(head):
            ref_type = idc.get_type(ref)
            ref_name = idc.get_name(ref) or f"data_{ref:X}"
            
            # Check if it's a string
            str_val = idc.get_strlit_contents(ref)
            if str_val:
                result["strings"].append({
                    "address": ref,
                    "value": str_val.decode('ascii', errors='replace')
                })
            
            result["data_refs"].append({
                "addr": head,
                "target": ref,
                "name": ref_name
            })
    
    # Get cross-references TO this function
    result["xrefs_from"] = []
    for ref in idautils.CodeRefsTo(func.start_ea, 0):
        caller_name = idc.get_func_name(ref) or f"unk_{ref:X}"
        result["xrefs_from"].append({
            "address": ref,
            "function": caller_name
        })
    
    return result

def main():
    # Target functions from R45 segment analysis
    targets = [
        (0x1561B0, "r45_position_calculator"),  # sub_18C
        (0x1573C3, "r45_menu_element_dispatcher")  # sub_1213 (already named)
    ]
    
    results = {}
    
    for addr, name in targets:
        print(f"Extracting {name} at 0x{addr:X}...")
        func_data = extract_function_full(addr, name)
        if func_data:
            results[name] = func_data
            print(f"  Size: {func_data['size']} bytes")
            print(f"  Instructions: {len(func_data['instructions'])}")
            print(f"  Calls: {len(func_data['calls'])}")
            print(f"  Data refs: {len(func_data['data_refs'])}")
            print(f"  Strings: {len(func_data['strings'])}")
            print(f"  Called from: {len(func_data['xrefs_from'])} locations")
        else:
            print(f"  FAILED to extract")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_core_functions.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved to {output_path}")

if __name__ == "__main__":
    main()
