"""
p3_xref_check.py  —  check each P3 batch-1 split entry for non-call inner xrefs.
Run: idat -A -S"analysis/s1/p3_xref_check.py" analysis/ida_falconcd/FALCONCD.EXE.i64
Writes: analysis/s1/p3_xref_check.json
"""
import idautils, idc, ida_funcs, ida_bytes, json, traceback
from pathlib import Path

SPLITS = [
    (0x20AC1, 0x20B29),
    (0x28CA1, 0x28CA4),
    (0x33443, 0x3352A),
    (0x39CE0, 0x39D02),
    (0x3C00C, 0x3C03D),
    (0x3E8C5, 0x3E8D2),
    (0x3E962, 0x3E96F),
    (0x3F62C, 0x3F62F),
    (0x3FD89, 0x3FD9A),
    (0x42AFA, 0x42C31),
    (0x42E31, 0x42E37),
    (0x49C67, 0x49C80),
    (0x4A4F6, 0x4A505),
    (0x4D3EC, 0x4D459),
    (0x4EE65, 0x4EE82),
    (0x4F7F0, 0x4F84B),
    (0x6E32A, 0x6E343),
    (0x13DB5D, 0x13DB5E),
    (0x13DC09, 0x13DC0A),
]

OUT = Path("analysis/s1/p3_xref_check.json")
LOG = Path("analysis/s1/p3_xref_check.log")

results = []
log = []

try:
    for ea, at in SPLITS:
        f = ida_funcs.get_func(ea)
        if f is None or f.start_ea != ea:
            results.append({"owner": hex(ea), "at": hex(at), "status": "owner_not_fn"})
            log.append("0x%X: owner not a function head" % ea)
            continue
        # check if 'at' is inside the function
        f2 = ida_funcs.get_func(at)
        if f2 is None or f2.start_ea != ea:
            results.append({"owner": hex(ea), "at": hex(at), "status": "at_not_inside_owner",
                            "at_fn": hex(f2.start_ea) if f2 else None})
            log.append("0x%X at 0x%X: at is not inside owner function (at_fn=0x%X)" % (ea, at, f2.start_ea if f2 else -1))
            continue
        # check xrefs to 'at' from inside 'ea'
        bad_xrefs = []
        ok_xrefs = []
        for xr in idautils.XrefsTo(at, 0):
            if not xr.iscode:
                continue
            xf = ida_funcs.get_func(xr.frm)
            if xf and xf.start_ea == ea:
                m = idc.print_insn_mnem(xr.frm)
                if m in ("call", "callf"):
                    ok_xrefs.append({"from": hex(xr.frm), "mnem": m})
                else:
                    bad_xrefs.append({"from": hex(xr.frm), "mnem": m})
        status = "bad_xref" if bad_xrefs else "ok"
        results.append({"owner": hex(ea), "at": hex(at), "status": status,
                        "bad_xrefs": bad_xrefs, "ok_xrefs": ok_xrefs})
        marker = "FAIL" if bad_xrefs else "ok  "
        log.append("%s  0x%X at 0x%X  bad=%s  ok=%s" % (marker, ea, at, bad_xrefs, ok_xrefs))

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))
except Exception:
    LOG.write_text(traceback.format_exc())

import idaapi; idaapi.qexit(0)
