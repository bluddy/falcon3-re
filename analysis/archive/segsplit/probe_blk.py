"""Read-only: functions in given ranges, and first code head after given EAs."""
import json, idaapi, idautils, ida_funcs, ida_bytes, idc
ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
res = {"funcs": {}, "next_code": {}, "func_at": {}}
for lo, hi in [(0x54AF0, 0x669F0), (0x500C0, 0x54AF0), (0x13DEE0, 0x154CB0), (0x12CEA0, 0x13D9C0)]:
    res["funcs"]["%X" % lo] = ["%X..%X" % (f, ida_funcs.get_func(f).end_ea) for f in idautils.Functions(lo, hi)]
for ea in [0x43AE0, 0x4F250, 0x4FD80, 0x4FD20, 0x11EB70, 0x1230E0, 0x1282A0, 0x131530, 0x131610, 0x132800, 0x1365A0]:
    e = ea
    while e < ea + 0x100 and not ida_bytes.is_code(ida_bytes.get_flags(e)):
        e += 1
    f = ida_funcs.get_func(ea)
    res["func_at"]["%X" % ea] = ("%X..%X" % (f.start_ea, f.end_ea)) if f else None
    res["next_code"]["%X" % ea] = "%X" % e
json.dump(res, open(ROOT + r"\probe_blk.json", "w"), indent=1)
idaapi.qexit(0)
