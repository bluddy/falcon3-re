"""
Extract the decompression and callback functions
"""
import idaapi
import idautils
import idc
import json

def get_function_disasm_detailed(ea, max_instrs=500):
    """Get complete disassembly of a function with all details"""
    func = idaapi.get_func(ea)
    if not func:
        return None
    
    lines = []
    ea = func.start_ea
    instr_count = 0
    
    while ea < func.end_ea and instr_count < max_instrs:
        disasm = idc.generate_disasm_line(ea, 0)
        
        # Get operand details
        operands = []
        for i in range(8):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_void:
                break
            op_str = idc.print_operand(ea, i)
            operands.append(op_str)
        
        # Get any xrefs from this instruction
        xrefs = []
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idc.fl_CF, idc.fl_CN, idc.fl_JN, idc.fl_JF]:
                target_name = idc.get_func_name(xref.to)
                if not target_name:
                    target_name = idc.get_name(xref.to)
                xref_type = 'call' if xref.type == idc.fl_CN else 'jump'
                xrefs.append({
                    'to': xref.to,
                    'hex_to': f'0x{xref.to:X}',
                    'name': target_name,
                    'type': xref_type
                })
        
        lines.append({
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'disasm': disasm,
            'operands': operands,
            'xrefs': xrefs
        })
        
        ea = idc.next_head(ea, func.end_ea)
        instr_count += 1
    
    return lines

def main():
    # Target functions involved in graphics decompression
    targets = {
        'graphics_record_processor': 0x2BFC3,  # Main decompressor loop
        'idx_record_callback_1': 0x1396E6,  # Callback 1 from loader
        'idx_record_callback_2': 0x139737,  # Callback 2 from loader
        'rle_vga_decompressor': 0x88460,  # The RLE decompressor we found earlier
    }
    
    result = {}
    
    for name, addr in targets.items():
        print(f"Extracting {name} at 0x{addr:X}...")
        disasm = get_function_disasm_detailed(addr)
        if disasm:
            result[name] = {
                'address': addr,
                'hex_addr': f'0x{addr:X}',
                'name': name,
                'size': len(disasm),
                'disassembly': disasm
            }
            print(f"  Got {len(disasm)} instructions")
        else:
            print(f"  Failed to get function at 0x{addr:X}")
    
    # Save results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\decompressor_disasm.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Found {len(result)} functions")

if __name__ == '__main__':
    main()
    idc.qexit(0)
