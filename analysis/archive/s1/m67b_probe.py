import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idautils, idc, idaapi, ida_name

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\m67b_probe.txt", "w")
LO, HI = 0x67F58, 0x6940E
fns = [f for f in idautils.Functions(LO, HI)]
# xrefs INTO hole starts and into the 4 tail regions before any change (data refs too)
for h in (0x68A18, 0x68F20, 0x69209, 0x6940B):
    out.write("xrefs to %X: %s\n" % (h, [(hex(r.frm), r.type) for r in idautils.XrefsTo(h, 0)]))
    out.write("  also any xref into [%X, +16): %s\n" % (h, [(hex(r.frm), hex(t), r.type) for t in range(h, h + 16) for r in idautils.XrefsTo(t, 0)]))
for a in fns:
    ida_funcs.del_func(a)
    ida_name.set_name(a, "", ida_name.SN_NOWARN)
ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
ext = [0x680BF, 0x6885E, 0x68E7D, 0x68F08, 0x69172, 0x6917A, 0x69182, 0x69227, 0x6930B, 0x67E29]
seen, fails = set(), []


def run(seeds):
    todo = list(seeds)
    while todo:
        a = todo.pop()
        while LO <= a < HI and a not in seen:
            n = ida_ua.create_insn(a)
            if not n:
                fails.append(a); break
            seen.add(a)
            mn = idc.print_insn_mnem(a)
            for r in idautils.XrefsFrom(a, 0):
                if r.type in (18, 19, 16, 17) and LO <= r.to < HI and r.to not in seen:
                    todo.append(r.to)
            if mn in ("retn", "retf", "iret", "jmp", "hlt"):
                break
            a += n


run([LO] + ext)
cov = lambda: {a + i for a in seen for i in range(idc.get_item_size(a))}
c = cov()


def holes():
    hs, h = [], None
    for a in range(LO, HI):
        if a not in c:
            h = a if h is None else h
        elif h is not None:
            hs.append((h, a - h)); h = None
    if h is not None:
        hs.append((h, HI - h))
    return hs


out.write("pass1 heads %d holes %s fails %s\n" % (len(seen), [(hex(a), n) for a, n in holes()], [hex(x) for x in fails]))
# seed holes that start with plausible code and see if they join the flow
for a, n in holes():
    before = len(seen)
    fails.clear()
    run([a])
    c = cov()
    out.write("  seed %X: +%d heads, fails %s\n" % (a, len(seen) - before, [hex(x) for x in fails]))
out.write("final holes %s\n" % [(hex(a), n) for a, n in holes()])
# which new-flow edges land inside decoded hole regions from OUTSIDE the holes (shows they are reached)
for a in (0x68A18, 0x68F20):
    out.write("xrefs to %X now: %s\n" % (a, [(hex(r.frm), r.type) for r in idautils.XrefsTo(a, 0)]))
for a, n in [(0x68A18, 12), (0x68F20, 12), (0x69209, 10), (0x6940B, 3)]:
    p = a
    for _ in range(n // 3 + 3):
        out.write("   %X %s\n" % (p, idc.generate_disasm_line(p, 0))); p += max(idc.get_item_size(p), 1)
    out.write("   --\n")
out.close()
idc.qexit(0)
