"""
Analyze DGROUP:0x4287 - FIXED VERSION with absolute paths and error handling.
"""

import idc
import idaapi
import idautils
import json

def analyze_dgroup_offset(offset):
    """Analyze a specific DGROUP offset."""
    
    print("="*80)
    print(f"ANALYZING DGROUP:0x{offset:X}")
    print("="*80)
    
    try:
        dgroup_sel = idc.selector_by_name("DGROUP")
        if dgroup_sel == idc.BADADDR:
            print("✗ DGROUP selector not found")
            return {"error": "DGROUP selector not found"}
        dgroup_base = idc.get_segm_by_sel(dgroup_sel)
        if dgroup_base == idc.BADADDR:
            print("✗ DGROUP not found")
            return {"error": "DGROUP not found"}
        
        addr = dgroup_base + offset
        print(f"Linear address: {hex(addr)}")
        print(f"DGROUP base: {hex(dgroup_base)}")
        
        # Get name and type
        name = idc.get_name(addr)
        type_str = idc.get_type(addr)
        
        print(f"Name: {name if name else 'unnamed'}")
        print(f"Type: {type_str if type_str else 'unknown'}")
        
        # Get xrefs (limit to avoid slowdown)
        xrefs = list(idautils.XrefsTo(addr, 0))
        print(f"Total xrefs: {len(xrefs)}")
        
        # Group by function (limit to first 100 xrefs to avoid timeout)
        xref_funcs = {}
        for xref in xrefs[:100]:
            func_name = idc.get_func_name(xref.frm)
            if func_name:
                if func_name not in xref_funcs:
                    xref_funcs[func_name] = []
                xref_funcs[func_name].append({
                    "address": hex(xref.frm),
                    "disasm": idc.GetDisasm(xref.frm)
                })
        
        print(f"\nUsed by {len(xref_funcs)} functions (sampled from {len(xrefs)} xrefs):")
        for func_name in sorted(xref_funcs.keys())[:10]:  # Show first 10
            refs = xref_funcs[func_name]
            print(f"  {func_name} ({len(refs)} refs)")
        
        if len(xref_funcs) > 10:
            print(f"  ... and {len(xref_funcs) - 10} more functions")
        
        return {
            "offset": hex(offset),
            "address": hex(addr),
            "name": name,
            "type": type_str,
            "xref_count": len(xrefs),
            "used_by_functions": list(xref_funcs.keys()),
            "sample_xrefs": {k: v[:3] for k, v in list(xref_funcs.items())[:5]}  # First 5 functions, 3 refs each
        }
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return {"error": str(e)}

def main():
    print("="*80)
    print("DGROUP:0x4287 ANALYSIS (FIXED)")
    print("="*80)
    
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    try:
        # Analyze the main offset
        analysis = analyze_dgroup_offset(0x4287)
        
        # Save with absolute path
        output_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\dgroup_4287_fixed.json"
        
        with open(output_file, "w") as f:
            json.dump({"dgroup_4287": analysis}, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        
        # Print summary
        if "error" not in analysis:
            print(f"\nSUMMARY:")
            print(f"  Address: {analysis['address']}")
            print(f"  XRefs: {analysis['xref_count']}")
            print(f"  Used by: {len(analysis['used_by_functions'])} functions")
            if analysis['used_by_functions']:
                print(f"  Key users: {', '.join(analysis['used_by_functions'][:5])}")
        
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        # Still try to save error
        with open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\dgroup_4287_error.json", "w") as f:
            json.dump({"error": str(e)}, f)
    
    print("\nExiting IDA...")
    idc.qexit(0)

if __name__ == "__main__":
    main()
