import idautils
import idc
import idaapi

idaapi.auto_wait()

print("=== IDA Search for OBJECTS ===")
# Search for string "OBJECTS"
for s in idautils.Strings():
    if "OBJECTS" in str(s).upper():
        print(f"String '{s}' at 0x{s.ea:x}")
        for ref in idautils.DataRefsTo(s.ea):
            print(f"  Data ref from 0x{ref:x} ({idc.get_func_name(ref)})")
        for ref in idautils.CodeRefsTo(s.ea):
            print(f"  Code ref from 0x{ref:x} ({idc.get_func_name(ref)})")

idc.qexit(0)
