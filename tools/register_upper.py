"""Finding 61 step P3b: register the manifest-planned upper-half ranges.

Reads registry/upper_register_expected.json (77 parentless ranges, 116 new
functions, 24 kept, 68 sha256-pinned holes) produced by tools/sweep_upper.py
+ tools/plan_register.py.  For every range:

  1. precondition: the range contains EXACTLY the keep functions and nothing
     else, and every data hole still hashes as recorded;
  2. convert holes (del_items + create_data) so strings stay data, never code;
  3. for each planned function: make sure the entry decodes (clear blocking
     items first -- finding 59's lesson), create the body's instructions only
     where no item exists (never contradicts an existing decode), then
     add_func + set_func_end + set_name;
  4. guards: spans match the manifest, the range still tiles exactly
     (new + keep + holes), hole bytes unchanged and function-free, no stray
     functions, and heads/code-refs outside the holes did not decrease;
  5. save ONLY if every guard passes.

Host takes FALCONCD.EXE.i64.bak_upper first (idat persists a dirty DB even
when a script refuses to save).  No auto_wait (finding 37).

Usage: cmd /c "tools\\run_idat.bat tools\\register_upper.py"
"""
import hashlib
import json
import os
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idautils
import idc

ROOT = r"C:\Users\yotam\projects\falcon3"
MANIFEST = os.environ.get(
    "FALCON_MANIFEST",
    ROOT + r"\registry\upper_register_expected.json")
IDB = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = os.environ.get(
    "FALCON_REG_LOG",
    ROOT + r"\analysis\ida_falconcd\register_upper.log")

TERMS = {"retn", "retf", "ret", "iret", "jmp"}
log = []
ok_all = False


def sha(raw):
    return hashlib.sha256(raw).hexdigest() if raw and len(raw) else None


def coverage(lo, hi, hole_spans):
    """heads + code refs in [lo,hi) excluding the data holes."""
    spans = list(hole_spans)
    hs = rs = 0
    for ea in idautils.Heads(lo, hi):
        if any(a <= ea < b for a, b in spans):
            continue
        hs += 1
        if idc.print_insn_mnem(ea):
            try:
                rs += len(list(idautils.CodeRefsFrom(ea, 0)))
            except Exception:
                pass
    return hs, rs


def build_body(s, e):
    """create instructions in [s,e) only where no item exists yet."""
    created = 0
    cur = s
    while cur < e:
        h = ida_bytes.get_item_head(cur)
        if h == cur and ida_bytes.is_code(ida_bytes.get_flags(cur)):
            cur += max(ida_bytes.get_item_size(cur), 1)
            continue
        if h != cur:                     # inside an existing item: trust it
            cur = h + max(ida_bytes.get_item_size(h), 1)
            continue
        if ida_bytes.is_data(ida_bytes.get_flags(cur)):
            cur += max(ida_bytes.get_item_size(cur), 1)
            continue
        ins = ida_ua.insn_t()
        k = ida_ua.decode_insn(ins, cur)
        if k <= 0:
            cur += 1
            continue
        if cur + k > e:
            cur += 1                     # would cross the planned end
            continue
        n = ida_ua.create_insn(cur)
        if n and cur + n <= e:
            created += 1
            cur += n
        else:
            cur += 1
    return created


def main():
    global ok_all
    man = json.loads(open(MANIFEST).read())
    ranges = man["ranges"]
    log.append("manifest: %d ranges, %d new fns, %d holes (%d B)"
               % (len(ranges), man["n_new_fns"], man["n_holes"], man["hole_bytes"]))

    # ---- preconditions: pre-state == keep (fresh) OR == keep+new (idempotent
    # re-run after a guard-failed attempt whose dirty DB idat persisted) ----
    pre = {}
    for rng in ranges:
        lo, hi = rng["range"]
        live = [(s, ida_funcs.get_func(s).end_ea) for s in idautils.Functions(lo, hi)]
        want = [(f["ea"], f["ea"] + f["size"]) for f in rng["keep_fns"]]
        applied = want + [(f["ea"], f["ea"] + f["size"]) for f in rng["new_fns"]]
        if sorted(live) == sorted(want):
            state = "keep"
        elif sorted(live) == sorted(applied):
            state = "already"
        else:
            raise SystemExit("FATAL: %s pre-state has %d fns, expected keep %d "
                             "or applied %d" % (rng["name"], len(live), len(want),
                                                len(applied)))
        rng["_state"] = state
        for h in rng["data_holes"]:
            if sha(idc.get_bytes(h["ea"], h["size"])) != h["sha256"]:
                raise SystemExit("FATAL: %s hole 0x%X bytes differ"
                                 % (rng["name"], h["ea"]))
            if ida_funcs.get_func(h["ea"]) or ida_funcs.get_func(h["ea"] + h["size"] - 1):
                raise SystemExit("FATAL: %s hole 0x%X already in a function"
                                 % (rng["name"], h["ea"]))
        pre[tuple(rng["range"])] = coverage(lo, hi, [])
    for h in man.get("standalone_holes", []):
        if sha(idc.get_bytes(h["ea"], h["size"])) != h["sha256"]:
            raise SystemExit("FATAL: standalone hole 0x%X bytes differ" % h["ea"])
        if ida_funcs.get_func(h["ea"]) or ida_funcs.get_func(h["ea"] + h["size"] - 1):
            raise SystemExit("FATAL: standalone hole 0x%X in a function" % h["ea"])
    log.append("preconditions OK (pre-state == keep for all ranges, "
               "all %d hashes match)" % (man["n_holes"]))

    # ---- apply (idempotent: skip ranges already applied, skip holes already
    # converted to data with the right hash) ----
    n_holes = n_fns = created_total = skipped = 0
    for rng in ranges:
        lo, hi = rng["range"]
        hole_spans = [(h["ea"], h["ea"] + h["size"]) for h in rng["data_holes"]]
        for h in rng["data_holes"]:
            ea, n = h["ea"], h["size"]
            if (ida_bytes.is_data(ida_bytes.get_flags(ea))
                    and sha(idc.get_bytes(ea, n)) == h["sha256"]):
                n_holes += 1
                continue                     # already converted
            ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, n)
            made = False
            try:
                made = ida_bytes.create_data(ea, ida_bytes.FF_BYTE, n,
                                             idaapi.BADNODE)
            except Exception as ex:
                log.append("  create_data(0x%X,%d) raised %r" % (ea, n, ex))
            if not made or not ida_bytes.is_data(ida_bytes.get_flags(ea)):
                raise SystemExit("FATAL: could not turn hole 0x%X..%d into data"
                                 % (ea, n))
            if sha(idc.get_bytes(ea, n)) != h["sha256"]:
                raise SystemExit("FATAL: hole 0x%X changed while converting" % ea)
            n_holes += 1
        if rng.get("_state") == "already":
            n_fns += len(rng["new_fns"])
            skipped += len(rng["new_fns"])
            continue
        for f in rng["new_fns"]:
            s, e, key = f["ea"], f["ea"] + f["size"], f["key"]
            # entry must be decodable: clear blocking items first (finding 59)
            for _try in range(8):
                ins = ida_ua.insn_t()
                k = ida_ua.decode_insn(ins, s)
                if k <= 0:
                    break
                blocking = []
                for pos in range(s + 1, min(s + k, e)):
                    hh = ida_bytes.get_item_head(pos)
                    if hh != s and ida_bytes.is_head(ida_bytes.get_flags(hh)):
                        blocking.append(hh)
                if not blocking:
                    break
                for hh in sorted(set(blocking)):
                    nn = max(ida_bytes.get_item_size(hh), 1)
                    ida_bytes.del_items(hh, ida_bytes.DELIT_SIMPLE, nn)
                    log.append("    cleared %dB item at 0x%X blocking entry 0x%X"
                               % (nn, hh, s))
            if not ida_bytes.is_code(ida_bytes.get_flags(s)):
                ida_ua.create_insn(s)
            created_total += build_body(s, e)
            r = ida_funcs.add_func(s, e)
            if r:
                ida_funcs.set_func_end(s, e)
            g = ida_funcs.get_func(s)
            good = bool(g) and g.start_ea == s and g.end_ea == e
            if good:
                if idc.get_func_name(s) != key:
                    ida_name.set_name(s, key, ida_name.SN_CHECK)
                good = (idc.get_func_name(s) == key)
            if not good:
                raise SystemExit("FATAL: add_func %s 0x%X..0x%X -> %s"
                                 % (key, s, e,
                                    ("%X..%X" % (g.start_ea, g.end_ea)) if g else "NONE"))
            n_fns += 1
    log.append("holes converted (or already): %d   functions registered: %d "
               "(%d idempotent-skip)   instructions created: %d"
               % (n_holes, n_fns, skipped, created_total))

    # ---- guards ----
    ok_all = True
    for rng in ranges:
        lo, hi = rng["range"]
        name = rng["name"]
        want = sorted([(f["ea"], f["ea"] + f["size"]) for f in rng["new_fns"]]
                      + [(f["ea"], f["ea"] + f["size"]) for f in rng["keep_fns"]])
        live = sorted((s, ida_funcs.get_func(s).end_ea) for s in idautils.Functions(lo, hi))
        if live != want:
            log.append("  %s: live spans differ from plan (%d vs %d)" % (name, len(live), len(want)))
            ok_all = False
        spans = sorted([(f["ea"], f["ea"] + f["size"]) for f in rng["new_fns"]]
                       + [(f["ea"], f["ea"] + f["size"]) for f in rng["keep_fns"]]
                       + [(h["ea"], h["ea"] + h["size"]) for h in rng["data_holes"]])
        cur, tiled = lo, True
        for s, e in spans:
            if s != cur:
                tiled = False
                break
            cur = e
        if not tiled or cur != hi:
            log.append("  %s: range no longer tiles (ends 0x%X)" % (name, cur))
            ok_all = False
        for h in rng["data_holes"]:
            if sha(idc.get_bytes(h["ea"], h["size"])) != h["sha256"]:
                log.append("  %s: hole 0x%X bytes changed" % (name, h["ea"]))
                ok_all = False
            if ida_funcs.get_func(h["ea"]) or ida_funcs.get_func(h["ea"] + h["size"] - 1):
                log.append("  %s: hole 0x%X covered by a function" % (name, h["ea"]))
                ok_all = False
        post_h, post_r = coverage(lo, hi, hole_spans)
        pre_h, pre_r = pre[(lo, hi)]
        if post_h < pre_h or post_r < pre_r:
            log.append("  %s: heads %d->%d refs %d->%d (must not decrease)"
                       % (name, pre_h, post_h, pre_r, post_r))
            ok_all = False
    for h in man.get("standalone_holes", []):
        if sha(idc.get_bytes(h["ea"], h["size"])) != h["sha256"] or \
                ida_funcs.get_func(h["ea"]):
            log.append("standalone hole 0x%X violated" % h["ea"])
            ok_all = False
    log.append("guards: %s" % ("PASSED" if ok_all else "FAILED"))


try:
    main()
except SystemExit as ex:
    log.append(str(ex))
    ok_all = False
except Exception:
    log.append("EXCEPTION (restore analysis/ida_falconcd/FALCONCD.EXE.i64.bak_upper):")
    log.append(traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_upper")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
