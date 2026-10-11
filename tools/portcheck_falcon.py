#!/usr/bin/env python3
"""
Portcheck for Falcon3 - compile C routines with MSC 5.1 under DOSBox-X
and verify against original binary bytes (from IDA database with fixups applied).
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import re
from pathlib import Path

# DOSBox-X and MSC 5.1 paths
DOSBOX_X = r"C:\dosbox-x\dosbox-x.exe"
MSC_ROOT = r"C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1"
# Borland C++ 2.0 (finding 22: the ACTUAL C compiler for Falcon's C functions;
# recipe: bcc -c -ml -1 -O  -> enter/leave codegen)
BCC_ROOT = r"C:\Users\yotam\projects\falcon3\dos_compilers\bcc2.0"
BCC_DEFAULT_FLAGS = "-c -ml -1 -O"

# Function bytes from IDA database (with fixups/relocations applied)
FUNCTION_BYTES_PATH = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\function_bytes.json"

# 8.3 filename constraints
def to_83(name: str) -> str:
    """Convert filename to 8.3 format (uppercase, max 8.3)."""
    base, ext = os.path.splitext(name)
    base = base.upper()[:8]
    ext = ext.upper()[:4]
    return base + ext


def run_dosbox(config_path: str, timeout: int = 60) -> tuple[bool, str]:
    """Run DOSBox-X with config and return (success, output)."""
    try:
        result = subprocess.run(
            [DOSBOX_X, "-exit", "-conf", config_path],
            capture_output=True, text=True, timeout=timeout, cwd=os.getcwd()
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def parse_cod_listing(cod_path: str, routine_name: str) -> bytes:
    """Parse MSC /Fc .cod listing to extract routine code bytes."""
    if not os.path.exists(cod_path):
        return b""
    
    with open(cod_path, "r", encoding="cp437", errors="ignore") as f:
        lines = f.readlines()
    
    in_routine = False
    routine_bytes = bytearray()
    
    # MSC prefixes C function names with underscore in .cod listing
    search_name = "_" + routine_name
    
    for line in lines:
        # Match with flexible whitespace: _name PROC or _name\tPROC etc.
        if search_name.upper() in line.upper() and "PROC" in line.upper():
            in_routine = True
            continue
        if in_routine and "ENDP" in line.upper():
            break
        if in_routine:
            # Parse code bytes from MSC /Fc listing format:
            # *** 000000\t9a 00 00 00 00 \t\tcall\tFAR PTR _sub_10bf_02c0
            # Extract hex bytes between offset and double-tab/instruction
            match = re.match(r'\s*\*{3}\s+[0-9a-fA-F]{6}[\t\s]+(.+?)(?:\t{2,}|\s{2,}|$)', line)
            if match:
                hex_bytes = match.group(1).strip().split()
                routine_bytes.extend(bytes(int(b, 16) for b in hex_bytes))
    
    return bytes(routine_bytes)


def to_83_cod(name: str) -> str:
    """Convert routine name to 8.3 .cod filename."""
    base = name.upper()[:8]
    return base + ".COD"


# Load function bytes from IDA database
FUNCTION_BYTES = {}
def load_function_bytes():
    global FUNCTION_BYTES
    if os.path.exists(FUNCTION_BYTES_PATH):
        with open(FUNCTION_BYTES_PATH, "r") as f:
            FUNCTION_BYTES = json.load(f)
        print(f"Loaded {len(FUNCTION_BYTES)} function byte records from IDA database")
    else:
        print(f"Warning: {FUNCTION_BYTES_PATH} not found, falling back to raw EXE")

load_function_bytes()


def get_original_bytes_from_ida(routine_name: str, length: int) -> bytes:
    """Get original bytes from IDA database for a routine."""
    if routine_name in FUNCTION_BYTES:
        data = FUNCTION_BYTES[routine_name]
        if data.get('bytes'):
            hex_bytes = data['bytes']
            return bytes.fromhex(hex_bytes)[:length]
    return None


def get_original_bytes(exe_path: str, segment: int, offset: int, length: int) -> bytes:
    """Extract bytes from original EXE at given IDA segment:offset.
    
    IDA uses segment base 0x1000 for first code segment (seg000).
    Load module starts at header_paras * 16 in the file.
    File offset = load_offset + (segment - 0x1000) * 16 + offset
    """
    with open(exe_path, "rb") as f:
        f.seek(0x08)
        header_paras = int.from_bytes(f.read(2), "little")
        load_offset = header_paras * 16
    
    # IDA segment 0x1000 = first code segment at load module offset 0
    linear_in_module = (segment - 0x1000) * 16 + offset
    file_offset = load_offset + linear_in_module
    
    with open(exe_path, "rb") as f:
        f.seek(file_offset)
        return f.read(length)


def to_83(name: str) -> str:
    """Convert filename to 8.3 format."""
    base, ext = os.path.splitext(name)
    # Truncate base to 8 chars max, ext to 3 chars max
    base = base[:8]
    ext = ext[:4]  # including dot
    return f"{base}{ext}"


def _compile_bcc_extract(routine_name: str, c_source: str, cflags: str):
    """Compile with Borland C++ 2.0 (finding 22 recipe) and extract routine bytes.

    Returns (bytes, fixup_mask_offsets). bcc -c -ml -1 -O <probe\\file.c>
    -> <file>.OBJ; bytes via obj_extract (PUBDEF+LEDATA+FIXUPP).
    fixup offsets = link-time-determined fields (call displacements, far
    pointers) -> masked during comparison (finding 15 normalization).
    """
    from obj_extract import extract_ex

    base83 = to_83(routine_name[:8] + ".c")
    probe = os.path.join(BCC_ROOT, "probe")
    os.makedirs(probe, exist_ok=True)
    src_path = os.path.join(probe, base83)
    with open(src_path, "w", encoding="ascii", errors="replace") as f:
        f.write(c_source)

    obj_stem = os.path.splitext(base83)[0]
    # clean stale objs (case-insensitive)
    for d in (BCC_ROOT, probe):
        for f in os.listdir(d):
            if f.lower().endswith(".obj") and os.path.splitext(f)[0].lower() == obj_stem.lower():
                os.remove(os.path.join(d, f))

    flags = (BCC_DEFAULT_FLAGS + " " + cflags).strip()
    with tempfile.TemporaryDirectory() as tmpdir:
        config_content = f"""[sdl]
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
mount c {BCC_ROOT.replace('\\', '\\\\')}
c:
BIN\\BCC {flags} probe\\{base83} > compile.log 2>&1
exit
"""
        config_path = os.path.join(tmpdir, "dosbox_bcc.conf")
        with open(config_path, "w", encoding="ascii") as f:
            f.write(config_content)
        success, _ = run_dosbox(config_path)

    obj_path = None
    for d in (BCC_ROOT, probe):
        for f in os.listdir(d):
            if f.lower().endswith(".obj") and os.path.splitext(f)[0].lower() == obj_stem.lower():
                obj_path = os.path.join(d, f)
    if not obj_path:
        log = os.path.join(BCC_ROOT, "compile.log")
        if os.path.exists(log):
            print("BCC compile log:")
            print(open(log, encoding="cp437", errors="ignore").read())
        print("BCC: no OBJ produced for", routine_name)
        return b"", []

    try:
        data, fixup_mask = extract_ex(obj_path, routine_name)
    finally:
        os.remove(obj_path)
        if os.path.exists(src_path):
            os.remove(src_path)
        log = os.path.join(BCC_ROOT, "compile.log")
        if os.path.exists(log):
            os.remove(log)
    return data, fixup_mask


def _compare_with_original(routine_name: str, routine_bytes: bytes,
                           segment: int, offset: int, how: str,
                           fixup_mask=()) -> bool:
    ida_hex = get_original_bytes_from_ida(routine_name, 1 << 30)
    if ida_hex is not None:
        expected = ida_hex
        print("  Using IDA database bytes")
    else:
        expected = get_original_bytes("game/FALCONCD.EXE", segment, offset,
                                      len(routine_bytes))
        print("  Using raw EXE bytes (IDA not found)")

    mask = set(fixup_mask)

    def equal(a: bytes, b: bytes) -> tuple:
        """(ok, n_reloc_normalized, first_diff) with mask + +/-0x1000 word logic."""
        norm = 0
        n = min(len(a), len(b))
        i = 0
        while i < n:
            if i in mask:
                i += 1
                continue
            if a[i] != b[i]:
                # MZ/RTLink relocation signature: got + 0x1000 == expected
                if i + 1 < n and (i + 1) not in mask:
                    gw = a[i] | (a[i + 1] << 8)
                    ew = b[i] | (b[i + 1] << 8)
                    if ((gw + 0x1000) & 0xFFFF) == ew:
                        norm += 1
                        i += 2
                        continue
                return False, norm, i
            i += 1
        return True, norm, n

    ok, norm, first = equal(routine_bytes, expected)
    pad = b""
    if (not ok and len(routine_bytes) > len(expected)
            and first >= len(expected)
            and all(b in (0x00, 0x90, 0xCC) for b in routine_bytes[len(expected):])):
        ok, norm, first = equal(routine_bytes[:len(expected)], expected)

    if ok:
        extra = []
        if norm:
            extra.append("%d reloc words (+0x1000)" % norm)
        if mask:
            extra.append("%d fixup bytes masked" % len(mask))
        suffix = (" [" + ", ".join(extra) + "]") if extra else ""
        print(f"OK {routine_name}: MATCH ({len(expected)} bytes, {how}){suffix}")
        return True

    print(f"FAIL {routine_name}: MISMATCH ({how})")
    print(f"  Expected ({len(expected)}): {expected.hex()}")
    print(f"  Got      ({len(routine_bytes)}): {routine_bytes.hex()}")
    n = min(len(expected), len(routine_bytes))
    for i in range(first, n):
        if i in mask:
            continue
        if expected[i] != routine_bytes[i]:
            print(f"  first diff @{i}: expected {expected[i]:02x} got {routine_bytes[i]:02x}")
            print(f"  expected ctx: {expected[max(0, i - 4):i + 8].hex()}")
            print(f"  got ctx:      {routine_bytes[max(0, i - 4):i + 8].hex()}")
            break
    else:
        print("  prefix equal, length differs")
    return False

def verify_routine(routine_name: str, c_source: str,
                   segment: int, offset: int, length: int, src_basename: str,
                   cflags: str = "", cc: str = "bcc") -> bool:
    """Compile C routine and verify against original binary."""
    
    msc_dir = os.path.join(os.getcwd(), r"dos_compilers\msc5.1")
    
    # 8.3 names - .c file named after routine (truncated to 8.3)
    c_83 = to_83(f"{routine_name[:8]}.c")
    # .c file will be truncated to 8.3 when written to MSC dir
    c_83 = to_83(c_83)
    # .cod filename is based on the 8.3 source filename
    cod_base = os.path.splitext(c_83)[0].upper()
    cod_83 = f"{cod_base}.COD"

    if cc == "bcc":
        routine_bytes, fixup_mask = _compile_bcc_extract(routine_name, c_source, cflags)
        if not routine_bytes:
            return False
        return _compare_with_original(routine_name, routine_bytes,
                                      segment, offset, "BCC 2.0",
                                      fixup_mask=fixup_mask)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write C source with 8.3 name in MSC dir
        c_path = os.path.join(msc_dir, c_83)
        with open(c_path, "w", encoding="ascii") as f:
            f.write(c_source)
        
        # Create DOSBox config - use 8.3 .cod filename
        config_content = f"""[sdl]
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
mount c {MSC_ROOT.replace('\\', '\\\\')}
c:
path c:\\rbin;c:\\rbinb
set INCLUDE=c:\\include
set LIB=c:\\lib
set PATH=c:\\rbin;c:\\rbinb
rbin\\cl /c /AL /Gs {cflags} /Fc{cod_83[:-4]} /Ic:\\include {c_83} > compile.log
exit
"""
        config_path = os.path.join(tmpdir, "dosbox_portcheck.conf")
        with open(config_path, "w", encoding="ascii") as f:
            f.write(config_content)
        
        # Run DOSBox
        success, output = run_dosbox(config_path)
        
        if not success:
            print(f"Compile failed for {routine_name}")
            # Check compile.log
            log_path = os.path.join(msc_dir, "compile.log")
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    print(f.read())
            return False
        
        # Parse routine bytes from .cod
        # The .cod file is created in the MSC directory (c: drive)
        cod_path = os.path.join(msc_dir, cod_83)
        routine_bytes = parse_cod_listing(cod_path, routine_name)
        
        if not routine_bytes:
            print(f"Could not extract bytes for {routine_name}")
            return False
        
        actual_length = len(routine_bytes)
        
        # Try IDA database first (relocated bytes), fall back to raw EXE
        original_bytes = get_original_bytes_from_ida(routine_name, actual_length)
        if original_bytes is None:
            original_bytes = get_original_bytes("game/FALCONCD.EXE", segment, offset, actual_length)
            print(f"  Using raw EXE bytes (IDA not found)")
        else:
            print(f"  Using IDA database bytes")
        
        # Cleanup MSC dir
        for fname in [c_83, f"{routine_name[:8]}.OBJ", "compile.log", cod_83]:
            fpath = os.path.join(msc_dir, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
        
        if routine_bytes[:actual_length] == original_bytes:
            print(f"OK {routine_name}: MATCH ({len(routine_bytes)} bytes)")
            return True
        else:
            print(f"FAIL {routine_name}: MISMATCH")
            print(f"  Expected ({len(original_bytes)}): {original_bytes.hex()}")
            print(f"  Got      ({len(routine_bytes)}): {routine_bytes.hex()}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Falcon3 portcheck - verify C routine against original")
    parser.add_argument("routine", help="Routine name")
    parser.add_argument("--source", required=True, help="C source file")
    parser.add_argument("--segment", type=lambda x: int(x, 0), required=True, help="Segment (hex)")
    parser.add_argument("--offset", type=lambda x: int(x, 0), required=True, help="Offset (hex)")
    parser.add_argument("--length", type=lambda x: int(x, 0), help="Length (optional)")
    parser.add_argument("--cflags", default="", help="Extra compiler flags")
    parser.add_argument("--cc", choices=["bcc", "msc"], default="bcc",
                        help="compiler: bcc = Borland C++ 2.0 -c -ml -1 -O (default, finding 22); msc = MSC 5.1 /AL")

    args = parser.parse_args()

    with open(args.source, "r") as f:
        c_source = f.read()

    # Use routine name as the base for 8.3 filenames
    src_basename = args.routine

    length = args.length if args.length else 0

    if args.cflags:
        print(f"cflags: {args.cflags}")
    ok = verify_routine(args.routine, c_source,
                       args.segment, args.offset, length, src_basename,
                       cflags=args.cflags, cc=args.cc)
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()