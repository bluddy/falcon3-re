"""
Extract disassembly of fixed_expand_0f3e - looks like a decompressor
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
        
        # Get operands
        operands = []
        for i in range(8):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_void:
                break
            operands.append(idc.print_operand(ea, i))
        
        # Get xrefs
        xrefs = []
        for xref in idautils.XrefsFrom(ea, 0):
            if xref.type in [idc.fl_CF, idc.fl_CN]:
                target_name = idc.get_func_name(xref.to)
                if not target_name:
                    target_name = idc.get_name(xref.to)
                xrefs.append({
                    'to': xref.to,
                    'hex_to': f'0x{xref.to:X}',
                    'name': target_name
                })
        
        lines.append({
            'addr': ea,
            'hex_addr': f'0x{ea:X}',
            'disasm': disasm,
            'operands': operands,
            'xrefs': xrefs
        })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return lines

def main():
    # Examine the fixed_expand function
    func_addr = 0x2859E
    
    print(f"Extracting fixed_expand_0f3e at 0x{func_addr:X}...")
    
    disasm = get_function_disasm(func_addr)
    
    if disasm:
        result = {
            'address': func_addr,
            'hex_addr': f'0x{func_addr:X}',
            'name': 'fixed_expand_0f3e',
            'size': len(disasm),
            'disassembly': disasm
        }
        
        output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\fixed_expand_disasm.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Saved {len(disasm)} instructions to: {output_path}")
    else:
        print("Failed to get function")

if __name__ == '__main__':
    main()
    idc.qexit(0)
