"""Positive IDA name read-back (read-only gate).

Checks that every semantic name we believe is in the IDB actually IS: for each
`function_bytes.json` entry with a non-null `name`, the EA must carry that name
in IDA.  Same for `data_symbols.json` (`kind: global` symbols).

IDAPython has no PyYAML (finding 45), so the name fields come from the JSON
artifacts rather than `registry/naming.yaml`.

Output: analysis/ida_falconcd/name_readback.log
Usage: cmd /c "tools\\run_idat.bat tools\\name_readback.py"
"""
import json
import traceback

import ida_name
import idaapi

ROOT = r"C:\Users\yotam\projects\falcon3"
IDA = ROOT + r"\analysis\ida_falconcd"
log = []

try:
    fn = json.load(open(IDA + r"\function_bytes.json"))
    ds = json.load(open(IDA + r"\data_symbols.json"))

    ok = bad = none = 0
    misses = []
    for k, v in fn.items():
        want = v.get("name")
        if not want:
            none += 1
            continue
        got = ida_name.get_ea_name(v["ea"])
        if got == want:
            ok += 1
        else:
            bad += 1
            misses.append("fn %s ea=0x%X want=%r got=%r"
                          % (k, v["ea"], want, got))

    gok = gbad = gnone = 0
    for e in ds:
        want = e.get("name")
        if not want:
            gnone += 1
            continue
        got = ida_name.get_ea_name(e["ea"])
        if got == want:
            gok += 1
        else:
            gbad += 1
            misses.append("data ea=0x%X want=%r got=%r" % (e["ea"], want, got))

    log.append("function_bytes: semantic names present=%d  match=%d  MISMATCH=%d  (unnamed %d)"
               % (ok + bad, ok, bad, none))
    log.append("data_symbols : semantic names present=%d  match=%d  MISMATCH=%d  (unnamed %d)"
               % (gok + gbad, gok, gbad, gnone))
    log.append("TOTAL: %d/%d function + %d/%d global" % (ok, ok + bad, gok, gok + gbad))
    log.append("VERDICT: " + ("OK" if bad == 0 and gbad == 0 else "MISMATCH"))
    for m in misses[:20]:
        log.append("  " + m)
except Exception:
    log.append(traceback.format_exc())

open(IDA + r"\name_readback.log", "w").write("\n".join(log))
idaapi.qexit(0)
