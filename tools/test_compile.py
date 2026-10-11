import os
import subprocess

msc_dir = r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1"

config_content = """[sdl]
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
mount c C:\\\\Users\\\\yotam\\\\projects\\\\falcon3\\\\dos_compilers\\\\msc5.1
c:
path c:\\\\bin;c:\\\\binb
set INCLUDE=c:\\\\include
set LIB=c:\\\\lib
set PATH=c:\\\\bin;c:\\\\binb
bin\\\\cl /c /Gs /FcHELLO /Ic:\\\\include HELLO.c > compile.log
exit
"""

config_path = r"C:\Users\yotam\projects\falcon3\test_dosbox.conf"
with open(config_path, "w") as f:
    f.write(config_content)

result = subprocess.run(
    [r"C:\dosbox-x\dosbox-x.exe", "-exit", "-conf", config_path],
    capture_output=True, text=True, timeout=60, cwd=r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1"
)

print("returncode:", result.returncode)
print("stdout:", result.stdout[-1000:])
print("stderr:", result.stderr[-500:])

# Check files
for f in ["compile.log", "HELLO.c", "HELLO.OBJ", "HELLO.COD"]:
    p = os.path.join(r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1", f)
    if os.path.exists(p):
        print(f"EXISTS: {p}")
        with open(p, "r") as f:
            print(f.read()[:500])
    else:
        print(f"MISSING: {p}")