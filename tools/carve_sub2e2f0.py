"""Finding 59 step 2: apply the manifest-planned carve of `sub_2E2F0`
(0x2E2F0..0x3ACAC) -- 51,644 B -> 260 functions + 3 data holes.

The plan lives in registry/subblock_split_expected.json (written by
tools/plan_carve.py BEFORE this runs), so this script is a dumb applier:

  1. verify the parent still has its recorded span and byte-exact content,
     and that all 3 data holes still hash as recorded;
  2. del_func(parent)  -- items are left in place (finding 50's idiom only
     del_items over ranges it intends to re-decode; here the decode must
     SURVIVE, otherwise the 1,053 refs into the blob are destroyed);
  3. del_items + create data over each hole;
  4. add_func + set_func_end + set_name for every planned child;
  5. re-verify: exact spans, exact tiling, hole bytes unchanged, and the
     instruction-head / code-ref counts outside the holes are preserved;
  6. save ONLY if every check passed.

NO auto_wait (finding 37).  The host takes FALCONCD.EXE.i64.bak_carve first,
because idat persists a dirty DB even when a script refuses to save.

Usage: cmd /c "tools\\run_idat.bat tools\\carve_sub2e2f0.py"
"""
import hashlib
import json
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
MANIFEST = ROOT + r"\registry\subblock_split_expected.json"
OUT = ROOT + r"\analysis\ida_falconcd\carve.log"
IDB = ROOT + r"\analysis\ida_falconcd\FALCONCD.EXE.i64"

log = []
ok_all = False


def sha(raw):
    return hashlib.sha256(raw).hexdigest() if raw else None


def coverage(lo, hi, holes):
    """heads + code refs in [lo,hi) excluding the data holes."""
    hs = rs = 0
    spans = [(a, a + n) for a, n, _w in holes]
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


def main():
    global ok_all
    e = json.loads(open(MANIFEST).read())["splits"][0]
    lo, hi = e["ea"], e["ea"] + e["old_size"]
    holes = [(h["ea"], h["size"], h["sha256"]) for h in e["data_holes"]]

    # ---- 1. preconditions ----
    p = ida_funcs.get_func(lo)
    if not p or p.start_ea != lo or (p.end_ea - p.start_ea) != e["old_size"]:
        raise SystemExit("FATAL: parent is %s, expected %s..%s"
                         % ("%X..%X" % (p.start_ea, p.end_ea) if p else "NONE",
                            hex(lo), hex(hi)))
    raw = idc.get_bytes(lo, e["old_size"])
    if sha(raw) != e["old_sha256"]:
        raise SystemExit("FATAL: parent bytes differ from the manifest")
    for a, n, want in holes:
        if sha(idc.get_bytes(a, n)) != want:
            raise SystemExit("FATAL: data hole 0x%X bytes differ" % a)
    pre_heads, pre_refs = coverage(lo, hi, holes)
    log.append("precondition OK: %d planned fns, %d holes, heads=%d refs=%d"
               % (len(e["new_fns"]), len(holes), pre_heads, pre_refs))

    # ---- 2. delete the parent (items survive) ----
    if not ida_funcs.del_func(lo):
        raise SystemExit("FATAL: del_func(0x%X) failed" % lo)
    if ida_funcs.get_func(lo):
        raise SystemExit("FATAL: parent still present after del_func")
    log.append("del_func done; heads still in range: %d"
               % len(list(idautils.Heads(lo, hi))))

    # ---- 3. data holes ----
    for a, n, _w in holes:
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, n)
        made = False
        try:
            made = ida_bytes.create_data(a, ida_bytes.FF_BYTE, n, idaapi.BADNODE)
        except Exception as ex:
            log.append("  create_data(0x%X,%d) raised %r" % (a, n, ex))
        if not made or not ida_bytes.is_data(ida_bytes.get_flags(a)):
            raise SystemExit("FATAL: could not turn 0x%X..0x%X into data"
                             % (a, a + n))
        log.append("  data hole 0x%X..0x%X ok (item size %d)"
                   % (a, a + n, ida_bytes.get_item_size(a)))

    # ---- 3b. items that would cut an instruction in half at a boundary ----
    # plan_carve already dropped every boundary crossed by a REAL instruction;
    # what remains here is zero padding the old sweep turned into `add` (and
    # whatever the hole conversion left over).  A non-padding crossing is a
    # plan bug -> abort rather than destroy code.
    edges = sorted({f["ea"] for f in e["new_fns"]}
                   | {f["ea"] + f["size"] for f in e["new_fns"]}
                   | {a for a, _n, _w in holes}
                   | {a + n for a, n, _w in holes})
    for B in edges:
        h = ida_bytes.get_item_head(B)
        n = ida_bytes.get_item_size(h)
        if h == B or h + n <= B:
            continue
        b0 = ida_bytes.get_byte(h)
        at_hole = any(lo <= B <= hi for lo, hi, _n in holes)
        if b0 == 0 or at_hole:
            ida_bytes.del_items(h, ida_bytes.DELIT_SIMPLE, n)
            log.append("  deleted %dB item @0x%X crossing 0x%X (first byte %02X)"
                       % (n, h, B, b0))
        else:
            raise SystemExit("FATAL: real instruction at 0x%X (%02X) crosses "
                             "boundary 0x%X -- plan is wrong" % (h, b0, B))

    # starts with no item at all need one, or the function would be empty and
    # export_callrefs would see nothing there
    need_decode = [f["ea"] for f in e["new_fns"]
                   if not ida_bytes.is_code(ida_bytes.get_flags(f["ea"]))
                   and not ida_bytes.is_data(ida_bytes.get_flags(f["ea"]))]
    log.append("planned starts with no item: %d" % len(need_decode))

    # ---- 4. planned functions ----
    # A start that carries no item still cannot be decoded if some OTHER item
    # sits inside its first instruction (the old sweep placed those bytes
    # differently).  Clear the blocking items, retry -- never guess: if the
    # entry still will not decode, the start flags it and add_func fails.
    for ea in need_decode:
        k = 0
        for _attempt in range(8):
            ins = ida_ua.insn_t()
            k = ida_ua.decode_insn(ins, ea)
            if k <= 0:
                break
            blocking = []
            for pos in range(ea + 1, ea + k):
                hh = ida_bytes.get_item_head(pos)
                if hh != ea and ida_bytes.is_head(ida_bytes.get_flags(hh)):
                    blocking.append(hh)
            if not blocking:
                break
            for hh in sorted(set(blocking)):
                nn = max(ida_bytes.get_item_size(hh), 1)
                ida_bytes.del_items(hh, ida_bytes.DELIT_SIMPLE, nn)
                log.append("    cleared %dB item at 0x%X blocking entry 0x%X"
                           % (nn, hh, ea))
        n = ida_ua.create_insn(ea)
        log.append("  create_insn(0x%X) -> %s (fresh=%s/%dB, item now: code=%s head=0x%X)"
                   % (ea, n, (ins.get_canon_mnem() or "").lower() if k > 0 else None,
                      k, bool(ida_bytes.is_code(ida_bytes.get_flags(ea))),
                      ida_bytes.get_item_head(ea)))
    ok_all = True
    for f in e["new_fns"]:
        s, sz = f["ea"], f["size"]
        if ida_bytes.get_item_head(s) != s:
            log.append("  start 0x%X is inside item @0x%X -- ** FAILED **"
                       % (s, ida_bytes.get_item_head(s)))
            ok_all = False
            break
        r = ida_funcs.add_func(s, s + sz)
        if r:
            ida_funcs.set_func_end(s, s + sz)
        g = ida_funcs.get_func(s)
        good = bool(g) and g.start_ea == s and g.end_ea == s + sz
        if good and idc.get_func_name(s) != f["key"]:
            ida_name.set_name(s, f["key"], ida_name.SN_CHECK)
            good = (idc.get_func_name(s) == f["key"])
        if not good:
            log.append("  add_func %s 0x%X+%d -> %s  ** FAILED **"
                       % (f["key"], s, sz,
                          ("%X..%X" % (g.start_ea, g.end_ea)) if g else "NONE"))
            ins = ida_ua.insn_t()
            k = ida_ua.decode_insn(ins, s)
            datas, ea2 = [], s
            while ea2 < s + sz:
                hh = ida_bytes.get_item_head(ea2)
                nn = max(ida_bytes.get_item_size(hh), 1)
                if ida_bytes.is_data(ida_bytes.get_flags(hh)):
                    datas.append((hh, nn))
                ea2 = hh + nn
            he = ida_bytes.get_item_head(s + sz - 1)
            log.append("     start: head=0x%X size=%d code=%s data=%s unk=%s fresh=%s/%s"
                       % (ida_bytes.get_item_head(s), ida_bytes.get_item_size(s),
                          bool(ida_bytes.is_code(ida_bytes.get_flags(s))),
                          bool(ida_bytes.is_data(ida_bytes.get_flags(s))),
                          bool(ida_bytes.is_unknown(ida_bytes.get_flags(s))),
                          (ins.get_canon_mnem() or "").lower() if k else None, k))
            log.append("     end  : item at 0x%X size=%d ends 0x%X ; data inside=%s"
                       % (he, ida_bytes.get_item_size(he),
                          he + ida_bytes.get_item_size(he),
                          [(hex(a), n) for a, n in datas[:6]]))
            ok_all = False
            break
    log.append("planned fns registered: %s"
               % (len(e["new_fns"]) if ok_all else "ABORTED (see above)"))

    if not ok_all:
        return

    # ---- 5. post-conditions ----
    have = []
    for f in e["new_fns"]:
        g = ida_funcs.get_func(f["ea"])
        if not g or g.start_ea != f["ea"] or g.end_ea != f["ea"] + f["size"]:
            log.append("  span mismatch for %s" % f["key"])
            ok_all = False
    covered = sum(f["size"] for f in e["new_fns"])
    if covered + sum(n for _a, n, _w in holes) != e["old_size"]:
        log.append("  tiling mismatch: %d + holes != %d"
                   % (covered, e["old_size"]))
        ok_all = False
    for a, n, want in holes:
        if sha(idc.get_bytes(a, n)) != want:
            log.append("  data hole 0x%X changed during the carve" % a)
            ok_all = False
        if ida_funcs.get_func(a) or ida_funcs.get_func(a + n - 1):
            log.append("  data hole 0x%X is covered by a function" % a)
            ok_all = False
    post_heads, post_refs = coverage(lo, hi, holes)
    log.append("post: heads=%d (pre %d)   refs=%d (pre %d)"
               % (post_heads, pre_heads, post_refs, pre_refs))
    if post_heads < pre_heads - len(need_decode) - 8:
        log.append("  ** instruction heads lost -- decode did not survive **")
        ok_all = False
    if post_refs < pre_refs - 8:
        log.append("  ** code refs lost -- the blob's edges would be destroyed **")
        ok_all = False
    stray = [f for f in idautils.Functions(lo, hi)
             if f not in {x["ea"] for x in e["new_fns"]}]
    if stray:
        log.append("  unexpected functions inside the old span: %s"
                   % [hex(x) for x in stray[:5]])
        ok_all = False


try:
    main()
except SystemExit as ex:
    log.append(str(ex))
    ok_all = False
except Exception:
    log.append("EXCEPTION (restore analysis/ida_falconcd/FALCONCD.EXE.i64.bak_carve):")
    log.append(traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_carve")

open(OUT, "w").write("\n".join(log))
idaapi.qexit(0)
