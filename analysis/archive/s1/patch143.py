p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
assert "\r\n" not in s

def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)

rep("""ADD += [(0x100457, 0x1004BE)]
""", """ADD += [(0x100457, 0x1004BE)]
# finding 143: the real entry sits in a misdecoded stretch behind a word table (0x12BF96) or inside a table's last bytes (0x155F18)
ADD += [(0x12BF96, 0x12BFA8), (0x12BFA8, 0x12BFE1), (0x155F18, 0x155F2A), (0x155F2A, 0x155F4C)]
""")
rep("""0x100457: (0x100457, 0x1004BE, [0x100457])}
""", """0x100457: (0x100457, 0x1004BE, [0x100457]),
             0x12BF96: (0x12BF88, 0x12BF99, [0x12BF96]), 0x155F18: (0x155F18, 0x155F1A, [0x155F18])}
# ea -> (lo, hi): word table entries inside the ADD_CLEAR range, made words again before the code behind them is redecoded
ADD_WORDS = {0x12BF96: (0x12BF88, 0x12BF96)}
""")
rep("""            ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        for sd in item["seeds"]:""", """            ida_bytes.del_items(clo, ida_bytes.DELIT_SIMPLE, chi - clo)
        if "words" in item:
            for a in range(item["words"][0], item["words"][1], 2):
                must(ida_bytes.create_word(a, 2), "create_word 0x%X" % a)
        for sd in item["seeds"]:""")
rep("""                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
""", """                it["clear"], it["seeds"] = list(ADD_CLEAR[ea][:2]), ADD_CLEAR[ea][2]
                if ea in ADD_WORDS:
                    it["words"] = list(ADD_WORDS[ea])
""")
rep('"finding": 139,', '"finding": 143,')
open(p, "w", newline="", encoding="utf-8").write(s)
