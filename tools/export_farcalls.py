"""Read-only IDA export of every direct far call/jmp (9A/EA) for tools/plan_variant_selectors.py (finding 123).

Per instruction: seg:off words, current code xrefs (to, type, user), the containing segment/function, and
the code/head/function-start state of the target under each 0x1E10-arena variant (R05 real, R27, R28,
R29 synthetic all share w0 = 0x1E10 and the R05 linear arena 0x2E100).  Also the segment table, the
DS/ES/SS ranges holding an R29-only selector, and the code heads whose direct memory operands are
addressed through one (with their current data xrefs).

Writes analysis/s1/farcall_probe.json (or $FARCALLS).  Never saves.
Usage: idat -A -S"tools\\export_farcalls.py" <idb copy>
"""
import json
import os
import struct
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_segment
import ida_segregs
import ida_ua
import ida_xref
import idaapi
import idautils
import idc

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("FARCALLS") or ROOT / "analysis/s1/farcall_probe.json")
ARENA = 0x2E100
# variant image base and length (registry/segsplit_expected.json records 5, 27, 28, 29)
V = {"R05": (0x2E100, 0x388F0), "R27": (0x10C9E0, 0x4B40), "R28": (0x111530, 0xAE80), "R29": (0x11C3C0, 0x388F0)}


def st(ea):
    fl = ida_bytes.get_flags(ea)
    f = ida_funcs.get_func(ea)
    return {"code": ida_bytes.is_code(fl), "head": ida_bytes.get_item_head(ea) == ea and ida_bytes.is_code(fl),
            "fs": bool(f and f.start_ea == ea), "fin": f.start_ea if f else None,
            "seg": ida_segment.get_segm_name(ida_segment.getseg(ea)) if ida_segment.getseg(ea) else None}


def main():
    R = {"segs": [], "calls": []}
    for s in idautils.Segments():
        g = ida_segment.getseg(s)
        R["segs"].append([ida_segment.get_segm_name(g), g.start_ea, g.end_ea, ida_segment.get_segm_base(g),
                          g.sel, g.bitness])
        ea = g.start_ea
        while ea != idaapi.BADADDR and ea < g.end_ea:
            if ida_bytes.is_code(ida_bytes.get_flags(ea)):
                b0 = ida_bytes.get_byte(ea)
                if b0 in (0x9A, 0xEA) and ida_bytes.get_item_size(ea) == 5:
                    off, seg = struct.unpack("<HH", idc.get_bytes(ea, 5)[1:])
                    lin = (seg << 4) + off
                    refs = [(x.to, x.type, x.user) for x in idautils.XrefsFrom(ea, ida_xref.XREF_FAR) if x.iscode]
                    f = ida_funcs.get_func(ea)
                    rec = {"ea": ea, "op": b0, "off": off, "seg": seg, "lin": lin, "refs": refs,
                           "cseg": ida_segment.get_segm_name(g), "infn": f.start_ea if f else None, "var": {}}
                    for n, (b, ln) in V.items():
                        o = lin - ARENA
                        if 0 <= o < ln:
                            rec["var"][n] = [b + o, st(b + o)]
                    rec["lin_st"] = st(lin)
                    R["calls"].append(rec)
            ea = idc.next_head(ea, g.end_ea)
    sreg_facts(R)
    OUT.write_text(json.dumps(R))
    print("far calls/jmps: %d, sreg heads: %d" % (len(R["calls"]), len(R["sreg_heads"])))


def sreg_facts(R):
    """Segment-register ranges whose value is an R29-only arena paragraph (link anchor + 0x1000), and the
    code heads with a direct memory operand addressed through such a register (their drefs were computed
    through the identity selector, i.e. into the R05 image)."""
    anchors = {}
    for name, *_ in R["segs"]:
        if name[:3] in V and len(name) >= 8:
            anchors.setdefault(name[:3], set()).add(int(name[4:8], 16))
    cand = {a + 0x1000 for a in anchors.get("R29", set()) - anchors.get("R05", set())} | {0x4FA8}
    R["sreg_ranges"], R["sreg_heads"] = [], []
    for rn in ("ds", "es", "ss"):
        reg = idaapi.str2reg(rn)
        for i in range(ida_segregs.get_sreg_ranges_qty(reg)):
            r = ida_segregs.sreg_range_t()
            ida_segregs.getn_sreg_range(r, reg, i)
            if r.val in cand:
                R["sreg_ranges"].append([rn, r.start_ea, r.end_ea, r.val, r.tag,
                                         ida_segment.get_segm_name(ida_segment.getseg(r.start_ea))])
    DS, ES = idaapi.str2reg("ds"), idaapi.str2reg("es")
    for s in idautils.Segments():
        g = ida_segment.getseg(s)
        for h in idautils.Heads(g.start_ea, g.end_ea):
            if not ida_bytes.is_code(ida_bytes.get_flags(h)):
                continue
            dv, ev = ida_segregs.get_sreg(h, DS), ida_segregs.get_sreg(h, ES)
            if dv not in cand and ev not in cand:
                continue
            insn = ida_ua.insn_t()
            if not ida_ua.decode_insn(insn, h):
                continue
            used = set()
            for op in insn.ops:
                if op.type == ida_ua.o_void:
                    break
                if op.type != ida_ua.o_mem:
                    continue
                txt = idc.print_operand(h, op.n) or ""
                if "cs:" in txt or "ss:" in txt:
                    continue
                if "es:" in txt:
                    if ev in cand:
                        used.add("es")
                elif dv in cand:
                    used.add("ds")
            if used:
                R["sreg_heads"].append([h, ida_bytes.get_item_size(h), sorted(used),
                                        sorted({ida_segregs.get_sreg(h, DS) if "ds" in used else ev}),
                                        insn.get_canon_mnem(),
                                        [(x.to, x.type, x.user) for x in idautils.XrefsFrom(h, ida_xref.XREF_FAR)
                                         if not x.iscode]])


try:
    main()
except Exception:
    traceback.print_exc()
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
