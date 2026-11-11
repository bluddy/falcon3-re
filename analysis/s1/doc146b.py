import re
SRC = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\time_log_before146.yaml"
DST = r"C:\Users\ybarnoy\projects\falcon3\docs\time_log.yaml"
cur = open(DST, newline="", encoding="utf-8").read().replace("\r\n", "\n")
row = [l for l in cur.split("\n") if l.startswith("| 2026-11-11 (session 55 cont.)")]
assert len(row) == 1
orig = open(SRC, newline="", encoding="utf-8").read().replace("\r\n", "\n")
lines = orig.split("\n")
last = max(i for i, l in enumerate(lines) if l.startswith("| 2026-"))
lines.insert(last + 1, row[0])
open(DST, "w", newline="", encoding="utf-8").write("\n".join(lines).replace("\n", "\r\n"))
print("row inserted after line", last + 1)
