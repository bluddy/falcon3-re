import re
P = r"C:\Users\ybarnoy\projects\falcon3\registry"


def cut(path, start_pat, end_pat):
    s = open(path, newline="", encoding="utf-8").read()
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    m = re.search(start_pat, s, re.M)
    assert m and len(re.findall(start_pat, s, re.M)) == 1, (path, start_pat)
    e = re.compile(end_pat, re.M).search(s, m.end())
    assert e
    print(path.split("\\")[-1], "removing:\n" + s[m.start():e.start()])
    s = s[:m.start()] + s[e.start():]
    open(path, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)


for ida in ("sub_6EF1C", "sub_6EC14"):
    cut(P + r"\naming.yaml", r"^- ida: %s\n" % ida, r"^- ")
for ea, hyp in ((454428, "r17_entry_partial"), (453652, "data_fragment_6ec14")):
    cut(P + r"\routines.yaml", r"^- ea: %d\n(?:(?!^- ).*\n)*?  hypothesis: %s\n" % (ea, hyp), r"^- ")
