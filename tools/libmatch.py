"""Compare executable strings against known compiler runtime libraries.

Usage: python tools/libmatch.py <exe> [<exe> ...]
Reads MSC 6.0 libs from ../gunship_2000/tools/msc6.0/C600/LIB (read-only).
"""
import re
import sys
import zlib
from pathlib import Path

MSC_LIB_DIR = Path.home() / "projects/gunship_2000/tools/msc6.0/C600/LIB"
MIN_LEN = 10


def strings(data, min_len=MIN_LEN):
    out = set()
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % min_len, data):
        out.add(m.group())
    return out


def load_omf_strings(path):
    """Walk OMF records in a .LIB and collect printable strings (also raw file)."""
    data = path.read_bytes()
    s = strings(data, 8)
    # OMF modules are not compressed; raw scan is enough
    return s


def main(argv):
    lib_strings = {}
    for lib in sorted(MSC_LIB_DIR.glob("*.LIB")):
        lib_strings[lib.name] = load_omf_strings(lib)
    # union
    all_lib = {}
    for name, ss in lib_strings.items():
        for s in ss:
            all_lib.setdefault(s, []).append(name)

    for exe in argv[1:]:
        data = Path(exe).read_bytes()
        ex = strings(data, 8)
        print(f"=== {exe}")
        # per-lib hit counts
        counts = {}
        examples = {}
        for s in ex:
            for lib in all_lib.get(s, ()):
                counts[lib] = counts.get(lib, 0) + 1
                examples.setdefault(lib, []).append(s)
        for lib, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"   {lib}: {n} shared strings")
            for s in sorted(examples[lib], key=len, reverse=True)[:8]:
                print(f"      {s.decode('ascii')}")
        # Borland markers
        for probe in [b"Abnormal program termination", b"Borland", b"Turbo",
                      b"Copyright (C) 1991 Borland", b"BGI", b"Microsoft",
                      b"Microsoft (R)", b"Microsoft C", b"floating point"]:
            if probe.lower() in data.lower():
                i = data.lower().find(probe.lower())
                print(f"   PROBE {probe!r} @{i:#x}: "
                      f"{re.sub(rb'[^\\x20-\\x7e]', b'.', data[max(0,i-60):i+90]).decode()}")
        print()


if __name__ == "__main__":
    main(sys.argv)
