"""Read-only readiness survey of the IDB (run on a COPY; DBFL_KILL).
Writes analysis/segsplit/survey_ready.json"""
import json, collections, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_ua, ida_xref, ida_idp, ida_frame
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\survey_ready.json"
R = {}
try:
    segs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        segs.append(s)
    tot = collections.Counter()
    perseg = {}
    for s in segs:
        nm = ida_segment.get_segm_name(s)
        cls = ida_segment.get_segm_class(s)
        c = collections.Counter()
        ea = s.start_ea
        while ea < s.end_ea:
            f = ida_bytes.get_flags(ea)
            if not ida_bytes.is_loaded(ea):
                c["unloaded"] += 1; ea += 1; continue
            if ida_bytes.is_code(f):
                sz = ida_bytes.get_item_size(ea)
                c["code_in_fn" if ida_funcs.get_func(ea) else "code_orphan"] += sz
                ea += sz; continue
            if ida_bytes.is_data(f):
                sz = ida_bytes.get_item_size(ea)
                c["data"] += sz; ea += sz; continue
            if ida_bytes.is_tail(f):
                c["tail"] += 1; ea += 1; continue
            c["unexplored"] += 1; ea += 1
        kind = "res" if s.start_ea < 0x2CF60 else ("ovl" if cls == "CODE" else "data")
        perseg[nm] = dict(c, start=s.start_ea, end=s.end_ea, cls=cls, kind=kind)
        for k, v in c.items():
            tot[(kind, cls, k)] += v
    R["bytes"] = {"%s/%s/%s" % k: v for k, v in sorted(tot.items())}
    R["perseg"] = perseg

    # functions & calls
    funcs = list(idautils.Functions())
    fs = set(funcs)
    fc = collections.Counter()
    calls = collections.Counter()
    unres = collections.Counter()
    edges = collections.defaultdict(set)
    nocall_in = 0
    for fea in funcs:
        f = ida_funcs.get_func(fea)
        name = idc.get_func_name(fea)
        fc["named" if not name.startswith(("sub_", "nullsub", "unknown_libname")) else "auto_named"] += 1
        if f.flags & ida_funcs.FUNC_NORET: fc["noret"] += 1
        if f.flags & ida_funcs.FUNC_SP_READY == 0: fc["sp_not_ready"] += 1
        if f.flags & ida_funcs.FUNC_FAR: fc["far"] += 1
        if not any(True for _ in idautils.CodeRefsTo(fea, 0)) and not any(True for _ in idautils.DataRefsTo(fea)):
            fc["no_refs_in"] += 1
        for item in idautils.FuncItems(fea):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, item):
                continue
            mn = insn.get_canon_mnem()
            isc = ida_idp.is_call_insn(insn)
            isj = mn in ("jmp", "jmpf", "jmpfi", "jmpni")
            if not (isc or isj):
                continue
            op = insn.ops[0]
            tag = "call" if isc else "jmp"
            if op.type in (idaapi.o_near, idaapi.o_far):
                tgt = None
                for x in idautils.CodeRefsFrom(item, 0):
                    tgt = x
                if tgt is None:
                    calls[tag + "_direct_noref"] += 1; continue
                g = ida_funcs.get_func(tgt)
                if g and g.start_ea == fea and isj:
                    continue  # intra-function jump
                if tgt in fs:
                    calls[tag + "_direct_fn"] += 1
                    edges[fea].add(tgt)
                elif g:
                    calls[tag + "_direct_into_fn_body"] += 1
                    if isc: unres["call_mid:%s" % ida_segment.get_segm_name(ida_segment.getseg(tgt))] += 1
                elif ida_bytes.is_code(ida_bytes.get_flags(tgt)):
                    calls[tag + "_direct_orphan_code"] += 1
                else:
                    calls[tag + "_direct_noncode"] += 1
                    if isc: unres["call_noncode:%s" % (ida_segment.get_segm_name(ida_segment.getseg(tgt)) if ida_segment.getseg(tgt) else "unmapped")] += 1
            else:
                # indirect: count whether any user cref was added
                xs = [x for x in idautils.CodeRefsFrom(item, 0)]
                if isc:
                    calls["call_indirect_" + ("hasref" if xs else "noref")] += 1
                    for x in xs:
                        if x in fs: edges[fea].add(x)
                else:
                    calls["jmp_indirect_" + ("hasref" if xs else "noref")] += 1
    R["funcs"] = dict(fc, total=len(funcs))
    R["calls"] = dict(calls)
    R["unres_top"] = unres.most_common(25)

    # SCCs (Tarjan, iterative)
    idx = {}; low = {}; on = set(); st = []; sccs = []; n = [0]
    for v0 in funcs:
        if v0 in idx: continue
        work = [(v0, iter(edges.get(v0, ())))]
        idx[v0] = low[v0] = n[0]; n[0] += 1; st.append(v0); on.add(v0)
        while work:
            v, it = work[-1]
            adv = False
            for w in it:
                if w not in idx:
                    idx[w] = low[w] = n[0]; n[0] += 1; st.append(w); on.add(w)
                    work.append((w, iter(edges.get(w, ())))); adv = True; break
                elif w in on:
                    low[v] = min(low[v], idx[w])
            if adv: continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == idx[v]:
                comp = []
                while True:
                    w = st.pop(); on.discard(w); comp.append(w)
                    if w == v: break
                sccs.append(comp)
    big = sorted((c for c in sccs if len(c) > 1), key=len, reverse=True)
    selfloops = sum(1 for v in funcs if v in edges.get(v, ()))
    R["scc"] = {"n_nontrivial": len(big), "sizes": [len(c) for c in big[:15]],
                "funcs_in_cycles": sum(len(c) for c in big), "self_recursive": selfloops,
                "largest_members": [idc.get_func_name(x) for x in big[0][:40]] if big else []}
    nin = collections.Counter()
    for v, ws in edges.items():
        for w in ws: nin[w] += 1
    R["graph"] = {"edges": sum(len(w) for w in edges.values()),
                  "leaves": sum(1 for v in funcs if not edges.get(v)),
                  "roots_no_static_caller": sum(1 for v in funcs if nin[v] == 0)}
    R["auto_queue_empty"] = bool(idaapi.auto_is_ok())
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
