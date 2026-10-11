"""Probe: does MSC 6.00ax emit enter/leave for sub_1A6D4-shaped code?"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

DOSBOX = r"C:\dosbox-x\dosbox-x.exe"
MSC6 = r"C:\Users\yotam\projects\gunship_2000\tools\msc6.0\C600"
SRC = open(r"src\sub_1A6D4.c").read()

# 8.3 names
C_NAME = "SUB_1A6D.C"
COD_NAME = "SUB_1A6D"
CODES_OF_INTEREST = ["c804", "c9cb", "558bec", "8be55d"]

tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(MSC6, "probe"), exist_ok=True)
# write source into the mounted tree
probe_dir = os.path.join(MSC6, "probe")
open(os.path.join(probe_dir, C_NAME), "w").write(SRC)

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
mount c {MSC6.replace(chr(92), chr(92)*2)}
c:
path c:\\bin;c:\\binb
set INCLUDE=c:\\include
set LIB=c:\\lib
set PATH=c:\\bin;c:\\binb
cd probe
c:\\bin\\cl /c /AL /Gs /Fc{COD_NAME} /Ic:\\include {C_NAME} > log.txt
exit
"""
conf_path = os.path.join(tmp, "p.conf")
open(conf_path, "w").write(conf)
r = subprocess.run([DOSBOX, "-exit", "-conf", conf_path], capture_output=True,
                   text=True, timeout=90)
cod = os.path.join(probe_dir, COD_NAME + ".COD")
log = os.path.join(probe_dir, "log.txt")
print("cl log:", open(log).read() if os.path.exists(log) else "NO LOG")
if os.path.exists(cod):
    text = open(cod, encoding="cp437", errors="ignore").read()
    import re
    first = [l for l in text.splitlines() if re.match(r'\s*\*{3}', l)][:6]
    print("--- first code lines ---")
    for l in first:
        print(l)
    low = text.lower()
    for sig in CODES_OF_INTEREST:
        print(sig, "->", "FOUND" if sig in low else "no")
else:
    print("NO COD produced")
    # leftover from cl output?
    print(r.stdout[-500:] if r.stdout else "")
