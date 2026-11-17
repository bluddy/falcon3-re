"""
Export the map projection and entity rendering functions.
These should reveal how aircraft and other objects are rendered on the tactical map.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def export_function_disasm(func_addr, name):
    """Export complete disassembly of a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return {
            'name': name,
            'address': hex(func_addr),
            'error': 'No function at address'
        }
    
    # Get function name
    fname = idc.get_func_name(func.start_ea)
    
    # Get size
    size = func.end_ea - func.start_ea
    
    # Get disassembly
    disasm_lines = []
    ea = func.start_ea
    offset = 0
    
    while ea < func.end_ea:
        # Get disassembly line with comments
        disasm = idc.generate_disasm_line(ea, 0)
        comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
        
        line_info = {
            'offset': offset,
            'address': hex(ea),
            'disasm': disasm
        }
        if comment:
            line_info['comment'] = comment
        
        disasm_lines.append(line_info)
        
        next_ea = idc.next_head(ea, func.end_ea)
        offset += next_ea - ea
        ea = next_ea
    
    # Find xrefs to this function
    xrefs_to = []
    for xref in idautils.XrefsTo(func.start_ea):
        caller_func = idaapi.get_func(xref.frm)
        if caller_func:
            xrefs_to.append({
                'from': hex(xref.frm),
                'caller': idc.get_func_name(caller_func.start_ea)
            })
    
    # Find calls from this function
    calls_from = []
    ea = func.start_ea
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == 'call':
            target = idc.get_operand_value(ea, 0)
            target_name = idc.get_func_name(target)
            if target_name:
                calls_from.append({
                    'at': hex(ea),
                    'to': hex(target),
                    'name': target_name
                })
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'name': fname,
        'address': hex(func.start_ea),
        'size': size,
        'xrefs_to_count': len(xrefs_to),
        'xrefs_to': xrefs_to[:10],  # First 10
        'calls_from': calls_from,
        'disasm': disasm_lines
    }

def main():
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    results = {}
    
    # Target functions
    targets = [
        (0x3A88D, 'map_view_project_pipeline'),
        (0x47871, 'map_view_entity_project'),
        (0x3A6B1, 'hud_map_overlay_frame'),
        (0x3A5D2, 'map_overlay_clip_frame'),
    ]
    
    print("=== Exporting Map Projection Functions ===\n")
    
    for addr, name in targets:
        print(f"Exporting {name} at 0x{addr:X}...")
        results[name] = export_function_disasm(addr, name)
        print(f"  Size: {results[name].get('size', 'N/A')} bytes")
        print(f"  Xrefs: {results[name].get('xrefs_to_count', 0)}")
        print(f"  Calls: {len(results[name].get('calls_from', []))}")
        print()
    
    # Save comprehensive JSON
    output_json = Path(__file__).parent / "map_projection_functions.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ JSON saved to: {output_json}\n")
    
    # Also save individual text files for easy reading
    print("=== Saving Individual Disassembly Files ===\n")
    
    for name, data in results.items():
        if 'error' in data:
            print(f"⚠ {name}: {data['error']}")
            continue
        
        output_txt = Path(__file__).parent.parent / "disassembly" / f"{name}_disasm.txt"
        
        with open(output_txt, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"{data['name']} Disassembly\n")
            f.write("=" * 80 + "\n")
            f.write(f"Address: {data['address']}\n")
            f.write(f"Size: {data['size']} bytes (0x{data['size']:X})\n")
            f.write("=" * 80 + "\n\n")
            
            # Xrefs
            if data['xrefs_to']:
                f.write(f"Called by {data['xrefs_to_count']} functions:\n")
                for xref in data['xrefs_to']:
                    f.write(f"  {xref['from']} - {xref['caller']}\n")
                f.write("\n")
            
            # Calls
            if data['calls_from']:
                f.write(f"Calls {len(data['calls_from'])} functions:\n")
                for call in data['calls_from']:
                    f.write(f"  {call['at']} -> {call['name']}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("Disassembly:\n")
            f.write("=" * 80 + "\n\n")
            
            # Disassembly
            for i, line in enumerate(data['disasm']):
                f.write(f"{i:4} | +0x{line['offset']:04X} | {line['address']} | {line['disasm']}")
                if 'comment' in line:
                    f.write(f"  ; {line['comment']}")
                f.write("\n")
        
        print(f"✓ {name}: {output_txt}")
    
    print(f"\n✓ All files saved!")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
