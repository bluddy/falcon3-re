"""
Extract the 6 render functions called by r45_menu_element_dispatcher.
These functions at offsets 0x92F, 0x99B, 0x126, 0x7E9, 0x4BF, 0xA5B
need to be resolved to absolute addresses in the R32_569Fs segment.
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

def find_segment_for_function(func_ea):
    """Find which segment a function belongs to."""
    seg = idaapi.getseg(func_ea)
    if seg:
        return {
            "name": idaapi.get_segm_name(seg),
            "start": seg.start_ea,
            "end": seg.end_ea,
            "size": seg.size()
        }
    return None

def main():
    # R45 segment base
    r45_seg_start = 0x1560B0
    
    # Target function offsets from r45_menu_element_dispatcher calls
    # These are segment-relative offsets
    targets = [
        (0x92F, "r45_render_type_1"),
        (0x99B, "r45_render_type_2"),
        (0x126, "r45_render_type_3"),
        (0x7E9, "r45_render_type_4"),
        (0x4BF, "r45_render_type_5"),
        (0xA5B, "r45_render_type_6")
    ]
    
    results = {}
    
    for offset, name in targets:
        # Calculate absolute address
        abs_addr = r45_seg_start + offset
        
        print(f"Extracting {name} at 0x{abs_addr:X} (offset 0x{offset:X})...")
        func_data = extract_function_full(abs_addr, name)
        
        if func_data:
            results[name] = func_data
            print(f"  Size: {func_data['size']} bytes")
            print(f"  Instructions: {len(func_data['instructions'])}")
            print(f"  Calls: {len(func_data['calls'])}")
            print(f"  Data refs: {len(func_data['data_refs'])}")
            print(f"  Strings: {len(func_data['strings'])}")
            
            # Print strings if found
            if func_data['strings']:
                print(f"  STRINGS FOUND:")
                for s in func_data['strings']:
                    print(f"    0x{s['address']:X}: '{s['value']}'")
        else:
            print(f"  FAILED to extract")
    
    # Also extract the dispatcher itself for reference
    dispatcher_addr = 0x1573C3
    print(f"\nExtracting dispatcher at 0x{dispatcher_addr:X}...")
    dispatcher_data = extract_function_full(dispatcher_addr, "r45_menu_element_dispatcher")
    if dispatcher_data:
        results["r45_menu_element_dispatcher"] = dispatcher_data
        print(f"  Size: {dispatcher_data['size']} bytes")
        if dispatcher_data['strings']:
            print(f"  STRINGS FOUND:")
            for s in dispatcher_data['strings']:
                print(f"    0x{s['address']:X}: '{s['value']}'")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_render_functions.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved to {output_path}")
    
    # Summary
    total_strings = sum(len(f['strings']) for f in results.values())
    print(f"\n=== SUMMARY ===")
    print(f"Extracted {len(results)} functions")
    print(f"Total strings found: {total_strings}")

if __name__ == "__main__":
    main()
