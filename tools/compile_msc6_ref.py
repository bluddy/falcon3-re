#!/usr/bin/env python3
"""Compile using MSC 6.0 under kvikdos"""
import subprocess
import sys
import os

KVIKDOS = "/home/yotam/projects/gunship2000-re/tools/f19re/mzretools/tools/emulators/kvikdos/kvikdos"
MSC60_ROOT = "/home/yotam/projects/gunship2000-re/tools/msc6.0/C600"
SRC_DIR = "/home/yotam/projects/gunship2000-re/src"
OBJ_DIR = "/home/yotam/projects/gunship2000-re/obj"

def compile_c(source_file, output_file, flags="/c /Os"):
    """Compile a C file using MSC 6.0 under kvikdos"""
    rel_source = os.path.relpath(source_file, SRC_DIR)
    rel_output = os.path.relpath(output_file, OBJ_DIR)
    
    cmd = [
        KVIKDOS,
        f"--mount=C:{MSC60_ROOT}/",
        f"--mount=D:{SRC_DIR}/",
        f"--mount=E:{OBJ_DIR}/",
        "--cwd-dos=D:\\",
        "--env=INCLUDE=C:\\INCLUDE",
        "--env=LIB=C:\\LIB",
        "--env=PATH=C:\\BIN;C:\\LIB",
        f"{MSC60_ROOT}/BIN/CL.EXE",
        flags,
        f"D:\\{rel_source}",
        f"/FoE:\\{rel_output}"
    ]
    
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: compile_msc6.py <source.c> <output.obj> [flags]")
        sys.exit(1)
    
    source = sys.argv[1]
    output = sys.argv[2]
    flags = sys.argv[3] if len(sys.argv) > 3 else "/c /Os"
    
    success = compile_c(source, output, flags)
    sys.exit(0 if success else 1)
