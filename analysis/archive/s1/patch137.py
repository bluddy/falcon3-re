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
     "# (ea, old_end, new_end, clear_hi): a function whose tail is really data (finding 137).  The end moves up to new_end,\n"
     "# [new_end, clear_hi) is cleared and the words in [new_end, words_hi) are made 2-byte data; whatever is left up to\n"
     "# clear_hi is re-decoded by the ADD entry that follows (so an ADD_CLEAR item must cover [words_hi, clear_hi)).\n"
     "TRIM = [(0x22C62, 0x22C8B, 0x22C71, 0x22C89, 0x22C91)]\n"
     "# (ea, end): existing functions whose body continues in orphan code"),
    ("def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=()):\n    before = snapshot()\n",
     '''def trim_state(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    f = ida_funcs.get_func(ea)
    if not f or f.start_ea != ea or uname(ea) != x["name"] or sha(ea, ch) != x["sha256"]:
        return "mismatch"
    if f.end_ea == oe and chunks(ea) == [[ea, oe]]:
        return "fresh"
    if f.end_ea == ne and chunks(ea) == [[ea, ne]]:
        for a in range(ne, wh, 2):
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch"
        return "applied"
    return "mismatch"


def trim(x):
    ea, oe, ne, wh, ch = x["ea"], x["old_end"], x["end"], x["words_hi"], x["clear_hi"]
    must((wh - ne) % 2 == 0, "word run of 0x%X" % ea)
    a, orig = ne, set()
    while a < ch:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    for h in sorted(orig):
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (ne <= r.frm < ch) and h != wh]
        must(not bad, "jump/call into trimmed head 0x%X from %s" % (h, [hex(b) for b in bad][:5]))
    must(ida_funcs.set_func_end(ea, ne), "set_func_end 0x%X" % ea)
    ida_bytes.del_items(ne, ida_bytes.DELIT_SIMPLE, ch - ne)
    for a in range(ne, wh, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    must(trim_state(x) == "applied", "trim of 0x%X" % ea)


def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=()):
    before = snapshot()
    for x in trs:
        if trim_state(x) != "applied":
            trim(x)
'''),
    ('''| {f["ea"] for x in tfs for f in x["funcs"]},''', '''| {f["ea"] for x in tfs for f in x["funcs"]} | {x["ea"] for x in trs},'''),
    ('''    if xts:
        log.append("text fix''', '''    if trs:
        log.append("trimmed: %s" % ["0x%X end 0x%X -> 0x%X" % (x["ea"], x["old_end"], x["end"]) for x in trs])
    if xts:
        log.append("text fix'''),
    ('''            must(not any(ida_funcs.get_func(a) for lo, hi in [(ea, end)] + tails for a in range(lo, hi)), "0x%X..0x%X already owned" % (ea, end))''',
     '''            freed = {a for (tea, toe, tne, twh, tch) in TRIM for a in range(tne, toe)}
            must(not any(ida_funcs.get_func(a) for lo, hi in [(ea, end)] + tails for a in range(lo, hi) if a not in freed), "0x%X..0x%X already owned" % (ea, end))'''),
    ('''        add_all(items, exts, rebs, rms, tfs, xts)
        MANIFEST.write_text(''',
     '''        oldtr = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("trim_funcs", [])} if MANIFEST.exists() else {}
        trs = []
        for ea, oe, ne, wh, ch in TRIM:
            if ea in oldtr:
                trs.append(oldtr[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea and f.end_ea == oe, "0x%X is not the planned function" % ea)
            trs.append({"ea": ea, "old_end": oe, "end": ne, "words_hi": wh, "clear_hi": ch, "name": uname(ea), "far": is_far(ea),
                        "sha256": sha(ea, ch), "kept_sha256": sha(ea, ne)})
        add_all(items, exts, rebs, rms, tfs, xts, trs)
        MANIFEST.write_text('''),
    ('''"text_fix": xts, "add_funcs": items},''', '''"text_fix": xts, "trim_funcs": trs, "add_funcs": items},'''),
    ('''{"finding": 136, "step": "S1c-4 orphan code registered as functions (findings 126-136)"''',
     '''{"finding": 137, "step": "S1c-4 orphan code registered as functions (findings 126-137)"'''),
    ('''    xts = doc.get("text_fix", [])
    states = (''', '''    xts = doc.get("text_fix", [])
    trs = doc.get("trim_funcs", [])
    states = ('''),
    ('''+ [xt_state(x) for x in xts])''', '''+ [xt_state(x) for x in xts] + [trim_state(x) for x in trs])
    fresh_trims = [x for x in trs if trim_state(x) == "fresh"]
    for i, it in enumerate(doc["add_funcs"]):
        if states[i] == "mismatch" and any(x["end"] <= it["ea"] < x["old_end"] for x in fresh_trims):
            states[i] = "fresh"'''),
    ('''    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts)
    if os.environ.get("OFDRY"):''', '''    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs)
    if os.environ.get("OFDRY"):'''),
    ('''       (0x100CA8, 0x100D00), (0x12C4F2, 0x12C504), (0x12C9D0, 0x12C9DF), (0x12CB27, 0x12CB2A)]''',
     '''       (0x100CA8, 0x100D00), (0x12C4F2, 0x12C504), (0x12C9D0, 0x12C9DF), (0x12CB27, 0x12CB2A), (0x22C89, 0x22C91)]'''),
    ('''0x100CA8: (0x100CA8, 0x100D00, [0x100CA8])}''', '''0x100CA8: (0x100CA8, 0x100D00, [0x100CA8]),
             0x22C89: (0x22C89, 0x22C91, [0x22C89])}'''),
])
