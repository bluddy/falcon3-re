#!/usr/bin/env python3
"""Falcon3 naming/annotation system - rename symbols outside the IDA database.

The ledger (registry/naming.yaml) maps immutable IDA names -> semantic names for
functions/globals/structs/fields. Renames are applied to:
  - src/**.c, src/asm/**.asm          (word-boundary text replace, both directions)
  - function_bytes.json / data_symbols.json  ("name" fields only; keys stay ida)
  - the IDB                            (optional: push-ida, sets names via idat)
The IDB is never the source of truth (binary, fragile, uncommitted).

Usage:
  python tools/naming.py list
  python tools/naming.py resolve <name-or-ida>
  python tools/naming.py apply [--dry-run]
  python tools/naming.py revert <ida_name> [--dry-run]   # drop rename + restore ida text
  python tools/naming.py check                           # consistency report (exit 1 on errors)
  python tools/naming.py push-ida                        # write names into the IDB (headless)

Import API (used by portcheck_falcon and tests):
  load_ledger, resolve, c_name, apply, check, apply_text
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "registry", "naming.yaml")
FUNCTION_BYTES = os.path.join(ROOT, "analysis", "ida_falconcd", "function_bytes.json")
DATA_SYMBOLS = os.path.join(ROOT, "analysis", "ida_falconcd", "data_symbols.json")
ROUTINES_YAML = os.path.join(ROOT, "registry", "routines.yaml")
STRUCTS = os.path.join(ROOT, "registry", "structs.yaml")
SRC_ROOTS = [os.path.join(ROOT, "src")]
TEXT_EXTS = (".c", ".h", ".asm")
IDB = os.path.join(ROOT, "analysis", "ida_falconcd", "FALCONCD.EXE.i64")
IDA = r"C:\Program Files\IDA Professional 9.1\idat.exe"

import yaml

IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
VALID_KINDS = ("function", "global", "struct", "field")


# ---------------------------------------------------------------- ledger I/O
def load_ledger(path=LEDGER):
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict) or "symbols" not in doc:
        raise ValueError("%s: missing 'symbols'" % path)
    return doc


def save_ledger(doc, path=LEDGER):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(doc, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def pairs(doc, forward=True):
    """[(ida, name, kind)] for entries with a decided rename."""
    out = []
    for e in doc.get("symbols", []):
        if e.get("name") and e["name"] != e["ida"]:
            out.append((e["ida"], e["name"], e.get("kind", "function")) if forward
                       else (e["name"], e["ida"], e.get("kind", "function")))
    return out


def resolve(name, doc=None, fb_path=FUNCTION_BYTES):
    """Accept an IDA name or a semantic name -> (ida_name, c_name).

    Unknown names degrade to (name, name) so unregistered routines still work.
    """
    doc = doc if doc is not None else load_ledger()
    for e in doc.get("symbols", []):
        if name == e["ida"]:
            return e["ida"], (e.get("name") or e["ida"])
        if e.get("name") and name == e["name"]:
            return e["ida"], e["name"]
    return name, name


def c_name(ida, doc=None):
    doc = doc if doc is not None else load_ledger()
    for e in doc.get("symbols", []):
        if e["ida"] == ida:
            return e.get("name") or ida
    return ida


# ---------------------------------------------------------------- text apply
def apply_text(text, word_pairs, forward=True):
    """Word-boundary replace [(from, to, ...)] direction-agnostic. Returns (text, n)."""
    n = 0
    for wp in word_pairs:
        a, b = wp[0], wp[1]
        if forward:
            frm, to = a, b
        else:
            frm, to = b, a
        text, k = re.subn(r"\b%s\b" % re.escape(frm), to, text)
        n += k
    return text, n


def _iter_text_files(roots):
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if fn.endswith(TEXT_EXTS):
                    yield os.path.join(dirpath, fn)


# ---------------------------------------------------------------- apply
def apply(doc=None, dry_run=False, fb_path=FUNCTION_BYTES, ds_path=DATA_SYMBOLS,
          roots=None, ida_pairs_only=None):
    """Apply ledger renames to all targets. Returns a summary dict."""
    doc = doc if doc is not None else load_ledger()
    roots = roots if roots is not None else SRC_ROOTS
    fw = pairs(doc, forward=True)
    summary = {"ledger_renames": len(fw), "text_files": 0, "text_hits": 0,
               "fb_fields": 0, "ds_fields": 0, "dry_run": dry_run}

    if not fw:
        return summary

    # 1) JSON name fields (keys stay immutable)
    if os.path.exists(fb_path):
        fb = json.load(open(fb_path, encoding="utf-8"))
        changed = 0
        for ida, sem, _kind in fw:
            if ida in fb and fb[ida].get("name") != sem:
                fb[ida]["name"] = sem
                changed += 1
        summary["fb_fields"] = changed
        if changed and not dry_run:
            json.dump(fb, open(fb_path, "w", encoding="utf-8"), indent=1)

    if os.path.exists(ds_path):
        ds = json.load(open(ds_path, encoding="utf-8"))
        changed = 0
        for e in ds:
            for ida, sem, kind in fw:
                if kind == "global" and e.get("ida_name") == ida and e.get("name") != sem:
                    e["name"] = sem
                    changed += 1
        summary["ds_fields"] = changed
        if changed and not dry_run:
            json.dump(ds, open(ds_path, "w", encoding="utf-8"), indent=1)

    # 2) text files
    for path in _iter_text_files(roots):
        text = open(path, encoding="utf-8", errors="surrogateescape").read()
        new, k = apply_text(text, fw, forward=True)
        if k:
            summary["text_files"] += 1
            summary["text_hits"] += k
            if not dry_run:
                open(path, "w", encoding="utf-8",
                     newline="\n").write(new)
    return summary


def revert(ida_name, doc=None, dry_run=False, fb_path=FUNCTION_BYTES,
           ds_path=DATA_SYMBOLS, roots=None, ledger_path=LEDGER):
    """Drop one rename from the ledger and restore the IDA name in all targets."""
    doc = doc if doc is not None else load_ledger(ledger_path)
    roots = roots if roots is not None else SRC_ROOTS
    entry = next((e for e in doc.get("symbols", []) if e["ida"] == ida_name), None)
    if entry is None:
        raise KeyError("not in ledger: %s" % ida_name)
    sem = entry.get("name")
    if not sem:
        print("%s has no rename; nothing to revert" % ida_name)
        return 0
    one = doc.get("symbols", [])  # operate on full ledger pairs but only this one
    single = {"symbols": [entry]}
    fw = pairs(single, forward=True)

    hits = 0
    if os.path.exists(fb_path):
        fb = json.load(open(fb_path, encoding="utf-8"))
        if ida_name in fb:
            fb[ida_name]["name"] = None
            if not dry_run:
                json.dump(fb, open(fb_path, "w", encoding="utf-8"), indent=1)
    if os.path.exists(ds_path):
        ds = json.load(open(ds_path, encoding="utf-8"))
        for e in ds:
            if e.get("ida_name") == ida_name:
                e["name"] = None
        if not dry_run:
            json.dump(ds, open(ds_path, "w", encoding="utf-8"), indent=1)
    for path in _iter_text_files(roots):
        text = open(path, encoding="utf-8", errors="surrogateescape").read()
        new, k = apply_text(text, fw, forward=False)
        if k:
            hits += k
            if not dry_run:
                open(path, "w", encoding="utf-8", newline="\n").write(new)
    entry["name"] = None
    if not dry_run:
        save_ledger(doc, ledger_path)
    print("reverted %s (text hits: %d)" % (ida_name, hits))
    return hits


# ---------------------------------------------------------------- check
def validate_structs(path=STRUCTS):
    problems = []
    if not os.path.exists(path):
        return ["%s missing" % path]
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    seen = set()
    for st in doc.get("structs", []):
        nm = st.get("name")
        if nm in seen:
            problems.append("struct: duplicate name %s" % nm)
        seen.add(nm)
        size = st.get("size")
        if not isinstance(size, int) or size <= 0:
            problems.append("struct %s: bad size %r" % (nm, size))
            continue
        fnames = set()
        for fld in st.get("fields", []):
            fn = fld.get("name")
            if fn in fnames:
                problems.append("struct %s: duplicate field %s" % (nm, fn))
            fnames.add(fn)
            off, sz = fld.get("offset"), fld.get("size")
            if not isinstance(off, int) or not isinstance(sz, int) or sz <= 0:
                problems.append("struct %s.%s: bad offset/size" % (nm, fn))
            elif off + sz > size:
                problems.append("struct %s.%s: extends past struct (0x%X+0x%X > 0x%X)"
                                % (nm, fn, off, sz, size))
    return problems


def check(doc=None, fb_path=FUNCTION_BYTES, ds_path=DATA_SYMBOLS, roots=None,
          routines=ROUTINES_YAML, structs=STRUCTS):
    """Consistency report: returns list of problem strings (empty = green)."""
    doc = doc if doc is not None else load_ledger()
    roots = roots if roots is not None else SRC_ROOTS
    problems = []
    fb = json.load(open(fb_path, encoding="utf-8")) if os.path.exists(fb_path) else {}
    ds = json.load(open(ds_path, encoding="utf-8")) if os.path.exists(ds_path) else []
    ds_by_ida = {e.get("ida_name"): e for e in ds}

    sem_seen = {}
    for e in doc.get("symbols", []):
        ida, sem, kind = e["ida"], e.get("name"), e.get("kind", "function")
        if kind not in VALID_KINDS:
            problems.append("ledger %s: bad kind %r" % (ida, kind))
        if sem:
            if not IDENT_RE.match(sem):
                problems.append("ledger %s: %r is not a C identifier" % (ida, sem))
            if sem in sem_seen:
                problems.append("ledger: %s and %s both -> %s" % (sem_seen[sem], ida, sem))
            sem_seen[sem] = ida
        # ida target exists
        if kind == "function" and ida not in fb:
            problems.append("ledger %s: not in function_bytes.json" % ida)
        if kind == "global" and ida not in ds_by_ida:
            problems.append("ledger %s: not in data_symbols.json" % ida)
        if kind == "function" and sem:
            if fb.get(ida, {}).get("name") != sem:
                problems.append("function_bytes[%s].name != %r (run apply)" % (ida, sem))
        if kind == "global" and sem:
            if ds_by_ida.get(ida, {}).get("name") != sem:
                problems.append("data_symbols[%s].name != %r (run apply)" % (ida, sem))

    # stale text: source file mentions ida name but not semantic (or vice versa)
    fw = pairs(doc, forward=True)
    for path in _iter_text_files(roots):
        text = open(path, encoding="utf-8", errors="surrogateescape").read()
        for ida, sem, _k in fw:
            has_ida = re.search(r"\b%s\b" % re.escape(ida), text) is not None
            has_sem = re.search(r"\b%s\b" % re.escape(sem), text) is not None
            if has_ida and not has_sem:
                problems.append("%s: still uses %s (run apply)" % (os.path.relpath(path, ROOT), ida))
            if has_sem and has_ida:
                # both present = mixed; allowed only in comments? flag as warning-level problem
                problems.append("%s: mixed %s + %s (check comments)" % (
                    os.path.relpath(path, ROOT), ida, sem))

    # routines.yaml hypothesis sync (read-only)
    if os.path.exists(routines):
        ry = yaml.safe_load(open(routines, encoding="utf-8")) or {}
        for ent in ry.get("routines", []):
            hyp = ent.get("hypothesis")
            ea = ent.get("ea")
            if not hyp:
                continue
            # find ledger entry by ea -> ida
            ida_for_ea = next((k for k, v in fb.items() if v.get("ea") == ea), None)
            led = next((e for e in doc.get("symbols", [])
                        if e["ida"] == ida_for_ea), None) if ida_for_ea else None
            if led and led.get("name") and led["name"] != hyp:
                problems.append("routines.yaml ea=0x%X hypothesis %r != naming %r" % (
                    ea, hyp, led["name"]))

    problems.extend(validate_structs(structs))
    return problems


# ---------------------------------------------------------------- push-ida
_PUSH_TMPL = '''import ida_name, ida_loader, idaapi, traceback
IDB = {idb!r}
pairs = {pairs!r}
log = []
try:
    for ida_name_str, new, _kind in pairs:
        ea = ida_name.get_name_ea(idaapi.BADADDR, ida_name_str)
        if ea == idaapi.BADADDR:
            log.append("MISSING " + ida_name_str)
            continue
        if not ida_name.set_name(ea, new, ida_name.SN_CHECK):
            log.append("FAIL " + ida_name_str + " -> " + new)
        else:
            log.append("OK " + ida_name_str + " -> " + new)
    ida_loader.save_database(IDB, 0)
    log.append("saved")
except Exception:
    log.append(traceback.format_exc())
open({logf!r}, "w").write("\\n".join(log))
idaapi.qexit(0)
'''


def push_ida(doc=None):
    doc = doc if doc is not None else load_ledger()
    fw = pairs(doc, forward=True)
    if not fw:
        print("no renames to push")
        return 0
    logf = os.path.join(tempfile.gettempdir(), "falcon3_pushnames.log")
    script = _PUSH_TMPL.format(idb=IDB, pairs=fw, logf=logf)
    sp = os.path.join(tempfile.gettempdir(), "falcon3_pushnames.py")
    open(sp, "w", encoding="utf-8").write(script)
    r = subprocess.run([IDA, "-A", "-S" + sp, IDB], capture_output=True, text=True,
                       timeout=300)
    print(open(logf, encoding="utf-8", errors="replace").read()
          if os.path.exists(logf) else "no log (ida exit %s)" % r.returncode)
    return r.returncode


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    r = sub.add_parser("resolve")
    r.add_argument("name")
    a = sub.add_parser("apply")
    a.add_argument("--dry-run", action="store_true")
    v = sub.add_parser("revert")
    v.add_argument("ida_name")
    v.add_argument("--dry-run", action="store_true")
    sub.add_parser("check")
    sub.add_parser("push-ida")
    args = ap.parse_args()

    if args.cmd == "list":
        doc = load_ledger()
        for e in doc.get("symbols", []):
            print("%-14s -> %-24s (%s)" % (e["ida"], e.get("name") or "-",
                                           e.get("kind", "function")))
    elif args.cmd == "resolve":
        ida, sem = resolve(args.name)
        print("ida: %s\nc:   %s" % (ida, sem))
    elif args.cmd == "apply":
        s = apply(dry_run=args.dry_run)
        print(json.dumps(s, indent=2))
    elif args.cmd == "revert":
        revert(args.ida_name, dry_run=args.dry_run)
    elif args.cmd == "check":
        problems = check()
        if problems:
            for p in problems:
                print("PROBLEM:", p)
            sys.exit(1)
        print("check OK (%d ledger entries, structs valid)" % len(load_ledger()["symbols"]))
    elif args.cmd == "push-ida":
        sys.exit(push_ida())


if __name__ == "__main__":
    main()
