import re
p = r"C:\Users\ybarnoy\projects\falcon3\tools\apply_orphan_funcs.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
new = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or138d.txt").read().split("ADD_NEW = ")[1].strip()
a = "(0x12CB27, 0x12CB2A), (0x22C89, 0x22C91)]\n"
assert s.count(a) == 1
s = s.replace(a, "(0x12CB27, 0x12CB2A), (0x22C89, 0x22C91)]\n"
              "# finding 139: no-xref runs that end in a terminator (far stubs, wrappers, an ISR); scan analysis/s1/orphan_scan138.json\n"
              "ADD += " + new + "\n")
s = s.replace('"finding": 138, "step": "S1c-4 orphan code registered as functions (findings 126-138)"',
              '"finding": 139, "step": "S1c-4 orphan code registered as functions (findings 126-139)"')
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok")
