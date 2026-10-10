import re
import sys
from pathlib import Path

pats = [
    b"Microsoft", b"Copyright", b"copyright", b"Version 6", b"Version 7",
    b"6.00", b"7.00", b"5.10", b"8.00", b"CLIB", b"MLIB", b"SLIB",
    b".LIB", b"run-time", b"R600", b"R601", b"CHKSTK", b"chksstk",
    b"Borland", b"Turbo", b"Overlay", b"overlay", b"FALCON", b"GLE",
    b"MicroProse", b"Spectrum", b"Overlay Manager", b"RTLink",
    b"overlay", b"Cd", b"CD-ROM", b"MSCDEX",
]

for f in sys.argv[1:] or ["game/FALCONCD.EXE", "game/HORNETCD.EXE", "game/MIGCD.EXE"]:
    data = Path(f).read_bytes()
    print("==", f, len(data))
    for p in pats:
        hits = [m.start() for m in re.finditer(re.escape(p), data)]
        if hits:
            print(f"  {p!r}: {len(hits)} hits, first @{hits[0]:#x}")
            for off in hits[:4]:
                s = max(0, off - 60)
                e = min(len(data), off + 80)
                print("     ", re.sub(rb"[^\x20-\x7e]", b".", data[s:e]).decode())
    print()
