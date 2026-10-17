"""Correct the overlay_tail_bridge_b registry entry after finding 56's split.

The note claimed "8B of code in a 210B range -- the rest is resident-tail
data/directory". The bytes say otherwise: all 210B are 21 consecutive
10B .RTLink thunks (E8 loader-call + EA jmp-far + rec-id). IDA only merged them
because decode stops at the JMP FAR, so the old note was read off a partial
decode. The function is now one 10B slot (split into 21, exact tile).

CRLF-preserving; idempotent.
"""
import io

NEW_NOTES = (
    'slot #056 of the .RTLink thunk table (10B). The 210B span it used to have '
    'was IDA merging 21 consecutive 10B thunks -- decode stops at the JMP FAR, so '
    'the inner slots never became jmp heads and export_callrefs could not see '
    'them. All 21 are E8 loader-call + EA jmp-far + rec-id stubs, so the old '
    "'rest is resident-tail data/directory' reading was wrong (finding 56). "
    "Split into 21 per-slot functions, exact tile, so each slot exports its own "
    "JMP FAR. conf: high"
)


def sub_block(text, start_marker, lines_around=14):
    i = text.index(start_marker)
    return i


# ---------- naming.yaml (LF) ----------
p = "registry/naming.yaml"
raw = io.open(p, encoding="utf-8", newline="").read()
if "was IDA merging 21 consecutive" in raw:
    print("naming.yaml already updated")
else:
    i = raw.index("- ida: sub_2BFCD")
    j = raw.index("    notes: ", i)
    k = raw.index("\n", j)
    cr = "\r" if raw[j:k].endswith("\r") else ""
    raw = raw[:j] + '    notes: "%s"%s' % (NEW_NOTES, cr) + raw[k:]
    io.open(p, "w", encoding="utf-8", newline="").write(raw)
    print("naming.yaml: notes replaced")

# ---------- routines.yaml (CRLF) ----------
p = "registry/routines.yaml"
raw = io.open(p, encoding="utf-8", newline="").read()
if "was IDA merging 21 consecutive" in raw:
    print("routines.yaml already updated")
else:
    h = raw.index('hypothesis: "overlay_tail_bridge_b"')
    # notes line after the hypothesis
    j = raw.index("    notes: ", h)
    k = raw.index("\n", j)
    cr = "\r" if raw[j:k].endswith("\r") else ""
    raw = raw[:j] + '    notes: "%s"%s' % (NEW_NOTES, cr) + raw[k:]
    # class: DATA -> ASM (this entry now ends in a real jmp)
    lo = raw.rindex("    class: ", 0, h)
    le = raw.index("\n", lo)
    old = raw[lo:le]
    assert old.rstrip("\r\n").strip() == "class: DATA", repr(old)
    raw = raw[:lo] + "    class: ASM" + cr + raw[le:]
    # updated stamp
    u = raw.index('    updated: "', h)
    ue = raw.index("\n", u)
    raw = raw[:u] + '    updated: "2026-10-17"' + cr + raw[ue:]
    io.open(p, "w", encoding="utf-8", newline="").write(raw)
    print("routines.yaml: notes + class + updated replaced")
