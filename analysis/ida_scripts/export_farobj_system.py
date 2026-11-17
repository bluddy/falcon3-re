"""
Export the far object system functions to understand symbol drawing.
This should reveal how aircraft and entity symbols are actually rendered.
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

def search_for_farobj_functions():
    """Search for all functions with 'farobj' or 'viewobj' in name."""
    results = []
    
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if func_name and ('farobj' in func_name.lower() or 'viewobj' in func_name.lower()):
            func = idaapi.get_func(func_ea)
            if func:
                results.append({
                    'name': func_name,
                    'address': hex(func_ea),
                    'size': func.end_ea - func.start_ea
                })
    
    return results

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    results = {}
    
    # Core far object functions (from sub_3A8B1 analysis)
    targets = [
        ('viewobj_project_advance', None),  # Will search by name
        ('farobj_sort_and_step', None),
        ('angle_matrix_far_invoke', None),
        ('es_ptr_slots_init', None),
        ('undoc_12418', 0x12418),  # Called by sub_3A8B1 path B
        ('active_farptr_set', None),
        ('view_extent_compute_1f6da', 0x1F6DA),
    ]
    
    print("=== Searching for Far Object Functions ===\n")
    
    # Search for functions by name
    found_addrs = {}
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        for target_name, target_addr in targets:
            if target_addr is None and func_name == target_name:
                found_addrs[target_name] = func_ea
                print(f"Found {target_name} at 0x{func_ea:X}")
            elif target_addr is not None and func_ea == target_addr:
                found_addrs[target_name] = func_ea
                print(f"Found {target_name} at 0x{func_ea:X}")
    
    print(f"\nFound {len(found_addrs)} target functions\n")
    
    # Export each found function
    print("=== Exporting Functions ===\n")
    
    for name, addr in found_addrs.items():
        print(f"Exporting {name}...")
        results[name] = export_function_disasm(addr, name)
        if 'error' not in results[name]:
            print(f"  Size: {results[name]['size']} bytes")
            print(f"  Calls: {len(results[name]['calls_from'])}")
        else:
            print(f"  ERROR: {results[name]['error']}")
        print()
    
    # Search for all farobj/viewobj functions
    print("=== Searching for All Far/View Object Functions ===\n")
    all_farobj = search_for_farobj_functions()
    print(f"Found {len(all_farobj)} farobj/viewobj functions\n")
    
    for func in all_farobj[:20]:  # First 20
        print(f"  {func['name']} - 0x{func['address']} ({func['size']} bytes)")
    
    results['all_farobj_functions'] = all_farobj
    
    # Save JSON
    output_json = Path(__file__).parent / "farobj_system_functions.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ JSON saved to: {output_json}\n")
    
    # Save text files
    print("=== Saving Individual Disassembly Files ===\n")
    
    for name, data in results.items():
        if name == 'all_farobj_functions':
            continue
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
