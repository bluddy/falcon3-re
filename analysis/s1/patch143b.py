p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("""# ea -> (lo, hi): word table""", """# functions that end by falling into the entry of the next function (0x155F4C is a shared `retn` stub)
FALL = {0x155F2A}
# ea -> (lo, hi): word table""")
rep("""must(ea in ADD_CLEAR or terminated(ea, end), "0x%X..0x%X does not end""", """must(ea in ADD_CLEAR or ea in FALL or terminated(ea, end), "0x%X..0x%X does not end""")
open(p, "w", newline="", encoding="utf-8").write(s)
