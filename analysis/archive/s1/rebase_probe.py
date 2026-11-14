"""Plan probe (COPY, DBFL_KILL): trial rebase of existing functions whose start is mid-instruction.
For each (old_start, new_start, clear_hi): remember name, del_func, drop the name, del_items(new_start..clear_hi), recursive-descend
from new_start inside [new_start, clear_hi), report disassembly, unreached bytes, and ORIGINAL code heads that are no longer heads.
Output: analysis/s1/rebase.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, ida_name, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\rebase.txt"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
# (label, old_start, new_start, clear_hi)
W = [("4334E", 0x4335A, 0x4334E, 0x43395)]
L = []


def descend(seed, lo, hi, made):
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
                    L.append("  create_insn FAILED at %X bytes %s" % (ea, (ida_bytes.get_bytes(ea, 5) or b"").hex()))
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
    for lab, old, new, hi in W:
        f = ida_funcs.get_func(old)
        name = idaapi.get_name(old)
        L.append("=== %s old=%X name=%s func %X-%X" % (lab, old, name, f.start_ea, f.end_ea))
        orig = set()
        a = new
        while a < hi:
            h = ida_bytes.get_item_head(a)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                orig.add(h)
            a = h + max(ida_bytes.get_item_size(h), 1)
        L.append("  del_func=%s" % ida_funcs.del_func(old))
        ida_name.set_name(old, "", ida_name.SN_NOWARN)
        ida_bytes.del_items(new, ida_bytes.DELIT_SIMPLE, hi - new)
        made = set()
        descend(new, new, hi, made)
        a = new
        while a < hi:
            h = ida_bytes.get_item_head(a)
            c = ida_bytes.is_code(ida_bytes.get_flags(h))
            L.append("  %X %-14s %s%s" % (h, (ida_bytes.get_bytes(h, max(ida_bytes.get_item_size(h), 1)) or b"").hex(),
                                          idc.generate_disasm_line(h, 0), "" if c else "   [NOT CODE]"))
            a = h + max(ida_bytes.get_item_size(h), 1)
        lost = sorted(x for x in orig if not (ida_bytes.is_code(ida_bytes.get_flags(x)) and ida_bytes.get_item_head(x) == x))
        L.append("  original code heads no longer heads: %d %s" % (len(lost), ["%X" % x for x in lost[:12]]))
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
