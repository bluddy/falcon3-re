import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag4.txt"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
L = []
def fn(a):
    f = ida_funcs.get_func(a)
    return ("%X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea))) if f else "-"
def xr(a):
    return ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]
def descend(seed, lo, hi, made, fails):
    todo = [seed]
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
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
                    if x.type in (18, 19) and lo <= x.to < hi: todo.append(x.to)
                if m == "jmp": break
            ea += ida_bytes.get_item_size(ea)
def trial(lab, start, lo, hi, seeds=None, dump=0):
    orig = set(); a = lo
    while a < hi:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)): orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    made, fails = set(), []
    for s in (seeds or [start]): descend(s, lo, hi, made, fails)
    cov = 0; a = lo; gaps = []; rets = []; out = []
    while a < hi:
        h = ida_bytes.get_item_head(a); sz = max(ida_bytes.get_item_size(h), 1)
        if ida_bytes.is_code(ida_bytes.get_flags(h)) and h in made:
            cov += sz
            if idc.print_insn_mnem(h) in RETS: rets.append("%X" % h)
            for x in idautils.XrefsFrom(h, 0):
                if x.type in (16, 17, 18, 19) and not (lo <= x.to < hi): out.append("%X->%X" % (h, x.to))
        else: gaps.append("%X(%d)" % (h, sz))
        a = h + sz
    lost = sorted(x for x in orig if not (ida_bytes.is_code(ida_bytes.get_flags(x)) and ida_bytes.get_item_head(x) == x))
    L.append("=== %s start %X [%X,%X): made %d fails %s covered %d/%d rets %s" % (lab, start, lo, hi, len(made), ["%X" % f for f in fails], cov, hi - lo, rets))
    L.append("   gaps %s" % gaps[:12])
    L.append("   lost heads %s" % [("%X" % x, xr(x)) for x in lost][:12])
    L.append("   outside flow %s" % out[:10])
    if dump:
        a = lo
        while a < min(hi, lo + dump):
            h = ida_bytes.get_item_head(a); sz = max(ida_bytes.get_item_size(h), 1)
            L.append("     %X %-14s %s" % (h, ida_bytes.get_bytes(h, sz).hex()[:28], idc.generate_disasm_line(h, 0)[:40])); a = h + sz
try:
    trial("69720", 0x69720, 0x69720, 0x69AC6, dump=40)
    trial("6EF30", 0x6EF30, 0x6EF30, 0x6F1CE, dump=40)
    trial("16743E", 0x16743E, 0x16743E, 0x167450, dump=60)
    L.append("6EF31 func end: %s ; 69723 end %s" % (fn(0x6EF31), fn(0x69723)))
    L.append("2E1C2 predecessor: ")
    a = 0x2E190
    while a < 0x2E1C2:
        h = ida_bytes.get_item_head(a); sz = max(ida_bytes.get_item_size(h), 1)
        L.append("  %X %-14s %-30s %s" % (h, ida_bytes.get_bytes(h, sz).hex()[:28], idc.generate_disasm_line(h, 0)[:30], fn(h).split()[0])); a = h + sz
    L.append("bytes 2E170: %s" % ida_bytes.get_bytes(0x2E170, 0x52).hex())
    L.append("22C71.. fn %s ; bytes 22C77 %s" % (fn(0x22C71), ida_bytes.get_bytes(0x22C77, 0x1A).hex()))
    L.append("data refs to 22C71..22C91: %s" % [(hex(a), xr(a)) for a in range(0x22C71, 0x22C91) if xr(a)])
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
