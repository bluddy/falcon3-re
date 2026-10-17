#!/usr/bin/env python3
"""Verify an IDB rebuild reproduced the committed ground truth.

The IDB is not committed, so the ONLY way to know a rebuild is faithful is to
diff the freshly-extracted `function_bytes.json` against the committed copy in
git HEAD (finding 40 audit: `extract_ida_bytes.py` overwrites it unconditionally
with no check, so a rebuild can silently lose ~150 functions).

Reports:
  LOST     key in HEAD but not now  (a function failed to re-register)
  ADDED    key now but not in HEAD  (expected only if new fns were added since)
  CHANGED  same key, different ea/size/bytes  (boundary or fixup drift)
  RENAMED  same ea/bytes, different key

Exit 0 = faithful (no LOST/CHANGED); exit 1 = divergence (do NOT commit).

Usage:  venv\\Scripts\\python tools\\verify_rebuild.py
        (run after: ida steps -> extract_ida_bytes.py)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
# Intentional-change manifest: entries here are allowlisted by exact
# (key, ea, old_size, new_size) so a deliberate bulk re-derivation cannot
# weaken the gate for anything not listed (finding 53).
EXPECTED = ROOT / "registry" / "bitness_fix_expected.json"


def load_expected():
    if not EXPECTED.exists():
        return set()
    m = json.loads(EXPECTED.read_text())
    return {(e["key"], e["ea"], e["old_size"], e["new_size"])
            for e in m.get("overlay_recode", [])}


def head_json():
    r = subprocess.run(["git", "show", "HEAD:analysis/ida_falconcd/function_bytes.json"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print("FATAL: cannot read committed function_bytes.json from git HEAD")
        print(r.stderr[:400])
        sys.exit(2)
    return json.loads(r.stdout)


def main():
    head = head_json()
    now = json.loads(FB.read_text())
    expected = load_expected()

    def is_expected_recode(k, a, b):
        """Allowlisted by the exact old->new size recorded in the manifest."""
        return (a.get("ea") == b.get("ea")
                and (k, a.get("ea"), a.get("size"), b.get("size")) in expected)

    def tile_count(ea, end):
        """How many current functions exactly tile [ea, end)? 0 if not a clean tile."""
        pos, n = ea, 0
        while pos < end and n < 5000:
            f = next((v for v in now.values() if v.get("ea") == pos), None)
            if not f or not f.get("size"):
                return 0
            pos += f["size"]
            n += 1
        return n if pos == end else 0

    def contiguous_chain(ea, end):
        return tile_count(ea, end) > 1

    lost = sorted(set(head) - set(now))
    added = sorted(set(now) - set(head))
    changed, renamed, splits, recodes = [], [], [], []
    for k in set(head) & set(now):
        a, b = head[k], now[k]
        # allowlisted bulk re-derivation (finding 53) -- checked first, and
        # only for an exact (key, ea, old_size, new_size) manifest match
        if is_expected_recode(k, a, b):
            recodes.append((k, "%s -> %s dB (bitness recode)"
                            % (a.get("size"), b.get("size"))))
            continue
        # same ea + same bytes = identity regardless of key spelling
        if a.get("ea") == b.get("ea") and a.get("bytes") == b.get("bytes"):
            if a.get("size") != b.get("size"):
                changed.append((k, "size %s->%s" % (a.get("size"), b.get("size"))))
            continue
        if a.get("ea") != b.get("ea"):
            changed.append((k, "ea %s->%s" % (a.get("ea"), b.get("ea"))))
            continue
        if a.get("bytes") != b.get("bytes"):
            # shrank + the old range is now tiled by new fns = intended split
            if b.get("size", 0) < a.get("size", 0):
                n = tile_count(a["ea"], a["ea"] + a["size"])
                if n > 1:
                    splits.append((k, "%d -> %dB, old range tiled by %d fns"
                                   % (a["size"], b["size"], n)))
                    continue
            if (a.get("size"), b.get("size")) and a.get("bytes") and b.get("bytes"):
                changed.append((k, "bytes differ (len %d->%d)"
                                % (len(a["bytes"]), len(b["bytes"]))))
            else:
                changed.append((k, "bytes missing/added"))
        else:
            renamed.append((k, b.get("ea")))

    print("committed: %d   now: %d" % (len(head), len(now)))
    print("  LOST    : %d" % len(lost))
    print("  ADDED   : %d" % len(added))
    print("  SPLIT   : %d  (intentional: old fn subdivided, full coverage)" % len(splits))
    print("  RECODE  : %d  (intentional: bitness fix, allowlisted in manifest)" % len(recodes))
    print("  CHANGED : %d" % len(changed))
    if recodes:
        print("\n-- RECODE (allowlisted bitness fix; verify the manifest is committed) --")
        for k, why in recodes[:10]:
            print("   %-16s %s" % (k, why))
        if len(recodes) > 10:
            print("   ... +%d" % (len(recodes) - 10))
    if splits:
        print("\n-- SPLIT (expected after a deliberate subdivision; verify it is yours) --")
        for k, why in splits[:20]:
            print("   %-16s %s" % (k, why))
    if lost:
        print("\n-- LOST (function failed to re-register) --")
        for k in lost[:40]:
            print("   %-16s ea=0x%X size=%s" % (k, head[k]["ea"], head[k]["size"]))
        if len(lost) > 40:
            print("   ... +%d" % (len(lost) - 40))
    if changed:
        print("\n-- CHANGED (boundary/byte drift) --")
        for k, why in changed[:40]:
            print("   %-16s %s" % (k, why))
        if len(changed) > 40:
            print("   ... +%d" % (len(changed) - 40))
    if added:
        print("\n-- ADDED (new since HEAD; expected if you registered fns) --")
        for k in added[:20]:
            print("   %-16s ea=0x%X size=%s" % (k, now[k]["ea"], now[k]["size"]))
        if len(added) > 20:
            print("   ... +%d" % (len(added) - 20))

    bad = len(lost) + len(changed)
    if bad:
        print("\nRESULT: DIVERGED (%d problems) — do NOT commit; fix the rebuild step"
              % bad)
        sys.exit(1)
    print("\nRESULT: faithful — matches committed ground truth")
    sys.exit(0)


if __name__ == "__main__":
    main()
