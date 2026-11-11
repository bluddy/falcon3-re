import os, json
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

runs = json.load(open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_scan138.json"))["runs"]
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
SKIP = {0x100505, 0x12BF89, 0x6E7C7, 0x67BA3, 0x6E16E, 0x2E235, 0x170F9, 0x172DA, 0x10852, 0x22269, 0x67F77, 0x6DFF0}
res = []
for r in runs:
    lo, hi = r["lo"], r["hi"]
    if lo in SKIP or r["size"] < 2 or r["last_mnem"] not in RETS | {"jmp"}:
        continue
    start, a = lo, lo
    while a < hi:
        n = ida_bytes.get_item_size(a)
        m = idc.print_insn_mnem(a)
        split = m in RETS
        if m == "jmp" and idc.get_operand_type(a, 0) in (idc.o_near, idc.o_far):
            tgt = idc.get_operand_value(a, 0)
            split = not (start <= tgt < a)
        a += n
        if split:
            res.append((start, a))
            start = a
    if start != hi:
        res.append(("UNTERMINATED", start, hi))
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or138d.txt", "w")
for x in res:
    out.write(repr(x) + "\n")
out.write("ADD_NEW = [%s]\n" % ", ".join("(0x%X, 0x%X)" % x for x in res if x[0] != "UNTERMINATED"))
out.close()
idc.qexit(0)
