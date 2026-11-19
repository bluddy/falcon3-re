import idaapi
import idc

idaapi.auto_wait()

ea = 0x28A98
dis = idc.generate_disasm_line(ea, 0)
op0 = idc.print_operand(ea, 0)
val = idc.get_operand_value(ea, 0)
b = [idc.get_wide_byte(ea+i) for i in range(5)]
print(f"Instruction at 0x{ea:X}: {dis}")
print(f"Bytes: {[hex(x) for x in b]}")
print(f"Operand 0: {op0}, value: {hex(val)}")

with open(r'c:\Users\yotam\projects\falcon3\temp\call_28a98.txt', 'w') as f:
    f.write(f"{dis} | bytes: {[hex(x) for x in b]} | op0: {op0} | val: {hex(val)}\n")

idc.qexit(0)
