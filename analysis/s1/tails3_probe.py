"""Read-only (DBFL_KILL on a COPY): trial decode of 0x100CA8 body. Output: analysis/s1/tails3.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tails3.txt"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
L = []


def descend(seed, lo, hi, made, fails):
    todo = [seed]
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea:
                if ea in made:
                    break
            else:
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
                if ida_ua.create_insn(ea) <= 0:
                    fails.append(ea)
                    break
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and lo <= x.to < hi:
                        todo.append(x.to)
                if m == "jmp":
                    break
            ea += ida_bytes.get_item_size(ea)


try:
    LO, HI = 0x100CA8, 0x100DFB
    for a in (0x100CA8, 0x100D01, 0x100D0D, 0x100DFB):
        f = ida_funcs.get_func(a)
        L.append("func at %X: %s" % (a, ("%X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea))) if f else None))
    L.append("xrefs to 100D0E: %s" % ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x100D0E, 0)])
    L.append("xrefs to 100DF4: %s" % ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x100DF4, 0)])
    L.append("xrefs to 100DFB: %s" % ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x100DFB, 0)])
    L.append("xrefs to 100CA8: %s" % ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x100CA8, 0)])
    orig = set()
    a = 0x100D0D
    while a < HI:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    ida_bytes.del_items(0x100D0D, ida_bytes.DELIT_SIMPLE, HI - 0x100D0D)
    made, fails = set(), []
    descend(0x100CA8, 0x100CA8, 0x100D01, made, fails)
    descend(0x100D0E, 0x100D0E, HI, made, fails)
    descend(0x100DF4, 0x100D0E, HI, made, fails)
    L.append("made %d fails %s" % (len(made), ["%X" % x for x in fails]))
    a = LO
    while a < HI:
        h = ida_bytes.get_item_head(a)
        sz = max(ida_bytes.get_item_size(h), 1)
        c = ida_bytes.is_code(ida_bytes.get_flags(h))
        L.append("  %X %-14s %s%s" % (h, (ida_bytes.get_bytes(h, sz) or b"").hex(), idc.generate_disasm_line(h, 0), "" if c else "   [NOT CODE]"))
        a = h + sz
    lost = sorted(x for x in orig if not (ida_bytes.is_code(ida_bytes.get_flags(x)) and ida_bytes.get_item_head(x) == x))
    L.append("original heads no longer heads: %s" % ["%X" % x for x in lost])
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
