import io
for tp in ("tools/_append_naming66.py", "tools/_append_routines66.py"):
    s = io.open(tp, encoding="utf-8").read()
    for var in ("sig", "notes"):
        old = var + ".replace('" + chr(34) + "', '" + chr(92)*2 + chr(34) + "')"
        new = (var + ".replace(chr(92), chr(92)*2)"
               ".replace('" + chr(34) + "', chr(92)*2 + '" + chr(34) + "')")
        n = s.count(old)
        s = s.replace(old, new)
        print(tp, var, "replaced", n)
    io.open(tp, "w", encoding="utf-8", newline="").write(s)
