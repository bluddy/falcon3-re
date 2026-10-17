"""Finding 55 IDA export (READ-ONLY): every direct FAR call/jmp operand inside a
function -> {ea, seg, off, dst}.  Host side then joins this against the RTLink
fixup tables to say WHY each operand is or isn't relocated.

Output: analysis/ida_falconcd/farops_export55.json
Usage: cmd /c "tools\\run_idat.bat tools\\farops_export55.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import idaapi
import idautils

ROOT = r"C:\Users\yotam\projects\falcon3"
IDA = ROOT + r"\analysis\ida_falconcd"
PREFIX = (0x2E, 0x36, 0x3E, 0x26)

out = []
log = []

try:
    for fea in idautils.Functions():
        f = ida_funcs.get_func(fea)
        if f is None:
            continue
        ea = f.start_ea
        while ea < f.end_ea:
            b = ida_bytes.get_bytes(ea, 7) or b""
            i = 0
            while i < len(b) and b[i] in PREFIX:
                i += 1
            if i < len(b) and b[i] in (0x9A, 0xEA) and len(b) >= i + 5:
                off = b[i + 1] | (b[i + 2] << 8)
                seg = b[i + 3] | (b[i + 4] << 8)
                out.append({"ea": ea, "seg": seg, "off": off,
                            "dst": (seg << 4) + off, "fn": f.start_ea})
                ea += i + 5
                continue
            nxt = ida_bytes.next_head(ea, f.end_ea)
            if nxt <= ea:
                break
            ea = nxt
    json.dump(out, open(IDA + r"\farops_export55.json", "w"))
    log.append("far-ops exported: %d" % len(out))
except Exception:
    log.append(traceback.format_exc())

open(IDA + r"\farops_export55.log", "w").write("\n".join(log))
idaapi.qexit(0)
