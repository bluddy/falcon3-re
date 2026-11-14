p = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
a = """    for t in m.get("table_fix", []):          # finding 135"""
assert s.count(a) == 1
s = s.replace(a, """    for x in m.get("glue_funcs", []):         # finding 144: a bogus fragment function deleted, its bytes glued onto the owner
        for g, fe in zip(x["frags"], x["frag_ends"]):
            out[g] = {"ea": g, "fn_end": fe, "end": fe, "name": x["frag_names"][str(g)], "fn_sha256": x["frag_sha256"][str(g)]}
""" + a)
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)

p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
a = '''"frag_names": {str(g): uname(g) for g in frags},'''
assert s.count(a) == 1
s = s.replace(a, '''"frag_names": {str(g): uname(g) for g in frags},
                        "frag_ends": [ida_funcs.get_func(g).end_ea for g in frags],
                        "frag_sha256": {str(g): sha(g, ida_funcs.get_func(g).end_ea) for g in frags},''')
open(p, "w", newline="", encoding="utf-8").write(s)
