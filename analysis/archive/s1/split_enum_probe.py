"""split_enum_probe.py: enumerate ALL pure-split targets (read-only, DBFL_KILL).
For each owner function, list all call targets inside it that follow a ret/jmp and
have no non-call inner xrefs (i.e. safe to split at that address).  Groups split
points by owner and outputs the minimum-at entry first so batch selection is easy.
Output: analysis/s1/split_all.json
"""
import os
os.environ["DBFL_KILL"] = "1"
import json
import collections
import traceback

import idaapi
import ida_bytes
import ida_funcs
import ida_segment
import ida_ua
import ida_idp
import idc
import idautils

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\split_all.json"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw", "jmp", "jmpf"}

try:
    # collect every call target that lands inside a function (not at start)
    tg = collections.defaultdict(list)   # target_ea -> [caller_ea]
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
                    tg[t].append(item)

    # for each target decide pure_split / shared_tail / multi_chunk / not_head
    # we want only pure_split targets
    owners = collections.defaultdict(list)   # owner_ea -> [at_ea]
    for t, frm in tg.items():
        g = ida_funcs.get_func(t)
        if not g:
            continue
        # must be on an instruction head
        if ida_bytes.get_item_head(t) != t:
            continue
        # the byte immediately before t must end in a ret/jmp
        prev = idc.prev_head(t, g.start_ea)
        pm = idc.print_insn_mnem(prev) if prev != idaapi.BADADDR else ""
        if pm not in RETS:
            continue
        # no fall-through from the byte immediately before t
        # CodeRefsTo(t, 1) yields addresses (flow refs only)
        if any(x == prev for x in idautils.CodeRefsTo(t, 1)):
            continue
        # no non-call inner xref from inside the same function
        inner = False
        for x in idautils.XrefsTo(t, 0):
            if not x.iscode:
                continue
            f2 = ida_funcs.get_func(x.frm)
            if f2 and f2.start_ea == g.start_ea:
                if idc.print_insn_mnem(x.frm) not in ("call", "callf"):
                    inner = True
                    break
        if inner:
            continue
        # owner must be single-chunk (no tail chunks)
        it = ida_funcs.func_tail_iterator_t(g)
        ok = it.main()
        nchunks = 0
        while ok:
            nchunks += 1
            ok = it.next()
        if nchunks != 1:
            continue
        owners[g.start_ea].append(t)

    out_list = []
    total_splits = 0
    for owner_ea in sorted(owners):
        f = ida_funcs.get_func(owner_ea)
        ats = sorted(owners[owner_ea])
        total_splits += len(ats)
        s = ida_segment.getseg(owner_ea)
        seg = ida_segment.get_segm_name(s) if s else "?"
        out_list.append({
            "owner":      "%X" % owner_ea,
            "owner_end":  "%X" % f.end_ea,
            "owner_name": idc.get_func_name(owner_ea) or "",
            "seg":        seg,
            "far":        bool(f.flags & ida_funcs.FUNC_FAR),
            "splits":     ["%X" % at for at in ats],
            # number of callers per split point from within this owner's callers
            "callers":    [len(tg.get(at, [])) for at in ats],
        })

    result = {
        "total_owners": len(owners),
        "total_splits": total_splits,
        "owners": out_list,
    }
    open(OUT, "w").write(json.dumps(result, indent=1))
except Exception:
    open(OUT, "w").write(json.dumps({"error": traceback.format_exc()}))

idc.qexit(0)
