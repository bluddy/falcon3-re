"""Plan probe (COPY, DBFL_KILL): clear [lo,hi) and recursive-descend from start; report coverage, terminators, unreached bytes,
call targets / branch targets leaving the range, and original code heads that stopped being heads.  Output: analysis/s1/trial.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\trial.txt"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
# (label, start, lo, hi)
W = [("129F7", 0x129F7, 0x129F7, 0x12B12), ("12B12", 0x12B12, 0x12B12, 0x12B62),
     ("10CE30+10CFA6", 0x10CE30, 0x10CFA5, 0x10CFEC)]
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
    for lab, start, lo, hi in W:
        orig = set()
        a = lo
        while a < hi:
            h = ida_bytes.get_item_head(a)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                orig.add(h)
            a = h + max(ida_bytes.get_item_size(h), 1)
        owners = sorted({"%X" % ida_funcs.get_func(a).start_ea for a in range(lo, hi) if ida_funcs.get_func(a)})
        for fs in [x for x in owners]:
            ida_funcs.del_func(int(fs, 16))
        ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
        made, fails = set(), []
        descend(start, start if start < lo else lo, hi, made, fails) if start < lo else descend(start, lo, hi, made, fails)
        L.append("=== %s start %X range %X..%X owners-in-range=%s" % (lab, start, lo, hi, owners))
        L.append("  heads made %d, create_insn failures %s" % (len(made), ["%X" % x for x in fails]))
        covered, a = 0, lo
        gaps, rets, out = [], [], []
        while a < hi:
            h = ida_bytes.get_item_head(a)
            sz = max(ida_bytes.get_item_size(h), 1)
            if ida_bytes.is_code(ida_bytes.get_flags(h)) and h in made:
                covered += sz
                m = idc.print_insn_mnem(h)
                if m in RETS:
                    rets.append("%X:%s" % (h, m))
                for x in idautils.XrefsFrom(h, 0):
                    if x.type in (16, 17, 18, 19) and not (lo <= x.to < hi):
                        out.append("%X->%X/%d" % (h, x.to, x.type))
            else:
                gaps.append((h, sz))
            a = h + sz
        L.append("  covered %d of %d bytes; rets %s" % (covered, hi - lo, rets))
        # merge gaps
        mg = []
        for h, sz in gaps:
            if mg and mg[-1][1] == h:
                mg[-1][1] = h + sz
            else:
                mg.append([h, h + sz])
        L.append("  unreached: %s" % ["%X-%X(%d)" % (x, y, y - x) for x, y in mg])
        for x, y in mg[:6]:
            L.append("    unreached %X: %s" % (x, (ida_bytes.get_bytes(x, min(y - x, 24)) or b"").hex()))
        lost = sorted(x for x in orig if not (ida_bytes.is_code(ida_bytes.get_flags(x)) and ida_bytes.get_item_head(x) == x))
        L.append("  original heads no longer heads: %d %s" % (len(lost), ["%X" % x for x in lost[:10]]))
        L.append("  out-of-range flow: %s" % out[:14])
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
