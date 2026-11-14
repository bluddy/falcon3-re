"""COPY, DBFL_KILL: clear 10CE30..10CFEC, descend from 10CE30; report tail and structure. Output analysis/s1/r27.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\r27.txt"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
LO, HI = 0x10CE30, 0x10CFEC
L = []
def descend(seed, made, fails):
    todo = [seed]
    while todo:
        ea = todo.pop()
        while LO <= ea < HI:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea:
                if ea in made: break
            else:
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
                if ida_ua.create_insn(ea) <= 0:
                    fails.append(ea); break
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS: break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and LO <= x.to < HI: todo.append(x.to)
                if m == "jmp": break
            ea += ida_bytes.get_item_size(ea)
try:
    f = ida_funcs.get_func(0x10CFA6)
    L.append("owners in range: %s" % sorted({"%X-%X" % (ida_funcs.get_func(a).start_ea, ida_funcs.get_func(a).end_ea) for a in range(LO, HI) if ida_funcs.get_func(a)}))
    L.append("xrefs to 10CFEC %s ; to 10CE30 %s" % (["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x10CFEC, 0)], ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x10CE30, 0)]))
    for fs in {ida_funcs.get_func(a).start_ea for a in range(LO, HI) if ida_funcs.get_func(a)}:
        ida_funcs.del_func(fs)
    import ida_name
    L.append('name at 10CFA6 before: %r' % idaapi.get_name(0x10CFA6))
    ida_name.set_name(0x10CFA6, '', ida_name.SN_NOWARN)
    ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
    made, fails = set(), []
    descend(LO, made, fails)
    L.append("made %d fails %s" % (len(made), ["%X" % x for x in fails]))
    a = LO
    while a < HI:
        h = ida_bytes.get_item_head(a); sz = max(ida_bytes.get_item_size(h), 1)
        L.append("%X %-16s %s%s" % (h, ida_bytes.get_bytes(h, sz).hex(), idc.generate_disasm_line(h, 0), "" if h in made else "  [NOT REACHED]"))
        a = h + sz
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
