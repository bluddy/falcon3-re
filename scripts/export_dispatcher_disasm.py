"""
Export disassembly of the dispatcher function directly.
Simple extraction without complex analysis.
"""

import idc
import idaapi

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\dispatcher_disasm.txt"

# Try the dispatcher address
dispatcher_addr = 0x03CE92

with open(output_file, 'w') as f:
    f.write("=== AI Entity Behavior Dispatcher Disassembly ===\n\n")
    
    func = idaapi.get_func(dispatcher_addr)
    if not func:
        f.write(f"ERROR: No function at 0x{dispatcher_addr:X}\n")
        idc.qexit(1)
        return
    
    f.write(f"Address: 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
    f.write(f"Size: {func.end_ea - func.start_ea} bytes\n\n")
    f.write("=" * 80 + "\n\n")
    
    # Export first 200 instructions
    ea = func.start_ea
    for i in range(200):
        if ea >= func.end_ea:
            f.write(f"\n[End of function at instruction {i}]\n")
            break
        
        disasm = idc.generate_disasm_line(ea, 0)
        f.write(f"0x{ea:05X}: {disasm}\n")
        ea = idc.next_head(ea)
    
    if ea < func.end_ea:
        f.write(f"\n[... {func.end_ea - ea} more bytes ...]\n")

print(f"Dispatcher disassembly: {output_file}")
idc.qexit(0)
