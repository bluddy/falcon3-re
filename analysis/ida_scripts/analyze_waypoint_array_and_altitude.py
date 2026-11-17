import idaapi
import idc
import idautils
import json

def analyze_waypoint_array_pointer():
    """Find and document waypoint array base pointer at 4FC2:0168"""
    results = {
        "waypoint_array_base": {
            "segment": "0x4FC2",
            "offset": "0x0168",
            "linear_address": None,
            "name": "waypoint_array_base",
            "accesses": []
        },
        "altitude_speed_fields": {
            "flight_record_fields": [],
            "waypoint_fields": [],
            "other_arrays": []
        }
    }
    
    # Calculate linear address for 4FC2:0168
    seg_addr = 0x4FC2 << 4  # Segment to linear
    waypoint_array_addr = seg_addr + 0x0168
    results["waypoint_array_base"]["linear_address"] = hex(waypoint_array_addr)
    
    # Search for references to segment 4FC2
    print(f"[*] Searching for references to segment 0x4FC2...")
    
    # Search for all mov instructions loading 0x4FC2
    for func_addr in idautils.Functions():
        func_name = idc.get_func_name(func_addr)
        for head in idautils.Heads(func_addr, idc.get_func_attr(func_addr, idc.FUNCATTR_END)):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: mov ax, 4FC2h or similar
            if "4FC2h" in disasm or "4fc2h" in disasm.lower():
                # Check next few instructions for offset 168h
                next_head = head
                context_instructions = []
                for i in range(10):
                    next_head = idc.next_head(next_head)
                    if next_head == idc.BADADDR:
                        break
                    next_disasm = idc.generate_disasm_line(next_head, 0)
                    context_instructions.append({
                        "addr": hex(next_head),
                        "disasm": next_disasm
                    })
                    
                    # Look for 168h offset
                    if "168h" in next_disasm or "0x168" in next_disasm:
                        results["waypoint_array_base"]["accesses"].append({
                            "function": func_name,
                            "func_addr": hex(func_addr),
                            "addr": hex(head),
                            "disasm": disasm,
                            "context": context_instructions[:i+1]
                        })
                        print(f"[+] Found waypoint array access in {func_name} @ {hex(head)}")
                        break
    
    return results

def find_altitude_speed_candidates():
    """
    Search for potential altitude/speed storage by looking for:
    1. Word/dword accesses in FlightRecord beyond known fields
    2. Separate arrays indexed by flight number
    3. References to altitude-related constants (e.g., feet, meters)
    """
    candidates = {
        "flight_record_word_accesses": [],  # +0x?? word/dword fields
        "altitude_constants": [],  # Numbers like 1000, 5000, 10000 (typical altitudes)
        "speed_constants": []      # Numbers like 300, 500, 600 (typical speeds in knots)
    }
    
    # Known altitude constants (feet)
    altitude_values = [1000, 2000, 5000, 10000, 15000, 20000, 25000, 30000]
    # Known speed constants (knots)
    speed_values = [200, 250, 300, 350, 400, 450, 500, 550, 600]
    
    print("[*] Searching for altitude/speed candidates...")
    
    # Search mission editor functions for word accesses in FlightRecord
    mission_funcs = [
        ("mission_editor_main_loop", 0x18BC28),
        ("waypoint_coordinate_processor", 0x1A2441),
        ("flight_record_handler", 0x1231FB)
    ]
    
    for func_name, func_addr in mission_funcs:
        print(f"[*] Analyzing {func_name}...")
        
        # Get function bounds
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            continue
            
        # Scan for FlightRecord accesses (stride 0x82 = 130 bytes)
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: mov dx, 82h (FlightRecord size)
            if "82h" in disasm and ("mov" in disasm.lower() and "dx" in disasm.lower()):
                # Found flight record multiplication - check what offset is accessed
                next_head = head
                for i in range(20):
                    next_head = idc.next_head(next_head)
                    if next_head == idc.BADADDR:
                        break
                    next_disasm = idc.generate_disasm_line(next_head, 0)
                    
                    # Look for es:[bx+OFFSET] accesses
                    if "es:[bx+" in next_disasm:
                        # Extract offset
                        try:
                            offset_str = next_disasm.split("es:[bx+")[1].split("]")[0].strip()
                            # Check if it's a word access (not already known)
                            if "word ptr" in next_disasm or "ax" in next_disasm:
                                candidates["flight_record_word_accesses"].append({
                                    "function": func_name,
                                    "addr": hex(next_head),
                                    "offset": offset_str,
                                    "disasm": next_disasm
                                })
                        except:
                            pass
            
            # Look for altitude constants
            for alt in altitude_values:
                if hex(alt)[2:] in disasm.lower() or str(alt) in disasm:
                    candidates["altitude_constants"].append({
                        "function": func_name,
                        "addr": hex(head),
                        "value": alt,
                        "disasm": disasm
                    })
            
            # Look for speed constants  
            for spd in speed_values:
                if hex(spd)[2:] in disasm.lower() or str(spd) in disasm:
                    candidates["speed_constants"].append({
                        "function": func_name,
                        "addr": hex(head),
                        "value": spd,
                        "disasm": disasm
                    })
    
    return candidates

def main():
    print("="*80)
    print("Waypoint Array and Altitude/Speed Analysis")
    print("="*80)
    
    results = {}
    
    # Find waypoint array pointer
    results["waypoint_array"] = analyze_waypoint_array_pointer()
    
    # Find altitude/speed candidates
    results["altitude_speed"] = find_altitude_speed_candidates()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\waypoint_array_altitude_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_path}")
    print(f"[*] Found {len(results['waypoint_array']['waypoint_array_base']['accesses'])} waypoint array accesses")
    print(f"[*] Found {len(results['altitude_speed']['flight_record_word_accesses'])} FlightRecord word accesses")
    print(f"[*] Found {len(results['altitude_speed']['altitude_constants'])} altitude constants")
    print(f"[*] Found {len(results['altitude_speed']['speed_constants'])} speed constants")
    print("[+] Analysis complete!")

if __name__ == "__main__":
    main()
