"""
Analyze pixel plotting and callback system:
- far_cb_gated (60 bytes) - The actual pixel/character plotting function
- far_cb_setup_dispatch (247 bytes) - Function pointer setup
- Other far_cb_* functions
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\pixel_plotting_analysis.json"

def analyze_function_complete(func_name):
    """Complete analysis of a function."""
    idaapi.auto_wait()
    
    addr = idc.get_name_ea_simple(func_name)
    if addr == idc.BADADDR:
        return {"name": func_name, "error": "Not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"name": func_name, "error": "Not a function"}
    
    result = {
        "name": func_name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": [],
        "calls": [],
        "data_refs": []
    }
    
    # Get disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        disasm = idc.GetDisasm(ea)
        
        inst_info = {
            "addr": hex(ea),
            "mnem": mnem,
            "inst": disasm
        }
        
        # Track calls
        if mnem == "call":
            parts = disasm.split()
            if len(parts) >= 2:
                inst_info["call_target"] = parts[-1]
                result["calls"].append(parts[-1])
        
        # Track memory references
        if mnem == "mov":
            op_type = idc.get_operand_type(ea, 0)
            if op_type == idc.o_mem or op_type == idc.o_displ:
                result["data_refs"].append({
                    "addr": hex(ea),
                    "inst": disasm
                })
        
        result["disassembly"].append(inst_info)
        ea = idc.next_head(ea, func.end_ea)
    
    return result

def find_xrefs_to_function(func_name):
    """Find what calls a function."""
    idaapi.auto_wait()
    
    addr = idc.get_name_ea_simple(func_name)
    if addr == idc.BADADDR:
        return []
    
    xrefs = []
    for xref in idautils.XrefsTo(addr):
        func = idaapi.get_func(xref.frm)
        caller_name = "unknown"
        if func:
            caller_name = idc.get_name(func.start_ea, idc.GN_VISIBLE)
            if not caller_name:
                caller_name = f"sub_{func.start_ea:X}"
        
        xrefs.append({
            "from_addr": hex(xref.frm),
            "from_func": caller_name,
            "inst": idc.GetDisasm(xref.frm)
        })
    
    return xrefs

# Main execution
try:
    functions_to_analyze = [
        "far_cb_gated",
        "far_cb_setup_dispatch",
        "far_cb_with_args",
        "far_cb_vector_invoke_entry"
    ]
    
    results = {}
    
    for func_name in functions_to_analyze:
        print(f"\nAnalyzing {func_name}...")
        analysis = analyze_function_complete(func_name)
        
        if "error" not in analysis:
            print(f"  Size: {analysis['size']} bytes")
            print(f"  Instructions: {len(analysis['disassembly'])}")
            if analysis['calls']:
                print(f"  Calls: {', '.join(analysis['calls'][:5])}")
            
            # Find what calls this function
            xrefs = find_xrefs_to_function(func_name)
            analysis["called_by"] = xrefs
            print(f"  Called by: {len(xrefs)} functions")
            if xrefs:
                for xref in xrefs[:5]:
                    print(f"    {xref['from_func']}: {xref['inst']}")
        else:
            print(f"  ERROR: {analysis['error']}")
        
        results[func_name] = analysis
    
    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nSaved: {OUTPUT_FILE}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
