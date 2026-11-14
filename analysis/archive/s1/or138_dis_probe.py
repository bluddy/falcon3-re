import os, json
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

runs = json.load(open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_scan138.json"))["runs"]
TERM = {"retn", "retf", "iret", "iretw", "retnw", "retfw", "jmp"}
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or138_dis.txt", "w")
for r in runs:
    if r["last_mnem"] not in TERM and not r["xin"]:
        continue
    lo, hi = r["lo"], r["hi"]
    pf = ida_funcs.get_func(lo - 1)
    nf = ida_funcs.get_func(hi)
    out.write("=== %X..%X %dB prev=%s(end %s) next=%s xin=%s\n" % (
        lo, hi, r["size"], r["prev_name"], hex(r["prev_end"]) if r["prev_end"] else None, hex(nf.start_ea) if nf else None,
        [(hex(y[0]), y[2]) for y in r["xin"][:4]]))
    a = lo
    while a < hi:
        out.write("   %X %-16s %s\n" % (a, ida_bytes.get_bytes(a, ida_bytes.get_item_size(a)).hex(), idc.generate_disasm_line(a, 0)[:80]))
        a += ida_bytes.get_item_size(a)
out.close()
idc.qexit(0)
