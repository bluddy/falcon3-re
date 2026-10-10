"""Compare CRT/overlay-manager startup bytes across executables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mzparse import MZ, disasm  # noqa: E402

GS = Path.home() / "projects/gunship_2000/analysis/GS.exe"


def dump(m, seg, off, n=96):
    fo = m.file_off(seg, off)
    code = m.data[fo:fo + n]
    print(f"  [{m.path.name}] {seg:#x}:{off:#x} file@{fo:#x}")
    print(disasm(code, 0, count=n))
    return code


def main(argv):
    f3 = MZ(argv[1])
    gs = MZ(GS)
    print("== Falcon entry chain (first 160 bytes)")
    print(disasm(f3.data[f3.entry_file_off:f3.entry_file_off + 160],
                 0, count=60))
    print("== GS entry chain (first 160 bytes)")
    print(disasm(gs.data[gs.entry_file_off:gs.entry_file_off + 160],
                 0, count=60))
    print("== GS CRT @00BF:0018")
    dump(gs, 0xBF, 0x18, 96)


if __name__ == "__main__":
    main(sys.argv)
