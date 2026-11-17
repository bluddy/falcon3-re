import idaapi
import idc
import idautils
import json

def analyze_flight_field_operations():
    """
    Analyze operations on FlightRecord fields to determine their purpose.
    Focus on fields +0x16, +0x18, +0x1A, +0x1C which showed division operations.
    """
    results = {
        "field_16_operations": [],
        "field_18_operations": [],
        "field_1A_operations": [],
        "field_1C_operations": [],
        "division_patterns": {
            "div_by_64": [],   # Likely altitude (64 feet?)
            "div_by_3": [],    # Likely speed (3 knots?)
            "div_by_5": [],    # Unknown
            "div_by_40": []    # Hex 0x40 = 64 decimal
        }
    }
    
    print("[*] Analyzing FlightRecord field operations...")
    
    # Function to check
    func_addr = 0x18BC28  # mission_editor_main_loop
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    
    if func_end == idc.BADADDR:
        print(f"[-] Function not found at 0x{func_addr:X}")
        return results
    
    print(f"[*] Analyzing function @ 0x{func_addr:X} to 0x{func_end:X}")
    
    # Track current field being accessed
    last_field_access = None
    instruction_context = []
    
    for head in idautils.Heads(func_addr, func_end):
        disasm = idc.generate_disasm_line(head, 0)
        
        # Track field accesses
        if "es:[bx+16h]" in disasm:
            last_field_access = {"field": "0x16", "addr": head, "disasm": disasm}
            instruction_context = [{"addr": hex(head), "disasm": disasm}]
            
        elif "es:[bx+18h]" in disasm:
            last_field_access = {"field": "0x18", "addr": head, "disasm": disasm}
            instruction_context = [{"addr": hex(head), "disasm": disasm}]
            
        elif "es:[bx+1Ah]" in disasm:
            last_field_access = {"field": "0x1A", "addr": head, "disasm": disasm}
            instruction_context = [{"addr": hex(head), "disasm": disasm}]
            
        elif "es:[bx+1Ch]" in disasm:
            last_field_access = {"field": "0x1C", "addr": head, "disasm": disasm}
            instruction_context = [{"addr": hex(head), "disasm": disasm}]
        
        # Track what happens to the value
        if last_field_access and len(instruction_context) < 15:
            instruction_context.append({"addr": hex(head), "disasm": disasm})
            
            # Look for division operations
            if "idiv" in disasm.lower() or "div" in disasm.lower():
                # Try to find the divisor in previous instructions
                divisor = None
                for ctx in instruction_context[-5:]:
                    if "mov" in ctx["disasm"] and ("bx" in ctx["disasm"] or "cx" in ctx["disasm"] or "dx" in ctx["disasm"]):
                        # Try to extract the value
                        if "40h" in ctx["disasm"]:
                            divisor = 64
                        elif ", 3" in ctx["disasm"]:
                            divisor = 3
                        elif ", 5" in ctx["disasm"]:
                            divisor = 5
                        elif "64" in ctx["disasm"]:
                            divisor = 64
                
                if divisor:
                    entry = {
                        "field": last_field_access["field"],
                        "field_addr": hex(last_field_access["addr"]),
                        "div_addr": hex(head),
                        "divisor": divisor,
                        "context": instruction_context[-10:]
                    }
                    
                    if divisor == 64:
                        results["division_patterns"]["div_by_64"].append(entry)
                    elif divisor == 3:
                        results["division_patterns"]["div_by_3"].append(entry)
                    elif divisor == 5:
                        results["division_patterns"]["div_by_5"].append(entry)
                    
                    # Store in field-specific list
                    field_key = f"field_{last_field_access['field'][2:]}_operations"
                    if field_key in results:
                        results[field_key].append(entry)
                    
                    print(f"[+] Found {last_field_access['field']} ÷ {divisor} @ {hex(head)}")
                    
                    # Clear tracking
                    last_field_access = None
                    instruction_context = []
            
            # If we've gone too far without finding division, clear tracking
            if len(instruction_context) >= 15:
                last_field_access = None
                instruction_context = []
    
    return results

def analyze_field_storage_patterns():
    """
    Look for write operations to these fields to understand data flow.
    """
    results = {
        "writes_to_16": [],
        "writes_to_1A": [],
        "writes_to_1C": []
    }
    
    print("\n[*] Searching for write operations to FlightRecord fields...")
    
    # Search in file loader and initialization functions
    search_funcs = [
        ("squadron_mission_file_loader", 0x17B437),
        ("mission_editor_main_loop", 0x18BC28)
    ]
    
    for func_name, func_addr in search_funcs:
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            continue
            
        print(f"[*] Checking {func_name}...")
        
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: mov es:[bx+16h], ...
            if "mov" in disasm.lower() and "es:[bx+" in disasm:
                if "+16h]" in disasm or "+1Ah]" in disasm or "+1Ch]" in disasm:
                    # Get context
                    context = []
                    ctx_head = head
                    for i in range(5):
                        ctx_head = idc.prev_head(ctx_head)
                        if ctx_head == idc.BADADDR:
                            break
                        context.insert(0, {
                            "addr": hex(ctx_head),
                            "disasm": idc.generate_disasm_line(ctx_head, 0)
                        })
                    
                    entry = {
                        "function": func_name,
                        "addr": hex(head),
                        "disasm": disasm,
                        "context": context
                    }
                    
                    if "+16h]" in disasm:
                        results["writes_to_16"].append(entry)
                        print(f"  [+] Write to +0x16 @ {hex(head)}")
                    elif "+1Ah]" in disasm:
                        results["writes_to_1A"].append(entry)
                        print(f"  [+] Write to +0x1A @ {hex(head)}")
                    elif "+1Ch]" in disasm:
                        results["writes_to_1C"].append(entry)
                        print(f"  [+] Write to +0x1C @ {hex(head)}")
    
    return results

def search_for_altitude_speed_strings():
    """
    Search for strings like "ALTITUDE", "SPEED", "ALT", "SPD" near field accesses.
    """
    results = {
        "altitude_strings": [],
        "speed_strings": []
    }
    
    print("\n[*] Searching for altitude/speed related strings...")
    
    altitude_keywords = ["ALT", "ALTITUDE", "HEIGHT", "FEET", "METERS"]
    speed_keywords = ["SPEED", "SPD", "KNOTS", "KTS", "VELOCITY", "MACH"]
    
    # Search all strings
    for str_addr in idautils.Strings():
        str_val = str(str_addr).upper()
        
        for keyword in altitude_keywords:
            if keyword in str_val:
                # Find xrefs to this string
                for xref in idautils.XrefsTo(str_addr.ea):
                    results["altitude_strings"].append({
                        "string": str(str_addr),
                        "string_addr": hex(str_addr.ea),
                        "xref_addr": hex(xref.frm),
                        "xref_func": idc.get_func_name(xref.frm)
                    })
                    print(f"[+] Found '{str_val}' referenced in {idc.get_func_name(xref.frm)}")
                break
        
        for keyword in speed_keywords:
            if keyword in str_val:
                for xref in idautils.XrefsTo(str_addr.ea):
                    results["speed_strings"].append({
                        "string": str(str_addr),
                        "string_addr": hex(str_addr.ea),
                        "xref_addr": hex(xref.frm),
                        "xref_func": idc.get_func_name(xref.frm)
                    })
                    print(f"[+] Found '{str_val}' referenced in {idc.get_func_name(xref.frm)}")
                break
    
    return results

def main():
    print("="*80)
    print("FlightRecord Field Analysis - Altitude/Speed Discovery")
    print("="*80)
    
    results = {}
    
    # Analyze operations on fields
    results["field_operations"] = analyze_flight_field_operations()
    
    # Analyze storage patterns
    results["storage_patterns"] = analyze_field_storage_patterns()
    
    # Search for related strings
    results["strings"] = search_for_altitude_speed_strings()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\flight_field_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"[+] Analysis complete! Results saved to: {output_path}")
    print("="*80)
    
    # Summary
    div_64_count = len(results["field_operations"]["division_patterns"]["div_by_64"])
    div_3_count = len(results["field_operations"]["division_patterns"]["div_by_3"])
    div_5_count = len(results["field_operations"]["division_patterns"]["div_by_5"])
    
    print(f"\n[*] Summary:")
    print(f"    Division by 64: {div_64_count} instances (altitude candidate)")
    print(f"    Division by 3:  {div_3_count} instances (speed candidate)")
    print(f"    Division by 5:  {div_5_count} instances (unknown)")
    print(f"    Altitude strings: {len(results['strings']['altitude_strings'])}")
    print(f"    Speed strings: {len(results['strings']['speed_strings'])}")
    print(f"    Write operations: {len(results['storage_patterns']['writes_to_16']) + len(results['storage_patterns']['writes_to_1A']) + len(results['storage_patterns']['writes_to_1C'])}")

if __name__ == "__main__":
    main()
