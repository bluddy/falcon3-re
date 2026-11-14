import os
os.environ["DBFL_KILL"] = "1"
import ida_auto, ida_bytes, ida_funcs, idautils, idc, idaapi, ida_name

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67f_probe.txt", "w")
LO, HI = 0x67F58, 0x683C5
fns = [(f, idaapi.get_name(f)) for f in idautils.Functions(LO, HI)]
out.write("functions in range: %s\n" % [(hex(a), n) for a, n in fns])
for a, n in fns:
    ida_funcs.del_func(a)
    ida_name.set_name(a, "", ida_name.SN_NOWARN)
ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
# own recursive descent from 67F58 inside the range
todo, seen, ends, outside = [LO], set(), [], set()
while todo:
    a = todo.pop()
    while LO <= a < HI + 0x400 and a not in seen:
        n = idc.create_insn(a)
        if not n:
            out.write("create_insn failed at %X\n" % a)
            break
        seen.add(a)
        m = idc.print_insn_mnem(a)
        nxt = a + n
        for r in idautils.XrefsFrom(a, 0):
            if r.type in (19, 18, 17, 16):
                if LO <= r.to < HI + 0x400:
                    if r.type in (19, 18):
                        todo.append(r.to)
                else:
                    outside.add((hex(a), hex(r.to), r.type))
        if m in ("retn", "retf", "iret", "jmp", "hlt"):
            ends.append((hex(a), idc.generate_disasm_line(a, 0)))
            break
        a = nxt
out.write("code heads: %d, max %X\n" % (len(seen), max(seen)))
out.write("terminators: %s\n" % ends)
out.write("outside refs: %s\n" % sorted(outside)[:40])
# data holes: bytes in range not covered by an instruction
cov = set()
for a in seen:
    for i in range(idc.get_item_size(a)):
        cov.add(a + i)
holes, h = [], None
for a in range(LO, max(seen) + 1):
    if a not in cov:
        if h is None:
            h = a
    else:
        if h is not None:
            holes.append((hex(h), a - h)); h = None
out.write("holes below max: %s\n" % holes[:30])
out.write("\ndisasm 67F58..67FF0\n")
a = LO
while a < LO + 0x90:
    out.write("%X %s\n" % (a, idc.generate_disasm_line(a, 0)))
    a += max(idc.get_item_size(a), 1)
out.close()
idc.qexit(0)
