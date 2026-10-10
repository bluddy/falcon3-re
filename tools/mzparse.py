"""Reusable 16-bit MZ parsing + first-instruction disassembly helpers."""
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_16, Cs


class MZ:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        d = self.data
        (self.magic, self.lastpage, self.pages, self.nreloc, self.hdrparas,
         self.minalloc, self.maxalloc, self.ss, self.sp, self.checksum,
         self.ip, self.cs, self.relocoff, self.ovno) = struct.unpack_from(
             "<14H", d, 0)
        self.hdr = self.hdrparas * 16
        if self.lastpage:
            self.imagesize = (self.pages - 1) * 512 + self.lastpage - self.hdr
        else:
            self.imagesize = self.pages * 512 - self.hdr
        self.tail = len(d) - self.hdr - self.imagesize

    @property
    def entry_file_off(self):
        return self.hdr + self.cs * 16 + self.ip

    def file_off(self, seg, off):
        return self.hdr + seg * 16 + off

    def relocs(self, limit=None):
        out = []
        n = self.nreloc if limit is None else min(limit, self.nreloc)
        for i in range(n):
            off, seg = struct.unpack_from("<HH", self.data, self.relocoff + i * 4)
            out.append((off, seg))
        return out

    def summary(self):
        print(f"== {self.path} ({len(self.data)} bytes)")
        print(f"   hdr={self.hdr:#x} nreloc={self.nreloc} @ {self.relocoff:#x} "
              f"table_end={self.relocoff + self.nreloc * 4:#x}")
        print(f"   image={self.imagesize:#x} tail={self.tail:#x} "
              f"minalloc={self.minalloc} maxalloc={self.maxalloc:#x} "
              f"chksum={self.checksum:#x}")
        print(f"   cs:ip={self.cs:#x}:{self.ip:#x} ss:sp={self.ss:#x}:{self.sp:#x} "
              f"ovno={self.ovno}")


def disasm(code, base=0, count=24):
    md = Cs(CS_ARCH_X86, CS_MODE_16)
    md.detail = False
    out = []
    for i, ins in enumerate(md.disasm(code, base)):
        out.append(f"  {ins.address:06x}: {ins.mnemonic:8s} {ins.op_str}")
        if i + 1 >= count:
            break
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        m = MZ(p)
        m.summary()
        print("   entry:")
        print(disasm(m.data[m.entry_file_off:m.entry_file_off + 64],
                     m.entry_file_off))
        print()
