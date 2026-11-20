import idaapi
import idautils
import idc

idaapi.auto_wait()

out_path = r"C:\Users\yotam\projects\falcon3\analysis\ida_objects_xrefs.txt"
with open(out_path, "w") as f:
    f.write("=== XREFS TO OBJECTS ===\n")
    # Search for string "OBJECTS"
    for s in idautils.Strings():
        if "OBJECTS" in str(s):
            f.write(f"String '{str(s)}' at 0x{s.ea:x}\n")
            for xref in idautils.XrefsTo(s.ea):
                f.write(f"  xref from 0x{xref.frm:x}\n")
                func = idaapi.get_func(xref.frm)
                if func:
                    f.write(f"    in func {idaapi.get_func_name(func.start_ea)} (0x{func.start_ea:x})\n")

print("Done IDA script")
idc.qexit(0)
