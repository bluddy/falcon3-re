p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
assert "\r\n" not in s
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)

rep("""# (ea, end): existing functions whose body continues in orphan code""", """# (lo, hi, kind): orphan "code" that is really data (finding 144): jump-table words ('w', an odd last byte stays a byte) or
# key / record bytes ('b').  [lo, hi) is cleared and re-made as data; nothing may jump or call into it.
DATAFIX = [(0x1982F, 0x19843, "w"), (0x1277CC, 0x1277DA, "w"), (0x1B4E0, 0x1B4E8, "w"), (0x1F75F, 0x1F769, "b"),
           (0x2E190, 0x2E194, "w"), (0x5CDA8, 0x5CDB2, "b"), (0x5CDFA, 0x5CDFD, "w"), (0x5D1E6, 0x5D1ED, "b"),
           (0x5D2E5, 0x5D2E9, "b"), (0x5D5AB, 0x5D5B3, "b"), (0x5D91B, 0x5D925, "b"), (0x5DA68, 0x5DA75, "b"),
           (0x6EA3A, 0x6EA4A, "w")]
# (ea, end): existing functions whose body continues in orphan code""")

rep("""def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=(), abs_=()):
    before = snapshot()
""", """def df_items(x):
    lo, hi, k = x["lo"], x["hi"], x["kind"]
    if k == "b":
        return [(a, 1) for a in range(lo, hi)]
    n = (hi - lo) // 2
    return [(lo + 2 * i, 2) for i in range(n)] + ([(hi - 1, 1)] if (hi - lo) % 2 else [])


def df_state(x):
    lo, hi = x["lo"], x["hi"]
    if sha(lo, hi) != x["sha256"] or any(ida_funcs.get_func(a) for a in range(lo, hi)):
        return "mismatch"
    if all(ida_bytes.is_data(ida_bytes.get_flags(a)) and ida_bytes.get_item_size(a) == n for a, n in df_items(x)):
        return "applied"
    return "fresh"


def datafix(x):
    lo, hi = x["lo"], x["hi"]
    must(ida_bytes.get_item_head(lo) == lo and ida_bytes.get_item_head(hi) == hi, "range 0x%X..0x%X cuts an item" % (lo, hi))
    bad = [(hex(r.frm), hex(t)) for t in range(lo, hi) for r in idautils.XrefsTo(t, 0)
           if r.type in (16, 17, 18, 19) and not (lo <= r.frm < hi)]
    must(not bad, "jump/call into data fix 0x%X from %s" % (lo, bad[:5]))
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    for a, n in df_items(x):
        must(ida_bytes.create_word(a, 2) if n == 2 else ida_bytes.create_byte(a, 1), "create data 0x%X" % a)
    must(df_state(x) == "applied", "data fix 0x%X" % lo)


def add_all(items, exts=(), rebs=(), rms=(), tfs=(), xts=(), trs=(), abs_=(), dfs=()):
    before = snapshot()
    for x in dfs:
        if df_state(x) != "applied":
            datafix(x)
""")
rep("""    if abs_:
        log.append("absorbed:""", """    if dfs:
        log.append("data fix: %s" % ["0x%X..0x%X %s" % (x["lo"], x["hi"], x["kind"]) for x in dfs])
    if abs_:
        log.append("absorbed:""")
rep("""        add_all(items, exts, rebs, rms, tfs, xts, trs, abs_)
        MANIFEST.write_text""", """        oldd = {x["lo"]: x for x in json.loads(MANIFEST.read_text()).get("data_fix", [])} if MANIFEST.exists() else {}
        dfs = []
        for lo, hi, k in DATAFIX:
            if lo in oldd:
                dfs.append(oldd[lo])
                continue
            must(not any(ida_funcs.get_func(a) for a in range(lo, hi)), "data fix 0x%X..0x%X is owned by a function" % (lo, hi))
            dfs.append({"lo": lo, "hi": hi, "kind": k, "sha256": sha(lo, hi)})
        add_all(items, exts, rebs, rms, tfs, xts, trs, abs_, dfs)
        MANIFEST.write_text""")
rep('"absorb_funcs": abs_, "add_funcs": items}', '"absorb_funcs": abs_, "data_fix": dfs, "add_funcs": items}')
rep('"finding": 142,', '"finding": 144,')
rep("""    abs_ = doc.get("absorb_funcs", [])
    states""", """    abs_ = doc.get("absorb_funcs", [])
    dfs = doc.get("data_fix", [])
    states""")
rep("""[ab_state(x) for x in abs_])""", """[ab_state(x) for x in abs_] + [df_state(x) for x in dfs])""")
rep("""    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_)
    if os.environ""", """    add_all(doc["add_funcs"], exts, rebs, rms, tfs, xts, trs, abs_, dfs)
    if os.environ""")
open(p, "w", newline="", encoding="utf-8").write(s)
