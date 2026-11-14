p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
assert "\r\n" not in s
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)

rep("""ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A)]""",
    """ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A),
          (0x166F80, 0x16781C, 0x16781A, 0x167827, 0x167AFF)]
# (func, [(lo, hi, seeds)]): finding 144.  Pieces of a function's own body that were misdecoded and left orphan: [lo, hi) is
# cleared, redecoded from the seeds and appended as a chunk of func (append_func_tail merges it with an adjacent chunk).
GLUE = [(0x2E20A, [(0x2E22F, 0x2E23D, [0x2E22F, 0x2E236]), (0x2E281, 0x2E28F, [0x2E281])])]""")

rep("""def add_all(items,""", """def gl_state(x):
    ea = x["ea"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea:
        return "mismatch"
    if chunks(ea) == x["chunks_after"] and f.end_ea == x["end"]:
        return "applied"
    if (chunks(ea) == x["chunks_before"] and f.end_ea == x["before_end"]
            and all(not any(ida_funcs.get_func(a) for a in range(lo, hi)) and sha(lo, hi) == h
                    for (lo, hi), h in zip(x["runs"], x["runs_sha256"]))):
        return "fresh"
    return "mismatch"


def glue(x):
    ea = x["ea"]
    runs = [list(r) for r in x["runs"]]
    orig = set()
    for lo, hi in runs:
        a = lo
        while a < hi:
            h = ida_bytes.get_item_head(a)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                orig.add(h)
            a = h + max(ida_bytes.get_item_size(h), 1)
        ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    for sd in x["seeds"]:
        rlo, rhi = next((lo, hi) for lo, hi in runs if lo <= sd < hi)
        descend(sd, rlo, rhi, set())
    for h in sorted(orig):
        if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
            bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not any(lo <= r.frm < hi for lo, hi in runs)]
            must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    for lo, hi in runs:
        a = lo
        while a < hi:
            must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in glue run 0x%X" % (a, lo))
            a += ida_bytes.get_item_size(a)
        must(a == hi, "glue run 0x%X..0x%X ends at 0x%X" % (lo, hi, a))
        must(ida_funcs.append_func_tail(ida_funcs.get_func(ea), lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (ea, lo, hi))
    if x["chunks_after"] is None:
        f = ida_funcs.get_func(ea)
        x["end"], x["chunks_after"] = f.end_ea, chunks(ea)
        x["sha256"] = sha(x["before_end"], x["end"])
    must(gl_state(x) == "applied", "glue of 0x%X (state %s, chunks %s)" % (ea, gl_state(x), chunks(ea)))


def add_all(items,""")
rep("trs=(), abs_=(), dfs=()):\n    before = snapshot()\n", """trs=(), abs_=(), dfs=(), gls=()):
    before = snapshot()
""")
rep("""    for x in abs_:
        if ab_state(x) != "applied":
            absorb(x)
""", """    for x in abs_:
        if ab_state(x) != "applied":
            absorb(x)
    for x in gls:
        if gl_state(x) != "applied":
            glue(x)
""")
rep("""| {x["ea"] for x in abs_} | {x["frag"] for x in abs_},""", """| {x["ea"] for x in abs_} | {x["frag"] for x in abs_} | {x["ea"] for x in gls},""")
rep("""    if dfs:
        log.append("data fix""", """    if gls:
        log.append("glued: %s" % ["0x%X + %s" % (x["ea"], ["0x%X..0x%X" % tuple(r) for r in x["runs"]]) for x in gls])
    if dfs:
        log.append("data fix""")
rep("""        oldd = {x["lo"]""", """        oldg = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("glue_funcs", [])} if MANIFEST.exists() else {}
        gls = []
        for ea, runs in GLUE:
            if ea in oldg:
                gls.append(oldg[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea, "0x%X is not a function start" % ea)
            gls.append({"ea": ea, "runs": [[lo, hi] for lo, hi, sd in runs], "seeds": [q for lo, hi, sd in runs for q in sd],
                        "runs_sha256": [sha(lo, hi) for lo, hi, sd in runs], "before_end": f.end_ea, "chunks_before": chunks(ea),
                        "end": None, "sha256": None, "chunks_after": None})
        oldd = {x["lo"]""")
rep("add_all(items, exts, rebs, rms, tfs, xts, trs, abs_, dfs)\n        MANIFEST", "add_all(items, exts, rebs, rms, tfs, xts, trs, abs_, dfs, gls)\n        MANIFEST")
rep('"data_fix": dfs,', '"data_fix": dfs, "glue_funcs": gls,')
rep('"finding": 143,', '"finding": 144,')
rep("""    dfs = doc.get("data_fix", [])
""", """    dfs = doc.get("data_fix", [])
    gls = doc.get("glue_funcs", [])
""")
rep("[df_state(x) for x in dfs])", "[df_state(x) for x in dfs] + [gl_state(x) for x in gls])")
rep("""add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_, dfs)""", """add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_, dfs, gls)""")
open(p, "w", newline="", encoding="utf-8").write(s)

p = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
rep("""        out[x["ea"]] = {"ea": x["ea"], "before_end": x["before_end"], "end": x["end"], "sha256": x["sha256"]}
    return out""", """        out[x["ea"]] = {"ea": x["ea"], "before_end": x["before_end"], "end": x["end"], "sha256": x["sha256"]}
    for x in m.get("glue_funcs", []):         # finding 144: misdecoded pieces of the function's own body glued on as chunks
        out[x["ea"]] = {"ea": x["ea"], "before_end": x["before_end"], "end": x["end"], "sha256": x["sha256"]}
    return out""")
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
