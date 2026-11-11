import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142b.txt", "w")
LO, HI = 0x6E69E, 0x6E8F0
# xrefs into the gap from anywhere
out.write("fn r69 end: %X ; next fn start: %X\n" % (ida_funcs.get_func(0x6E581).end_ea, 0x6E8F0))
ins = []
for ea in range(LO, HI):
    for r in idautils.XrefsTo(ea, 0):
        if r.type in (16, 17, 18, 19, 1, 2, 3) and not (LO <= r.frm < HI):
            out.write("xref -> %X from %X type %d\n" % (ea, r.frm, r.type))
# item classification
kinds = {}
a = LO
while a < HI:
    fl = ida_bytes.get_flags(a); sz = max(ida_bytes.get_item_size(a), 1)
    k = "code" if ida_bytes.is_code(fl) else "data"
    kinds.setdefault(k, []).append((a, sz)); a += sz
out.write("code items %d (%d B), data items %d (%d B)\n" % (len(kinds.get("code", [])), sum(s for _, s in kinds.get("code", [])), len(kinds.get("data", [])), sum(s for _, s in kinds.get("data", []))))
cr = [a for a, _ in kinds.get("code", [])]
if cr: out.write("code range %X..%X\n" % (cr[0], cr[-1]))
# xrefs out of the gap (calls/jumps made by decoded code), and callers in loc_ symbols
for ea in range(LO, HI):
    n = idaapi.get_name(ea)
    if n and ida_bytes.has_user_name(ida_bytes.get_flags(ea)): out.write("name %X %s\n" % (ea, n))
out.close(); idc.qexit(0)
