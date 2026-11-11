p = r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md"
s = open(p, newline="", encoding="utf-8").read().replace("\r\n", "\n")
a = s.index("- **Layout** (parsed from the bytes")
b = s.index("- **0x10614A** is not text")
new = """- **Layout** (parsed from the bytes, read-only probe): 0x105DE6..0x10626E is a sequence of NUL-terminated ASCII strings,
  each optionally preceded by a one-byte layout code (1..6, probably a column/row or colour selector).  Entries 12-17, 30
  and 37 of the table all point at 0x106260 ("SET UP ERROR").  A parse that looks only for NUL glues the code byte 0x03 at
  0x1061BA to the end of "SESSION TERMINATED  ", which would leave table entry 40 (0x1061BB) mid-string; splitting at every
  byte below 0x20 fixes that.
- **Result:** 118 items (strings and code bytes) with no gaps; all 43 table words land on an item head (nearly all on the
  layout-code byte in front of their string).
"""
s = s[:a] + new + s[b:]
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n"))
print("ok")
