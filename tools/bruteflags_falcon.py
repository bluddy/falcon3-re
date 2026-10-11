"""Brute-force MSC 5.1 flag combos for a routine until portcheck MATCHes.

Adapted from f19re/mzretools/tools/bruteflags.py (per-file flag sets found there:
/AS /Gs /Os [ /Oa ... ]). Here we vary extra flags over our fixed /c /AL /Gs.

Usage: bruteflags_falcon.py <routine> <source.c> <seg_hex> <ofs_hex> [extra_flag ...]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from portcheck_falcon import verify_routine

STATIC_HINT = "(/AL /Gs always on inside verify_routine)"


def main():
    routine = sys.argv[1]
    source = sys.argv[2]
    seg = int(sys.argv[3], 0)
    ofs = int(sys.argv[4], 0)
    combos = sys.argv[5:] or [""]

    src = open(source).read()
    results = []
    for combo in combos:
        print("=" * 70)
        print("combo: %r  %s" % (combo, STATIC_HINT))
        ok = verify_routine(routine, src, seg, ofs, 0, routine, cflags=combo)
        results.append((combo, ok))
        if ok:
            print("MATCH with flags: %r" % combo)
            return 0
    print("no match; tried:")
    for c, ok in results:
        print("  %r -> %s" % (c, "OK" if ok else "fail"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
