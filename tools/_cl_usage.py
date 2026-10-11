"""Dump MSC 5.1 CL usage (all options) via DOSBox."""
import os
import subprocess
import tempfile

DOSBOX = r"C:\dosbox-x\dosbox-x.exe"
MSC = r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1"

tmp = tempfile.mkdtemp()
conf = f"""[sdl]
fullscreen=false
[dosbox]
machine=svga_s3
memsize=16
[cpu]
core=normal
cycles=max
[mixer]
nosound=true
[autoexec]
mount c {MSC.replace(chr(92), chr(92)*2)}
c:
path c:\\rbin;c:\\rbinb
rbin\\cl > usage.txt 2>&1
exit
"""
p = os.path.join(tmp, "u.conf")
open(p, "w").write(conf)
subprocess.run([DOSBOX, "-exit", "-conf", p], capture_output=True, text=True, timeout=60)
out = os.path.join(MSC, "usage.txt")
print(open(out, encoding="cp437", errors="ignore").read() if os.path.exists(out) else "NO usage.txt")
