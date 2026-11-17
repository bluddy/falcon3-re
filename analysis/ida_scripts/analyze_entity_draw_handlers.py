"""
Analyze the entity drawing handlers from the dispatch table.
Export a few key handlers to understand the drawing mechanism.
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
    
    # Get disassembly (first 100 lines only for large functions)
    disasm_lines = []
    ea = func.start_ea
    offset = 0
    line_count = 0
    max_lines = 100
    
    while ea < func.end_ea and line_count < max_lines:
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
        line_count += 1
    
    # Find calls
    calls_from = []
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem in ['call', 'callf']:
            target = idc.get_operand_value(ea, 0)
            if target != idc.BADADDR:
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
        'calls_from': calls_from[:20],  # First 20 calls
        'disasm': disasm_lines,
        'truncated': line_count >= max_lines
    }

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    # Target handlers from the dispatch table
    # Focus on even indices (odd are all sub_1F6C)
    handlers = [
        (0x900E, 'handler_00_sub_900E', 0),
        (0x90B4, 'handler_02_sub_90B4', 2),
        (0x8A87, 'handler_04_sub_8A87', 4),
        (0x7AC0, 'handler_06_sub_7AC0', 6),
        (0x7A7D, 'handler_08_sub_7A7D', 8),
        (0x7618, 'handler_10_sub_7618', 10),
        (0x1F6C, 'handler_ODD_sub_1F6C', 1),  # The common handler
    ]
    
    results = {}
    
    print("=== Exporting Entity Drawing Handlers ===\n")
    
    for addr, name, idx in handlers:
        print(f"Exporting {name} (index {idx})...")
        results[name] = export_function_disasm(addr, name)
        if 'error' not in results[name]:
            print(f"  Size: {results[name]['size']} bytes")
            print(f"  Calls: {len(results[name]['calls_from'])}")
            if results[name]['calls_from']:
                print(f"  Key calls:")
                for call in results[name]['calls_from'][:5]:
                    print(f"    - {call['name']}")
        else:
            print(f"  ERROR: {results[name]['error']}")
        print()
    
    # Save JSON
    output_json = Path(__file__).parent / "entity_draw_handlers.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ JSON saved to: {output_json}\n")
    
    # Save individual text files
    print("=== Saving Individual Handler Files ===\n")
    
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
            if data.get('truncated'):
                f.write("NOTE: Disassembly truncated to first 100 lines\n")
            f.write("=" * 80 + "\n\n")
            
            if data['calls_from']:
                f.write(f"Calls {len(data['calls_from'])} functions (showing first 20):\n")
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
            
            if data.get('truncated'):
                f.write("\n[... disassembly truncated ...]\n")
        
        print(f"✓ {name}: {output_txt}")
    
    print(f"\n✓ All files saved!")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
