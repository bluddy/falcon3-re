"""
Extract disassembly of font_file_parser - likely the actual RLE decompressor!

Run in IDA: File > Script file > disasm_font_parser.py
"""

import idaapi
import idc
import idautils

def disassemble_function(func_ea, output_file):
    """Extract complete disassembly."""
    
    func = idaapi.get_func(func_ea)
    if not func:
        print(f"ERROR: No function at 0x{func_ea:x}")
        return
    
    name = idc.get_func_name(func_ea)
    size = func.end_ea - func.start_ea
    
    print(f"Disassembling {name} @ 0x{func_ea:x} ({size} bytes)")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Function: {name}\n")
        f.write(f"Address: 0x{func_ea:x}\n")
        f.write(f"Size: {size} bytes\n")
        f.write(f"="*80 + "\n\n")
        
        for head in idautils.Heads(func.start_ea, func.end_ea):
            disasm = idc.GetDisasm(head)
            f.write(f"0x{head:06x}:  {disasm}\n")
            
            # Add call targets
            xrefs = list(idautils.XrefsFrom(head, 0))
            if xrefs:
                for xref in xrefs:
                    if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                        target_name = idc.get_func_name(xref.to)
                        if target_name:
                            f.write(f"          -> calls {target_name} @ 0x{xref.to:x}\n")
    
    print(f"Saved to: {output_file}")

def main():
    print("="*80)
    print("DISASSEMBLING font_file_parser - THE RLE DECOMPRESSOR!")
    print("="*80)
    
    idaapi.auto_wait()
    
    func_ea = 0x13142E
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\disasm_font_file_parser.txt'
    
    disassemble_function(func_ea, output_file)
    
    print(f"\n{'='*80}")
    print("Done! Analyze the output file to understand the RLE algorithm.")
    print("="*80)

if __name__ == '__main__':
    main()
