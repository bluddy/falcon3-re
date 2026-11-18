import idc
import idaapi
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\store_impact_disasm.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Disassembling store_impact_step @ 0x397FB...")
idaapi.auto_wait()

func_start = 0x397FB
func_end = idc.find_func_end(func_start)

print(f"Function: 0x{func_start:X} - 0x{func_end:X} ({func_end-func_start} bytes)\n")
print("Complete disassembly:\n")

ea = func_start
while ea < func_end:
    disasm = idc.generate_disasm_line(ea, 0)
    print(f"{disasm}")
    ea = idc.next_head(ea, func_end)

print("\n\nCalled by:\n")
callers = list(idautils.CodeRefsTo(func_start, True))
for caller in callers:
    caller_func = idc.get_func_name(caller)
    print(f"0x{caller:X} in {caller_func if caller_func else 'unknown'}")

print("\nDone.")
output_file.close()
idc.qexit(0)
