"""Synchronize a fresh or partial IDB to the committed ground truth (Finding 119).

After running:
  1. tools/ida_snapshot.py
  2. tools/rebuild_overlay_segments.py
  3. tools/apply_overlay_fixups.py
  4. tools/patch_thunks_ida.py

this script enforces the committed `data_holes.json` (70 holes) and
`function_bytes.json` (2,401 functions) directly on the IDB:
  - Converts all recorded data holes to data items and verifies their sha256.
  - Deletes any functions not present in `function_bytes.json` or whose start_ea
    differs from `function_bytes.json`.
  - Ensures instructions are decoded across each function's `[ea, ea + size)`
    and registers/resizes every function to match `[ea, ea + size)` and its
    semantic display name (`name or key`).

Usage: cmd /c "tools\\run_idat.bat tools\\sync_idb_to_ground_truth.py"
"""
import hashlib
import json
import traceback
from pathlib import Path

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idautils

ROOT = Path(r"C:\Users\yotam\projects\falcon3")
IDA = ROOT / "analysis/ida_falconcd"
IDB = str(IDA / "FALCONCD.EXE.i64")
FB = IDA / "function_bytes.json"
HOLES = IDA / "data_holes.json"
LOG = IDA / "sync_ground_truth.log"

log = []
ok_all = False

try:
    fb = json.loads(FB.read_text(encoding="utf-8"))
    holes = json.loads(HOLES.read_text(encoding="utf-8")).get("holes", [])

    want_fns = {}
    for k, v in fb.items():
        ea = v.get("ea")
        sz = v.get("size")
        if ea is None or not sz:
            continue
        want_fns[ea] = (k, sz, v.get("name") or k)

    # 1. Remove functions whose start_ea is not in want_fns or whose span conflicts
    removed = 0
    for s in list(idautils.Functions()):
        f = ida_funcs.get_func(s)
        if not f:
            continue
        if s not in want_fns or (f.end_ea - f.start_ea) != want_fns[s][1]:
            ida_funcs.del_func(s)
            removed += 1
    log.append(f"removed {removed} non-matching/stale functions")

    # 2. Enforce all data holes from data_holes.json
    holes_ok = 0
    for h in holes:
        hea, hsz, hsha = h["ea"], h["size"], h["sha256"]
        raw = ida_bytes.get_bytes(hea, hsz) or b""
        live_sha = hashlib.sha256(raw).hexdigest()
        if live_sha != hsha:
            raise RuntimeError(f"hole 0x{hea:X} sha mismatch: live={live_sha} want={hsha}")
        if not ida_bytes.is_data(ida_bytes.get_flags(hea)):
            ida_bytes.del_items(hea, ida_bytes.DELIT_SIMPLE, hsz)
            ida_bytes.create_byte(hea, hsz)
        holes_ok += 1
    log.append(f"verified/formatted {holes_ok} data holes")

    # 3. Ensure every function in want_fns exists with exact [ea, ea + size)
    created = 0
    kept = 0
    insns_made = 0
    for ea in sorted(want_fns):
        key, sz, want_name = want_fns[ea]
        end = ea + sz
        f = ida_funcs.get_func(ea)
        if f and f.start_ea == ea and f.end_ea == end:
            kept += 1
            continue

        # Ensure instructions are decoded inside [ea, end)
        pos = ea
        ins = ida_ua.insn_t()
        while pos < end:
            flags = ida_bytes.get_flags(pos)
            if ida_bytes.is_code(flags):
                step = ida_bytes.get_item_size(pos)
                if pos + step <= end:
                    pos += step
                    continue
                ida_bytes.del_items(pos, ida_bytes.DELIT_SIMPLE, step)
            n = ida_ua.decode_insn(ins, pos)
            if n <= 0 or pos + n > end:
                break
            if not ida_ua.create_insn(pos):
                ida_bytes.del_items(pos, ida_bytes.DELIT_SIMPLE, n)
                if not ida_ua.create_insn(pos):
                    break
            insns_made += 1
            pos += n

        if ida_funcs.get_func(ea):
            ida_funcs.del_func(ea)
        ida_funcs.add_func(ea, end)
        f = ida_funcs.get_func(ea)
        if f and f.end_ea != end:
            ida_funcs.set_func_end(ea, end)
        created += 1

    log.append(f"functions: kept={kept}, created/resized={created}, insns_made={insns_made}")

    # 4. Two-pass rename to avoid temporary collisions when a semantic name moved EAs
    renamed = 0
    for ea, (key, sz, want_name) in sorted(want_fns.items()):
        cur = ida_name.get_name(ea)
        if cur != want_name:
            ida_name.set_name(ea, f"__tmp_{ea:X}", ida_name.SN_NOWARN | ida_name.SN_NOCHECK)
    for ea, (key, sz, want_name) in sorted(want_fns.items()):
        cur = ida_name.get_name(ea)
        if cur != want_name:
            ida_name.set_name(ea, want_name, ida_name.SN_NOWARN | ida_name.SN_NOCHECK)
            renamed += 1
    log.append(f"renamed {renamed} functions")

    # 5. Final verification
    live_fns = {s: (ida_funcs.get_func(s).end_ea - s, ida_name.get_name(s))
                for s in idautils.Functions()}
    missing = [hex(ea) for ea in want_fns if ea not in live_fns]
    span_bad = [hex(ea) for ea, (_, sz, _) in want_fns.items()
                if ea in live_fns and live_fns[ea][0] != sz]
    name_bad = [hex(ea) for ea, (_, _, nm) in want_fns.items()
                if ea in live_fns and live_fns[ea][1] != nm]
    if missing or span_bad or name_bad or len(live_fns) != len(want_fns):
        log.append(f"GUARD FAILED: count={len(live_fns)}/{len(want_fns)} missing={missing[:5]} span_bad={span_bad[:5]} name_bad={name_bad[:5]}")
        ok_all = False
    else:
        log.append(f"GUARD PASSED: {len(live_fns)} functions match ground truth 100%")
        ok_all = True

except Exception:
    log.append("EXCEPTION:\n" + traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED")

LOG.write_text("\n".join(log), encoding="utf-8")
idaapi.qexit(0)
