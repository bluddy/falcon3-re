import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idautils, idc, idaapi, ida_name

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\m67_probe.txt", "w")
LO, HI = 0x67F58, 0x6940E
fns = [(f, idaapi.get_name(f)) for f in idautils.Functions(LO, HI)]
out.write("functions in [%X,%X): %d\n" % (LO, HI, len(fns)))
for a, n in fns:
    out.write("  %X %s\n" % (a, n))
# external references into the range, before clearing
ext = {}
for t in range(LO, HI):
    for r in idautils.XrefsTo(t, 0):
        if r.type in (16, 17, 18, 19) and not (LO <= r.frm < HI):
            ext.setdefault(t, []).append((hex(r.frm), r.type))
out.write("external code refs into range: %s\n" % ext)
for a, n in fns:
    ida_funcs.del_func(a)
    ida_name.set_name(a, "", ida_name.SN_NOWARN)
ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
seeds = [LO] + sorted(ext)
todo, seen = list(seeds), set()
term_mn = ("retn", "retf", "iret", "jmp", "hlt")
fails = []
while todo:
    a = todo.pop()
    while LO <= a < HI and a not in seen:
        n = ida_ua.create_insn(a)
        if not n:
            fails.append(a)
            break
        seen.add(a)
        mn = idc.print_insn_mnem(a)
        for r in idautils.XrefsFrom(a, 0):
            if r.type in (18, 19, 16, 17) and LO <= r.to < HI and r.to not in seen:
                todo.append(r.to)
        if mn in term_mn:
            break
        a += n
out.write("heads %d  max %X  fails %s\n" % (len(seen), max(seen), [hex(x) for x in fails]))
cov = set()
for a in seen:
    for i in range(idc.get_item_size(a)):
        cov.add(a + i)
holes, h = [], None
for a in range(LO, HI):
    if a not in cov:
        if h is None:
            h = a
    elif h is not None:
        holes.append((h, a - h)); h = None
if h is not None:
    holes.append((h, HI - h))
out.write("holes: %s\n" % [(hex(a), n) for a, n in holes])
out.write("\nlast-terminator before each hole / near end:\n")
for a, n in holes[:40]:
    p = idc.prev_head(a, LO)
    out.write("  hole %X(+%d): prev %X %s ; bytes %s\n" % (a, n, p, idc.generate_disasm_line(p, 0), ida_bytes.get_bytes(a, min(n, 16)).hex(" ")))
# data refs from the new code into the hole regions
out.close()
idc.qexit(0)
