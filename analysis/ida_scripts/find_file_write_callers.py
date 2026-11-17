import idaapi
import idc
import idautils
import json

def find_callers_of_file_write():
    """
    Find all functions that call file_write (0x2271F).
    Focus on those that might be saving mission files.
    """
    results = {
        "file_write_callers": [],
        "mission_related_callers": []
    }
    
    file_write_addr = 0x2271F
    
    print(f"[*] Finding callers of file_write @ 0x{file_write_addr:X}...")
    
    # Get all cross-references to file_write
    for xref in idautils.XrefsTo(file_write_addr):
        caller_addr = xref.frm
        caller_func = idc.get_func_name(caller_addr)
        caller_segment = idc.get_segm_name(caller_addr)
        
        # Get context around the call
        context = []
        ctx_addr = caller_addr
        for i in range(15):
            ctx_addr = idc.prev_head(ctx_addr)
            if ctx_addr == idc.BADADDR:
                break
            context.insert(0, {
                "addr": hex(ctx_addr),
                "disasm": idc.generate_disasm_line(ctx_addr, 0)
            })
        
        caller_info = {
            "function": caller_func,
            "addr": hex(caller_addr),
            "segment": caller_segment,
            "context": context
        }
        
        results["file_write_callers"].append(caller_info)
        
        # Check if mission-related
        func_name_lower = caller_func.lower() if caller_func else ""
        if any(keyword in func_name_lower for keyword in ["mission", "squad", "save", "write", "file", "r55", "r56"]):
            results["mission_related_callers"].append(caller_info)
            print(f"[+] Mission-related caller: {caller_func} @ {hex(caller_addr)}")
        else:
            print(f"    Caller: {caller_func} @ {hex(caller_addr)}")
    
    return results

def analyze_squadron_file_functions():
    """
    Analyze functions near squadron_mission_file_loader to find the save counterpart.
    """
    results = {
        "nearby_functions": []
    }
    
    loader_addr = 0x17B437
    search_range = 0x2000  # 8KB range
    
    print(f"\n[*] Analyzing functions near squadron_mission_file_loader @ 0x{loader_addr:X}...")
    
    # Get all functions in range
    for func_addr in idautils.Functions(loader_addr - search_range // 2, loader_addr + search_range):
        func_name = idc.get_func_name(func_addr)
        func_size = idc.get_func_attr(func_addr, idc.FUNCATTR_END) - func_addr
        
        if func_size == idc.BADADDR:
            continue
        
        # Check if function calls file_write
        calls_file_write = False
        calls_file_create = False
        has_loop = False
        
        for head in idautils.Heads(func_addr, idc.get_func_attr(func_addr, idc.FUNCATTR_END)):
            disasm = idc.generate_disasm_line(head, 0)
            
            # Check for calls to file I/O functions
            if "call" in disasm.lower():
                if "file_write" in disasm.lower() or "2271" in disasm:
                    calls_file_write = True
                if "file_create" in disasm.lower() or "226a1" in disasm:
                    calls_file_create = True
            
            # Check for loops (common in save operations)
            if "loop" in disasm.lower() or ("jnz" in disasm.lower() and "short" in disasm.lower()):
                has_loop = True
        
        if calls_file_write or calls_file_create:
            results["nearby_functions"].append({
                "name": func_name,
                "addr": hex(func_addr),
                "size": func_size,
                "offset_from_loader": hex(func_addr - loader_addr),
                "calls_file_write": calls_file_write,
                "calls_file_create": calls_file_create,
                "has_loop": has_loop
            })
            print(f"[+] Function: {func_name} @ {hex(func_addr)}")
            print(f"    Size: {func_size}, Calls write: {calls_file_write}, Calls create: {calls_file_create}")
    
    return results

def search_r55_r56_file_operations():
    """
    Search R55/R56 (mission editor) overlays for file operations.
    """
    results = {
        "r55_file_ops": [],
        "r56_file_ops": []
    }
    
    print("\n[*] Searching R55/R56 overlays for file operations...")
    
    # R55 and R56 segments
    overlays = [
        ("R55", 0x18BC28, "mission_editor_main_loop"),  # Known mission editor
        ("R56", 0x190000, None)  # R56 overlay (approximate)
    ]
    
    for overlay_name, base_addr, known_func in overlays:
        print(f"\n[*] Checking {overlay_name} overlay around 0x{base_addr:X}...")
        
        # Search for functions that call file I/O
        search_end = base_addr + 0x10000  # 64KB range
        
        for func_addr in idautils.Functions(base_addr, search_end):
            func_name = idc.get_func_name(func_addr)
            
            # Check if function has file operations
            has_file_ops = False
            file_ops = []
            
            for head in idautils.Heads(func_addr, idc.get_func_attr(func_addr, idc.FUNCATTR_END)):
                disasm = idc.generate_disasm_line(head, 0)
                
                if "call" in disasm.lower():
                    if any(x in disasm.lower() for x in ["file_write", "file_create", "file_open", "file_close"]):
                        has_file_ops = True
                        file_ops.append({
                            "addr": hex(head),
                            "disasm": disasm
                        })
            
            if has_file_ops:
                func_info = {
                    "function": func_name,
                    "addr": hex(func_addr),
                    "operations": file_ops
                }
                
                if overlay_name == "R55":
                    results["r55_file_ops"].append(func_info)
                else:
                    results["r56_file_ops"].append(func_info)
                
                print(f"  [+] {func_name} @ {hex(func_addr)} - {len(file_ops)} file operations")
    
    return results

def main():
    print("="*80)
    print("File Write Caller Analysis")
    print("="*80)
    
    results = {}
    
    # Find all callers of file_write
    results["file_write_callers"] = find_callers_of_file_write()
    
    # Analyze functions near squadron loader
    results["squadron_functions"] = analyze_squadron_file_functions()
    
    # Search R55/R56 overlays
    results["overlay_operations"] = search_r55_r56_file_operations()
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\file_write_callers.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"[+] Results saved to: {output_path}")
    print("="*80)
    
    # Summary
    total_callers = len(results["file_write_callers"]["file_write_callers"])
    mission_callers = len(results["file_write_callers"]["mission_related_callers"])
    squadron_funcs = len(results["squadron_functions"]["nearby_functions"])
    r55_ops = len(results["overlay_operations"]["r55_file_ops"])
    r56_ops = len(results["overlay_operations"]["r56_file_ops"])
    
    print(f"\n[*] Summary:")
    print(f"    Total file_write callers: {total_callers}")
    print(f"    Mission-related callers: {mission_callers}")
    print(f"    Functions near squadron loader: {squadron_funcs}")
    print(f"    R55 functions with file ops: {r55_ops}")
    print(f"    R56 functions with file ops: {r56_ops}")
    print("\n[+] Analysis complete!")

if __name__ == "__main__":
    main()
