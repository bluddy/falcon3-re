p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a, s.count(a))
    s = s.replace(a, b)


rep("(0x129F7, 0x12B12), (0x12B12, 0x12B62)]\n# ea ->", "(0x129F7, 0x12B12), (0x12B12, 0x12B62),\n       (0x100CA8, 0x100D00)]\n# ea ->")
rep("0x12B12: (0x12B12, 0x12B62, [0x12B12])}\n",
    "0x12B12: (0x12B12, 0x12B62, [0x12B12]), 0x100CA8: (0x100CA8, 0x100D00, [0x100CA8])}\n"
    "# ea -> (tail chunk, clear ranges, seeds, pad bytes): a function whose second chunk lies after a foreign function that sits\n"
    "# inside its span (finding 131); pad bytes are single data bytes inside a chunk that no flow reaches\n"
    "TAILS = {0x100CA8: ([(0x100D0E, 0x100DFA)], [(0x100CA8, 0x100D00), (0x100D0D, 0x100DFA)], [0x100CA8, 0x100D0E, 0x100DF4], [0x100DEC])}\n")
rep("(0x10CFA6, 0x10CE30, 0x10CFEC, 0x10CFA5, None)]", "(0x10CFA6, 0x10CE30, 0x10CFEC, 0x10CFA5, None),\n          (0x4335A, 0x4334E, 0x43395, 0x4334E, None)]")
rep('''    lo, hi = item["ea"], item["end"]
    if "clear" in item:
        clo, chi = item["clear"]
        a, orig = clo, set()
        while a < chi:
            h = ida_bytes.get_item_head(a)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                orig.add(h)
            a = h + max(ida_bytes.get_item_size(h), 1)
        ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        for sd in item["seeds"]:
            descend(sd, lo, hi, set())
        for h in sorted(orig):
            if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
                bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not (lo <= r.frm < hi)]
''', '''    lo, hi = item["ea"], item["end"]
    if "clear" in item or "clears" in item:
        regs = regions(item)
        orig = set()
        for clo, chi in item.get("clears") or [item["clear"]]:
            a = clo
            while a < chi:
                h = ida_bytes.get_item_head(a)
                if ida_bytes.is_code(ida_bytes.get_flags(h)):
                    orig.add(h)
                a = h + max(ida_bytes.get_item_size(h), 1)
            ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        for sd in item["seeds"]:
            rlo, rhi = next((x, y) for x, y in regs if x <= sd < y)
            descend(sd, rlo, rhi, set())
        for h in sorted(orig):
            if not (ida_bytes.is_code(ida_bytes.get_flags(h)) and ida_bytes.get_item_head(h) == h):
                bad = [r.frm for r in idautils.XrefsTo(h, 0) if r.type in (16, 17, 18, 19) and not any(x <= r.frm < y for x, y in regs)]
''')
rep('''def state(item):
    f = ida_funcs.get_func(item["ea"])
    if f and f.start_ea == item["ea"] and f.end_ea == item["end"]:
        return "applied"
    if (not any(ida_funcs.get_func(a) for a in range(item["ea"], item["end"]))
            and sha(item["ea"], item["end"]) == item["sha256"]):
        return "fresh"
    return "mismatch"
''', '''def regions(item):
    return [[item["ea"], item["end"]]] + [list(t) for t in item.get("tails", [])]


def state(item):
    f = ida_funcs.get_func(item["ea"])
    if f and f.start_ea == item["ea"] and f.end_ea == item["end"] and (not item.get("tails") or chunks(item["ea"]) == sorted(regions(item))):
        return "applied"
    if (not any(ida_funcs.get_func(a) for lo, hi in regions(item) for a in range(lo, hi))
            and sha(item["ea"], item["end"]) == item["sha256"]
            and all(sha(lo, hi) == t for (lo, hi), t in zip(item.get("tails", []), item.get("tails_sha256", [])))):
        return "fresh"
    return "mismatch"


def uname(ea):
    return idaapi.get_name(ea) if ida_bytes.has_user_name(ida_bytes.get_flags(ea)) else None
''')
rep('idaapi.get_name(new) == x["name"]:\n        return "applied"', 'uname(new) == x["name"]:\n        return "applied"')
rep('idaapi.get_name(old) == x["name"]\n', 'uname(old) == x["name"]\n')
rep('''    must(ida_name.set_name(new, x["name"], ida_name.SN_NOWARN), "name of 0x%X" % new)''',
    '''    if x["name"]:
        must(ida_name.set_name(new, x["name"], ida_name.SN_NOWARN), "name of 0x%X" % new)''')
rep('''"name": idaapi.get_name(old),
                         "far"''', '''"name": uname(old),
                         "far"''')
rep('must(x["old_ea"] not in after and after[x["ea"]][0] == x["name"], "rebase of 0x%X" % x["old_ea"])',
    'must(x["old_ea"] not in after and (x["name"] is None or after[x["ea"]][0] == x["name"]), "rebase of 0x%X" % x["old_ea"])')
rep('''        must(f.start_ea == it["ea"] and f.end_ea == it["end"], "span of 0x%X" % it["ea"])
        must(chunks(it["ea"]) == [[it["ea"], it["end"]]], "chunks of 0x%X" % it["ea"])
        if "clear" in it:
            must(terminated(it["ea"], it["end"]), "0x%X..0x%X does not end in a terminator" % (it["ea"], it["end"]))
''', '''        must(f.start_ea == it["ea"] and f.end_ea == it["end"], "span of 0x%X" % it["ea"])
        for lo, hi in it.get("tails", []):
            must(ida_funcs.append_func_tail(f, lo, hi), "append_func_tail 0x%X 0x%X..0x%X" % (it["ea"], lo, hi))
            f = ida_funcs.get_func(it["ea"])
        must(chunks(it["ea"]) == sorted(regions(it)), "chunks of 0x%X" % it["ea"])
        if "clear" in it or "clears" in it:
            for lo, hi in regions(it):
                must(terminated(lo, hi), "0x%X..0x%X does not end in a terminator" % (lo, hi))
''')
rep('''            a = it["ea"]
            while a < it["end"]:
                must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                a += ida_bytes.get_item_size(a)''', '''            for lo, hi in regions(it):
                a = lo
                while a < hi:
                    if a in it.get("pad", []):
                        a += 1
                        continue
                    must(ida_bytes.is_code(ida_bytes.get_flags(a)), "non-code head 0x%X in 0x%X" % (a, it["ea"]))
                    a += ida_bytes.get_item_size(a)''')
rep('''            must(not any(ida_funcs.get_func(a) for a in range(ea, end)), "0x%X..0x%X already owned" % (ea, end))
            must(ea in ADD_CLEAR or terminated(ea, end), "0x%X..0x%X does not end in a terminator" % (ea, end))
            it = {"ea": ea, "end": end, "last": None, "callers": callers(ea), "sha256": sha(ea, end)}
            if ea in ADD_CLEAR:
                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
''', '''            tails = TAILS[ea][0] if ea in TAILS else []
            must(not any(ida_funcs.get_func(a) for lo, hi in [(ea, end)] + tails for a in range(lo, hi)), "0x%X..0x%X already owned" % (ea, end))
            must(ea in ADD_CLEAR or terminated(ea, end), "0x%X..0x%X does not end in a terminator" % (ea, end))
            it = {"ea": ea, "end": end, "last": None, "callers": callers(ea), "sha256": sha(ea, end)}
            if ea in ADD_CLEAR:
                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
            if ea in TAILS:
                it["tails"], it["tails_sha256"] = [list(t) for t in tails], [sha(lo, hi) for lo, hi in tails]
                it["clears"], it["seeds"], it["pad"] = [list(c) for c in TAILS[ea][1]], TAILS[ea][2], TAILS[ea][3]
                del it["clear"]
''')
rep('{"finding": 130, "step": "S1c-4 orphan code registered as functions (findings 126-130)"', '{"finding": 131, "step": "S1c-4 orphan code registered as functions (findings 126-131)"')
open(p, "w", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("patched, crlf =", crlf)
