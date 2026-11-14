from pathlib import Path

p = Path(r"C:\Users\ybarnoy\projects\falcon3\docs\workflow\idb_regeneration.md")
raw = p.read_bytes()
text = raw.decode("utf-8")
# the mangled line holds a bare CR (from "\r" in "tools\run_idat") and a BEL (from "\a" in "\apply")
lines = text.split("\r\n")
bad = [i for i, l in enumerate(lines) if l.startswith('cmd /c "tools') and "pply_flow_fixes" in l and "\\" not in l]
print("mangled lines:", bad, [lines[i].encode() for i in bad])
for i in bad:
    lines[i] = 'cmd /c "tools\\run_idat.bat tools\\apply_flow_fixes.py"'
p.write_bytes("\r\n".join(lines).encode("utf-8"))
raw = p.read_bytes()
print("after: CRLF", raw.count(b"\r\n"), "bare CR", raw.count(b"\r") - raw.count(b"\r\n"), "BEL", raw.count(b"\x07"))
print(lines[bad[0]])
