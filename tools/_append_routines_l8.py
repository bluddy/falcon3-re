"""Append Finding-79 Level-8 (13) entries to registry/routines.yaml,
inserted just before the `counts:` block.  Idempotent (skips ea already
present).  routines.yaml is CRLF -- normalize appended content after write.
"""
import io, json, re, sys

LEDGER = "registry/routines.yaml"
NAMES = "analysis/ida_falconcd/level8_names.json"
FB = "analysis/ida_falconcd/function_bytes.json"

analysis = json.load(open(NAMES, encoding="utf-8"))
fb = json.load(open(FB, encoding="utf-8"))
raw = io.open(LEDGER, encoding="utf-8", newline="").read()

existing_eas = set(int(m, 16) for m in re.findall(r"^  - ea: (0x[0-9A-Fa-f]+)", raw, re.M))

blocks = []
added = 0
for key in sorted(analysis, key=lambda k: analysis[k][0]):
    name, sig, notes, conf = analysis[key]
    v = fb[key]
    ea = v["ea"]
    if ea in existing_eas:
        continue
    seg = ea >> 4
    ofs = ea & 0xF
    far = "true" if v.get("is_far") else "false"
    cls = "ASM"  # class from classification is coarse; use ASM for code leaves
    sig_e = sig.replace(chr(92), chr(92)*2).replace('"', chr(92)*2 + '"')
    notes_e = notes.replace(chr(92), chr(92)*2).replace('"', chr(92)*2 + '"')
    blocks.append(
        "  - ea: 0x%X\n"
        "    seg: 0x%X\n"
        "    ofs: 0x%X\n"
        "    size: %d\n"
        "    far: %s\n"
        "    class: %s\n"
        '    hypothesis: "%s"\n'
        '    sig: "%s"\n'
        "    port_status: unported\n"
        "    verified: null\n"
        '    notes: "%s"\n'
        '    updated: "2026-10-19"\n' %
        (ea, seg, ofs, v["size"], far, cls, name, sig_e, notes_e))
    added += 1

if added == 0:
    print("routines.yaml: all 13 already present")
    sys.exit(0)

marker = "\ncounts:"
i = raw.rindex(marker)
new = raw[:i] + "\n" + "".join(blocks) + raw[i:]
# normalize entire file to CRLF (routines.yaml convention)
new = new.replace("\r\n", "\n").replace("\n", "\r\n")
io.open(LEDGER, "w", encoding="utf-8", newline="").write(new)
print("routines.yaml: inserted %d entries before counts block" % added)
t2 = io.open(LEDGER, encoding="utf-8").read()
n = len(re.findall(r"^  - ea: ", t2, re.M))
print("total entries now: %d" % n)
