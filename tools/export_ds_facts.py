"""Read-only IDA export of the facts tools/plan_default_ds.py needs (finding 122).

For every function: entry DS as IDA has it, every DS change point inside the
function (with the instruction that opened it), every call into it, and its
implicit-DS memory operands.  DS at any instruction is expressed as a *state*:
  "E"          the range began at/before the function start (= entry DS)
  "R:<ea>"     the range opened at <ea> inside the function
`pop ds` change points carry the matching push (flow-sensitive stack
emulation over the function's flow chart), `mov ds,cs:[x]` ones the slot.

Writes analysis/dgroup/ds_facts.json (or $DSFACTS).  Never saves.
Usage: idat -A -S"tools\\export_ds_facts.py" <idb copy>
"""
import json
import os
import traceback

import ida_bytes
import ida_funcs
import ida_gdl
import ida_loader
import ida_segment
import ida_segregs
import ida_ua
import ida_xref
import idaapi
import idautils
import idc

OUT = os.environ.get("DSFACTS") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "analysis", "dgroup", "ds_facts.json")
DS, ES, SS, CS = (idaapi.str2reg(r) for r in ("ds", "es", "ss", "cs"))
SREG_NAME = {DS: "ds", ES: "es", SS: "ss", CS: "cs"}
SP, BP = 4, 5  # o_reg numbers in the 8086 module


def para(v):
    if v is None or v in (idaapi.BADSEL, 0xFFFF, 0xFFFFFFFF):
        return None
    return ida_segment.sel2para(v)


def in_func(f, ea):
    g = ida_funcs.get_func(ea)
    return g is not None and g.start_ea == f.start_ea


def state(f, ea):
    rr = ida_segregs.sreg_range_t()
    if not ida_segregs.get_sreg_range(rr, ea, DS):
        return "E"
    if rr.start_ea <= f.start_ea or not in_func(f, rr.start_ea):
        return "E"
    return "R:%d" % rr.start_ea


def brk(ea):
    """True if a DS range starts exactly at ea"""
    rr = ida_segregs.sreg_range_t()
    return bool(ida_segregs.get_sreg_range(rr, ea, DS) and rr.start_ea == ea)


def decode(ea):
    insn = ida_ua.insn_t()
    return insn if ida_ua.decode_insn(insn, ea) else None


def ds_ops(ea, insn):
    """implicit-DS memory operands: no segment prefix, not BP-based"""
    out = []
    for op in insn.ops:
        if op.type == ida_ua.o_void:
            break
        if op.type not in (ida_ua.o_mem, ida_ua.o_displ, ida_ua.o_phrase):
            continue
        txt = idc.print_operand(ea, op.n) or ""
        if any(p in txt for p in ("es:", "cs:", "ss:")):
            continue
        if op.type != ida_ua.o_mem and "bp" in txt:
            continue
        out.append(op)
    return out


def ret_pop(fs):
    """bytes popped by the callee's returns (pascal `ret N`), None if unknown/mixed"""
    f = ida_funcs.get_func(fs)
    if f is None:
        return None
    ns = set()
    for h in idautils.FuncItems(fs):
        insn = decode(h)
        if insn and insn.get_canon_mnem() in ("retn", "retf"):
            ns.add(insn.ops[0].value if insn.ops[0].type == ida_ua.o_imm else 0)
    return ns.pop() if len(ns) == 1 else None


_retpop = {}


def callee_pop(h, insn):
    for x in idautils.XrefsFrom(h, 0):
        if x.iscode and x.type in (ida_xref.fl_CN, ida_xref.fl_CF):
            g = ida_funcs.get_func(x.to)
            if g is None or g.start_ea != x.to:
                return None
            if x.to not in _retpop:
                _retpop[x.to] = ret_pop(x.to)
            return _retpop[x.to]
    return None


def step(h, insn, st, pops):
    """apply one instruction to the symbolic stack; st = (stack tuple, bp depth) or None"""
    if st is None:
        return None
    stk, bpd = list(st[0]), st[1]
    m = insn.get_canon_mnem()
    o0, o1 = insn.ops[0], insn.ops[1]
    if m == "push":
        if o0.type == ida_ua.o_reg and o0.reg in SREG_NAME:
            stk.append(("s", SREG_NAME[o0.reg], h))
        else:
            stk.append(("?",))
    elif m == "pop":
        if not stk:
            return None
        top = stk.pop()
        if o0.type == ida_ua.o_reg and o0.reg == DS:
            pops.setdefault(h, set()).add(top)
        elif o0.type == ida_ua.o_reg and o0.reg == SP:
            return None
    elif m == "pushf":
        stk.append(("?",))
    elif m == "popf":
        if not stk:
            return None
        stk.pop()
    elif m == "pusha":
        stk += [("?",)] * 8
    elif m == "popa":
        if len(stk) < 8:
            return None
        del stk[-8:]
    elif m in ("call", "callfi", "callni"):
        if m == "call":
            n = callee_pop(h, insn)
            if n is None:
                return None
        else:
            return None
        if n % 2 or len(stk) < n // 2:
            return None
        if n:
            del stk[-(n // 2):]
    elif m == "enter":
        if o0.type != ida_ua.o_imm or o0.value > 0x2000:
            return None
        stk.append(("?",))
        bpd = len(stk)
        stk += [("?",)] * (o0.value // 2)
    elif m == "leave":
        if bpd is None or bpd > len(stk) or bpd == 0:
            return None
        del stk[bpd:]
        stk.pop()
        bpd = None
    elif o0.type == ida_ua.o_reg and o0.reg == SP:
        if m in ("add", "sub") and o1.type == ida_ua.o_imm and o1.value % 2 == 0:
            v = o1.value & 0xFFFF
            k = v // 2 if v < 0x8000 else -((0x10000 - v) // 2)
            if abs(k) > 0x1000:
                return None
            if m == "sub":
                stk += [("?",)] * k if k >= 0 else []
                if k < 0:
                    return None
            else:
                if k < 0 or len(stk) < k:
                    return None
                if k:
                    del stk[-k:]
        elif m == "mov" and o1.type == ida_ua.o_reg and o1.reg == BP:
            if bpd is None or bpd > len(stk):
                return None
            del stk[bpd:]
        elif m == "lea" and o1.type == ida_ua.o_displ and o1.phrase in (6,) and bpd is not None:
            d = o1.addr if o1.addr < 0x8000 else o1.addr - 0x10000
            if d > 0 or d % 2:
                return None
            k = bpd + (-d) // 2
            if k > len(stk):
                return None
            del stk[k:]
        else:
            return None
    elif m == "mov" and o0.type == ida_ua.o_reg and o0.reg == BP and o1.type == ida_ua.o_reg and o1.reg == SP:
        bpd = len(stk)
    elif o0.type == ida_ua.o_reg and o0.reg == BP and m in ("pop",):
        bpd = None
    elif m in ("xchg",) and ((o0.type == ida_ua.o_reg and o0.reg == SP) or (o1.type == ida_ua.o_reg and o1.reg == SP)):
        return None
    return (tuple(stk), bpd)


def merge(a, b):
    if a is None or b is None:
        return None
    if a == b:
        return a
    if len(a[0]) != len(b[0]):
        return None
    stk = tuple(x if x == y else ("?",) for x, y in zip(a[0], b[0]))
    return (stk, a[1] if a[1] == b[1] else None)


def match_pops(f):
    """flow-sensitive push/pop matching -> {pop_ea: (sreg, push_ea) | None}"""
    try:
        fc = ida_gdl.FlowChart(f)
    except Exception:
        return {}
    blocks = {b.start_ea: b for b in fc}
    entry_st = {f.start_ea: ((), None)}
    work = [f.start_ea]
    seen = 0
    pops = {}
    while work and seen < 20000:
        seen += 1
        bs = work.pop()
        b = blocks.get(bs)
        if b is None:
            continue
        st = entry_st[bs]
        ea = b.start_ea
        while ea < b.end_ea and ea != idaapi.BADADDR:
            insn = decode(ea)
            if insn is None:
                st = None
                break
            st = step(ea, insn, st, pops)
            ea = idc.next_head(ea, b.end_ea)
        for s in b.succs():
            old = entry_st.get(s.start_ea, "unset")
            new = st if old == "unset" else merge(old, st)
            if old == "unset" or new != old:
                entry_st[s.start_ea] = new
                work.append(s.start_ea)
    out = {}
    for h, tops in pops.items():
        if len(tops) == 1:
            t = next(iter(tops))
            out[h] = [t[1], t[2]] if t[0] == "s" else None
        else:
            out[h] = None
    return out


def opener(f, rs, pops):
    """classify the instruction that opened DS range rs"""
    p = idc.prev_head(rs, f.start_ea)
    if p == idaapi.BADADDR or not in_func(f, p) or p + ida_bytes.get_item_size(p) != rs:
        return {"kind": "other"}
    insn = decode(p)
    if insn is None:
        return {"kind": "other"}
    m = insn.get_canon_mnem()
    o0, o1 = insn.ops[0], insn.ops[1]
    if m == "pop" and o0.type == ida_ua.o_reg and o0.reg == DS:
        mt = pops.get(p)
        d = {"kind": "pop", "at": p}
        # what follows the pop (an epilogue `pop ds; retf` restores the caller's DS)
        nxt, h = [], rs
        while len(nxt) < 4 and h != idaapi.BADADDR and in_func(f, h):
            ni = decode(h)
            if ni is None:
                break
            nxt.append(ni.get_canon_mnem())
            h = idc.next_head(h, idaapi.BADADDR)
        d["next"] = nxt
        if mt:
            d["push_reg"], d["push_ea"] = mt
            d["push_state"] = state(f, mt[1])
            if mt[0] == "es":
                d["es"] = para(ida_segregs.get_sreg(mt[1], ES))
        return d
    if m == "mov" and o0.type == ida_ua.o_reg and o0.reg == DS:
        if o1.type == ida_ua.o_mem and "cs:" in (idc.print_operand(p, 1) or ""):
            cs = ida_segregs.get_sreg(p, CS)
            seg = ida_segment.getseg(p)
            off = o1.addr & 0xFFFF
            return {"kind": "slot", "at": p, "slot_ea": ida_segment.get_segm_base(seg) + off,
                    "cs_para": para(cs), "off": off,
                    "code": ida_bytes.get_bytes(p, 16).hex()}
        q = idc.prev_head(p, f.start_ea)
        qi = decode(q) if q != idaapi.BADADDR and in_func(f, q) else None
        prev = idc.generate_disasm_line(q, 0).split(";")[0].strip() if qi else None
        if o1.type == ida_ua.o_reg:
            if (qi and qi.get_canon_mnem() == "mov" and qi.ops[0].type == ida_ua.o_reg
                    and qi.ops[0].reg == o1.reg and qi.ops[1].type == ida_ua.o_reg and qi.ops[1].reg == SS):
                return {"kind": "ss", "at": p}
            if (qi and qi.get_canon_mnem() == "mov" and qi.ops[0].type == ida_ua.o_reg
                    and qi.ops[0].reg == o1.reg and qi.ops[1].type == ida_ua.o_reg
                    and qi.ops[1].reg in (ES, DS, CS)):
                # `mov r,es|ds|cs; mov ds,r` (only when the copy is adjacent)
                src = SREG_NAME[qi.ops[1].reg]
                return {"kind": "copy", "at": p, "src": src, "src_state": state(f, q),
                        "src_val": para(ida_segregs.get_sreg(q, qi.ops[1].reg))}
            # `xor r,r` / `mov r,0` right before: DS really is 0 (BIOS data area)
            zero = bool(qi and ((qi.get_canon_mnem() in ("xor", "sub") and qi.ops[0].type == ida_ua.o_reg
                                 and qi.ops[1].type == ida_ua.o_reg and qi.ops[0].reg == qi.ops[1].reg == o1.reg)
                                or (qi.get_canon_mnem() == "mov" and qi.ops[0].type == ida_ua.o_reg
                                    and qi.ops[0].reg == o1.reg and qi.ops[1].type == ida_ua.o_imm
                                    and qi.ops[1].value == 0)))
            return {"kind": "movreg", "at": p, "prev": prev, "zero": zero}
        return {"kind": "movmem", "at": p, "prev": prev}
    if m == "lds":
        return {"kind": "lds", "at": p}
    return {"kind": "other", "at": p}


def main():
    funcs = []
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        seg = ida_segment.getseg(fs)
        chunks = [list(c) for c in idautils.Chunks(fs)]
        pops = match_pops(f)
        ranges = {}
        ops = {}
        for cs_, ce in chunks:
            rr = ida_segregs.sreg_range_t()
            ea = cs_
            while ea < ce:
                if not ida_segregs.get_sreg_range(rr, ea, DS):
                    break
                if rr.start_ea > fs and in_func(f, rr.start_ea) and rr.start_ea not in ranges:
                    d = opener(f, rr.start_ea, pops)
                    d["val"] = para(rr.val)
                    d["tag"] = rr.tag
                    ranges[rr.start_ea] = d
                ea = rr.end_ea
        for h in idautils.FuncItems(fs):
            insn = decode(h)
            if insn is None:
                continue
            ol = ds_ops(h, insn)
            if not ol:
                continue
            k = state(f, h)
            o = ops.setdefault(k, {"n": 0, "mem": []})
            o["n"] += len(ol)
            for op in ol:
                if op.type == ida_ua.o_mem:
                    o["mem"].append(op.addr & 0xFFFF)
        calls = []
        for x in idautils.XrefsTo(fs, 0):
            if not x.iscode or x.type not in (ida_xref.fl_CN, ida_xref.fl_CF, ida_xref.fl_JN, ida_xref.fl_JF,
                                              ida_xref.fl_F):
                continue
            g = ida_funcs.get_func(x.frm)
            if g is not None and g.start_ea == fs:
                continue
            if x.type in (ida_xref.fl_JN, ida_xref.fl_JF, ida_xref.fl_F) and g is None:
                continue
            calls.append({"frm": x.frm, "far": x.type in (ida_xref.fl_CF, ida_xref.fl_JF),
                          "jump": x.type in (ida_xref.fl_JN, ida_xref.fl_JF),
                          "fall": x.type == ida_xref.fl_F,
                          "user": bool(x.user),
                          "func": g.start_ea if g else None,
                          "state": state(g, x.frm) if g else None,
                          "ida": para(ida_segregs.get_sreg(x.frm, DS))})
        # tail chunks: DS state at every in-function branch into them
        tails = {}
        for cs_, _ce in chunks:
            if cs_ == fs:
                continue
            tails[str(cs_)] = {"val": para(ida_segregs.get_sreg(cs_, DS)),
                               "states": [state(f, x.frm) for x in idautils.XrefsTo(cs_, 0)
                                          if x.iscode and in_func(f, x.frm) and x.frm != cs_]}
        er = ida_segregs.sreg_range_t()
        ida_segregs.get_sreg_range(er, fs, DS)
        prologue, h = [], fs
        while len(prologue) < 6 and h != idaapi.BADADDR and in_func(f, h):
            prologue.append(idc.generate_disasm_line(h, 0).split(";")[0].strip())
            h = idc.next_head(h, idaapi.BADADDR)
        funcs.append({"start": fs, "end": f.end_ea, "chunks": chunks, "tails": tails,
                      "name": idaapi.get_name(fs),
                      "seg": ida_segment.get_segm_name(seg), "cs": para(seg.sel),
                      "seg_start": seg.start_ea,
                      "entry": para(ida_segregs.get_sreg(fs, DS)),
                      "entry_rs": er.start_ea, "entry_tag": er.tag,
                      "entry_ss": para(ida_segregs.get_sreg(fs, SS)),
                      "prologue": prologue,
                      "end_ds": para(ida_segregs.get_sreg(f.end_ea, DS)),
                      # DS just past each chunk and whether a range starts there
                      "chunk_ends": [[ce, para(ida_segregs.get_sreg(ce, DS)), brk(ce)] for _s, ce in chunks],
                      "ranges": {str(k): v for k, v in sorted(ranges.items())},
                      "ops": ops, "calls": calls})
    segs = []
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        segs.append({"name": ida_segment.get_segm_name(s), "start": s.start_ea, "end": s.end_ea,
                     "base": ida_segment.get_segm_base(s), "para": para(s.sel),
                     "class": ida_segment.get_segm_class(s),
                     "def_ds": para(ida_segregs.get_sreg(s.start_ea, DS)),
                     "def_ss": para(ida_segregs.get_sreg(s.start_ea, SS))})
    ss = []
    rr = ida_segregs.sreg_range_t()
    for k in range(ida_segregs.get_sreg_ranges_qty(SS)):
        ida_segregs.getn_sreg_range(rr, SS, k)
        p = idc.prev_head(rr.start_ea, 0)
        ss.append([rr.start_ea, rr.end_ea, para(rr.val), rr.tag,
                   idc.generate_disasm_line(p, 0).split(";")[0].strip() if p != idaapi.BADADDR else ""])
    return {"funcs": funcs, "segments": segs, "ss_ranges": ss}


res = {}
try:
    res = main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"))
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
