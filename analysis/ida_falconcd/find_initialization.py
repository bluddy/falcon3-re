"""
Find initialization code for HUD callback function pointers.

Looking for code that writes to these addresses:
- cs:dword_35924 (primary drawing callback)
- cs:dword_35920 (secondary drawing callback)  
- cs:dword_220A8 (pixel plotter)
- cs:dword_220E0 (alternative pixel plotter)
- cs:dword_2217C (vector callback 1)
- cs:dword_22180 (vector callback 2)

Strategy:
1. Find all cross-references to these addresses (writes)
2. Find functions that reference video mode or initialization
3. Look for patterns of multiple pointer assignments together
"""

import idc
import idaapi
import idautils
import json

def find_pointer_initialization():
    """Find where callback function pointers are initialized."""
    
    # Target addresses to search for
    targets = {
        0x35924: "dword_35924 (primary drawing)",
        0x35920: "dword_35920 (secondary drawing)",
        0x220A8: "dword_220A8 (pixel plotter)",
        0x220E0: "dword_220E0 (alt pixel plotter)",
        0x2217C: "dword_2217C (vector callback 1)",
        0x22180: "dword_22180 (vector callback 2)",
    }
    
    results = {}
    
    print("=" * 80)
    print("SEARCHING FOR FUNCTION POINTER INITIALIZATION")
    print("=" * 80)
    
    for addr, name in targets.items():
        print(f"\n[*] Searching for writes to {name} at 0x{addr:X}")
        
        xrefs = []
        for xref in idautils.XrefsTo(addr):
            xref_addr = xref.frm
            xref_type = xref.type
            
            # We want data writes (not code references)
            type_name = str(xref_type)
            
            func = idaapi.get_func(xref_addr)
            func_name = idc.get_func_name(xref_addr) if func else "no_function"
            func_start = func.start_ea if func else 0
            
            # Get the instruction at this xref
            disasm = idc.generate_disasm_line(xref_addr, 0)
            
            xrefs.append({
                "xref_addr": xref_addr,
                "xref_type": type_name,
                "function": func_name,
                "func_start": func_start,
                "disasm": disasm
            })
            
            print(f"  0x{xref_addr:05X}: [{type_name:15}] {func_name:40} | {disasm}")
        
        results[name] = {
            "target_addr": addr,
            "xrefs": xrefs
        }
    
    return results

def find_video_mode_functions():
    """Find functions related to video mode initialization."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR VIDEO MODE / INITIALIZATION FUNCTIONS")
    print("=" * 80)
    
    # Search for function names containing these keywords
    keywords = [
        "video", "mode", "init", "setup", "vga", "screen", "display",
        "graphics", "ega", "cga", "mcga", "tandy"
    ]
    
    found_functions = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_name_lower = func_name.lower()
        
        for keyword in keywords:
            if keyword in func_name_lower:
                func_end = idc.get_func_attr(func_ea, idc.FUNCATTR_END)
                func_size = func_end - func_ea
                
                found_functions.append({
                    "address": func_ea,
                    "name": func_name,
                    "size": func_size,
                    "keyword": keyword
                })
                
                print(f"  0x{func_ea:05X}: {func_name:50} ({func_size:4} bytes) [matched: {keyword}]")
                break
    
    return found_functions

def find_initialization_patterns():
    """Look for functions that set multiple pointers in sequence."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR INITIALIZATION PATTERNS")
    print("=" * 80)
    print("Looking for functions that write to multiple function pointers...")
    
    # Count how many target addresses each function writes to
    target_addrs = [0x35924, 0x35920, 0x220A8, 0x220E0, 0x2217C, 0x22180]
    function_writes = {}
    
    for target_addr in target_addrs:
        for xref in idautils.XrefsTo(target_addr):
            func = idaapi.get_func(xref.frm)
            if func:
                func_name = idc.get_func_name(func.start_ea)
                if func_name not in function_writes:
                    function_writes[func_name] = {
                        "func_addr": func.start_ea,
                        "targets": [],
                        "count": 0
                    }
                function_writes[func_name]["targets"].append(target_addr)
                function_writes[func_name]["count"] += 1
    
    # Sort by count (most writes first)
    sorted_funcs = sorted(function_writes.items(), key=lambda x: x[1]["count"], reverse=True)
    
    print("\nFunctions that write to multiple callback pointers:")
    for func_name, info in sorted_funcs:
        if info["count"] > 1:
            print(f"\n  {func_name} at 0x{info['func_addr']:05X} - writes to {info['count']} pointers:")
            for target in info["targets"]:
                print(f"    - 0x{target:05X}")
    
    return sorted_funcs

def search_for_segment_a000():
    """Search for references to segment 0xA000 (VGA memory)."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR VGA SEGMENT 0xA000 REFERENCES")
    print("=" * 80)
    
    # Search for the immediate value 0xA000
    results = []
    
    for seg_ea in idautils.Segments():
        for head in idautils.Heads(seg_ea, idc.get_segm_end(seg_ea)):
            if idc.is_code(idc.get_full_flags(head)):
                disasm = idc.generate_disasm_line(head, 0)
                if "0A000h" in disasm or "0xa000" in disasm.lower():
                    func = idaapi.get_func(head)
                    func_name = idc.get_func_name(head) if func else "no_function"
                    
                    results.append({
                        "address": head,
                        "function": func_name,
                        "disasm": disasm
                    })
                    
                    print(f"  0x{head:05X}: {func_name:40} | {disasm}")
    
    return results

def main():
    """Main analysis entry point."""
    
    print("\n" + "=" * 80)
    print("FALCON 3.0 - INITIALIZATION CODE DISCOVERY")
    print("=" * 80)
    
    # Run all analyses
    pointer_results = find_pointer_initialization()
    video_functions = find_video_mode_functions()
    init_patterns = find_initialization_patterns()
    vga_refs = search_for_segment_a000()
    
    # Save results
    output = {
        "pointer_initialization": pointer_results,
        "video_mode_functions": video_functions,
        "initialization_patterns": [{"name": name, "info": info} for name, info in init_patterns],
        "vga_segment_references": vga_refs
    }
    
    output_path = "init_code_discovery.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
