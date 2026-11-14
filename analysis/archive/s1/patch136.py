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
     "# Text fix (finding 136): the message text behind the 0x105D90 offset table becomes strings.  table: (lo, hi, base) offset\n"
     "# words; text: (lo, hi) typed as C strings and single control bytes (1..0x1f, bare NUL); keep: bytes that are variables\n"
     "# inside the text (0x10614A is the patched player digit of \"PLAYER #2 HAS\") and stay one-byte items.\n"
     "TEXTFIX = [{\"table\": (0x105D90, 0x105DE6, 0x105D90), \"text\": (0x105DE6, 0x10626E), \"keep\": [0x10614A]}]\n"
     "# (ea, end): existing functions whose body continues in orphan code"),
    ("def add_all(items, exts=(), rebs=(), rms=(), tfs=()):\n    before = snapshot()\n",
     '''def text_segments(x):
    lo, hi = x["text"]
    keep = set(x["keep"])
    bs = ida_bytes.get_bytes(lo, hi - lo)
    out, a = [], lo
    while a < hi:
        b = bs[a - lo]
        if a in keep or b < 0x20:
            out.append((a, 1, "b"))
            a += 1
            continue
        e = a
        while e < hi and bs[e - lo] >= 0x20 and e not in keep:
            e += 1
        if e < hi and bs[e - lo] == 0 and e not in keep:
            e += 1
        out.append((a, e - a, "s"))
        a = e
    return out


def xt_state(x):
    lo, hi = x["text"]
    tlo, thi, base = x["table"]
    if sha(lo, hi) != x["text_sha256"] or sha(tlo, thi) != x["table_sha256"]:
        return "mismatch"
    if any(ida_funcs.get_func(a) for a in range(tlo, hi)):
        return "mismatch"
    ok = all(ida_bytes.is_off0(ida_bytes.get_flags(a)) for a in range(tlo, thi, 2))
    for a, n, k in text_segments(x):
        fl = ida_bytes.get_flags(a)
        ok = ok and ida_bytes.get_item_size(a) == n and ida_bytes.is_head(fl) and (
            ida_bytes.is_strlit(fl) if k == "s" else ida_bytes.is_byte(fl))
    return "applied" if ok else "fresh"


def textfix(x):
    lo, hi = x["text"]
    tlo, thi, base = x["table"]
    for a in range(tlo, thi, 2):
        must(idc.op_plain_offset(a, 0, base), "offset 0x%X" % a)
    for a, n, k in text_segments(x):
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, n)
        if k == "b":
            must(ida_bytes.create_byte(a, 1), "create_byte 0x%X" % a)
        else:
            must(ida_bytes.create_strlit(a, n, ida_nalt.STRTYPE_C), "create_strlit 0x%X" % a)
    must(xt_state(x) == "applied", "text fix 0x%X" % lo)


def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=()):
    before = snapshot()
    for x in xts:
        if xt_state(x) != "applied":
            textfix(x)
'''),
    ("import ida_loader\n", "import ida_loader\nimport ida_nalt\n"),
    ('''    if tfs:
        log.append("table fix''', '''    if xts:
        log.append("text fix: %s" % ["0x%X..0x%X (%d items)" % (x["text"][0], x["text"][1], len(text_segments(x))) for x in xts])
    if tfs:
        log.append("table fix'''),
    ('''        add_all(items, exts, rebs, rms, tfs)
        MANIFEST.write_text(''',
     '''        oldx2 = {x["text"][0]: x for x in json.loads(MANIFEST.read_text()).get("text_fix", [])} if MANIFEST.exists() else {}
        xts = []
        for t in TEXTFIX:
            if t["text"][0] in oldx2:
                xts.append(oldx2[t["text"][0]])
                continue
            xts.append({"table": list(t["table"]), "table_sha256": sha(t["table"][0], t["table"][1]), "text": list(t["text"]),
                        "text_sha256": sha(*t["text"]), "keep": list(t["keep"])})
        add_all(items, exts, rebs, rms, tfs, xts)
        MANIFEST.write_text('''),
    ('''"table_fix": tfs, "add_funcs": items},''', '''"table_fix": tfs, "text_fix": xts, "add_funcs": items},'''),
    ('''{"finding": 135, "step": "S1c-4 orphan code registered as functions (findings 126-135)"''',
     '''{"finding": 136, "step": "S1c-4 orphan code registered as functions (findings 126-136)"'''),
    ('''    tfs = doc.get("table_fix", [])
    states = (''', '''    tfs = doc.get("table_fix", [])
    xts = doc.get("text_fix", [])
    states = ('''),
    ('''+ [rm_state(x) for x in rms] + [tf_state(x) for x in tfs])''',
     '''+ [rm_state(x) for x in rms] + [tf_state(x) for x in tfs] + [xt_state(x) for x in xts])'''),
    ('''    add_all(doc["add_funcs"], exts, rebs, rms, tfs)
    if os.environ.get("OFDRY"):''', '''    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts)
    if os.environ.get("OFDRY"):'''),
])
