"""
Export clip_or_draw_dispatch and related drawing dispatcher functions.
These are the core of the map rendering system.
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
    
    fname = idc.get_func_name(func.start_ea)
    size = func.end_ea - func.start_ea
    
    # Get disassembly
    disasm_lines = []
    ea = func.start_ea
    offset = 0
    
    while ea < func.end_ea:
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
    
    # Find xrefs
    xrefs_to = []
    for xref in idautils.XrefsTo(func.start_ea):
        caller_func = idaapi.get_func(xref.frm)
        if caller_func:
            xrefs_to.append({
                'from': hex(xref.frm),
                'caller': idc.get_func_name(caller_func.start_ea)
            })
    
    # Find calls
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
        'xrefs_to': xrefs_to[:20],
        'calls_from': calls_from,
        'disasm': disasm_lines
    }

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    results = {}
    
    # Key dispatcher functions
    targets = [
        (0x26099, 'clip_or_draw_dispatch'),
        (0x2245A, 'draw_from_struct'),
        (0x224C2, 'draw_struct_args_dispatch'),
        (0x3A8B1, 'sub_3A8B1'),  # Called by map_view_entity_project
    ]
    
    print("=== Exporting Drawing Dispatcher Functions ===\n")
    
    for addr, name in targets:
        print(f"Exporting {name} at 0x{addr:X}...")
        results[name] = export_function_disasm(addr, name)
        if 'error' not in results[name]:
            print(f"  Size: {results[name]['size']} bytes")
            print(f"  Xrefs: {results[name]['xrefs_to_count']}")
            print(f"  Calls: {len(results[name]['calls_from'])}")
        else:
            print(f"  ERROR: {results[name]['error']}")
        print()
    
    # Save JSON
    output_json = Path(__file__).parent / "draw_dispatch_functions.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ JSON saved to: {output_json}\n")
    
    # Save text files
    print("=== Saving Individual Disassembly Files ===\n")
    
    for name, data in results.items():
        if 'error' in data:
            continue
        
        output_txt = Path(__file__).parent.parent / "disassembly" / f"{name}_disasm.txt"
        
        with open(output_txt, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"{data['name']} Disassembly\n")
            f.write("=" * 80 + "\n")
            f.write(f"Address: {data['address']}\n")
            f.write(f"Size: {data['size']} bytes (0x{data['size']:X})\n")
            f.write("=" * 80 + "\n\n")
            
            if data['xrefs_to']:
                f.write(f"Called by {data['xrefs_to_count']} functions (showing first 20):\n")
                for xref in data['xrefs_to']:
                    f.write(f"  {xref['from']} - {xref['caller']}\n")
                f.write("\n")
            
            if data['calls_from']:
                f.write(f"Calls {len(data['calls_from'])} functions:\n")
                for call in data['calls_from']:
                    f.write(f"  {call['at']} -> {call['name']}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("Disassembly:\n")
            f.write("=" * 80 + "\n\n")
            
            for i, line in enumerate(data['disasm']):
                f.write(f"{i:4} | +0x{line['offset']:04X} | {line['address']} | {line['disasm']}")
                if 'comment' in line:
                    f.write(f"  ; {line['comment']}")
                f.write("\n")
        
        print(f"✓ {name}: {output_txt}")
    
    print(f"\n✓ All files saved!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
