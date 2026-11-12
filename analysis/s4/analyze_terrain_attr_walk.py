"""
Analyze terrain_attr_walk_13110 - THE hot terrain function called 3x.
Real address: 0x13110 (not 0x1570 which was a relative offset!)
"""

import idc
import idaapi
import idautils
import json

# Absolute output paths
OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_attr_walk_analysis.json"
ERROR_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_attr_walk_error.json"

def analyze_function():
    """Analyze terrain_attr_walk_13110."""
    
    print("="*80)
    print("TERRAIN_ATTR_WALK_13110 ANALYSIS")
    print("="*80)
    
    try:
        # Function address and name
        addr = 0x13110
        func_name = "terrain_attr_walk_13110"
        
        print(f"Analyzing: {func_name} at {hex(addr)}")
        
        func = idaapi.get_func(addr)
        if not func:
            return {"error": f"No function at {hex(addr)}"}
        
        size = func.end_ea - func.start_ea
        print(f"Size: {size} bytes")
        
        # Get CALL instructions
        calls = []
        ea = func.start_ea
        
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem and mnem.startswith("call"):
                disasm = idc.GetDisasm(ea)
                target_name = disasm.split()[-1] if ' ' in disasm else "unknown"
                target_addr = idc.get_name_ea_simple(target_name)
                
                calls.append({
                    "address": hex(ea),
                    "target": hex(target_addr) if target_addr != idc.BADADDR else "unknown",
                    "name": target_name
                })
            ea = idc.next_head(ea, func.end_ea)
        
        print(f"Found {len(calls)} CALL instructions")
        
        # Get callers
        xrefs = list(idautils.XrefsTo(addr, 0))
        callers = {}
        
        for xref in xrefs[:50]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                if caller_name not in callers:
                    callers[caller_name] = 0
                callers[caller_name] += 1
        
        print(f"Called by {len(callers)} functions ({len(xrefs)} total call sites)")
        
        # Get full disassembly (only 82 bytes)
        disasm = []
        ea = func.start_ea
        while ea < func.end_ea:
            disasm.append({
                "address": hex(ea),
                "disasm": idc.GetDisasm(ea)
            })
            ea = idc.next_head(ea, func.end_ea)
        
        # Check for loops
        loops = []
        ea = func.start_ea
        while ea < func.end_ea:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ["jmp", "je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae", "loop"]:
                target = idc.get_operand_value(ea, 0)
                if target < ea:  # Backward jump
                    loops.append({
                        "address": hex(ea),
                        "target": hex(target),
                        "type": mnem
                    })
            ea = idc.next_head(ea, func.end_ea)
        
        result = {
            "name": func_name,
            "address": hex(addr),
            "size": size,
            "call_count": len(calls),
            "calls": calls,
            "xref_count": len(xrefs),
            "unique_callers": len(callers),
            "callers": callers,
            "loop_count": len(loops),
            "loops": loops,
            "disassembly": disasm
        }
        
        # Print summary
        print(f"\nSUMMARY:")
        print(f"  Size: {size} bytes")
        print(f"  Calls: {len(calls)}")
        print(f"  Loops: {len(loops)}")
        print(f"  Called by: {len(callers)} unique functions, {len(xrefs)} call sites")
        
        return result
        
    except Exception as e:
        return {"error": str(e), "details": repr(e)}

def main():
    try:
        # Wait for auto-analysis
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        # Analyze
        result = analyze_function()
        
        # Save
        with open(OUTPUT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        
        if "error" in result:
            print(f"\n✗ Error: {result['error']}")
        else:
            print(f"\n✓ Analysis complete")
        
        print(f"Results saved to: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        with open(ERROR_FILE, "w") as f:
            json.dump({"fatal_error": str(e)}, f)
    
    finally:
        print("\nExiting IDA...")
        idc.qexit(0)

if __name__ == "__main__":
    main()
