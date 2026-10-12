"""Dump IDA data symbols (globals) -> analysis/ida_falconcd/data_symbols.json.

Each entry: {ea, size, ida_name, name, seg, kind}  (name = null until renamed
via tools/naming.py). Committed; rename = update 'name' in place + IDA push.
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_name
import ida_nalt
import ida_ua
import idaapi
import idautils

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\data_symbols.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\datasym.log"

log = []
try:
    syms = []
    n = 0
    for ea in idautils.Heads():
        # data heads only: not in a function, has a name, not anonymous
        if ida_funcs.get_func(ea) is not None:
            continue
        name = ida_name.get_ea_name(ea)
        if not name:
            continue
        # skip code-segment instruction starts that leaked through
        flags = ida_bytes.get_flags(ea)
        if not ida_bytes.is_data(flags) and not ida_bytes.is_unknown(flags):
            continue
        # size via item head
        head = ida_bytes.get_item_head(ea)
        if head != ea:
            continue
        sz = ida_bytes.get_item_size(ea)
        kind = "auto"
        if name.startswith("byte_"):
            kind = "byte"
        elif name.startswith("word_"):
            kind = "word"
        elif name.startswith("dword_"):
            kind = "dword"
        elif name.startswith("unk_"):
            kind = "unknown"
        elif name.startswith("asc_"):
            kind = "string"
        syms.append(dict(ea=ea, size=sz, ida_name=name, name=None, kind=kind))
        n += 1
    json.dump(syms, open(OUT, "w"), indent=1)
    log.append("dumped %d data symbols" % n)
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
