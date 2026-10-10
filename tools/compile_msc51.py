#!/usr/bin/env python3
"""Compile using MSC 5.1 under DOSBox-X"""
import subprocess
import sys
import os
import argparse

DOSBOX_X = r"C:\dosbox-x\dosbox-x.exe"
MSC51_ROOT = r"C:\dos_compilers\MSC51"
SRC_DIR = r"C:\Users\yotam\projects\falcon3\src"
OBJ_DIR = r"C:\Users\yotam\projects\falcon3\obj"

def compile_c(source_file, output_file, flags="/c /Os /AS"):
    """Compile a C file using MSC 5.1 under DOSBox-X"""
    # Convert to DOS 8.3 names
    rel_source = os.path.relpath(source_file, SRC_DIR)
    rel_output = os.path.relpath(output_file, OBJ_DIR)
    
    # Convert to DOS paths
    dos_src = rel_source.replace('/', '\\')
    dos_out = rel_output.replace('/', '\\')
    
    # Build DOSBox-X command
    # Mount MSC 5.1 as C:, source as D:, output as E:
    cmd = [
        DOSBOX_X,
        "-c", f"mount c {MSC51_ROOT}",
        "-c", f"mount d {SRC_DIR}",
        "-c", f"mount e {OBJ_DIR}",
        "-c", "d:",
        "-c", f"c:\\cl.exe {flags} d:\\{dos_src} /Foe:\\{dos_out}",
        "-c", "exit"
    ]
    
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

def link_exe(obj_files, output_exe, libs="slibce.lib"):
    """Link object files into EXE"""
    dos_objs = " ".join([f"e:\\{os.path.relpath(f, OBJ_DIR).replace('/', '\\')}" for f in obj_files])
    
    cmd = [
        DOSBOX_X,
        "-c", f"mount c {MSC51_ROOT}",
        "-c", f"mount e {OBJ_DIR}",
        "-c", "e:",
        "-c", f"c:\\link.exe {dos_objs}, {os.path.basename(output_exe)},, {libs}",
        "-c", "exit"
    ]
    
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

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