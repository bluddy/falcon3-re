"""Finding 55 IDA pass (READ-ONLY, no del_items, no auto_wait, no save).

1. Concrete: patched thunk at 0x2BD9D -- bytes, disasm, CodeRefsFrom on the JMP FAR,
   and whether the target resolves to a registered function (r*_e* / entry_ea).
2. For every unresolved dst whose +0x10000 lands exactly on a function start:
   show the source instruction, its raw far operand, and the two candidate linears.

Output: analysis/ida_falconcd/bridge55.log + analysis/ida_falconcd/bridge55.json
Usage: cmd /c "tools\\run_idat.bat tools\\bridge55.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_ua
import idaapi
import idautils
import idc

ROOT = r"C:\Users\yotam\projects\falcon3"
IDA = ROOT + r"\analysis\ida_falconcd"
log = []

try:
    cls = json.load(open(IDA + r"\classification.json"))
    refs = json.load(open(IDA + r"\callgraph_refs.json"))["refs"]
    starts = sorted(v["ea"] for v in cls.values())
    ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())
    from bisect import bisect_right

    def resolve(ea):
        i = bisect_right(starts, ea) - 1
        if i >= 0:
            s, e, k = ivs[i]
            if s <= ea < e:
                return k, (ea == s)
        return None, False

    # ---------- 1. the patched thunk ----------
    T = 0x2BD9D
    log.append("=== patched thunk @ 0x%X ===" % T)
    b = ida_bytes.get_bytes(T, 10)
    log.append("bytes: %s" % (b.hex() if b else "NONE"))
    ea = T
    heads = []
    for _ in range(6):
        m = idc.print_insn_mnem(ea)
        if not m:
            break
        heads.append(ea)
        log.append("  0x%X  %-8s %s" % (ea, m, idc.print_operand(ea, 0)))
        ea = ida_bytes.next_head(ea, T + 16)
        if ea >= T + 16:
            break
    for h in heads:
        for d in idautils.CodeRefsFrom(h, 0):
            k, ex = resolve(d)
            log.append("  CodeRefsFrom(0x%X) -> 0x%X  fn=%s exact=%s" % (h, d, k, ex))
        for d in idautils.DataRefsFrom(h):
            log.append("  DataRefsFrom(0x%X) -> 0x%X" % (h, d))
    f = ida_funcs.get_func(T)
    log.append("func covering 0x%X: %s" % (T, ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))

    # ---------- 2. shifted destinations: +0x10000 lands exactly on a fn start ----------
    dsts = sorted({d for s, d, _ in refs
                   if resolve(s)[0] is not None and resolve(d)[0] is None})
    shifted = []
    for d in dsts:
        k, ex = resolve(d + 0x10000)
        if k is not None and (d + 0x10000) in {iv[0] for iv in ivs}:
            shifted.append((d, k))
    log.append("")
    log.append("=== dst +0x10000 lands EXACT on a fn start: %d ===" % len(shifted))

    rows = []
    # pick the sources for the biggest clusters of such dsts
    want = dict(shifted)
    by_dst = {}
    for s, d, _ in refs:
        if d in want and resolve(s)[0] is not None:
            by_dst.setdefault(d, []).append(s)
    for d, k in shifted[:12]:
        srcs = by_dst.get(d, [])[:2]
        for s in srcs:
            f = ida_funcs.get_func(s)
            seg_s = idc.get_segm_name(s)
            seg_d = idc.get_segm_name(d)
            mn = idc.print_insn_mnem(s)
            # raw far operand if present
            op0 = idc.print_operand(s, 0)
            raw = None
            ins = ida_ua.insn_t()
            if ida_ua.decode_insn(ins, s) > 0:
                # operand 1 is the far target for call/jmp far (seg:off in op1)
                raw = "%s" % idc.print_operand(s, 1)
            rows.append(dict(src=s, dst=d, shifted=d + 0x10000, fn=k,
                             src_mnem=mn, src_op0=op0, src_op1=raw,
                             src_seg=seg_s, dst_seg=seg_d,
                             src_fn=(f.start_ea if f else None),
                             dst_seg_start=idc.get_segm_attr(d, idc.SEGATTR_START) if idc.get_segm_name(d) else None))
            log.append("  src 0x%X %-6s %-10s op0=%-12s op1=%-14s [%s -> %s]"
                       % (s, mn, "", str(op0)[:10], str(raw)[:14], seg_s, seg_d))
            log.append("       dst 0x%X  +0x10000 -> 0x%X = %s (fn start)" % (d, d + 0x10000, k))
    # segment bases for the two sides
    log.append("")
    log.append("segment bases (dst vs shifted):")
    seen = set()
    for d, k in shifted:
        key = (idc.get_segm_name(d), idc.get_segm_name(d + 0x10000))
        if key in seen:
            continue
        seen.add(key)
        ds = idc.get_segm_attr(d, idc.SEGATTR_START) if idc.get_segm_name(d) else None
        ss = idc.get_segm_attr(d + 0x10000, idc.SEGATTR_START) if idc.get_segm_name(d + 0x10000) else None
        log.append("   dst in %-12s(base=0x%X)  shifted in %-12s(base=0x%X)"
                   % (key[0], ds or 0, key[1], ss or 0))
        if len(seen) > 8:
            break

    json.dump(dict(thunk=dict(ea=T, bytes=(b.hex() if b else None)),
                   shifted=[dict(dst=d, fn=k) for d, k in shifted],
                   rows=rows),
              open(IDA + r"\bridge55.json", "w"), indent=1)
    log.append("wrote bridge55.json")
except Exception:
    log.append(traceback.format_exc())

open(IDA + r"\bridge55.log", "w").write("\n".join(log))
idaapi.qexit(0)
