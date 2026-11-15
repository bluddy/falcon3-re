import idaapi
import idautils
import idc
import json

addr = 0x11C884
name = idc.get_func_name(addr)
print(f"Extracting {name} @ 0x{addr:X}")

func = idaapi.get_func(addr)
if not func:
    print("No function found!")
else:
    instructions = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            disasm = idc.generate_disasm_line(head, 0)
            instructions.append(f"0x{head:X}: {disasm}")
    
    output = '\n'.join(instructions)
    print(output)
    
    with open(rf'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\func_11c884_disasm.txt', 'w') as f:
        f.write(output)
    print(f"\n[+] Saved {len(instructions)} instructions")
