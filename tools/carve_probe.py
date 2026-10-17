"""Finding 59 (read-only): why would add_func refuse the planned ranges?

For every (start, end) in registry/subblock_split_expected.json reports, on the
current (pre-carve) IDB:

  * item state at start: is it an item head, is an existing item CROSSING the
    start (head < start < head+size), its size;
  * item state at end-1: does an item CROSS the end (the classic reason
    add_func/set_func_end refuses: the range would cut an instruction in half);
  * a fresh decode from start: first instruction size, and whether it already
    runs past `end` (range too small for even one instruction).

Also reports the same crossings for the 3 data-hole boundaries, because the
hole conversion happens before add_func.

NO mutation, always qexit.

Usage: cmd /c "tools\\run_idat.bat tools\\carve_probe.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_ua
import idaapi
import idc

ROOT = r"C:\Users\yotam\projects\falcon3"
MANIFEST = ROOT + r"\registry\subblock_split_expected.json"
OUT = ROOT + r"\analysis\ida_falconcd\carve_probe.json"
LOG = ROOT + r"\analysis\ida_falconcd\carve_probe.log"

log = []


def item_at(ea):
    h = ida_bytes.get_item_head(ea)
    n = ida_bytes.get_item_size(h)
    fl = ida_bytes.get_flags(h)
    code = bool(ida_bytes.is_code(fl))
    data = bool(ida_bytes.is_data(fl))
    mn = (idc.print_insn_mnem(h) or "").lower() if code else ""
    return h, n, code, data, mn


def main():
    e = json.loads(open(MANIFEST).read())["splits"][0]
    rows = []
    for f in e["new_fns"]:
        s, end = f["ea"], f["ea"] + f["size"]
        r = {"key": f["key"], "ea": s, "size": f["size"]}
        h, n, code, data, mn = item_at(s)
        r["start"] = {"head": h, "is_head": h == s, "item_size": n,
                      "code": code, "data": data, "mnem": mn,
                      "crosses": h < s < h + n}
        # what does an item ending at (end-1) do?
        h2, n2, c2, d2, mn2 = item_at(end - 1)
        r["end"] = {"head": h2, "item_end": h2 + n2, "size": n2,
                    "code": c2, "data": d2, "mnem": mn2,
                    "crosses": h2 < end < h2 + n2}
        insn = ida_ua.insn_t()
        k = ida_ua.decode_insn(insn, s)
        r["fresh"] = {"size": k,
                      "mnem": (insn.get_canon_mnem() or "").lower() if k else "",
                      "overruns_end": bool(k and s + k > end)}

        # full fresh decode chain from the start: does it tile [s, end) exactly?
        cur, chain, blocked = s, [], None
        while cur < end:
            ins = ida_ua.insn_t()
            nn = ida_ua.decode_insn(ins, cur)
            if nn <= 0:
                blocked = ("undecodable@0x%X" % cur)
                break
            if cur + nn > end:
                blocked = ("overrun: %s/%dB @0x%X ends 0x%X > end 0x%X"
                           % ((ins.get_canon_mnem() or "").lower(), nn, cur,
                              cur + nn, end))
                break
            chain.append(nn)
            cur += nn
        r["chain"] = {"n": len(chain), "bytes": sum(chain),
                      "lands_on_end": cur == end, "blocked": blocked}
        # items inside the range that are DATA (add_func refuses those)
        datas = []
        ea = s
        while ea < end:
            h = ida_bytes.get_item_head(ea)
            n = ida_bytes.get_item_size(h)
            fl = ida_bytes.get_flags(h)
            if ida_bytes.is_data(fl):
                datas.append((h, n))
            ea = h + max(n, 1)
        r["data_items"] = datas[:6]
        g = ida_funcs.get_func(s)
        r["parent"] = ("%X..%X" % (g.start_ea, g.end_ea)) if g else None
        rows.append(r)

    # hole boundary crossings (the hole conversion precedes add_func)
    hole_rows = []
    for h in e["data_holes"]:
        a, b = h["ea"], h["ea"] + h["size"]
        for edge in (a, b):
            hh, nn, cc, dd, mm = item_at(edge)
            hole_rows.append({"edge": edge, "head": hh, "item_size": nn,
                              "crosses": hh < edge < hh + nn,
                              "code": cc, "data": dd, "mnem": mm})

    json.dump({"fns": rows, "hole_edges": hole_rows}, open(OUT, "w"))

    bad_start_cross = [r for r in rows if r["start"]["crosses"]]
    not_head = [r for r in rows if not r["start"]["is_head"]]
    bad_end_cross = [r for r in rows if r["end"]["crosses"]]
    overrun = [r for r in rows if r["fresh"]["overruns_end"]]
    log.append("planned fns                 : %d" % len(rows))
    log.append("start is not an item head   : %d" % len(not_head))
    log.append("an item CROSSES the start   : %d" % len(bad_start_cross))
    log.append("an item CROSSES the end     : %d  (add_func refusal cause)"
               % len(bad_end_cross))
    log.append("fresh decode overruns end   : %d  (range smaller than one insn)"
               % len(overrun))
    log.append("hole edges crossed by items : %d"
               % sum(1 for h in hole_rows if h["crosses"]))
    bad_chain = [r for r in rows if not r["chain"]["lands_on_end"]]
    with_data = [r for r in rows if r["data_items"]]
    log.append("fresh chain does NOT land on end: %d  (add_func refusal cause)"
               % len(bad_chain))
    log.append("ranges containing DATA items    : %d" % len(with_data))
    for r in bad_chain[:20]:
        log.append("   chain %-12s 0x%X+%d  %s"
                   % (r["key"], r["ea"], r["size"], r["chain"]["blocked"]
                      or ("lands at 0x%X" % (r["ea"] + r["chain"]["bytes"]))))
    for r in with_data[:20]:
        log.append("   data  %-12s 0x%X+%d  %s"
                   % (r["key"], r["ea"], r["size"],
                      ", ".join("0x%X(%dB)" % (h, n) for h, n in r["data_items"])))
    for r in bad_end_cross[:15]:
        log.append("   end-cross %-12s 0x%X+%d  item %d@0x%X (%s) ends 0x%X"
                   % (r["key"], r["ea"], r["size"], r["end"]["size"],
                      r["end"]["head"], r["end"]["mnem"], r["end"]["item_end"]))
    for r in bad_start_cross[:15]:
        log.append("   start-cross %-12s 0x%X  item %d@0x%X (%s)"
                   % (r["key"], r["ea"], r["start"]["item_size"],
                      r["start"]["head"], r["start"]["mnem"]))
    for r in overrun[:15]:
        log.append("   overrun %-12s 0x%X+%d  first insn %s/%dB"
                   % (r["key"], r["ea"], r["size"], r["fresh"]["mnem"],
                      r["fresh"]["size"]))


try:
    main()
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
