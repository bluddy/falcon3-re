def edit(p, pairs):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    for a, b in pairs:
        assert s.count(a) == 1, (p, a[:70], s.count(a))
        s = s.replace(a, b)
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
    print("patched", p, crlf)


T = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
edit(T, [
    ("# (ea, end): existing functions whose body continues in orphan code",
     "# (owner, frag, clear_lo, clear_hi, new_end): finding 138.  frag is a bogus function made of fragments of owner's own body;\n"
     "# it is deleted, [clear_lo, clear_hi) is redecoded from clear_lo, owner's tail chunks inside [main_end, new_end) are dropped\n"
     "# and owner's main chunk is extended to new_end.\n"
     "ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A)]\n"
     "# (ea, end): existing functions whose body continues in orphan code"),
    ("def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=()):\n    before = snapshot()\n",
     '''def ab_state(x):
    ea, fr, be, ne = x["ea"], x["frag"], x["before_end"], x["end"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea or sha(be, ne) != x["sha256"]:
        return "mismatch"
    g = ida_funcs.get_func(fr)
    if f.end_ea == ne and chunks(ea) == x["chunks_after"] and not (g and g.start_ea == fr):
        return "applied"
    if (f.end_ea == be and chunks(ea) == x["chunks_before"] and g and g.start_ea == fr and uname(fr) == x["frag_name"]
            and chunks(fr) == x["frag_chunks"] and sha(fr, x["frag_end"]) == x["frag_sha256"]):
        return "fresh"
    return "mismatch"


def absorb(x):
    ea, fr, be, ne = x["ea"], x["frag"], x["before_end"], x["end"]
    clo, chi = x["clear"]
    far = is_far(ea)
    must(not is_far(fr) or far, "far flag of 0x%X" % fr)
    a, orig = clo, set()
    while a < chi:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    must(ida_funcs.del_func(fr), "del_func 0x%X" % fr)
    ida_name.set_name(fr, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
    a = clo
    while a < chi:
        n = ida_ua.create_insn(a)
        must(n > 0, "create_insn 0x%X" % a)
        a += n
    must(a == chi, "redecode of 0x%X..0x%X ends at 0x%X" % (clo, chi, a))
    lost = sorted(h for h in orig if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h))
    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (clo <= r.frm < chi)]
        must(not bad, "jump/call into stale head 0x%X from %s" % (h, [hex(b) for b in bad]))
    f = ida_funcs.get_func(ea)
    for lo, hi in chunks(ea)[1:]:
        if be <= lo < ne:
            must(ida_funcs.remove_func_tail(ida_funcs.get_func(ea), lo), "remove_func_tail 0x%X" % lo)
    must(ida_funcs.set_func_end(ea, ne), "set_func_end 0x%X -> 0x%X" % (ea, ne))
    must(is_far(ea) == far, "far flag of 0x%X" % ea)
    if x["chunks_after"] is None:
        x["chunks_after"] = chunks(ea)
    must(ab_state(x) == "applied", "absorb into 0x%X (state %s, chunks %s)" % (ea, ab_state(x), chunks(ea)))


def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=(), abs_=()):
    before = snapshot()
    for x in abs_:
        if ab_state(x) != "applied":
            absorb(x)
'''),
    ('''| {f["ea"] for x in tfs for f in x["funcs"]} | {x["ea"] for x in trs},''',
     '''| {f["ea"] for x in tfs for f in x["funcs"]} | {x["ea"] for x in trs} | {x["ea"] for x in abs_} | {x["frag"] for x in abs_},'''),
    ('''    must(not any(x["ea"] in after for x in rms) and not any(f["ea"] in after for x in tfs for f in x["funcs"]),''',
     '''    must(not any(x["frag"] in after for x in abs_), "absorbed function still present")
    must(not any(x["ea"] in after for x in rms) and not any(f["ea"] in after for x in tfs for f in x["funcs"]),'''),
    ('''    if trs:
        log.append("trimmed:''', '''    if abs_:
        log.append("absorbed: %s" % ["0x%X into 0x%X (end 0x%X)" % (x["frag"], x["ea"], x["end"]) for x in abs_])
    if trs:
        log.append("trimmed:'''),
    ('''        add_all(items, exts, rebs, rms, tfs, xts, trs)
        MANIFEST.write_text(''', '''        olda = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("absorb_funcs", [])} if MANIFEST.exists() else {}
        abs_ = []
        for ea, fr, clo, chi, ne in ABSORB:
            if ea in olda:
                abs_.append(olda[ea])
                continue
            f, g = ida_funcs.get_func(ea), ida_funcs.get_func(fr)
            must(f and f.start_ea == ea and g and g.start_ea == fr, "0x%X / 0x%X are not the planned functions" % (ea, fr))
            abs_.append({"ea": ea, "frag": fr, "frag_end": g.end_ea, "frag_name": uname(fr), "frag_far": is_far(fr),
                         "frag_chunks": chunks(fr), "frag_sha256": sha(fr, g.end_ea), "clear": [clo, chi],
                         "before_end": f.end_ea, "end": ne, "sha256": sha(f.end_ea, ne), "chunks_before": chunks(ea),
                         "chunks_after": None})
        add_all(items, exts, rebs, rms, tfs, xts, trs, abs_)
        MANIFEST.write_text('''),
    ('''"trim_funcs": trs, "add_funcs": items},''', '''"trim_funcs": trs, "absorb_funcs": abs_, "add_funcs": items},'''),
    ('''{"finding": 137, "step": "S1c-4 orphan code registered as functions (findings 126-137)"''',
     '''{"finding": 138, "step": "S1c-4 orphan code registered as functions (findings 126-138)"'''),
    ('''    trs = doc.get("trim_funcs", [])
    states = (''', '''    trs = doc.get("trim_funcs", [])
    abs_ = doc.get("absorb_funcs", [])
    states = ('''),
    ('''+ [trim_state(x) for x in trs])
    fresh_trims''', '''+ [trim_state(x) for x in trs]
              + [ab_state(x) for x in abs_])
    fresh_trims'''),
    ('''    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs)
    if os.environ.get("OFDRY"):''', '''    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_)
    if os.environ.get("OFDRY"):'''),
])

V = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
edit(V, [
    ('''    return {e["ea"]: e for e in json.loads(p.read_text()).get("extend_funcs", [])}''',
     '''    m = json.loads(p.read_text())
    out = {e["ea"]: e for e in m.get("extend_funcs", [])}
    for x in m.get("absorb_funcs", []):       # finding 138: the owner's main chunk grows over the absorbed fragment's bytes
        out[x["ea"]] = {"ea": x["ea"], "before_end": x["before_end"], "end": x["end"], "sha256": x["sha256"]}
    return out'''),
    ('''    for t in m.get("table_fix", []):          # finding 135''', '''    for x in m.get("absorb_funcs", []):       # finding 138: a bogus function deleted, its bytes now belong to the owner
        out[x["frag"]] = {"ea": x["frag"], "fn_end": x["frag_end"], "end": x["frag_end"], "name": x["frag_name"],
                          "fn_sha256": x["frag_sha256"]}
    for t in m.get("table_fix", []):          # finding 135'''),
])
