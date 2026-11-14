p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
a = """    if f.end_ea == ne and chunks(ea) == x["chunks_after"] and not (g and g.start_ea == fr):
        return "applied\""""
assert s.count(a) == 1
s = s.replace(a, """    if (f.end_ea >= ne and not (g and g.start_ea == fr)
            and all(any(c[0] <= lo and hi <= c[1] for c in chunks(ea)) for lo, hi in x["chunks_after"])):   # a later glue may merge chunks
        return "applied\"""")
open(p, "w", newline="", encoding="utf-8").write(s)
for p, key in ((r"C:\Users\ybarnoy\projects\falcon3\registry\naming.yaml", "- ida: r38_e149\n"), (r"C:\Users\ybarnoy\projects\falcon3\registry\routines.yaml", "- ea: 1472540\n")):
    s = open(p, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    assert s.count(key) == 1
    i = s.index(key)
    j = s.index("\n- ", i + 1) + 1
    print(p, crlf, repr(s[i:j][:60]), j - i)
    s = s[:i] + s[j:]
    open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
