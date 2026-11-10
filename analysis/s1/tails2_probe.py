"""Read-only (DBFL_KILL on a COPY). Output analysis/s1/tails2.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tails2.txt"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
L = []
try:
    f = ida_funcs.get_func(0x4335A)
    L.append("4335A func %X-%X name %s flags %X ; xrefs to 4335A %s ; to 43353 %s ; to 4334E %s" % (f.start_ea, f.end_ea, idaapi.get_name(0x4335A), f.flags,
        ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x4335A, 0)], ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x43353, 0)], ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x4334E, 0)]))
    f = ida_funcs.get_func(0x42F5B); L.append("42F5B func %X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(0x42F5B)))
    L.append("prev items of 4335A: " + str([("%X" % idc.prev_head(0x4335A, 0x43300))]))
    L.append("-- raw bytes 100CA8..100D40: " + ida_bytes.get_bytes(0x100CA8, 0x98).hex())
    L.append("-- 100D00 fixup/bytes: " + ida_bytes.get_bytes(0x100CFC, 14).hex())
    # who references offsets CA8/D0D/D01 as immediates in segment 2CF6
    for lab, ofs in (("CA8", 0x0CA8), ("D01", 0x0D01), ("D0D", 0x0D0D), ("D0E", 0x0D0E)):
        hits = []
        for ea in idautils.Heads(0x100000, 0x1011A0):
            if idc.print_insn_mnem(ea) in ("mov", "push") and idc.get_operand_type(ea, 1 if idc.print_insn_mnem(ea) == "mov" else 0) == idc.o_imm and idc.get_operand_value(ea, 1 if idc.print_insn_mnem(ea) == "mov" else 0) == ofs:
                hits.append("%X" % ea)
        L.append("imm %s hits in seg: %s" % (lab, hits))
    # trial: clear 100CA8..100D01 and descend from 100CA8
    LO, HI = 0x100CA8, 0x100D01
    for ea in range(LO, HI): pass
    ida_bytes.del_items(LO, ida_bytes.DELIT_SIMPLE, HI - LO)
    made = set(); todo = [LO]; fails = []
    while todo:
        ea = todo.pop()
        while LO <= ea < HI:
            if ea in made: break
            ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 1)
            if ida_ua.create_insn(ea) <= 0: fails.append(ea); break
            made.add(ea); m = idc.print_insn_mnem(ea)
            if m in RETS: break
            if m.startswith("j") or m.startswith("loop"):
                for x in idautils.XrefsFrom(ea, 0):
                    if x.type in (18, 19) and LO <= x.to < HI: todo.append(x.to)
                if m == "jmp": break
            ea += ida_bytes.get_item_size(ea)
    L.append("trial 100CA8: made %d fails %s" % (len(made), ["%X" % x for x in fails]))
    a = LO
    while a < HI:
        h = ida_bytes.get_item_head(a); sz = max(ida_bytes.get_item_size(h), 1)
        L.append("%X %-14s %s%s" % (h, ida_bytes.get_bytes(h, min(sz, 7)).hex(), idc.generate_disasm_line(h, 0), "" if h in made else "  [NOT REACHED]"))
        a = h + sz
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
