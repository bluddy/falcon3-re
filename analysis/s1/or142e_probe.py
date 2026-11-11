import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_ua, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142e.txt", "w")
LO, HI = 0x6E696, 0x6E8B7
ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
RET = {"retn", "retf", "iret"}
seen, todo, blocks = set(), [0x6E696, 0x6E6BB, 0x6E6BC], set()
while todo:
    ea = todo.pop()
    blocks.add(ea)
    while LO <= ea < HI and ea not in seen:
        if ida_ua.create_insn(ea) <= 0:
            out.write("CANNOT DECODE %X\n" % ea); break
        seen.add(ea)
        m = idc.print_insn_mnem(ea); n = ida_bytes.get_item_size(ea)
        if m.startswith("j") or m.startswith("loop"):
            for x in idautils.XrefsFrom(ea, 0):
                if x.type in (18, 19) and LO <= x.to < HI: todo.append(x.to)
            if m == "jmp": break
        if m in RET: break
        ea += n
cov = sorted(seen)
out.write("decoded %d insns\n" % len(cov))
# gaps = bytes in [LO,HI) not covered by decoded insns
cov_b = set()
for a in cov:
    for i in range(ida_bytes.get_item_size(a)): cov_b.add(a + i)
gaps, a = [], LO
while a < HI:
    if a not in cov_b:
        b = a
        while b < HI and b not in cov_b: b += 1
        gaps.append((a, b)); a = b
    else: a += 1
out.write("gaps: %s\n" % [("%X-%X" % g) for g in gaps])
out.write("block starts reached: %s\n" % sorted("%X" % b for b in blocks))
for lo, hi in gaps:
    out.write("--- gap %X..%X\n" % (lo, hi))
    out.write("  " + ida_bytes.get_bytes(lo, hi - lo).hex(" ") + "\n")
out.close(); idc.qexit(0)
