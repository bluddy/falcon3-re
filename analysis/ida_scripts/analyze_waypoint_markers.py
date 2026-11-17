import idaapi
import idc
import idautils
import json

def analyze_marker_field_usage():
    """
    Analyze how marker_1 (+0x03) and marker_2 (+0x07) fields are used in code.
    Look for comparisons, bit operations, and branching based on these values.
    """
    results = {
        "marker_1_operations": [],
        "marker_2_operations": [],
        "marker_constants": []
    }
    
    print("[*] Analyzing waypoint marker field usage...")
    
    # Known marker values from file analysis
    known_values = {
        "marker_1": [-8, -2, 0xF8FF, 0xFEFF],
        "marker_2": [-12, -9, 0xF4FF, 0xF7FF]
    }
    
    # Search mission editor and waypoint display functions
    target_funcs = [
        ("mission_editor_main_loop", 0x18BC28),
        ("waypoint_flags_processor", 0x18DE3B),
        ("waypoint_display_processor", 0x1A0F10),
        ("waypoint_coordinate_processor", 0x1A2441),
        ("waypoint_display_helper", 0x1A163A)
    ]
    
    for func_name, func_addr in target_funcs:
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            print(f"[-] Function {func_name} not found")
            continue
        
        print(f"[*] Analyzing {func_name}...")
        
        # Track waypoint structure access
        waypoint_access = None
        
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for waypoint offset calculation (index * 21)
            if "15h" in disasm and "imul" in disasm.lower():
                waypoint_access = head
                print(f"  [+] Waypoint access @ {hex(head)}")
            
            # Look for marker_1 access (+0x03 from waypoint base)
            if waypoint_access and any(x in disasm for x in ["+3]", "+3h]", "[bx+3]"]):
                # Get context
                context = []
                ctx_head = head
                for i in range(10):
                    ctx_head = idc.next_head(ctx_head)
                    if ctx_head == idc.BADADDR:
                        break
                    ctx_disasm = idc.generate_disasm_line(ctx_head, 0)
                    context.append({
                        "addr": hex(ctx_head),
                        "disasm": ctx_disasm
                    })
                    
                    # Stop at next waypoint access or function call
                    if "call" in ctx_disasm.lower() or "ret" in ctx_disasm.lower():
                        break
                
                results["marker_1_operations"].append({
                    "function": func_name,
                    "addr": hex(head),
                    "disasm": disasm,
                    "context": context
                })
                print(f"    [+] marker_1 access @ {hex(head)}")
            
            # Look for marker_2 access (+0x07 from waypoint base)
            if waypoint_access and any(x in disasm for x in ["+7]", "+7h]", "[bx+7]"]):
                context = []
                ctx_head = head
                for i in range(10):
                    ctx_head = idc.next_head(ctx_head)
                    if ctx_head == idc.BADADDR:
                        break
                    ctx_disasm = idc.generate_disasm_line(ctx_head, 0)
                    context.append({
                        "addr": hex(ctx_head),
                        "disasm": ctx_disasm
                    })
                    
                    if "call" in ctx_disasm.lower() or "ret" in ctx_disasm.lower():
                        break
                
                results["marker_2_operations"].append({
                    "function": func_name,
                    "addr": hex(head),
                    "disasm": disasm,
                    "context": context
                })
                print(f"    [+] marker_2 access @ {hex(head)}")
            
            # Look for comparisons with known marker values
            for marker_type, values in known_values.items():
                for value in values:
                    value_hex = hex(value & 0xFFFF) if value < 0 else hex(value)
                    if value_hex[2:].upper() in disasm.upper() and ("cmp" in disasm.lower() or "test" in disasm.lower()):
                        results["marker_constants"].append({
                            "function": func_name,
                            "addr": hex(head),
                            "marker_type": marker_type,
                            "value": value,
                            "disasm": disasm
                        })
                        print(f"    [+] Comparison with {marker_type} value {value} @ {hex(head)}")
    
    return results

def search_waypoint_type_strings():
    """
    Search for strings that might indicate waypoint types/actions.
    """
    results = {
        "action_strings": [],
        "waypoint_strings": []
    }
    
    print("\n[*] Searching for waypoint action strings...")
    
    # Action-related keywords
    action_keywords = [
        "ATTACK", "TARGET", "BOMB", "STRIKE", "WAYPOINT", "WP", "NAV",
        "PATROL", "CAP", "CAS", "SEAD", "ESCORT", "INTERCEPT",
        "LANDING", "TAKEOFF", "RTB", "REFUEL", "INGRESS", "EGRESS"
    ]
    
    for str_addr in idautils.Strings():
        str_val = str(str_addr).upper()
        
        for keyword in action_keywords:
            if keyword in str_val and len(str_val) < 50:  # Reasonable length
                # Find references
                refs = []
                for xref in idautils.XrefsTo(str_addr.ea):
                    refs.append({
                        "addr": hex(xref.frm),
                        "function": idc.get_func_name(xref.frm)
                    })
                
                if refs:  # Only include if referenced
                    results["action_strings"].append({
                        "string": str(str_addr),
                        "keyword": keyword,
                        "string_addr": hex(str_addr.ea),
                        "references": refs
                    })
                    print(f"[+] Found '{str_val}' containing '{keyword}'")
                break
        
        # Also look for waypoint-specific strings
        if "WAYPOINT" in str_val or "WP" in str_val:
            refs = []
            for xref in idautils.XrefsTo(str_addr.ea):
                refs.append({
                    "addr": hex(xref.frm),
                    "function": idc.get_func_name(xref.frm)
                })
            
            if refs:
                results["waypoint_strings"].append({
                    "string": str(str_addr),
                    "string_addr": hex(str_addr.ea),
                    "references": refs
                })
    
    return results

def analyze_marker_correlation():
    """
    Try to find patterns correlating marker values with mission types or actions.
    """
    results = {
        "mission_type_checks": [],
        "marker_branches": []
    }
    
    print("\n[*] Analyzing marker value correlation with mission context...")
    
    # Look in mission editor for branches based on markers
    func_addr = 0x18BC28  # mission_editor_main_loop
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    
    if func_end == idc.BADADDR:
        print("[-] mission_editor_main_loop not found")
        return results
    
    # Track control flow around marker accesses
    for head in idautils.Heads(func_addr, func_end):
        disasm = idc.generate_disasm_line(head, 0)
        
        # Look for conditional jumps after potential marker access
        if any(x in disasm.lower() for x in ["jz", "jnz", "je", "jne", "jl", "jg", "jle", "jge"]):
            # Look back for comparison or test
            check_head = head
            found_marker = False
            
            for i in range(5):
                check_head = idc.prev_head(check_head)
                if check_head == idc.BADADDR:
                    break
                
                check_disasm = idc.generate_disasm_line(check_head, 0)
                
                # Check if this compares/tests a marker field
                if any(x in check_disasm for x in ["+3]", "+7]", "+3h]", "+7h]"]):
                    found_marker = True
                    
                    # Get jump target
                    jump_target = None
                    operands = disasm.split()
                    if len(operands) > 1:
                        jump_target = operands[-1]
                    
                    results["marker_branches"].append({
                        "comparison_addr": hex(check_head),
                        "comparison": check_disasm,
                        "branch_addr": hex(head),
                        "branch": disasm,
                        "target": jump_target
                    })
                    print(f"[+] Marker-based branch @ {hex(head)}: {disasm}")
                    break
    
    return results

def main():
    print("="*80)
    print("Waypoint Marker Analysis")
    print("="*80)
    
    results = {}
    
    # Analyze marker field usage
    results["marker_usage"] = analyze_marker_field_usage()
    
    # Search for action strings
    results["action_strings"] = search_waypoint_type_strings()
    
    # Analyze correlations
    results["correlations"] = analyze_marker_correlation()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\waypoint_marker_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"[+] Results saved to: {output_path}")
    print("="*80)
    
    # Summary
    marker_1_ops = len(results["marker_usage"]["marker_1_operations"])
    marker_2_ops = len(results["marker_usage"]["marker_2_operations"])
    marker_consts = len(results["marker_usage"]["marker_constants"])
    action_strs = len(results["action_strings"]["action_strings"])
    waypoint_strs = len(results["action_strings"]["waypoint_strings"])
    branches = len(results["correlations"]["marker_branches"])
    
    print(f"\n[*] Summary:")
    print(f"    marker_1 operations: {marker_1_ops}")
    print(f"    marker_2 operations: {marker_2_ops}")
    print(f"    Marker constant comparisons: {marker_consts}")
    print(f"    Action-related strings: {action_strs}")
    print(f"    Waypoint strings: {waypoint_strs}")
    print(f"    Marker-based branches: {branches}")
    print("\n[+] Analysis complete!")

if __name__ == "__main__":
    main()
