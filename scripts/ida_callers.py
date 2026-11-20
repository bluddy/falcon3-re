import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_callers.txt"
with open(out_path, "w") as f:
    for target in [0x264c5, 0x2676d, 0x268dd, 0x26b2e, 0x286ce]:
        name = idaapi.get_func_name(target)
        f.write(f"\nCallers to {name} (0x{target:x}):\n")
        for xref in idautils.XrefsTo(target):
            caller_name = idaapi.get_func_name(xref.frm)
            f.write(f"  0x{xref.frm:x} in {caller_name}\n")

idc.qexit(0)
