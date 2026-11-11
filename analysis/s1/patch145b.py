p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("""ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A),
          (0x166F80, 0x16781C, 0x16781A, 0x167827, 0x167AFF)]""", """ABSORB = [(0x166F80, 0x167440, 0x16743E, 0x167450, 0x16781A)]""")
rep("""# (func, [(lo, hi, seeds)]): finding 144.  Pieces of a function's own body that were misdecoded and left orphan: [lo, hi) is
# cleared, redecoded from the seeds and appended as a chunk of func (append_func_tail merges it with an adjacent chunk).
GLUE = [(0x2E20A, [(0x2E22F, 0x2E23D, [0x2E22F, 0x2E236]), (0x2E281, 0x2E28F, [0x2E281])])]""",
"""# (func, [(lo, hi, seeds)], [frag functions]): finding 144.  Pieces of a function's own body that were misdecoded and left orphan
# (or owned by a bogus fragment function, which is deleted and unnamed first): [lo, hi) is cleared, redecoded from the seeds and
# appended as a chunk of func (append_func_tail merges it with an adjacent chunk).
GLUE = [(0x2E20A, [(0x2E22F, 0x2E23D, [0x2E22F, 0x2E236]), (0x2E281, 0x2E28F, [0x2E281])], []),
        (0x166F80, [(0x16781A, 0x167827, [0x16781A])], [0x16781C])]""")
rep("""            and all(not any(ida_funcs.get_func(a) for a in range(lo, hi)) and sha(lo, hi) == h
                    for (lo, hi), h in zip(x["runs"], x["runs_sha256"]))):""", """            and all(not any(ida_funcs.get_func(a) and ida_funcs.get_func(a).start_ea not in x["frags"] for a in range(lo, hi))
                    and sha(lo, hi) == h for (lo, hi), h in zip(x["runs"], x["runs_sha256"]))
            and all(ida_funcs.get_func(g) and ida_funcs.get_func(g).start_ea == g and uname(g) == x["frag_names"][str(g)]
                    for g in x["frags"])):""")
rep("""    if chunks(ea) == x["chunks_after"] and f.end_ea == x["end"]:
        return "applied"
    if (chunks(ea) == x["chunks_before"] and f.end_ea == x["before_end"]
            and all(not any""", """    if chunks(ea) == x["chunks_after"] and f.end_ea == x["end"] and not any(ida_funcs.get_func(g) and ida_funcs.get_func(g).start_ea == g
                                                                          for g in x["frags"]):
        return "applied"
    if (chunks(ea) == x["chunks_before"] and f.end_ea == x["before_end"]
            and all(not any""")
rep("""    ea = x["ea"]
    runs = [list(r) for r in x["runs"]]
    orig = set()
""", """    ea = x["ea"]
    runs = [list(r) for r in x["runs"]]
    orig = set()
    for g in x["frags"]:
        must(ida_funcs.del_func(g), "del_func 0x%X" % g)
        ida_name.set_name(g, "", ida_name.SN_NOWARN)
""")
rep("""for ea, runs in GLUE:""", """for ea, runs, frags in GLUE:""")
rep(""""runs_sha256": [sha(lo, hi) for lo, hi, sd in runs], "before_end\"""", """"runs_sha256": [sha(lo, hi) for lo, hi, sd in runs], "frags": frags,
                        "frag_names": {str(g): uname(g) for g in frags}, "before_end\"""")
rep("""    if gls:
        log.append("glued""", """    must(not any(g in after for x in gls for g in x["frags"]), "glued fragment function still present")
    if gls:
        log.append("glued""")
rep("""| {x["ea"] for x in gls},""", """| {x["ea"] for x in gls} | {g for x in gls for g in x["frags"]},""")
open(p, "w", newline="", encoding="utf-8").write(s)

p = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
print(s[s.index("def load_removes"):][:1500].count("absorb_funcs"))
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
