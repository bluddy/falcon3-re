"""Assemble BCC-generated ASM with TASM, extract _sub_1a6d4 bytes, compare to IDA."""
import json
import os
import subprocess
import tempfile

DOSBOX = r"C:\dosbox-x\dosbox-x.exe"
BCC = r"C:\Users\yotam\projects\falcon3\dos_compilers\bcc2.0"
ROOT = r"C:\Users\yotam\projects\falcon3"

# fresh asm from the -c -ml -1 build (v2 already made; re-make for reproducibility)
tmp = tempfile.mkdtemp()
conf = f"""[sdl]
fullscreen=false
[dosbox]
machine=svga_s3
memsize=16
[cpu]
core=normal
cputype=386
cycles=max
[mixer]
nosound=true
[autoexec]
mount c {BCC.replace(chr(92), chr(92)*2)}
c:
BIN\\BCC -c -ml -1 -S probe\\T.C > bcc.log 2>&1
if exist T.ASM move /Y T.ASM final.ASM >nul
BIN\\TASM /ml /la final.ASM final.OBJ > tasm.log 2>&1
exit
"""
p = os.path.join(tmp, "t.conf")
open(p, "w").write(conf)
subprocess.run([DOSBOX, "-exit", "-conf", p], capture_output=True, text=True, timeout=120)

for f in ("bcc.log", "tasm.log"):
    path = os.path.join(BCC, f)
    if os.path.exists(path):
        print(f, ":", open(path, encoding="cp437", errors="ignore").read().strip()[:400])

lst = os.path.join(BCC, "final.LST")
if not os.path.exists(lst):
    print("NO LISTING")
    raise SystemExit(1)

# parse TASM listing: between "_sub_1a6d4 PROC" and "ENDP", collect machine bytes
text = open(lst, encoding="cp437", errors="ignore").read().splitlines()
in_proc = False
code = bytearray()
for line in text:
    if "_sub_1a6d4" in line and "PROC" in line.upper():
        in_proc = True
        continue
    if in_proc and "ENDP" in line.upper():
        break
    if not in_proc:
        continue
    # TASM /la listing line: OFFSET  HEXBYTES ...
    # hex bytes appear right after the offset column (4-6 hex chars + space)
    s = line.rstrip()
    # strip line number prefix if present
    m = None
    import re
    m = re.match(r"^\s*\d+\s+[0-9A-Fa-f]{4}\s+((?:[0-9A-Fa-f]{2}[0-9A-Fa-f]? ?)+)", s)
    if not m:
        m = re.match(r"^\s*([0-9A-Fa-f]{4})\s+((?:[0-9A-Fa-f]{2} ?)+)", s)
        if m:
            hexpart = m.group(2)
        else:
            continue
    else:
        hexpart = m.group(1)
    for tok in hexpart.split():
        if len(tok) in (2, 4, 6, 8) and all(c in "0123456789abcdefABCDEF" for c in tok):
            # tokens of >2 chars = grouped; split into bytes
            for k in range(0, len(tok), 2):
                code.extend(bytes([int(tok[k:k + 2], 16)]))

got = bytes(code)
want = bytes.fromhex(json.load(open(
    os.path.join(ROOT, r"analysis\ida_falconcd\function_bytes.json")))["sub_1A6D4"]["bytes"])
print("got  (%d): %s" % (len(got), got.hex()))
print("want (%d): %s" % (len(want), want.hex()))
print("MATCH!" if got == want else "DIFFER")
if got != want:
    for i in range(min(len(got), len(want))):
        if got[i] != want[i]:
            print("first diff at %d: got %02x want %02x" % (i, got[i], want[i]))
            print("got ctx :", got[max(0, i - 4):i + 8].hex())
            print("want ctx:", want[max(0, i - 4):i + 8].hex())
            break
    if len(got) != len(want):
        print("length differs")
