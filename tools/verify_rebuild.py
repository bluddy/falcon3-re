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
import hashlib
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
# Byte-patch manifest (finding 57): sub-block fixup rewrites change words but
# must NOT change ea/size.  Allowlisted only when the before AND after sha256
# both match, so a rebuild that patches the wrong word still fails here.
SUBBLOCK = ROOT / "registry" / "subblock_fixups_expected.json"


def _sha(hexstr):
    if not hexstr:
        return None
    return hashlib.sha256(bytes.fromhex(hexstr)).hexdigest()


def load_expected():
    if not EXPECTED.exists():
        return set()
    m = json.loads(EXPECTED.read_text())
    return {(e["key"], e["ea"], e["old_size"], e["new_size"])
            for e in m.get("overlay_recode", [])}


def load_patches():
    """{(key, ea, size): (old_sha256, new_sha256)} for the allowlisted byte patches."""
    if not SUBBLOCK.exists():
        return {}
    m = json.loads(SUBBLOCK.read_text())
    return {(e["key"], e["ea"], e["size"]): (e["old_sha256"], e["new_sha256"])
            for e in m.get("patches", [])}


# Carve manifest (finding 59): a parent function is subdivided into PLANNED
# functions plus data holes that must stay outside every function and keep
# their recorded sha256.  The live hole bytes come from verify_idb's export
# (data_holes.json), so this gate checks plan <-> live IDB <-> ground truth.
SPLITMAN = ROOT / "registry" / "subblock_split_expected.json"
HOLES_EXPORT = ROOT / "analysis" / "ida_falconcd" / "data_holes.json"


def load_splits():
    if not SPLITMAN.exists():
        return {}
    return {e["key"]: e
            for e in json.loads(SPLITMAN.read_text()).get("splits", [])}


def load_holes():
    if not HOLES_EXPORT.exists():
        return {}
    return {h["ea"]: h for h in json.loads(HOLES_EXPORT.read_text()).get("holes", [])}


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
    patches = load_patches()
    split_man = load_splits()
    hole_live = load_holes()
    split_plan_keys = {f["key"] for e in split_man.values() for f in e["new_fns"]}

    def validate_split(k, a, b):
        """Manifest plan vs current ground truth vs the live hole export.

        `b` is None when the parent key itself disappeared (LOST path).
        Returns (ok, why).
        """
        e = split_man[k]
        want = {(f["key"], f["ea"], f["size"]) for f in e["new_fns"]}
        lo, hi = a["ea"], a["ea"] + e["old_size"]
        have = {(kk, v["ea"], v["size"]) for kk, v in now.items()
                if lo <= (v.get("ea") if v.get("ea") is not None else -1) < hi}
        if want != have:
            return False, ("new_fns mismatch: missing %d %s / extra %d %s"
                           % (len(want - have), sorted(want - have)[:3],
                              len(have - want), sorted(have - want)[:3]))
        carved = bool(have)
        if carved and b is not None and b.get("size", 0) >= a.get("size", 0):
            return False, "parent key did not shrink (%d -> %d)" % (
                a.get("size"), b.get("size"))
        for h in e["data_holes"]:
            for kk, v in now.items():
                s, sz = v.get("ea"), v.get("size")
                if s is None or not sz:
                    continue
                if s < h["ea"] + h["size"] and h["ea"] < s + sz:
                    return False, "function %s overlaps data hole 0x%X..0x%X" % (
                        kk, h["ea"], h["ea"] + h["size"])
            if carved:
                live = hole_live.get(h["ea"])
                if not live:
                    return False, ("no live hole export for 0x%X -- run "
                                   "tools/verify_idb.py first" % h["ea"])
                if (live.get("size"), live.get("sha256")) != (h["size"], h["sha256"]):
                    return False, "hole 0x%X bytes differ: live %s vs manifest %s" % (
                        h["ea"], live.get("sha256"), h["sha256"])
                if live.get("in_function") or not live.get("is_data"):
                    return False, "hole 0x%X in_function=%s is_data=%s (must be free data)" % (
                        h["ea"], live.get("in_function"), live.get("is_data"))
        return True, ("%d planned fns + %d data holes tile 0x%X..0x%X (%d B)"
                      % (len(want), len(e["data_holes"]), lo, hi, e["old_size"]))

    def is_expected_recode(k, a, b):
        """Allowlisted by the exact old->new size recorded in the manifest."""
        return (a.get("ea") == b.get("ea")
                and (k, a.get("ea"), a.get("size"), b.get("size")) in expected)

    def is_expected_patch(k, a, b):
        """Exact-match byte patch: same (key, ea, size), before+after sha256."""
        if a.get("ea") != b.get("ea") or a.get("size") != b.get("size"):
            return False
        want = patches.get((k, a.get("ea"), a.get("size")))
        if not want:
            return False
        return (_sha(a.get("bytes")), _sha(b.get("bytes"))) == want

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
    changed, renamed, splits, recodes, bytepatches, splitdata = [], [], [], [], [], []
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
            # exact-match word patch (finding 57): boundaries identical, both
            # hashes exactly as recorded -- counts as intentional, not drift
            if is_expected_patch(k, a, b):
                bytepatches.append((k, "bytes patched in place (sub-block fixups)"))
                continue
            # shrank + the old range is now tiled by new fns = intended split
            if b.get("size", 0) < a.get("size", 0):
                # finding 59: a manifest-planned carve, with data holes, is
                # accepted ONLY on an exact (key, ea, size) match of every
                # planned function plus verified live sha256 on every hole
                if k in split_man:
                    ok, why = validate_split(k, a, b)
                    if ok:
                        splitdata.append((k, why))
                    else:
                        changed.append((k, "carve manifest violated: " + why))
                    continue
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

    # a manifest parent may legitimately retire outright (its key disappears
    # because every byte moved into a planned child)
    for k in list(lost):
        if k not in split_man:
            continue
        ok, why = validate_split(k, head[k], None)
        if ok:
            lost.remove(k)
            splitdata.append((k, why + "  [parent key retired]"))

    added_split = [k for k in added if k in split_plan_keys]
    added_free = [k for k in added if k not in split_plan_keys]

    print("committed: %d   now: %d" % (len(head), len(now)))
    print("  LOST    : %d" % len(lost))
    print("  ADDED   : %d  (%d planned by the carve manifest, %d new otherwise)"
          % (len(added), len(added_split), len(added_free)))
    print("  SPLIT   : %d  (intentional: old fn subdivided, full coverage)" % len(splits))
    print("  CARVE   : %d  (intentional: manifest-planned fns + sha256-pinned data holes)"
          % len(splitdata))
    print("  RECODE  : %d  (intentional: bitness fix, allowlisted in manifest)" % len(recodes))
    print("  PATCH   : %d  (intentional: sub-block fixup words, exact sha match)"
          % len(bytepatches))
    print("  CHANGED : %d" % len(changed))
    if bytepatches:
        print("\n-- PATCH (allowlisted byte patch; verify the manifest is committed) --")
        for k, why in bytepatches[:10]:
            print("   %-16s %s" % (k, why))
        if len(bytepatches) > 10:
            print("   ... +%d" % (len(bytepatches) - 10))
    if recodes:
        print("\n-- RECODE (allowlisted bitness fix; verify the manifest is committed) --")
        for k, why in recodes[:10]:
            print("   %-16s %s" % (k, why))
        if len(recodes) > 10:
            print("   ... +%d" % (len(recodes) - 10))
    if splitdata:
        print("\n-- CARVE (manifest-planned subdivision; data holes checked "
              "against the live IDB export) --")
        for k, why in splitdata:
            print("   %-16s %s" % (k, why))
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
