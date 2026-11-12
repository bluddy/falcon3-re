"""
Find where the pixel plotter pointers are initialized.

cs:dword_220A8 - called by far_cb_gated
cs:dword_220E0 - called by far_cb_with_args
"""

import idc
import idaapi
import idautils
import json

def find_plotter_init():
    """Find initialization of pixel plotter pointers."""
    
    print("=" * 80)
    print("FINDING PIXEL PLOTTER INITIALIZATION")
    print("=" * 80)
    
    plotters = {
        0x220A8: "cs:dword_220A8 (used by far_cb_gated)",
        0x220E0: "cs:dword_220E0 (used by far_cb_with_args)"
    }
    
    results = {}
    
    for addr, name in plotters.items():
        print(f"\n[*] Searching for writes to {name} at 0x{addr:05X}")
        print("-" * 40)
        
        writes = []
        
        for xref in idautils.XrefsTo(addr):
            ea = xref.frm
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for mov instructions (writes)
            if "mov" in disasm.lower() and "word ptr" in disasm.lower():
                func = idaapi.get_func(ea)
                func_name = idc.get_func_name(func.start_ea) if func else "unknown"
                
                writes.append({
                    "addr": ea,
                    "function": func_name,
                    "disasm": disasm
                })
                
                print(f"  0x{ea:05X} in {func_name:40} : {disasm}")
        
        # Also show calls (reads)
        reads = []
        for xref in idautils.XrefsTo(addr):
            ea = xref.frm
            disasm = idc.generate_disasm_line(ea, 0)
            
            if "call" in disasm.lower():
                func = idaapi.get_func(ea)
                func_name = idc.get_func_name(func.start_ea) if func else "unknown"
                
                reads.append({
                    "addr": ea,
                    "function": func_name
                })
        
        print(f"\n  Writes: {len(writes)}, Reads (calls): {len(reads)}")
        
        results[name] = {
            "address": addr,
            "writes": writes,
            "reads": reads
        }
    
    return results

def search_dispatcher_functions():
    """Search for dispatcher functions that might initialize plotters."""
    
    print("\n" + "=" * 80)
    print("SEARCHING FOR DISPATCHER/INIT FUNCTIONS")
    print("=" * 80)
    
    # Look for functions with 'dispatch' or 'init' in name that reference plotter addresses
    keywords = ["dispatch", "init", "setup", "install"]
    
    found_funcs = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        func_name_lower = func_name.lower()
        
        # Check if function name contains keywords
        for keyword in keywords:
            if keyword in func_name_lower:
                # Check if this function references our plotter addresses
                func = idaapi.get_func(func_ea)
                if func:
                    ea = func.start_ea
                    refs_plotters = False
                    
                    while ea < func.end_ea:
                        for xref in idautils.DataRefsFrom(ea):
                            if xref == 0x220A8 or xref == 0x220E0:
                                refs_plotters = True
                                break
                        
                        if refs_plotters:
                            break
                        
                        ea = idc.next_head(ea)
                    
                    if refs_plotters:
                        func_size = func.end_ea - func.start_ea
                        found_funcs.append({
                            "name": func_name,
                            "addr": func_ea,
                            "size": func_size
                        })
                        print(f"  ✓ {func_name} at 0x{func_ea:05X} ({func_size} bytes)")
                
                break
    
    return found_funcs

def analyze_dispatch_220dc_stub():
    """Analyze dispatch_220dc_stub which is called during init."""
    
    print("\n" + "=" * 80)
    print("ANALYZING: dispatch_220dc_stub")
    print("=" * 80)
    
    # We know this is called during view initialization
    func_addr = 0x255C3  # From earlier analysis, need to find actual address
    
    # Search for it
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if "220dc" in func_name or "dispatch_220dc" in func_name:
            func_addr = func_ea
            break
    
    if not func_addr:
        print("  Could not find dispatch_220dc_stub")
        return None
    
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"  No function at 0x{func_addr:05X}")
        return None
    
    func_name = idc.get_func_name(func_addr)
    func_size = func.end_ea - func.start_ea
    
    print(f"\nFunction: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("\nDisassembly:")
    print("-" * 40)
    
    ea = func.start_ea
    count = 0
    while ea < func.end_ea and count < 30:
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
        count += 1
    
    if ea < func.end_ea:
        remaining = 0
        while ea < func.end_ea:
            ea = idc.next_head(ea)
            remaining += 1
        print(f"... ({remaining} more instructions)")

def main():
    """Main analysis."""
    
    print("=" * 80)
    print("FALCON 3.0 - PIXEL PLOTTER INITIALIZATION DISCOVERY")
    print("=" * 80)
    
    # Find writes to plotter pointers
    plotter_results = find_plotter_init()
    
    # Search for relevant dispatcher functions
    dispatcher_funcs = search_dispatcher_functions()
    
    # Analyze dispatch_220dc_stub
    analyze_dispatch_220dc_stub()
    
    # Save results
    output = {
        "plotter_initialization": plotter_results,
        "dispatcher_functions": dispatcher_funcs
    }
    
    output_path = "pixel_plotter_init.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
