import io
p = r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md"
s = io.open(p, "r", newline="", encoding="utf-8").read()
old = u"### Finding 126 \u2014 S1c-4: call-reached orphan code registered as functions"
new = u"## 2026-11-10 126 - Call-reached orphan code registered as functions (S1c-4)"
assert s.count(old) == 1
io.open(p, "w", newline="", encoding="utf-8").write(s.replace(old, new))
print("ok")
