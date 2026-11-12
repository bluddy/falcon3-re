"""
Analyze terrain_attr_lookup_3840_b - actual terrain data lookup.
Address: 0x14040
"""

import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_attr_lookup_3840_b_analysis.json"
ERROR_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\terrain_attr_lookup_3840_b_error.json"

def analyze_function():
    """Analyze terrain_attr_lookup_3840_b."""
    
    print("="*80)
    print("TERRAIN_ATTR_LOOKUP_3840_B ANALYSIS")
    print("="*80)
    
    try:
        addr = 0x14040
        func_name = "terrain_attr_lookup_3840_b"
        
        print(f"Analyzing: {func_name} at {hex(addr)}")
        
        func = idaapi.get_func(addr)
        if not func:
            return {"error": f"No function at {hex(addr)}"}
        
        size = func.end_ea - func.start_ea
        print(f"Size: {size} bytes")
        
        # Get CALL instructions (limit to 30)
        calls = []
        ea = func.start_ea
        call_count = 0
        
        while ea < func.end_ea and call_count < 30:
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
                call_count += 1
            ea = idc.next_head(ea, func.end_ea)
        
        print(f"Found {len(calls)} CALL instructions")
        
        # Get callers (limit to 20)
        xrefs = list(idautils.XrefsTo(addr, 0))
        callers = {}
        
        for xref in xrefs[:20]:
            caller_name = idc.get_func_name(xref.frm)
            if caller_name:
                if caller_name not in callers:
                    callers[caller_name] = 0
                callers[caller_name] += 1
        
        print(f"Called by {len(callers)} functions ({len(xrefs)} total call sites)")
        
        # Sample disassembly (first 50 instructions)
        disasm = []
        ea = func.start_ea
        count = 0
        while ea < func.end_ea and count < 50:
            disasm.append({
                "address": hex(ea),
                "disasm": idc.GetDisasm(ea)
            })
            ea = idc.next_head(ea, func.end_ea)
            count += 1
        
        result = {
            "name": func_name,
            "address": hex(addr),
            "size": size,
            "call_count": len(calls),
            "calls": calls,
            "xref_count": len(xrefs),
            "unique_callers": len(callers),
            "callers": callers,
            "disasm_sample": disasm,
            "disasm_sample_note": f"First {count} instructions of {size} bytes"
        }
        
        print(f"\nSUMMARY:")
        print(f"  Size: {size} bytes")
        print(f"  Calls: {len(calls)}")
        print(f"  Called by: {len(callers)} unique functions, {len(xrefs)} call sites")
        
        return result
        
    except Exception as e:
        return {"error": str(e), "details": repr(e)}

def main():
    try:
        print("Waiting for auto-analysis...")
        idaapi.auto_wait()
        print("Auto-analysis complete\n")
        
        result = analyze_function()
        
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
