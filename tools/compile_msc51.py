#!/usr/bin/env python3
"""Compile using MSC 5.1 under DOSBox-X"""
import subprocess
import sys
import os
import argparse
import tempfile
import shutil

DOSBOX_X = r"C:\dosbox-x\dosbox-x.exe"
MSC51_ROOT = r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1"
SRC_DIR = r"C:\Users\yotam\projects\falcon3\src"
OBJ_DIR = r"C:\Users\yotam\projects\falcon3\obj"
CONF_FILE = r"C:\Users\yotam\projects\falcon3\dosbox_msc51.conf"

def ensure_dirs():
    os.makedirs(SRC_DIR, exist_ok=True)
    os.makedirs(OBJ_DIR, exist_ok=True)

def write_dosbox_conf():
    """Write DOSBox config file for MSC 5.1"""
    conf = f"""[sdl]
fullscreen=false
fulldouble=false
window_size=1024x768
output=opengl
autolock=true
mouse_sensitivity=100
waitonerror=true
priority=higher,normal
mapperfile=mapper-0.74-3.map
keyboard_layout=us

[dosbox]
machine=svga_s3
captures=capture
memsize=16

[render]
cpu_cycles=max
cpu_cycles_protected=auto
cpu_throttle=1
presentation_mode=dos_rate

[render]
shader=none

[cpu]
core=normal
cputype=386
cpu_cycles=max
cpu_cycles_protected=auto
cpu_throttle=1

[mixer]
nosound=true
rate=44100
blocksize=1024
prebuffer=25

[midi]
mpu401=none
mididevice=none
midiconfig=

[sblaster]
sbtype=none
sbbase=220
irq=7
dma=1
hdma=5
sbmixer=true
oplmode=auto
oplrate=44100

[gus]
gus=false
gusrate=44100
gusbase=240
gusirq=5
gusdma=3
ultradir=C:\\ULTRASND

[speaker]
pcspeaker=false
pcrate=44100
tandy=auto
tandyrate=44100
disney=true

[joystick]
joysticktype=none
timed=true
autofire=false
swap34=false
buttonwrap=false

[serial]
serial1=directserial realport:COM1
serial2=disabled
serial3=disabled
serial4=disabled

[dos]
xms=true
ems=true
umb=true
keyboard_layout=us

[ipx]
ipx=false

[autoexec]
mount c {MSC51_ROOT.replace('\\', '\\\\')}
c:
path c:\\bin;c:\\binb
set INCLUDE=c:\\include
set LIB=c:\\lib
set PATH=c:\\bin;c:\\binb
"""
    with open(CONF_FILE, 'w') as f:
        f.write(conf)

def compile_c(source_file, output_file, flags="/c /Os /AS"):
    """Compile a C file using MSC 5.1 under DOSBox-X"""
    ensure_dirs()
    
    rel_source = os.path.relpath(source_file, SRC_DIR)
    rel_output = os.path.relpath(output_file, OBJ_DIR)
    
    # Convert to DOS paths
    dos_src = rel_source.replace('/', '\\')
    dos_out = rel_output.replace('/', '\\')
    
    # Write DOSBox config
    write_dosbox_conf()
    
    # Create BAT file with the compile command
    bat_content = f"""@echo off
d:
c:\\cl.exe {flags} d:\\{dos_src} /Foe:\\{dos_out}
if errorlevel 1 exit /b 1
"""
    
    # Create temp directory for bat/log files
    with tempfile.TemporaryDirectory() as tmpdir:
        bat_file = os.path.join(tmpdir, "compile.bat")
        log_file = os.path.join(tmpdir, "compile.log")
        
        with open(bat_file, 'w') as f:
            f.write(bat_content)
        
        # Copy config file to temp dir
        tmp_conf = os.path.join(tmpdir, "dosbox.conf")
        shutil.copy2(CONF_FILE, tmp_conf)
        
        # Run DOSBox-X
        cmd = [
            "C:\\dosbox-x\\dosbox-x.exe",
            "-conf", tmp_conf,
            bat_file,
            "-exit"
        ]
        
        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=SRC_DIR)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check if output file was created
        if os.path.exists(output_file):
            print(f"Success: {output_file} created")
            return True
        else:
            print(f"Failed: {output_file} not created")
            if os.path.exists(os.path.join(tmpdir, "compile.log")):
                with open(os.path.join(tmpdir, "compile.log")) as f:
                    print(f.read())
            return False

def link_exe(obj_files, output_exe, libs="slibce.lib"):
    """Link object files into EXE"""
    ensure_dirs()
    
    dos_objs = " ".join([f"e:\\{os.path.relpath(f, OBJ_DIR).replace('/', '\\')}" for f in obj_files])
    
    bat_content = f"""@echo off
e:
c:\\link.exe {dos_objs}, {os.path.basename(output_exe)},, {libs}
if errorlevel 1 exit /b 1
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bat_file = os.path.join(tmpdir, "link.bat")
        log_file = os.path.join(tmpdir, "link.log")
        
        with open(bat_file, 'w') as f:
            f.write(bat_content)
        
        tmp_conf = os.path.join(tmpdir, "dosbox.conf")
        shutil.copy2(CONF_FILE, tmp_conf)
        
        cmd = [
            "C:\\dosbox-x\\dosbox-x.exe",
            "-conf", os.path.join(tmpdir, "dosbox.conf"),
            os.path.join(tmpdir, "link.bat"),
            "-exit"
        ]
        
        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=OBJ_DIR)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if os.path.exists(output_exe):
            print(f"Success: {output_exe} created")
            return True
        else:
            print(f"Failed: {output_exe} not created")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile C with MSC 5.1 under DOSBox-X")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    compile_parser = subparsers.add_parser("compile", help="Compile C source to object")
    compile_parser.add_argument("source", help="Source .c file")
    compile_parser.add_argument("output", help="Output .obj file")
    compile_parser.add_argument("--flags", default="/c /Os /AS", help="Compiler flags")
    
    link_parser = subparsers.add_parser("link", help="Link objects to EXE")
    link_parser.add_argument("objects", nargs="+", help="Object files")
    link_parser.add_argument("output", help="Output .exe file")
    link_parser.add_argument("--libs", default="slibce.lib", help="Libraries to link")
    
    args = parser.parse_args()
    
    if args.command == "compile":
        os.makedirs(OBJ_DIR, exist_ok=True)
        success = compile_c(args.source, args.output, args.flags)
        sys.exit(0 if success else 1)
    elif args.command == "link":
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        success = link_exe(args.objects, args.output, args.libs)
        sys.exit(0 if success else 1)