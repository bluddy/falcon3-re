import os, json
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idautils
runs = json.load(open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_scan138.json"))["runs"]
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or144b.txt", "w")
for r in runs:
    lo, hi = r["lo"], r["hi"]
    if r["size"] < 3 or lo in (0x6e7c7, 0x67ba3):
        continue
    ctx = ida_bytes.get_bytes(lo - 6, hi - lo + 12)
    pre = ida_bytes.get_item_head(lo - 1); nxt = hi
    out.write("%X..%X %d B  bytes[-6..+6]: %s | %s\n" % (lo, hi, hi - lo, ctx[:6].hex(), ctx[6:6 + hi - lo].hex() + " | " + ctx[6 + hi - lo:].hex()))
    out.write("   before: %s   after: %s\n" % (idc.generate_disasm_line(pre, 0)[:50], idc.generate_disasm_line(hi, 0)[:50]))
    out.write("   xrefs-to (any): %s\n" % [(hex(x.frm), x.type) for h in range(lo, hi) for x in idautils.XrefsTo(h, 0)][:6])
out.close(); idc.qexit(0)
