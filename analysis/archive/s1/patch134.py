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
     "# (ea, fn_end, data_end): a \"function\" that is really the head of a word table (finding 134).  The function is deleted,\n"
     "# [ea, data_end) is cleared and re-made as words; nothing may jump or call into it from outside.\n"
     "REMOVE = [(0x6EC14, 0x6EC17, 0x6EC2C), (0x6EF1C, 0x6EF1F, 0x6EF30), (0x2E1C2, 0x2E1E8, 0x2E20A)]\n"
     "# (ea, end): existing functions whose body continues in orphan code"),
    ("def add_all(items, exts=(), rebs=()):\n    before = snapshot()\n",
     '''def rm_state(x):
    ea, fe, end = x["ea"], x["fn_end"], x["end"]
    f = ida_funcs.get_func(ea)
    if sha(ea, end) != x["data_sha256"]:
        return "mismatch"
    if not any(ida_funcs.get_func(a) for a in range(ea, end)):
        a = ea
        while a < end:
            if not (ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == 2):
                return "mismatch"
            a += 2
        return "applied"
    if (f and f.start_ea == ea and f.end_ea == fe and chunks(ea) == [[ea, fe]] and uname(ea) == x["name"]
            and not any(ida_funcs.get_func(a) for a in range(fe, end))):
        return "fresh"
    return "mismatch"


def remove(x):
    ea, fe, end = x["ea"], x["fn_end"], x["end"]
    must((end - ea) % 2 == 0, "word table length 0x%X" % ea)
    a, orig = ea, set()
    while a < end:
        h = ida_bytes.get_item_head(a)
        if ida_bytes.is_code(ida_bytes.get_flags(h)):
            orig.add(h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    for h in sorted(orig):
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (ea <= r.frm < end)]
        must(not bad, "jump/call into table head 0x%X from %s" % (h, [hex(b) for b in bad]))
    must(ida_funcs.del_func(ea), "del_func 0x%X" % ea)
    ida_name.set_name(ea, "", ida_name.SN_NOWARN)
    ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, end - ea)
    for a in range(ea, end, 2):
        must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
    must(rm_state(x) == "applied", "removal of 0x%X" % ea)


def add_all(items, exts=(), rebs=(), rms=()):
    before = snapshot()
    for x in rms:
        if rm_state(x) != "applied":
            remove(x)
'''),
    ('''    must(set(changed) <= {x["ea"] for x in exts} | {x["old_ea"] for x in rebs},''',
     '''    must(set(changed) <= {x["ea"] for x in exts} | {x["old_ea"] for x in rebs} | {x["ea"] for x in rms},'''),
    ('''    must(set(after) - set(before) <= new, "unplanned new functions''',
     '''    must(not any(x["ea"] in after for x in rms), "removed function still present")
    must(set(after) - set(before) <= new, "unplanned new functions'''),
    ('''        ["0x%X -> 0x%X %s" % (x["old_ea"], x["ea"], x["name"]) for x in rebs], len(before), len(after)))''',
     '''        ["0x%X -> 0x%X %s" % (x["old_ea"], x["ea"], x["name"]) for x in rebs], len(before), len(after)))
    if rms:
        log.append("removed (word tables): %s" % ["0x%X..0x%X %s" % (x["ea"], x["end"], x["name"]) for x in rms])'''),
    ('''        add_all(items, exts, rebs)
        MANIFEST.write_text(''',
     '''        oldm = {x["ea"]: x for x in json.loads(MANIFEST.read_text()).get("remove_funcs", [])} if MANIFEST.exists() else {}
        rms = []
        for ea, fe, end in REMOVE:
            if ea in oldm:
                rms.append(oldm[ea])
                continue
            f = ida_funcs.get_func(ea)
            must(f and f.start_ea == ea and f.end_ea == fe, "0x%X is not the planned function" % ea)
            rms.append({"ea": ea, "fn_end": fe, "end": end, "name": uname(ea), "far": is_far(ea),
                        "fn_sha256": sha(ea, fe), "data_sha256": sha(ea, end)})
        add_all(items, exts, rebs, rms)
        MANIFEST.write_text('''),
    ('''"extend_funcs": exts, "rebase_funcs": rebs, "add_funcs": items},''',
     '''"extend_funcs": exts, "rebase_funcs": rebs, "remove_funcs": rms, "add_funcs": items},'''),
    ('''{"finding": 133, "step": "S1c-4 orphan code registered as functions (findings 126-133)"''',
     '''{"finding": 134, "step": "S1c-4 orphan code registered as functions (findings 126-134)"'''),
    ('''    rebs = doc.get("rebase_funcs", [])
    states = [state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs]''',
     '''    rebs = doc.get("rebase_funcs", [])
    rms = doc.get("remove_funcs", [])
    states = [state(it) for it in doc["add_funcs"]] + [ext_state(x) for x in exts] + [rb_state(x) for x in rebs] + [rm_state(x) for x in rms]'''),
    ('''    add_all(doc["add_funcs"], exts, rebs)
    if os.environ.get("OFDRY"):''', '''    add_all(doc["add_funcs"], exts, rebs, rms)
    if os.environ.get("OFDRY"):'''),
])

V = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
edit(V, [
    ('''def is_expected_rebase(rebases, a, b):''',
     '''def load_removes():
    """{ea: entry} of orphan_funcs_expected.json "remove_funcs" (finding 134): a 'function' that is the head of a word
    table and was deleted; accepted as a missing key only on an exact (ea, size, name, sha256) match."""
    p = ROOT / "registry" / "orphan_funcs_expected.json"
    if not p.exists():
        return {}
    return {e["ea"]: e for e in json.loads(p.read_text()).get("remove_funcs", [])}


def is_expected_remove(removes, a, now):
    x = removes.get(a.get("ea"))
    if not x or a.get("size") != x["fn_end"] - x["ea"]:
        return False
    if _sha(a.get("bytes")) != x["fn_sha256"] or (a.get("name") or None) != x["name"]:
        return False
    return not any(v.get("ea") is not None and x["ea"] <= v["ea"] < x["end"] for v in now.values())


def is_expected_rebase(rebases, a, b):'''),
    ('''    rebases = load_rebases()
    rebased = []''', '''    rebases = load_rebases()
    removes = load_removes()
    removed = []
    rebased = []'''),
    ('''    for k in list(lost):
        a = head[k]
''', '''    for k in list(lost):
        a = head[k]
        if is_expected_remove(removes, a, now):
            lost.remove(k)
            removed.append((k, "0x%X..0x%X deleted, 0x%X..0x%X is a word table now"
                            % (a["ea"], a["ea"] + a["size"], a["ea"], removes[a["ea"]]["end"])))
            continue
'''),
    ('''        keep = {(f["key"], f["ea"], f["size"]) for f in rng.get("keep_fns", [])}
        want = keep | {(f["key"], f["ea"], f["size"]) for f in rng["new_fns"]}''',
     '''        keep = {(f["key"], f["ea"], f["size"]) for f in rng.get("keep_fns", [])}
        want = keep | {(f["key"], f["ea"], f["size"]) for f in rng["new_fns"]}
        # a function deleted by the remove manifest (finding 134) is no longer expected; its span still tiles the range
        want = {w for w in want if not (w[1] in removes and w[2] == removes[w[1]]["fn_end"] - w[1])}'''),
    ('''    print("  CHANGED : %d" % len(changed))
    for k, why in extended + rebased:''', '''    print("  REMOVE  : %d  (intentional: word-table head deleted, sha256 pinned)" % len(removed))
    print("  CHANGED : %d" % len(changed))
    for k, why in extended + rebased + removed:'''),
])
