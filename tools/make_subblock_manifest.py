"""Build the exact-match manifest for the finding-57 sub-block fixup patches.

`verify_rebuild.py` fails on ANY byte drift (finding 40/53), which is exactly
what we want -- so an intentional bulk patch has to be listed precisely rather
than weaken the gate.  Each entry pins (key, ea, size) plus the sha256 of the
bytes BEFORE and AFTER, so:

  * a rebuild that reproduces the patch matches both hashes -> classed PATCH,
    counts as intentional;
  * a rebuild that lands somewhere else (or patches the wrong word) fails on a
    hash mismatch -> CHANGED, exit 1.

Refuses to write if any function changed its ea/size (that is drift, not patch)
or if a byte change has no attributable fixup.

Usage: venv\\Scripts\\python tools\\make_subblock_manifest.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDA = ROOT / "analysis" / "ida_falconcd"
OUT = ROOT / "registry" / "subblock_fixups_expected.json"


def sha(hexstr):
    if not hexstr:
        return None
    return hashlib.sha256(bytes.fromhex(hexstr)).hexdigest()


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
    now = json.loads((IDA / "function_bytes.json").read_text())

    missing = sorted(set(head) - set(now))
    added = sorted(set(now) - set(head))
    if missing or added:
        print("FATAL: function set differs from HEAD (LOST=%d ADDED=%d) -- run verify_rebuild first"
              % (len(missing), len(added)))
        sys.exit(1)

    # Attribute patched WORDS to every function whose bytes they touch.  A
    # fixup is a 2-byte word at `ea`, which can straddle a boundary (0x3FD81
    # touches sub_3FD82 starting at 0x3FD82), so owner-lookup by ea alone
    # misses exactly those neighbours.  Skip rules mirror apply_overlay_fixups.
    places = {p["idx"]: p for p in json.loads((IDA / "overlay_placement.json").read_text())}
    fixups = {int(k): v for k, v in json.loads((IDA / "fixups_to_apply.json").read_text()).items()}
    eas = []
    for idx, plist in fixups.items():
        p = places.get(idx)
        if not p or p["addr"] == "skip" or not p["ida_len"]:
            continue
        base = p["ida_ea"]
        eas.extend(base + rel for rel, _w in plist)

    spans = sorted((v["ea"], v["ea"] + max(v["size"], 1), k)
                   for k, v in now.items() if v.get("bytes"))

    def touching(ea0, ea1):
        """keys of functions whose byte range intersects [ea0, ea1)."""
        out = []
        for s, e, k in spans:
            if s < ea1 and ea0 < e:
                out.append(k)
            if s >= ea1:
                break
        return out

    per_fn = {}
    for ea in eas:
        for k in touching(ea, ea + 2):
            per_fn[k] = per_fn.get(k, 0) + 1

    entries = []
    ea_changed = []
    unchanged = 0
    for k in sorted(head):
        a, b = head[k], now[k]
        if a.get("ea") != b.get("ea"):
            ea_changed.append("%s ea %s -> %s" % (k, a.get("ea"), b.get("ea")))
            continue
        if a.get("size") != b.get("size"):
            ea_changed.append("%s size %s -> %s (drift, not a byte patch)"
                              % (k, a.get("size"), b.get("size")))
            continue
        if a.get("bytes") == b.get("bytes"):
            unchanged += 1
            continue
        n = per_fn.get(k)
        if not n:
            ea_changed.append("%s bytes changed but intersects no patched word" % k)
            continue
        entries.append({
            "key": k,
            "ea": a["ea"],
            "size": a["size"],
            "n_touching_fixup_eas": n,
            "old_sha256": sha(a.get("bytes")),
            "new_sha256": sha(b.get("bytes")),
        })

    if ea_changed:
        print("FATAL: %d unexpected differences -- fix before writing the manifest"
              % len(ea_changed))
        for e in ea_changed[:20]:
            print("   ", e)
        sys.exit(1)

    manifest = {
        "schema": 1,
        "reason": ("finding 57: RTLink sub-block fixups, abs_off = (seg-w0)*16+off, "
                   "word += 0x1000. Generated from the applied result; each entry "
                   "pins the bytes before AND after so verify_rebuild can allowlist "
                   "EXACTLY this change."),
        "n_entries": len(entries),
        "n_touching_fixup_eas": sum(e["n_touching_fixup_eas"] for e in entries),
        "patches": entries,
    }
    OUT.write_text(json.dumps(manifest, indent=1))
    print("functions unchanged           : %d" % unchanged)
    print("functions patched (manifested): %d" % len(entries))
    print("fixup eas touching a function : %d" % manifest["n_touching_fixup_eas"])
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
