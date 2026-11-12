"""
Analyze terrain_frame_update_driver - major terrain system from game loop.
Uses IDA automation best practices.
"""

import idc
import idaapi
import idautils
import json

# Absolute output path
OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_system_analysis.json"
ERROR_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_system_error.json"

def analyze_terrain_function():
    """Analyze the terrain system entry point."""
    
    print("="*80)
    print("TERRAIN SYSTEM ANALYSIS")
    print("="*80)
    
    try:
        # Find the function
        func_name = "terrain_frame_update_driver"
        addr = idc.get_name_ea_simple(func_name)
        
        if addr == idc.BADADDR:
            # Try alternate names
            for alt_name in ["terrain_update", "terrain_driver", "sub_3805"]:
                addr = idc.get_name_ea_simple(alt_name)
                if addr != idc.BADADDR:
                    func_name = alt_name
                    break
        
        if addr == idc.BADADDR:
            # Try by address from game loop analysis
            addr = 0x3805
            func_name = idc.get_func_name(addr) or "sub_3805"
        
        print(f"Analyzing: {func_name} at {hex(addr)}")
        
        func = idaapi.get_func(addr)
        if not func:
            return {"error": f"No function at {hex(addr)}"}
        
        size = func.end_ea - func.start_ea
        print(f"Size: {size} bytes")
        
        # Get CALL instructions (limit to avoid timeout)
        calls = []
        ea = func.start_ea
        call_count = 0
        
        while ea < func.end_ea and call_count < 50:  # Limit to 50 calls
            mnem = idc.print_insn_mnem(ea)
            if mnem and mnem.startswith("call"):
                op_type = idc.get_operand_type(ea, 0)
                if op_type in (idc.o_near, idc.o_far):
                    target = idc.get_operand_value(ea, 0)
                    target_name = idc.get_func_name(target) or idc.get_name(target) or f"sub_{target:X}"
                    calls.append({
                        "address": hex(ea),
                        "target": hex(target),
                        "name": target_name
                    })
                    call_count += 1
            ea = idc.next_head(ea, func.end_ea)
        
        print(f"Found {len(calls)} CALL instructions")
        
        # Get callers (limit to first 20)
        xrefs = list(idautils.XrefsTo(func.start_ea, 0))
        callers = {}
        
        for xref in xrefs[:20]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                if caller_name not in callers:
                    callers[caller_name] = 0
                callers[caller_name] += 1
        
        print(f"Called by {len(callers)} functions ({len(xrefs)} total call sites)")
        
        # Look for terrain-related calls
        terrain_calls = [c for c in calls if any(kw in c['name'].lower() 
                        for kw in ['terrain', 'height', 'ground', 'map', 'tile'])]
        
        # Look for rendering-related calls
        render_calls = [c for c in calls if any(kw in c['name'].lower()
                       for kw in ['render', 'draw', 'view', 'proj', 'display'])]
        
        result = {
            "name": func_name,
            "address": hex(addr),
            "size": size,
            "call_count": len(calls),
            "calls": calls[:20],  # First 20
            "callers": callers,
            "caller_count": len(xrefs),
            "terrain_related_calls": len(terrain_calls),
            "terrain_calls": terrain_calls[:10],
            "render_related_calls": len(render_calls),
            "render_calls": render_calls[:10]
        }
        
        # Print summary
        print(f"\nSUMMARY:")
        print(f"  Size: {size} bytes")
        print(f"  Calls: {len(calls)}")
        print(f"  Terrain-related: {len(terrain_calls)}")
        print(f"  Render-related: {len(render_calls)}")
        print(f"  Called by: {len(callers)} functions")
        
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
        result = analyze_terrain_function()
        
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
