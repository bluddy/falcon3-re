p = r"C:\Users\ybarnoy\projects\falcon3\tools\verify_rebuild.py"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
pairs = [
    ('''def load_rebases():''', '''def load_trims():
    """{ea: entry} of registry/orphan_funcs_expected.json "trim_funcs" (finding 137): a function whose tail is
    really data.  Allowlisted only when the new bytes are a prefix of the old and both hashes are as recorded."""
    p = ROOT / "registry" / "orphan_funcs_expected.json"
    if not p.exists():
        return {}
    return {e["ea"]: e for e in json.loads(p.read_text()).get("trim_funcs", [])}


def is_expected_trim(trims, a, b):
    x = trims.get(a.get("ea"))
    if not x or a.get("ea") != b.get("ea"):
        return False
    if (a.get("size"), b.get("size")) != (x["old_end"] - x["ea"], x["end"] - x["ea"]):
        return False
    ab, bb = a.get("bytes") or "", b.get("bytes") or ""
    return ab.startswith(bb) and _sha(bb) == x["kept_sha256"]


def load_rebases():'''),
    ('''    extends = load_extends()
    rebases = load_rebases()''', '''    extends = load_extends()
    trims = load_trims()
    rebases = load_rebases()'''),
    ('''    extended = []
    split_man''', '''    extended = []
    trimmed = []
    split_man'''),
    ('''            # shrank + the old range is now tiled by new fns = intended split''',
     '''            if is_expected_trim(trims, a, b):
                trimmed.append((k, "end trimmed %dB -> %dB, tail is data" % (a["size"], b["size"])))
                continue
            # shrank + the old range is now tiled by new fns = intended split'''),
    ('''    print("  CHANGED : %d" % len(changed))
    for k, why in extended + rebased + removed:''', '''    print("  TRIM    : %d  (intentional: tail of a function is data, kept bytes sha256-pinned)" % len(trimmed))
    print("  CHANGED : %d" % len(changed))
    for k, why in extended + rebased + removed + trimmed:'''),
]
for a, b in pairs:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok")
