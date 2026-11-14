p = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
a = '''        have = {(k, v["ea"], reg_size(v)) for k, v in now.items()
                if v.get("ea") is not None and lo <= v["ea"] < hi}
'''
b = '''        # a rebased start (finding 132) is read back at its pre-rebase (ea, size); the rebase itself is verified above
        rb_new = {x["ea"]: x for x in rebases.values()}

        def reg_key(k, v):
            x = rb_new.get(v["ea"])
            if x and v["size"] == x["end"] - x["ea"]:
                return (k, x["old_ea"], x["end"] - x["old_ea"])
            return (k, v["ea"], reg_size(v))
        have = {reg_key(k, v) for k, v in now.items()
                if v.get("ea") is not None and (lo <= v["ea"] < hi or v["ea"] in rb_new and lo <= rb_new[v["ea"]]["old_ea"] < hi)}
'''
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok", crlf)
