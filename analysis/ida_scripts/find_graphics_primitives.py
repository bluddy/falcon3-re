import idaapi
import idc
import idautils
import json

def find_vga_memory_access():
    """
    Find direct VGA memory access (segment 0xA000).
    This is how pixels are plotted in VGA mode.
    """
    results = {
        "vga_access": [],
        "vga_functions": []
    }
    
    print("[*] Searching for VGA memory access (0xA000)...")
    
    # Search all code segments
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        # Skip data segments
        if not idc.get_segm_attr(seg_ea, idc.SEGATTR_PERM) & idaapi.SEGPERM_EXEC:
            continue
        
        for head in idautils.Heads(seg_ea, seg_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: mov ax, 0A000h or mov es, 0A000h
            if "0a000h" in disasm.lower() or "a000h" in disasm:
                func_name = idc.get_func_name(head)
                
                # Get context
                context = []
                ctx_head = head
                for i in range(10):
                    ctx_head = idc.next_head(ctx_head)
                    if ctx_head == idc.BADADDR:
                        break
                    context.append({
                        "addr": hex(ctx_head),
                        "disasm": idc.generate_disasm_line(ctx_head, 0)
                    })
                
                results["vga_access"].append({
                    "addr": hex(head),
                    "function": func_name,
                    "segment": seg_name,
                    "disasm": disasm,
                    "context": context
                })
                
                # Track unique functions
                if func_name not in [f["name"] for f in results["vga_functions"]]:
                    results["vga_functions"].append({
                        "name": func_name,
                        "addr": hex(idc.get_func_attr(head, idc.FUNCATTR_START))
                    })
                    print(f"[+] Found VGA access in {func_name} @ {hex(head)}")
    
    return results

def find_bios_video_calls():
    """
    Find BIOS video interrupt calls (INT 10h).
    """
    results = {
        "int_10h_calls": []
    }
    
    print("\n[*] Searching for BIOS video calls (INT 10h)...")
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        if not idc.get_segm_attr(seg_ea, idc.SEGATTR_PERM) & idaapi.SEGPERM_EXEC:
            continue
        
        for head in idautils.Heads(seg_ea, seg_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for: int 10h
            if "int" in disasm.lower() and "10h" in disasm:
                func_name = idc.get_func_name(head)
                
                # Get context - look for AH setup (video function)
                context = []
                check_head = head
                for i in range(10):
                    check_head = idc.prev_head(check_head)
                    if check_head == idc.BADADDR:
                        break
                    ctx_disasm = idc.generate_disasm_line(check_head, 0)
                    context.insert(0, {
                        "addr": hex(check_head),
                        "disasm": ctx_disasm
                    })
                    
                    # Extract video function if AH is set
                    if "ah" in ctx_disasm.lower() and "mov" in ctx_disasm.lower():
                        # Try to extract value
                        if "," in ctx_disasm:
                            parts = ctx_disasm.split(",")
                            if len(parts) > 1:
                                value = parts[1].strip()
                                break
                
                results["int_10h_calls"].append({
                    "addr": hex(head),
                    "function": func_name,
                    "segment": seg_name,
                    "disasm": disasm,
                    "context": context[-5:]  # Last 5 instructions
                })
                
                print(f"[+] Found INT 10h in {func_name} @ {hex(head)}")
    
    return results

def find_coordinate_math_patterns():
    """
    Find coordinate transformation patterns in display functions.
    Look for operations on waypoint X/Y fields.
    """
    results = {
        "coordinate_ops": []
    }
    
    print("\n[*] Searching for coordinate transformation patterns...")
    
    # Focus on display functions
    functions = [
        ("waypoint_coordinate_processor", 0x1A2441),
        ("waypoint_display_processor", 0x1A0F10),
        ("waypoint_display_helper", 0x1A163A)
    ]
    
    for func_name, func_addr in functions:
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            continue
        
        print(f"[*] Analyzing {func_name}...")
        
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Look for waypoint X coordinate access (+0x01)
            if "+1]" in disasm or "+1h]" in disasm:
                # Check if this is after waypoint offset calculation
                check_head = head
                found_waypoint_calc = False
                for i in range(10):
                    check_head = idc.prev_head(check_head)
                    if check_head == idc.BADADDR:
                        break
                    check_disasm = idc.generate_disasm_line(check_head, 0)
                    if "15h" in check_disasm and "imul" in check_disasm.lower():
                        found_waypoint_calc = True
                        break
                
                if found_waypoint_calc:
                    # Get what happens after reading coordinate
                    context = []
                    ctx_head = head
                    for i in range(15):
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
                    
                    results["coordinate_ops"].append({
                        "function": func_name,
                        "addr": hex(head),
                        "field": "+0x01 (X coordinate)",
                        "disasm": disasm,
                        "operations": context
                    })
                    print(f"  [+] Found X coordinate access @ {hex(head)}")
            
            # Look for waypoint Y coordinate access (+0x05)
            if "+5]" in disasm or "+5h]" in disasm:
                check_head = head
                found_waypoint_calc = False
                for i in range(10):
                    check_head = idc.prev_head(check_head)
                    if check_head == idc.BADADDR:
                        break
                    check_disasm = idc.generate_disasm_line(check_head, 0)
                    if "15h" in check_disasm and "imul" in check_disasm.lower():
                        found_waypoint_calc = True
                        break
                
                if found_waypoint_calc:
                    context = []
                    ctx_head = head
                    for i in range(15):
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
                    
                    results["coordinate_ops"].append({
                        "function": func_name,
                        "addr": hex(head),
                        "field": "+0x05 (Y coordinate)",
                        "disasm": disasm,
                        "operations": context
                    })
                    print(f"  [+] Found Y coordinate access @ {hex(head)}")
    
    return results

def find_screen_dimension_constants():
    """
    Search for common screen resolution constants (320, 200, 640, 480, 256).
    """
    results = {
        "screen_constants": []
    }
    
    print("\n[*] Searching for screen dimension constants...")
    
    constants = {
        320: "Screen width (320x200 VGA)",
        200: "Screen height (320x200 VGA)",
        640: "Screen width (640x480 VGA)",
        480: "Screen height (640x480 VGA)",
        256: "Possible zoom/scale factor",
        160: "Half screen width (320/2)",
        100: "Half screen height (200/2)"
    }
    
    # Focus on display functions
    functions = [
        ("waypoint_coordinate_processor", 0x1A2441),
        ("waypoint_display_processor", 0x1A0F10),
        ("tactical_screen_coordinator", 0x12DB6A)
    ]
    
    for func_name, func_addr in functions:
        func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
        if func_end == idc.BADADDR:
            continue
        
        for head in idautils.Heads(func_addr, func_end):
            disasm = idc.generate_disasm_line(head, 0)
            
            for value, description in constants.items():
                hex_val = hex(value)[2:].upper() + "h"
                dec_val = str(value)
                
                if hex_val in disasm or (", " + dec_val) in disasm:
                    results["screen_constants"].append({
                        "function": func_name,
                        "addr": hex(head),
                        "value": value,
                        "description": description,
                        "disasm": disasm
                    })
                    print(f"[+] Found {description} ({value}) in {func_name}")
                    break
    
    return results

def main():
    print("="*80)
    print("Graphics Primitives and Coordinate Math Search")
    print("="*80)
    
    results = {}
    
    # Find VGA memory access
    results["vga"] = find_vga_memory_access()
    
    # Find BIOS video calls
    results["bios_video"] = find_bios_video_calls()
    
    # Find coordinate transformation
    results["coordinates"] = find_coordinate_math_patterns()
    
    # Find screen dimensions
    results["screen_dims"] = find_screen_dimension_constants()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\graphics_primitives_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"[+] Results saved to: {output_path}")
    print("="*80)
    
    # Summary
    vga_funcs = len(results["vga"]["vga_functions"])
    vga_access = len(results["vga"]["vga_access"])
    int_10h = len(results["bios_video"]["int_10h_calls"])
    coord_ops = len(results["coordinates"]["coordinate_ops"])
    screen_consts = len(results["screen_dims"]["screen_constants"])
    
    print(f"\n[*] Summary:")
    print(f"    VGA functions found: {vga_funcs}")
    print(f"    VGA memory accesses: {vga_access}")
    print(f"    INT 10h calls: {int_10h}")
    print(f"    Coordinate operations: {coord_ops}")
    print(f"    Screen dimension constants: {screen_consts}")
    print("\n[+] Analysis complete!")

if __name__ == "__main__":
    main()
