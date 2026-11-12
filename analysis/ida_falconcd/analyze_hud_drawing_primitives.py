"""
Analyze HUD drawing primitives - find what the function pointers point to.
cs:dword_35924 (at 0x62E4) - primary drawing function (6 calls)
cs:dword_35920 (at 0x62E0) - secondary drawing function (3 calls)
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\hud_drawing_primitives_analysis.json"

def read_dword_ptr(addr):
    """Read a dword pointer from code segment."""
    idaapi.auto_wait()
    
    # Read 4 bytes (dword)
    val = idc.get_wide_dword(addr)
    return val

def analyze_function_from_ptr(ptr_addr, ptr_name):
    """Analyze function that a pointer points to."""
    idaapi.auto_wait()
    
    # Read the pointer value
    func_addr = read_dword_ptr(ptr_addr)
    
    # Get segment and offset from far pointer
    # Far pointer format: offset:segment (16:16)
    offset = func_addr & 0xFFFF
    segment = (func_addr >> 16) & 0xFFFF
    
    # Calculate linear address (segment * 16 + offset)
    linear_addr = (segment << 4) + offset
    
    result = {
        "pointer_name": ptr_name,
        "pointer_address": hex(ptr_addr),
        "pointer_value": hex(func_addr),
        "segment": hex(segment),
        "offset": hex(offset),
        "linear_address": hex(linear_addr),
    }
    
    # Try to find function at this address
    func = idaapi.get_func(linear_addr)
    if func:
        name = idc.get_name(linear_addr, idc.GN_VISIBLE)
        if not name:
            name = f"sub_{linear_addr:X}"
        
        result["function_found"] = True
        result["function_name"] = name
        result["function_start"] = hex(func.start_ea)
        result["function_end"] = hex(func.end_ea)
        result["function_size"] = func.end_ea - func.start_ea
        
        # Count calls in this function
        call_count = 0
        calls = []
        for ea in idautils.FuncItems(linear_addr):
            if idc.print_insn_mnem(ea) == "call":
                disasm = idc.GetDisasm(ea)
                parts = disasm.split()
                if len(parts) >= 2:
                    target_name = parts[-1]
                    calls.append({
                        "from": hex(ea),
                        "target": target_name
                    })
                call_count += 1
        
        result["num_calls"] = call_count
        result["calls"] = calls[:10]  # First 10 calls
    else:
        result["function_found"] = False
        result["error"] = f"No function at linear address {hex(linear_addr)}"
        
        # Try to read some bytes and disassemble
        result["bytes"] = []
        for i in range(16):
            b = idc.get_wide_byte(linear_addr + i)
            result["bytes"].append(hex(b))
    
    return result

def analyze_sprite_functions():
    """Analyze sprite-related functions called by hud_readout_render."""
    funcs_to_analyze = [
        "sprite_offset_dispatch_343e",
        "sprite_in_view_test",
        "int32_to_ascii",
        "angle_quad_norm_far",
        "view_rotation_far_thunk"
    ]
    
    results = []
    for func_name in funcs_to_analyze:
        addr = idc.get_name_ea_simple(func_name)
        if addr == idc.BADADDR:
            results.append({"name": func_name, "error": "Not found"})
            continue
        
        func = idaapi.get_func(addr)
        if not func:
            results.append({"name": func_name, "error": "Not a function"})
            continue
        
        # Get basic info
        info = {
            "name": func_name,
            "address": hex(addr),
            "size": func.end_ea - func.start_ea,
            "calls": []
        }
        
        # Get calls
        for ea in idautils.FuncItems(addr):
            if idc.print_insn_mnem(ea) == "call":
                disasm = idc.GetDisasm(ea)
                parts = disasm.split()
                if len(parts) >= 2:
                    info["calls"].append(parts[-1])
        
        info["num_calls"] = len(info["calls"])
        results.append(info)
    
    return results

# Main execution
try:
    print("Analyzing HUD drawing function pointers...")
    
    results = {
        "function_pointers": [],
        "sprite_functions": []
    }
    
    # Analyze the two function pointers
    print("\n1. Analyzing cs:dword_35924 (primary drawing, 6 calls)...")
    ptr1 = analyze_function_from_ptr(0x35924, "cs:dword_35924")
    results["function_pointers"].append(ptr1)
    print(f"   Pointer at {ptr1['pointer_address']} = {ptr1['pointer_value']}")
    if ptr1.get("function_found"):
        print(f"   Points to: {ptr1['function_name']} ({ptr1['function_size']} bytes, {ptr1['num_calls']} calls)")
    else:
        print(f"   ERROR: {ptr1.get('error', 'Unknown error')}")
    
    print("\n2. Analyzing cs:dword_35920 (secondary drawing, 3 calls)...")
    ptr2 = analyze_function_from_ptr(0x35920, "cs:dword_35920")
    results["function_pointers"].append(ptr2)
    print(f"   Pointer at {ptr2['pointer_address']} = {ptr2['pointer_value']}")
    if ptr2.get("function_found"):
        print(f"   Points to: {ptr2['function_name']} ({ptr2['function_size']} bytes, {ptr2['num_calls']} calls)")
    else:
        print(f"   ERROR: {ptr2.get('error', 'Unknown error')}")
    
    # Analyze sprite functions
    print("\n3. Analyzing sprite and utility functions...")
    sprite_funcs = analyze_sprite_functions()
    results["sprite_functions"] = sprite_funcs
    
    for sf in sprite_funcs:
        if "error" not in sf:
            print(f"   {sf['name']}: {sf['size']} bytes, {sf['num_calls']} calls")
        else:
            print(f"   {sf['name']}: {sf['error']}")
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nAnalysis saved: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
