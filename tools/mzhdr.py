"""Dump MZ header fields for a DOS executable."""
import struct
import sys
from pathlib import Path


def dump(path):
    d = Path(path).read_bytes()
    (magic, lastpage, pages, nreloc, hdrparas, minalloc, maxalloc,
     ss, sp, checksum, ip, cs, relocoff, ovno) = struct.unpack_from("<14H", d, 0)
    hdr = hdrparas * 16
    load = len(d) - hdr
    if lastpage:
        load = (pages - 1) * 512 + lastpage - hdr
    print(f"== {path}")
    print(f"   size={len(d)} magic={magic!r} pages={pages} lastpage={lastpage}")
    print(f"   hdr={hdr} relocs={nreloc} @0x{relocoff:x} minalloc={minalloc} "
          f"maxalloc={maxalloc:#x} chksum={checksum:#x}")
    print(f"   cs:ip={cs:#x}:{ip:#x} ss:sp={ss:#x}:{sp:#x} ovno={ovno}")
    print(f"   load image size={load} (file-hdr), tail={len(d)-hdr-load} bytes")
    # first 32 bytes hex
    print("   hdr[0:32]:", d[:32].hex(" "))
    # entry bytes
    entry = hdr + cs * 16 + ip
    if entry < len(d):
        print(f"   entry file off=0x{entry:x}: {d[entry:entry+32].hex(' ')}")
    return d, hdr


if __name__ == "__main__":
    for p in sys.argv[1:]:
        dump(p)
        print()
