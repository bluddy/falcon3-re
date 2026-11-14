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
     "# Table repair (finding 135): functions that are misread table words are deleted, the table and the text behind it are\n"
     "# remade as data, and the two dispatch tables that caused the misread are rebuilt.  funcs: (ea, end) to delete;\n"
     "# clear: [lo, hi) cleared to bytes; words: [lo, hi) remade as plain words; offwords: (lo, hi, base) words that are\n"
     "# offsets from base; plain: (lo, hi) words that are not pointers.\n"
     "TABLEFIX = [{\"funcs\": [(0x105D9D, 0x105DA7), (0x105DA7, 0x105DA9)], \"clear\": (0x105D90, 0x105EB5),\n"
     "             \"words\": (0x105D90, 0x105DE6), \"offwords\": (0x1069B4, 0x1069BE, 0x105D90), \"plain\": (0x1069BE, 0x1069C8)}]\n"
     "# (ea, end): existing functions whose body continues in orphan code"),
    ("def add_all(items, exts=(), rebs=(), rms=()):\n    before = snapshot()\n",
     '''def tf_outside(x):
    lo, hi = x["clear"]
    return sorted((r.frm, t) for t in range(lo, hi) for r in idautils.XrefsTo(t, 0)
                  if r.type in (1, 16, 17, 18, 19) and not (lo <= r.frm < hi))


def tf_state(x):
    lo, hi = x["clear"]
    olo, ohi, base = x["offwords"]
    plo, phi = x["plain"]
    if (sha(lo, hi) != x["clear_sha256"] or sha(olo, ohi) != x["offwords_sha256"]
            or sha(plo, phi) != x["plain_sha256"]):
        return "mismatch"
    if all(ida_funcs.get_func(f["ea"]) and ida_funcs.get_func(f["ea"]).start_ea == f["ea"]
           and ida_funcs.get_func(f["ea"]).end_ea == f["fn_end"] and uname(f["ea"]) == f["name"] for f in x["funcs"]):
        return "fresh"
    if any(ida_funcs.get_func(a) for a in range(lo, hi)):
        return "mismatch"
    wlo, whi = x["words"]
    for a in list(range(wlo, whi, 2)) + list(range(olo, phi, 2)):
        fl = ida_bytes.get_flags(a)
        if not (ida_bytes.is_data(fl) and ida_bytes.get_item_size(a) == 2):
            return "mismatch"
    if any(ida_bytes.is_code(ida_bytes.get_flags(a)) for a in range(lo, hi)) or tf_outside(x):
        return "mismatch"
    return "applied"


def tablefix(x):
    lo, hi = x["clear"]
    olo, ohi, base = x["offwords"]
    plo, phi = x["plain"]
    for f in x["funcs"]:
        must(ida_funcs.del_func(f["ea"]), "del_func 0x%X" % f["ea"])
        ida_name.set_name(f["ea"], "", ida_name.SN_NOWARN)
    ida_bytes.del_items(olo, ida_bytes.DELIT_SIMPLE, phi - olo)
    for a in range(olo, ohi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
        must(idc.op_plain_offset(a, 0, base), "offset 0x%X" % a)
    for a in range(plo, phi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    wlo, whi = x["words"]
    for a in range(wlo, whi, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    for a in range(whi, hi):
        must(ida_bytes.create_byte(a, 1), "create_byte 0x%X" % a)
    for frm, t in tf_outside(x):
        ida_xref.del_cref(frm, t, 0)
    left = tf_outside(x)
    must(not left, "references into the table remain %s" % [(hex(a), hex(b), ) for a, b in left][:6])
    must(tf_state(x) == "applied", "table fix 0x%X" % lo)


def add_all(items, exts=(), rebs=(), rms=(), tfs=()):
    before = snapshot()
    for x in tfs:
        if tf_state(x) != "applied":
            tablefix(x)
'''),
    ('''| {x["ea"] for x in rms},''', '''| {x["ea"] for x in rms} | {f["ea"] for x in tfs for f in x["funcs"]},'''),
    ('''    must(not any(x["ea"] in after for x in rms), "removed function still present")''',
     '''    must(not any(x["ea"] in after for x in rms) and not any(f["ea"] in after for x in tfs for f in x["funcs"]),
         "removed function still present")'''),
    ('''    if rms:
        log.append(''', '''    if tfs:
        log.append("table fix: %s" % ["0x%X..0x%X (%d functions deleted)" % (x["clear"][0], x["clear"][1], len(x["funcs"])) for x in tfs])
    if rms:
        log.append('''),
    ('''        add_all(items, exts, rebs, rms)
        MANIFEST.write_text(''',
     '''        oldt = {x["clear"][0]: x for x in json.loads(MANIFEST.read_text()).get("table_fix", [])} if MANIFEST.exists() else {}
        tfs = []
        for t in TABLEFIX:
            if t["clear"][0] in oldt:
                tfs.append(oldt[t["clear"][0]])
                continue
            fl = []
            for ea, fe in t["funcs"]:
                f = ida_funcs.get_func(ea)
                must(f and f.start_ea == ea and f.end_ea == fe, "0x%X is not the planned function" % ea)
                fl.append({"ea": ea, "fn_end": fe, "end": t["words"][1], "name": uname(ea), "far": is_far(ea),
                           "fn_sha256": sha(ea, fe)})
            tfs.append({"funcs": fl, "clear": list(t["clear"]), "clear_sha256": sha(*t["clear"]), "words": list(t["words"]),
                        "offwords": list(t["offwords"]), "offwords_sha256": sha(t["offwords"][0], t["offwords"][1]),
                        "plain": list(t["plain"]), "plain_sha256": sha(*t["plain"])})
        add_all(items, exts, rebs, rms, tfs)
        MANIFEST.write_text('''),
    ('''"remove_funcs": rms, "add_funcs": items},''', '''"remove_funcs": rms, "table_fix": tfs, "add_funcs": items},'''),
    ('''{"finding": 134, "step": "S1c-4 orphan code registered as functions (findings 126-134)"''',
     '''{"finding": 135, "step": "S1c-4 orphan code registered as functions (findings 126-135)"'''),
    ('''    rms = doc.get("remove_funcs", [])
    states = [state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs] + [rm_state(x) for x in rms]''',
     '''    rms = doc.get("remove_funcs", [])
    tfs = doc.get("table_fix", [])
    states = ([state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs]
              + [rm_state(x) for x in rms] + [tf_state(x) for x in tfs])'''),
    ('''    add_all(doc["add_funcs"], exts, rebs, rms)
    if os.environ.get("OFDRY"):''', '''    add_all(doc["add_funcs"], exts, rebs, rms, tfs)
    if os.environ.get("OFDRY"):'''),
])

V = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
edit(V, [
    ('''    return {e["ea"]: e for e in json.loads(p.read_text()).get("remove_funcs", [])}


def is_expected_remove''',
     '''    m = json.loads(p.read_text())
    out = {e["ea"]: e for e in m.get("remove_funcs", [])}
    for t in m.get("table_fix", []):          # finding 135: functions deleted together with the table they were misread from
        for f in t["funcs"]:
            out[f["ea"]] = f
    return out


def is_expected_remove'''),
])
