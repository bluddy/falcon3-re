#!/usr/bin/env python3
"""
Extract function bytes from IDA database (with fixups applied).
Enumerates ALL live functions (resident + rebuilt overlays), not the stale survey.

Keys are stable: the previous extract's key for the same ea, else sub_%X -- never a
display name, so a rename cannot change a key.  Names: the live IDB is canonical
(finding 124) -- 'name' is the function's user-given IDB name, null for dummy/auto
names; registry/naming.yaml must agree (tools/naming.py check).

Read-only (DBFL_KILL).  FBOUT env overrides the output path, FBPREV the previous
extract that supplies the stable keys (both default to function_bytes.json).
Run via: idat.exe -A -S"tools/extract_ida_bytes.py" <copy of FALCONCD.EXE.i64>
"""
import json
import os
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_name
import idaapi
import idautils

ROOT = Path(__file__).resolve().parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"


def main():
    out = Path(os.environ.get("FBOUT") or FB)
    prev = Path(os.environ.get("FBPREV") or FB)
    ea_to_key = {}
    if prev.exists():
        for k, v in json.loads(prev.read_text()).items():
            ea_to_key.setdefault(v.get("ea"), k)

    func_bytes = {}
    for ea in idautils.Functions():
        f = ida_funcs.get_func(ea)
        size = f.end_ea - f.start_ea
        key = ea_to_key.get(ea) or "sub_%X" % ea
        if key in func_bytes:
            key = "sub_%X" % ea
        if key in func_bytes:
            raise RuntimeError("duplicate key %s at 0x%X" % (key, ea))
        data = ida_bytes.get_bytes(ea, size)
        user = ida_bytes.has_user_name(ida_bytes.get_flags(ea))
        func_bytes[key] = {
            "ea": ea,
            "size": size,
            "bytes": data.hex() if data else None,
            "is_far": bool(f.flags & ida_funcs.FUNC_FAR),
            "overlay": ea >= 0x2CF60,
            "name": ida_name.get_ea_name(ea) if user else None,
        }

    with open(out, "w") as fh:
        json.dump(func_bytes, fh, indent=1)
    nov = sum(1 for v in func_bytes.values() if v["overlay"])
    print("Extracted bytes for %d functions (%d overlay)" % (len(func_bytes), nov))


try:
    main()
finally:
    idaapi.set_database_flag(idaapi.DBFL_KILL)
    idaapi.qexit(0)
