"""
Extract UI rendering functions to understand F-16 and weapon graphics display.

Focus on:
- ui_element_render_complex_a (called by R57 display handlers)
- Image loading functions
- Graphics data structures
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def get_function_info(addr):
    """Get detailed function information."""
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    result = {
        'address': hex(addr),
        'name': idc.get_func_name(addr),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'calls': [],
        'xrefs_to': [],
        'disassembly': []
    }
    
    # Get calls made by this function
    for ea in idautils.FuncItems(addr):
        insn = idautils.DecodeInstruction(ea)
        if insn and insn.itype in [idaapi.NN_call, idaapi.NN_callfi, idaapi.NN_callni]:
            for xref in idautils.XrefsFrom(ea, idaapi.XREF_FAR):
                target_name = idc.get_func_name(xref.to)
                if target_name:
                    result['calls'].append({
                        'address': hex(xref.to),
                        'name': target_name,
                        'from': hex(ea)
                    })
    
    # Get functions that call this one
    for xref in idautils.XrefsTo(addr, idaapi.XREF_FAR):
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            result['xrefs_to'].append({
                'address': hex(xref.frm),
                'name': caller_name
            })
    
    # Get disassembly
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        result['disassembly'].append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    return result

def find_image_strings():
    """Find strings related to images, graphics files."""
    keywords = ['.pic', '.dat', '.idx', 'f16', 'f-16', 'bomb', 'missile', 
                'weapon', 'loadout', 'picfont', 'madfont', 'sprite', 'bitmap']
    
    results = []
    for s in idautils.Strings():
        s_str = str(s).lower()
        if any(kw in s_str for kw in keywords):
            # Find xrefs to this string
            xrefs = []
            for xref in idautils.XrefsTo(s.ea):
                func_name = idc.get_func_name(xref.frm)
                if func_name:
                    xrefs.append({
                        'function': func_name,
                        'address': hex(xref.frm)
                    })
            
            if xrefs:
                results.append({
                    'address': hex(s.ea),
                    'string': str(s),
                    'xrefs': xrefs
                })
    
    return results

def main():
    print("="*80)
    print("EXTRACTING UI RENDERING AND GRAPHICS LOADING")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    output_dir = Path(__file__).parent.parent
    
    # Extract key rendering functions
    functions_to_extract = {
        'ui_element_render_complex_a': 0x11cc39,
        'ui_element_render_with_draw': 0x11d074,
        'draw_from_struct': 0x022455,
        'menu_r57_flight_display_handler': 0x1a6aa6,
        'menu_r57_loadout_flight_display': 0x1a86c6,
    }
    
    results = {}
    
    print("\nExtracting functions...")
    for name, addr in functions_to_extract.items():
        print(f"  Extracting {name} at 0x{addr:08X}...")
        info = get_function_info(addr)
        if info:
            results[name] = info
            print(f"    Size: {info['size']} bytes, {len(info['calls'])} calls")
        else:
            print(f"    ERROR: Not a function!")
    
    # Find image-related strings
    print("\nSearching for image/graphics strings...")
    image_strings = find_image_strings()
    print(f"  Found {len(image_strings)} image-related strings")
    
    results['image_strings'] = image_strings
    
    # Save results
    json_file = output_dir / "ui_rendering_extraction.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved to: {json_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Functions extracted: {len([k for k in results.keys() if k != 'image_strings'])}")
    print(f"Image strings found: {len(image_strings)}")
    
    # Show some image strings
    if image_strings:
        print("\nSample image strings:")
        for item in image_strings[:10]:
            print(f"  '{item['string']}' -> {item['xrefs'][0]['function']}")
    
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    
    # Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
