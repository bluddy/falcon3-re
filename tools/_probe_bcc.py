"""Probe Borland C++ 2.0 codegen for sub_1A6D4: which flags emit enter/leave?"""
import os
import shutil
import subprocess
import tempfile

DOSBOX = r"C:\dosbox-x\dosbox-x.exe"
ROOT = r"C:\Users\yotam\projects\falcon3"
BCC = ROOT + r"\dos_compilers\bcc2.0"

src_file = r"src\sub_1A6D4.c"
tmp = tempfile.mkdtemp()
# work inside the install tree so relative include/paths resolve
work = os.path.join(BCC, "probe")
os.makedirs(work, exist_ok=True)
shutil.copy(src_file, os.path.join(work, "T.C"))

variants = [
    ("v1_noopt", "-c -ml -S"),
    ("v2_186", "-c -ml -1 -S"),
    ("v3_286", "-c -ml -2 -S"),
    ("v4_O_186", "-c -ml -O -1 -S"),
    ("v5_O_286", "-c -ml -O -2 -S"),
    ("v6_O", "-c -ml -O -S"),
]

bat_lines = ["@echo off"]
for name, flags in variants:
    bat_lines.append(f"BIN\\BCC {flags} probe\\T.C > {name}.log 2>&1")
    bat_lines.append(f"if exist T.ASM move /Y T.ASM {name}.ASM >nul")
    bat_lines.append(f"if exist probe\\T.ASM move /Y probe\\T.ASM {name}.ASM >nul")
bat_lines.append("exit")
bat = os.path.join(BCC, "run.bat")
open(bat, "w").write("\r\n".join(bat_lines))

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
call run.bat
exit
"""
conf_path = os.path.join(tmp, "bcc.conf")
open(conf_path, "w").write(conf)
subprocess.run([DOSBOX, "-exit", "-conf", conf_path], capture_output=True,
               text=True, timeout=120)

for name, flags in variants:
    asm = None
    log = None
    for d in (BCC, work):
        if asm is None and os.path.exists(os.path.join(d, name + ".ASM")):
            asm = os.path.join(d, name + ".ASM")
        if log is None and os.path.exists(os.path.join(d, name + ".log")):
            log = os.path.join(d, name + ".log")
    print("=" * 60)
    print(name, flags)
    if log:
        txt = open(log, encoding="cp437", errors="ignore").read().strip()
        if txt:
            print("  log:", txt[:300].replace("\n", " | "))
    if asm:
        a = open(asm, encoding="cp437", errors="ignore").read().lower()
        has_enter = "enter" in a
        has_leave = "leave" in a
        print(f"  ASM produced: enter={has_enter} leave={has_leave}  ({asm})")
        i = a.find("_sub_1a6d4")
        if i >= 0:
            print("  " + a[i:i+500].replace("\r", "").replace("\n", "\n  ")[:500])
    else:
        print("  NO ASM")
