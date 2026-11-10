p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:60], s.count(a))
    s = s.replace(a, b)


rep("# (old_start, new_start, end, clear_lo, ds_para): existing function whose real entry is new_start (finding 130).\n"
    "# [clear_lo, end) is cleared and redecoded from new_start; ds_para (or None) extends the DS range down to new_start.\n",
    "# (old_start, new_start, end, clear_lo, ds_para[, clear_hi]): existing function whose real entry is new_start (finding 130).\n"
    "# [clear_lo, clear_hi) (default end) is cleared and redecoded from new_start; ds_para (or None) extends the DS range\n"
    "# down to new_start.  A narrow clear_hi (finding 132, an instruction boundary) leaves the rest of a long body alone.\n")
rep("          (0x4335A, 0x4334E, 0x43395, 0x4334E, None)]",
    "          (0x4335A, 0x4334E, 0x43395, 0x4334E, None),\n"
    "          (0x6EF31, 0x6EF30, 0x6F1CE, 0x6EF30, None, 0x6EF39), (0x69723, 0x69720, 0x69AC6, 0x69720, None, 0x6972B)]")
rep('''    old, new, end, clo = x["old_ea"], x["ea"], x["end"], x["clear_lo"]
    far = is_far(old)
    must(far == x["far"], "far flag of 0x%X" % old)
    a, orig = clo, set()
    while a < end:''', '''    old, new, end, clo = x["old_ea"], x["ea"], x["end"], x["clear_lo"]
    chi = x.get("clear_hi") or end
    far = is_far(old)
    must(far == x["far"], "far flag of 0x%X" % old)
    a, orig = clo, set()
    while a < chi:''')
rep('''    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, end - clo)
    if x.get("ds") is not None:''', '''    ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
    if x.get("ds") is not None:''')
rep('''    descend(new, new, end, made)
    a = new
    while a < end:
        must(ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.get_item_head(a) == a, "non-code head 0x%X in rebased 0x%X" % (a, new))''',
    '''    descend(new, new, chi, made)
    a = new
    while a < chi:
        must(ida_bytes.is_code(ida_bytes.get_flags(a)) and ida_bytes.get_item_head(a) == a, "non-code head 0x%X in rebased 0x%X" % (a, new))''')
rep('''    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (new <= r.frm < end)]''',
    '''    for h in lost:
        bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (new <= r.frm < end)]''')
rep('''    for old, new, end, clo, ds in REBASE:
            if new in oldr:
                rebs.append(oldr[new])
                continue''', '''    for old, new, end, clo, ds, *chi in REBASE:
            if new in oldr:
                rebs.append(oldr[new])
                continue''')
rep('''"prefix_sha256": sha(new, old), "lost_heads": None})''', '''"prefix_sha256": sha(new, old), "lost_heads": None, **({"clear_hi": chi[0]} if chi else {})})''')
rep('{"finding": 131, "step": "S1c-4 orphan code registered as functions (findings 126-131)"', '{"finding": 132, "step": "S1c-4 orphan code registered as functions (findings 126-132)"')
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("patched crlf=", crlf)
