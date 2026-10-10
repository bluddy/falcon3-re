"""Identify which C runtime library an EXE was linked against.

Parses OMF .LIB archives (Microsoft C format), takes library module code
bytes, and searches the target image for them with a tolerant matcher
(fixups perturb a few bytes).

Usage:
  python tools/libscan.py game/FALCONCD.EXE [libdir]
"""
import sys
from pathlib import Path

from libmf import parse_lib

MSC_LIB_DIR = Path.home() / "projects/gunship_2000/tools/msc6.0/C600/LIB"


def fuzzy_find(img, block, probe=16, step=4, min_score=0.85):
    """Find best alignment of `block` inside `img`, tolerating mismatches."""
    n, m = len(block), len(img)
    best = None
    for s in range(0, n - probe, step):
        p = img.find(block[s:s + probe])
        if p < 0:
            continue
        base = p - s
        if base < 0 or base + n > m:
            continue
        seg = img[base:base + n]
        match = sum(1 for a, b in zip(seg, block) if a == b)
        score = match / n
        if best is None or score > best[0]:
            best = (score, base)
            if score >= min_score:
                return best
    return best


def main(argv):
    exe = Path(argv[1])
    libdir = Path(argv[2]) if len(argv) > 2 else MSC_LIB_DIR
    img = exe.read_bytes()
    print(f"target: {exe} ({len(img)} bytes)")
    for lib in sorted(libdir.glob("*.LIB")):
        mods = parse_lib(lib)
        results = []
        blocks = 0
        for m in mods:
            for seg in m["segs"]:
                data = bytes(seg["data"])
                if len(data) < 64:
                    continue
                blocks += 1
                # use the largest fixup-free-ish slice: whole block
                r = fuzzy_find(img, data)
                if r and r[0] >= 0.90:
                    results.append((r[0], m["name"], r[1]))
        results.sort(reverse=True)
        print(f"  {lib.name}: {len(mods)} modules / {blocks} code blocks, "
              f"{len(results)} >=90% match")
        for score, name, off in results[:15]:
            print(f"      {score*100:5.1f}%  {name:<24} image@{off:#x}")


if __name__ == "__main__":
    main(sys.argv)
