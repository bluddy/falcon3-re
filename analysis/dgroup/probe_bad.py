"""Read-only: classify why implicit-DS operands have BAD DS -> probe_bad.json
For each BAD implicit-DS operand head: is its DS range inherited from the
function entry, or opened inside the function (and by which instruction)?"""
import collections
import json
import os
import traceback

import ida_funcs
import ida_segregs
import ida_ua
import idaapi
import idautils
import idc

OUT = os.environ.get("OUT", r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\probe_bad.json")
DS = idaapi.str2reg("ds")
res = {}


def is_bad(v):
    return v in (idaapi.BADSEL, 0xFFFF)


def ds_ops(ea, insn):
    n = 0
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
        n += 1
    return n


def main():
    cause = collections.Counter()
    opener = collections.Counter()
    pershape = collections.Counter()
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        for h in idautils.FuncItems(fs):
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, h):
                continue
            n = ds_ops(h, insn)
            if not n:
                continue
            if not is_bad(ida_segregs.get_sreg(h, DS)):
                continue
            rr = ida_segregs.sreg_range_t()
            ida_segregs.get_sreg_range(rr, h, DS)
            if rr.start_ea <= fs:
                cause["entry"] += n
            else:
                p = idc.prev_head(rr.start_ea, 0)
                insn2 = ida_ua.insn_t()
                ida_ua.decode_insn(insn2, p)
                d = idc.generate_disasm_line(p, 0).split(";")[0].strip()
                mn = insn2.get_canon_mnem()
                if mn == "pop":
                    k = "pop ds"
                elif mn in ("mov",):
                    k = "mov ds," + ("reg" if insn2.ops[1].type == ida_ua.o_reg else "mem")
                elif mn == "lds":
                    k = "lds"
                elif p < fs or not ida_funcs.func_contains(f, p):
                    k = "range opened outside func"
                else:
                    k = "other:" + mn
                cause["inner"] += n
                opener[k] += n
                if len(pershape) < 400 or (k, d) in pershape:
                    pershape[(k, d)] += n
    res["cause"] = dict(cause)
    res["opener"] = dict(opener)
    res["shapes"] = [[a, b, n] for (a, b), n in pershape.most_common(80)]


try:
    main()
except Exception:
    res["error"] = traceback.format_exc()
json.dump(res, open(OUT, "w"), indent=0)
idaapi.qexit(0)
