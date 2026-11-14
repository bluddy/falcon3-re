"""Read-only: for every direct call whose target is inside a function body,
dump target context + caller context.  Output analysis/s1/mid_detail.json"""
import json, collections, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_ua, ida_idp
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\mid_detail.json"
R = {"targets": []}


def lines(ea, nb, na):
    out = []
    x = ea
    for _ in range(nb):
        p = idc.prev_head(x, 0)
        if p == idaapi.BADADDR:
            break
        x = p
    for _ in range(nb + na + 1):
        if x == idaapi.BADADDR:
            break
        out.append("%X %s %s" % (x, "C" if ida_bytes.is_code(ida_bytes.get_flags(x)) else "D",
                                 idc.generate_disasm_line(x, 0)))
        x = idc.next_head(x, idaapi.BADADDR)
    return out


try:
    tg = collections.defaultdict(list)
    for fea in idautils.Functions():
        for item in idautils.FuncItems(fea):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, item) or not ida_idp.is_call_insn(insn):
                continue
            if insn.ops[0].type not in (idaapi.o_near, idaapi.o_far):
                continue
            for t in idautils.CodeRefsFrom(item, 0):
                g = ida_funcs.get_func(t)
                if g and g.start_ea != t:
                    tg[t].append((item, fea))
    for t, frm in sorted(tg.items()):
        g = ida_funcs.get_func(t)
        head = ida_bytes.get_item_head(t)
        rec = {"t": t, "fn": g.start_ea, "fn_end": g.end_ea, "fn_name": idc.get_func_name(g.start_ea),
               "seg": ida_segment.get_segm_name(ida_segment.getseg(t)), "head": head,
               "bytes": (idc.get_bytes(t, 8) or b"").hex(),
               "tctx": lines(head, 3, 3),
               "callers": [{"ea": a, "fn": f, "fn_name": idc.get_func_name(f),
                            "ctx": lines(a, 2, 1)} for a, f in frm[:6]],
               "n": len(frm)}
        # would decoding at t give a sane instruction run ending in a terminator?
        x, run, term = t, 0, None
        while run < 64:
            insn = ida_ua.insn_t()
            n = ida_ua.decode_insn(insn, x)
            if n <= 0:
                term = "undecodable"
                break
            m = insn.get_canon_mnem()
            run += 1
            if m in ("retn", "retf", "iret", "jmp", "jmpf", "jmpfi", "jmpni"):
                term = m
                break
            x += n
        rec["fresh"] = [run, term, x]
        R["targets"].append(rec)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
