"""
Extract disassembly of ui_menu_panel_renderer - the graphics loader function
"""
import idaapi
import idautils
import idc
import json

def get_function_disasm(ea):
    """Get complete disassembly of a function"""
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        # Get operand details
        operands = []
        for i in range(8):  # Check up to 8 operands
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_void:
                break
            op_str = idc.print_operand(ea, i)
            operands.append(op_str)
        
        # Get any comment
        comment = idc.get_cmt(ea, 0)
        if not comment:
            comment = idc.get_cmt(ea, 1)
        
        # Get any xrefs from this instruction
        xrefs = []
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idc.fl_CF, idc.fl_CN]:  # Call or jump
                target_name = idc.get_func_name(xref.to)
                if not target_name:
                    target_name = idc.get_name(xref.to)
                xrefs.append({
                    'to': xref.to,
                    'name': target_name,
                    'type': 'call' if xref.type == idc.fl_CN else 'jump'
                })
        
        lines.append({
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'disasm': disasm,
            'operands': operands,
            'comment': comment,
            'xrefs': xrefs
        })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return lines

def main():
    # Function addresses from rendering_analysis.json
    targets = {
        'ui_menu_panel_renderer': 0x133ADC,
        'menu_field_offset_calculate': 0x138E9C,  # Called by panel renderer
        'undoc_138E6A': 0x138E6A,  # Also called by panel renderer
    }
    
    result = {}
    
    for name, addr in targets.items():
        print(f"Extracting {name} at 0x{addr:X}...")
        disasm = get_function_disasm(addr)
        if disasm:
            result[name] = {
                'address': addr,
                'hex_addr': f'0x{addr:X}',
                'name': name,
                'disassembly': disasm
            }
            print(f"  Got {len(disasm)} instructions")
        else:
            print(f"  Failed to get function")
    
    # Save results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\graphics_loader_disasm.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Found {len(result)} functions")

if __name__ == '__main__':
    main()
    idc.qexit(0)
