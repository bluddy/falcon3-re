import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_ua, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142h.txt", "w")
LO, HI = 0x6E696, 0x6E8B7
ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
RET = {"retn", "retf", "iret"}
BASE = 0x6E0B0
seeds = [0x6E696, 0x6E6BB, 0x6E6BC, 0x6E76A, 0x6E78D, 0x6E7B3, 0x6E809, 0x6E84B, 0x6E851]
# table words at odd addr 6E157.. : print raw
out.write("table bytes 6E150..6E1B0: %s\n" % ida_bytes.get_bytes(0x6E150, 0x60).hex(" "))
seen, todo = set(), list(seeds)
while todo:
    ea = todo.pop()
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
a = LO
while a < HI:
    if a in seen:
        out.write("%X %-16s %s\n" % (a, ida_bytes.get_bytes(a, ida_bytes.get_item_size(a)).hex(), idc.generate_disasm_line(a, 0)[:64])); a += ida_bytes.get_item_size(a)
    else:
        b = a
        while b < HI and b not in seen: b += 1
        out.write("%X -- undecoded %d bytes up to %X\n" % (a, b - a, b)); a = b
out.close(); idc.qexit(0)
