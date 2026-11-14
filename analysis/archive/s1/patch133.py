p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
a = "       (0x100CA8, 0x100D00)]\n# ea ->"
assert s.count(a) == 1
s = s.replace(a, "       (0x100CA8, 0x100D00), (0x12C4F2, 0x12C504), (0x12C9D0, 0x12C9DF), (0x12CB27, 0x12CB2A)]\n# ea ->")
a = '{"finding": 132, "step": "S1c-4 orphan code registered as functions (findings 126-132)"'
assert s.count(a) == 1
s = s.replace(a, '{"finding": 133, "step": "S1c-4 orphan code registered as functions (findings 126-133)"')
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok", crlf)
