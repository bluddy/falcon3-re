p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")

a = "# ea -> (clear_lo, clear_hi, seeds): orphan run with a misdecoded stretch"
assert s.count(a) == 1
s = s.replace(a, "# finding 141: a switch function entered through an overlay stub that pushes its offset; its second chunk lies after the stub\nADD += [(0x100457, 0x1004BE)]\n" + a)

b = "             0x22C89: (0x22C89, 0x22C91, [0x22C89])}"
assert s.count(b) == 1
s = s.replace(b, "             0x22C89: (0x22C89, 0x22C91, [0x22C89]), 0x100457: (0x100457, 0x1004BE, [0x100457])}")

c = "TAILS = {0x100CA8: ([(0x100D0E, 0x100DFA)], [(0x100CA8, 0x100D00), (0x100D0D, 0x100DFA)], [0x100CA8, 0x100D0E, 0x100DF4], [0x100DEC])}"
assert s.count(c) == 1
s = s.replace(c, c[:-1] + ",\n         0x100457: ([(0x1004CC, 0x10059E)], [(0x100457, 0x1004BE), (0x1004CC, 0x10059E)],\n                    [0x100457, 0x1004CC, 0x1004D3, 0x1004E4, 0x100502], [0x100501])}")
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok crlf=", crlf)
