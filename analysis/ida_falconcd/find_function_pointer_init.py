"""
Find where the drawing function pointers are initialized.
Search for writes to cs:dword_35924 and cs:dword_35920
"""
import idc
import idaapi
import idautils
import json

OUTPUT_FILE = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\function_pointer_init.json"

def find_xrefs_to_address(addr):
    """Find all cross-references to an address."""
    idaapi.auto_wait()
    
    xrefs = []
    for xref in idautils.XrefsTo(addr):
        xref_info = {
            "from": hex(xref.frm),
            "to": hex(xref.to),
            "type": xref.type,
            "type_name": idautils.XrefTypeName(xref.type),
            "instruction": idc.GetDisasm(xref.frm)
        }
        
        # Get function containing this xref
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_name(func.start_ea, idc.GN_VISIBLE)
            if not func_name:
                func_name = f"sub_{func.start_ea:X}"
            xref_info["function"] = func_name
            xref_info["function_addr"] = hex(func.start_ea)
        
        xrefs.append(xref_info)
    
    return xrefs

def analyze_sprite_offset_dispatch():
    """Analyze sprite_offset_dispatch_343e in detail."""
    addr = idc.get_name_ea_simple("sprite_offset_dispatch_343e")
    if addr == idc.BADADDR:
        return {"error": "Function not found"}
    
    func = idaapi.get_func(addr)
    if not func:
        return {"error": "Not a function"}
    
    result = {
        "name": "sprite_offset_dispatch_343e",
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "disassembly": []
    }
    
    # Get full disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        result["disassembly"].append({
            "address": hex(ea),
            "instruction": idc.GetDisasm(ea)
        })
        ea = idc.next_head(ea, func.end_ea)
    
    return result

# Main execution
try:
    print("Searching for function pointer initialization...")
    
    results = {
        "pointer_xrefs": {},
        "sprite_dispatch_detail": {}
    }
    
    # Find xrefs to the two function pointers
    print("\n1. Finding xrefs to cs:dword_35924...")
    xrefs1 = find_xrefs_to_address(0x35924)
    results["pointer_xrefs"]["cs:dword_35924"] = {
        "address": hex(0x35924),
        "num_xrefs": len(xrefs1),
        "xrefs": xrefs1
    }
    print(f"   Found {len(xrefs1)} cross-references")
    for xref in xrefs1[:10]:  # Show first 10
        print(f"   {xref['from']}: {xref['instruction']} (in {xref.get('function', 'unknown')})")
    
    print("\n2. Finding xrefs to cs:dword_35920...")
    xrefs2 = find_xrefs_to_address(0x35920)
    results["pointer_xrefs"]["cs:dword_35920"] = {
        "address": hex(0x35920),
        "num_xrefs": len(xrefs2),
        "xrefs": xrefs2
    }
    print(f"   Found {len(xrefs2)} cross-references")
    for xref in xrefs2[:10]:
        print(f"   {xref['from']}: {xref['instruction']} (in {xref.get('function', 'unknown')})")
    
    # Analyze sprite_offset_dispatch in detail
    print("\n3. Analyzing sprite_offset_dispatch_343e...")
    sprite_detail = analyze_sprite_offset_dispatch()
    results["sprite_dispatch_detail"] = sprite_detail
    
    if "error" not in sprite_detail:
        print(f"   {sprite_detail['size']} bytes, {len(sprite_detail['disassembly'])} instructions")
        print("   Disassembly:")
        for inst in sprite_detail["disassembly"]:
            print(f"     {inst['address']}: {inst['instruction']}")
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\nAnalysis saved: {OUTPUT_FILE}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
