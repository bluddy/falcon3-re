"""Read-only: dump disassembly windows listed in dis_req.json -> dis_out.txt"""
import json
import idaapi
import idc
import ida_bytes
import ida_funcs

ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
req = json.load(open(ROOT + r"\dis_req.json"))
out = []
for lo, n in req:
    out.append("==== %X" % lo)
    ea = lo
    for _ in range(n):
        f = ida_funcs.get_func(ea)
        fn = ("[%X..%X]" % (f.start_ea, f.end_ea)) if f else "[nofn]"
        name = idc.get_name(ea) or ""
        sz = max(1, idc.get_item_size(ea))
        raw = " ".join("%02X" % ida_bytes.get_byte(ea + i) for i in range(min(sz, 8)))
        out.append("%06X %-14s %-24s %-14s %s" % (ea, fn, raw, name[:14], idc.generate_disasm_line(ea, 0)))
        ea = idc.next_head(ea, ea + 0x1000)
        if ea == idaapi.BADADDR:
            break
open(ROOT + r"\dis_out.txt", "w").write("\n".join(out))
idaapi.qexit(0)
