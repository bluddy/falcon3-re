"""Scan executables for compiler/assembler/linker fingerprints."""
import re
import sys
from pathlib import Path

PATTERNS = [
    # Microsoft C / LINK
    r"Microsoft \(R\)",
    r"Microsoft C",
    r"Microsoft C/C\+\+",
    r"MSC",
    r"Copyright \(C\) 19\d\d Microsoft",
    r"LINK : error",
    r"LINK : warning",
    r"Segment Executable Linker",
    r"Overlay Linker",
    r"CL\.EXE",
    r"C\+\+ 7\.0",
    r"_CHKSTK",
    r"CHKSTK",
    r"__chksstk",
    r"_cinit",
    r"run-time error",
    r"R60\d\d",
    # Borland / Turbo
    r"Borland",
    r"Turbo",
    r"BGI",
    r"CODEVIEW",
    r"CodeView",
    # Watcom
    r"WATCOM",
    r"Open Watcom",
    # Phar Lap / DOS extenders
    r"Phar Lap",
    r"Runtime DOS Extender",
    # Linkers / overlay managers
    r"RTLink",
    r"BLINK",
    r"Bink",
    r"LINK 3\.\d+",
    r"OPTLINK",
    r"OMF",
    # Assemblers
    r"MASM",
    r"Microsoft Macro Assembler",
    r"TASM",
    r"Turbo Assembler",
    r"NASM",
    r"QuickASM",
    r"UASM",
    # Misc CRT / debug
    r"_NULLSEG",
    r"__nmalloc",
    r"_fmalloc",
    r"Borland C\+\+",
    r"ScottFrame",
]

COMPILED = [(re.compile(p.encode(), re.IGNORECASE), p) for p in PATTERNS]


def scan(path: Path, ctx: int = 90):
    data = path.read_bytes()
    hits = {}
    for rx, name in COMPILED:
        for m in rx.finditer(data):
            s = max(0, m.start() - ctx)
            e = min(len(data), m.end() + ctx)
            chunk = data[s:e]
            txt = re.sub(rb"[^\x20-\x7e]", b".", chunk).decode("ascii", "replace")
            hits.setdefault(name, []).append((m.start(), txt))
    return hits


def main(argv):
    paths = [Path(a) for a in argv[1:]] or sorted(Path("game").glob("*.EXE"))
    for p in paths:
        print(f"=== {p} ({p.stat().st_size} bytes)")
        hits = scan(p)
        if not hits:
            print("   (no known fingerprints)")
        for name, occ in hits.items():
            print(f"   [{name}] x{len(occ)}")
            for off, txt in occ[:3]:
                print(f"      @{off:#x}: {txt}")
        print()


if __name__ == "__main__":
    main(sys.argv)
