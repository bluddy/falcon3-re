from pathlib import Path

p = Path(r"C:\Users\ybarnoy\projects\falcon3\docs\findings_log.md")
raw = p.read_bytes()
bare = raw.count(b"\n") - raw.count(b"\r\n")
print("before: CRLF", raw.count(b"\r\n"), "bare LF", bare, "CR", raw.count(b"\r") - raw.count(b"\r\n"), "BEL", raw.count(b"\x07"))
fixed = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
p.write_bytes(fixed)
raw = p.read_bytes()
print("after: CRLF", raw.count(b"\r\n"), "bare LF", raw.count(b"\n") - raw.count(b"\r\n"))
