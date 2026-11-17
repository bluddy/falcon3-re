"""Quick xref dump for byte_595B2"""
import idaapi
import idc
import idautils

idaapi.auto_wait()

var = 0x595B2
print(f"Cross-references to byte_595B2 (0x{var:X}):")

count = 0
for xref in idautils.DataRefsTo(var):
    count += 1
    func = idc.get_func_name(idc.get_func_attr(xref, idc.FUNCATTR_START))
    print(f"{count}. 0x{xref:X} in {func}: {idc.generate_disasm_line(xref, 0)}")
    if count > 50:
        print("... (truncated, >50 references)")
        break

idc.qexit(0)
